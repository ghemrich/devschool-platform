#!/bin/bash
# =============================================================================
# OpenSchool Platform — Unified Maintenance Script
# Usage: ./scripts/maintenance.sh <command>
#
# Commands:
#   backup          Create a database backup
#   health          Check all services health
#   disk            Check disk and Docker usage
#   docker-cleanup  Remove unused Docker resources
#   ssl-check       Check SSL certificate expiry
#   security-audit  Run pip-audit inside the backend container
#   log-errors      Scan recent logs for errors
#   db-status       Show database stats (connections, table sizes)
#   full-daily      Run all daily tasks
#   full-weekly     Run all weekly tasks
#   full-monthly    Run all monthly tasks
# =============================================================================
set -euo pipefail

# --- Configuration -----------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${COMPOSE_FILE:-$PROJECT_DIR/docker-compose.prod.yml}"
COMPOSE="docker compose -f $COMPOSE_FILE"
BACKUP_DIR="${BACKUP_DIR:-/opt/openschool/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
SSL_DOMAIN="${SSL_DOMAIN:-}"
SSL_WARNING_DAYS="${SSL_WARNING_DAYS:-30}"
NOTIFY_EMAIL="${NOTIFY_EMAIL:-}"
DISCORD_WEBHOOK_URL="${DISCORD_WEBHOOK_URL:-}"
LOG_FILE="${LOG_FILE:-/var/log/openschool-maintenance.log}"

# --- Colors (disabled if not a terminal) --------------------------------------
if [ -t 1 ]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; NC=''
fi

# --- Helpers ------------------------------------------------------------------
log()  { echo -e "$(date '+%Y-%m-%d %H:%M:%S') [INFO]  $*" | tee -a "$LOG_FILE"; }
warn() { echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${YELLOW}[WARN]${NC}  $*" | tee -a "$LOG_FILE"; }
err()  { echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE" >&2; }
ok()   { echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${GREEN}[OK]${NC}    $*" | tee -a "$LOG_FILE"; }

notify() {
    local subject="$1" body="$2"
    if [ -n "$NOTIFY_EMAIL" ] && command -v mail &>/dev/null; then
        echo "$body" | mail -s "[OpenSchool] $subject" "$NOTIFY_EMAIL"
    fi
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        local discord_body
        discord_body=$(printf '%s' "$body" | head -c 1500)
        curl -sf -X POST "$DISCORD_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{\"content\": \"**[OpenSchool] $subject**\n\`\`\`\n$discord_body\n\`\`\`\"}" \
            >/dev/null 2>&1 || true
    fi
}

ensure_dir() { mkdir -p "$1"; }
ensure_dir "$BACKUP_DIR"

# --- Commands -----------------------------------------------------------------

cmd_backup() {
    log "Starting database backup..."
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/db_${timestamp}.sql.gz"

    if ! $COMPOSE exec -T db pg_isready -U "$DB_USER" -d "$DB_NAME" &>/dev/null; then
        err "Database is not ready — aborting backup"
        notify "Backup FAILED" "Database is not reachable."
        return 1
    fi

    $COMPOSE exec -T db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$backup_file"

    local size
    size=$(du -h "$backup_file" | cut -f1)
    ok "Backup created: $backup_file ($size)"

    # Retention cleanup
    local deleted
    deleted=$(find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +"$BACKUP_RETENTION_DAYS" -print -delete | wc -l)
    if [ "$deleted" -gt 0 ]; then
        log "Removed $deleted backup(s) older than $BACKUP_RETENTION_DAYS days"
    fi
}

cmd_health() {
    log "Checking service health..."
    local all_ok=true

    # Container status
    local containers
    containers=$($COMPOSE ps --format '{{.Name}} {{.Status}}' 2>/dev/null || true)
    if [ -z "$containers" ]; then
        err "No containers found — are services running?"
        return 1
    fi

    while IFS= read -r line; do
        local name status
        name=$(echo "$line" | awk '{print $1}')
        status=$(echo "$line" | cut -d' ' -f2-)
        if echo "$status" | grep -qi "up"; then
            ok "Container $name: $status"
        else
            err "Container $name: $status"
            all_ok=false
        fi
    done <<< "$containers"

    # Backend /health endpoint
    if curl -sf http://localhost:8000/health &>/dev/null; then
        ok "Backend /health: responding"
    else
        err "Backend /health: NOT responding"
        all_ok=false
    fi

    # Database connectivity
    if $COMPOSE exec -T db pg_isready -U "${DB_USER:-openschool}" &>/dev/null; then
        ok "PostgreSQL: ready"
    else
        err "PostgreSQL: NOT ready"
        all_ok=false
    fi

    if [ "$all_ok" = false ]; then
        notify "Health Check FAILED" "One or more services are unhealthy. Check logs."
        return 1
    fi
    ok "All services healthy"
}

cmd_disk() {
    log "Checking disk usage..."

    echo ""
    echo "=== Filesystem ==="
    df -h / | tail -1 | awk '{printf "  Used: %s / %s (%s)\n", $3, $2, $5}'

    local usage_pct
    usage_pct=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
    if [ "$usage_pct" -ge 90 ]; then
        err "Disk usage is critical: ${usage_pct}%!"
        notify "Disk CRITICAL" "Disk usage at ${usage_pct}%"
    elif [ "$usage_pct" -ge 80 ]; then
        warn "Disk usage is high: ${usage_pct}%"
    else
        ok "Disk usage: ${usage_pct}%"
    fi

    echo ""
    echo "=== Docker Disk Usage ==="
    docker system df 2>/dev/null || warn "Cannot read Docker disk usage"

    echo ""
    echo "=== Backup Directory ==="
    local backup_count backup_size
    backup_count=$(find "$BACKUP_DIR" -name "db_*.sql.gz" 2>/dev/null | wc -l)
    backup_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo "N/A")
    echo "  Backups: $backup_count files, $backup_size total"
}

cmd_docker_cleanup() {
    log "Cleaning up Docker resources..."

    echo "=== Removing dangling images ==="
    docker image prune -f 2>/dev/null || true

    echo ""
    echo "=== Removing images older than 30 days ==="
    docker image prune -a --filter "until=720h" -f 2>/dev/null || true

    echo ""
    echo "=== Removing unused build cache ==="
    docker builder prune -f --filter "until=720h" 2>/dev/null || true

    echo ""
    echo "=== Docker usage after cleanup ==="
    docker system df 2>/dev/null || true

    ok "Docker cleanup complete"
}

cmd_ssl_check() {
    if [ -z "$SSL_DOMAIN" ]; then
        warn "SSL_DOMAIN not set — skipping SSL check"
        echo "  Set SSL_DOMAIN environment variable or in /etc/openschool-maintenance.conf"
        return 0
    fi

    log "Checking SSL certificate for $SSL_DOMAIN..."

    local expiry_date expiry_epoch now_epoch days_left
    expiry_date=$(echo | openssl s_client -servername "$SSL_DOMAIN" -connect "$SSL_DOMAIN:443" 2>/dev/null \
        | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)

    if [ -z "$expiry_date" ]; then
        err "Could not retrieve SSL certificate for $SSL_DOMAIN"
        notify "SSL Check FAILED" "Cannot retrieve cert for $SSL_DOMAIN"
        return 1
    fi

    expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null)
    now_epoch=$(date +%s)
    days_left=$(( (expiry_epoch - now_epoch) / 86400 ))

    if [ "$days_left" -le 0 ]; then
        err "SSL certificate EXPIRED for $SSL_DOMAIN!"
        notify "SSL EXPIRED" "Certificate for $SSL_DOMAIN has expired!"
    elif [ "$days_left" -le "$SSL_WARNING_DAYS" ]; then
        warn "SSL certificate expires in $days_left days ($expiry_date)"
        notify "SSL Expiring Soon" "Certificate for $SSL_DOMAIN expires in $days_left days."
    else
        ok "SSL certificate valid for $days_left more days (expires: $expiry_date)"
    fi
}

cmd_security_audit() {
    log "Running security audit..."

    echo "=== pip-audit ==="
    if $COMPOSE exec -T backend pip-audit 2>/dev/null; then
        ok "pip-audit: no vulnerabilities found"
    else
        warn "pip-audit found issues or is not installed"
        echo "  Install with: docker compose exec backend pip install pip-audit"
    fi
}

cmd_log_errors() {
    log "Scanning logs for errors (last 500 lines)..."

    echo ""
    echo "=== Backend Errors ==="
    local backend_errors
    backend_errors=$($COMPOSE logs --tail=500 backend 2>/dev/null | grep -ci "error\|exception\|traceback\|critical" || true)
    if [ "$backend_errors" -gt 0 ]; then
        warn "Found $backend_errors error line(s) in backend logs"
        echo "  Recent errors:"
        $COMPOSE logs --tail=500 backend 2>/dev/null | grep -i "error\|exception\|traceback\|critical" | tail -10
    else
        ok "No errors in recent backend logs"
    fi

    echo ""
    echo "=== Nginx Errors ==="
    local nginx_errors
    nginx_errors=$($COMPOSE logs --tail=500 nginx 2>/dev/null | grep -ci "error\|warn" || true)
    if [ "$nginx_errors" -gt 0 ]; then
        warn "Found $nginx_errors error/warning line(s) in nginx logs"
        $COMPOSE logs --tail=500 nginx 2>/dev/null | grep -i "error\|warn" | tail -5
    else
        ok "No errors in recent nginx logs"
    fi
}

cmd_db_status() {
    log "Checking database status..."

    echo ""
    echo "=== Active Connections ==="
    $COMPOSE exec -T db psql -U "${DB_USER:-openschool}" -d "${DB_NAME:-openschool}" \
        -c "SELECT count(*) AS active_connections FROM pg_stat_activity;" 2>/dev/null || err "Cannot query DB"

    echo ""
    echo "=== Table Sizes ==="
    $COMPOSE exec -T db psql -U "${DB_USER:-openschool}" -d "${DB_NAME:-openschool}" \
        -c "SELECT relname AS table, pg_size_pretty(pg_total_relation_size(relid)) AS size
            FROM pg_catalog.pg_statio_user_tables
            ORDER BY pg_total_relation_size(relid) DESC
            LIMIT 20;" 2>/dev/null || err "Cannot query DB"

    echo ""
    echo "=== Current Migration ==="
    $COMPOSE exec -T backend alembic current 2>/dev/null || warn "Cannot check alembic version"
}

# --- Composite Commands -------------------------------------------------------

cmd_full_daily() {
    log "========== DAILY MAINTENANCE START =========="
    cmd_health
    cmd_backup
    cmd_log_errors
    log "========== DAILY MAINTENANCE COMPLETE =========="
}

cmd_full_weekly() {
    log "========== WEEKLY MAINTENANCE START =========="
    cmd_health
    cmd_backup
    cmd_disk
    cmd_docker_cleanup
    cmd_db_status
    log "========== WEEKLY MAINTENANCE COMPLETE =========="
}

cmd_full_monthly() {
    log "========== MONTHLY MAINTENANCE START =========="
    cmd_health
    cmd_backup
    cmd_disk
    cmd_docker_cleanup
    cmd_ssl_check
    cmd_security_audit
    cmd_db_status
    cmd_log_errors
    log "========== MONTHLY MAINTENANCE COMPLETE =========="
}

# --- Main ---------------------------------------------------------------------

# Load config file if exists
if [ -f /etc/openschool-maintenance.conf ]; then
    # shellcheck source=/dev/null
    source /etc/openschool-maintenance.conf
fi

# Load .env.prod for DB credentials if available
if [ -f "$PROJECT_DIR/.env.prod" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$PROJECT_DIR/.env.prod"
    set +a
elif [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck source=/dev/null
    source "$PROJECT_DIR/.env"
    set +a
fi

usage() {
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  backup          Create a database backup"
    echo "  health          Check all services health"
    echo "  disk            Check disk and Docker usage"
    echo "  docker-cleanup  Remove unused Docker resources"
    echo "  ssl-check       Check SSL certificate expiry"
    echo "  security-audit  Run pip-audit inside backend container"
    echo "  log-errors      Scan recent logs for errors"
    echo "  db-status       Show database stats"
    echo "  full-daily      Run all daily tasks (health + backup + log scan)"
    echo "  full-weekly     Run all weekly tasks (daily + disk + cleanup + db)"
    echo "  full-monthly    Run all monthly tasks (weekly + ssl + security)"
    echo ""
}

case "${1:-}" in
    backup)          cmd_backup ;;
    health)          cmd_health ;;
    disk)            cmd_disk ;;
    docker-cleanup)  cmd_docker_cleanup ;;
    ssl-check)       cmd_ssl_check ;;
    security-audit)  cmd_security_audit ;;
    log-errors)      cmd_log_errors ;;
    db-status)       cmd_db_status ;;
    full-daily)      cmd_full_daily ;;
    full-weekly)     cmd_full_weekly ;;
    full-monthly)    cmd_full_monthly ;;
    -h|--help|help)  usage ;;
    *)
        err "Unknown command: ${1:-<none>}"
        usage
        exit 1
        ;;
esac
