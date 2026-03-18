#!/bin/bash
# =============================================================================
# OpenSchool Platform — VPS Bootstrap Script
# Sets up a fresh Ubuntu/Debian VPS for production deployment.
#
# Usage (run on a fresh VPS as root):
#   curl -fsSL https://raw.githubusercontent.com/ghemrich/openschool-platform/main/scripts/bootstrap-vps.sh | bash
#   # or:
#   sudo ./scripts/bootstrap-vps.sh
#
# What it does:
#   1. Installs Docker + Docker Compose
#   2. Configures firewall (UFW)
#   3. Creates deploy user and project directory
#   4. Clones the repository
#   5. Generates .env.prod with strong secrets
#   6. Starts all services
#   7. Runs database migrations + optional seed data
#   8. Sets up SSL with Let's Encrypt (interactive)
#   9. Runs provisioning (cron, backups, etc.)
#  10. Runs security checklist
# =============================================================================
set -euo pipefail

# --- Configuration -----------------------------------------------------------
REPO_URL="${REPO_URL:-git@github.com:ghemrich/openschool-platform.git}"
PROJECT_DIR="${PROJECT_DIR:-/opt/openschool}"
DEPLOY_USER="${DEPLOY_USER:-}"

# --- Colors -------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

log()  { echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} $*"; }
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
err()  { echo -e "${RED}✗${NC} $*" >&2; }

prompt() {
    local var="$1" msg="$2" default="${3:-}"
    local input
    if [ -n "$default" ]; then
        read -r -p "$msg [$default]: " input
        printf -v "$var" '%s' "${input:-$default}"
    else
        read -r -p "$msg: " input
        printf -v "$var" '%s' "$input"
    fi
}

# --- Sanity checks ------------------------------------------------------------
if [ "$(id -u)" -ne 0 ]; then
    err "This script must be run as root (sudo)."
    exit 1
fi

echo ""
echo "========================================"
echo " OpenSchool Platform — VPS Bootstrap"
echo "========================================"
echo ""

# --- Gather info interactively ------------------------------------------------
if [ -z "$DEPLOY_USER" ]; then
    prompt DEPLOY_USER "Deploy user (will be created if needed)" "openschool"
fi

prompt DOMAIN "Your domain (e.g. yourdomain.com)" ""
prompt SETUP_SSL "Set up SSL with Let's Encrypt? (y/n)" "y"
prompt LOAD_SEED "Load initial course data? (y/n)" "y"

prompt GH_CLIENT_ID "GitHub OAuth Client ID" ""
prompt GH_CLIENT_SECRET "GitHub OAuth Client Secret" ""

echo ""
log "Starting setup for $DOMAIN with user $DEPLOY_USER..."
echo ""

# =============================================================================
# 1. System packages
# =============================================================================
log "[1/10] Installing system packages..."

apt-get update -qq
apt-get install -y -qq curl git ufw > /dev/null 2>&1

ok "System packages installed"

# =============================================================================
# 2. Docker
# =============================================================================
log "[2/10] Installing Docker..."

if command -v docker &>/dev/null; then
    ok "Docker already installed: $(docker --version)"
else
    curl -fsSL https://get.docker.com | sh > /dev/null 2>&1
    ok "Docker installed: $(docker --version)"
fi

if ! docker compose version &>/dev/null; then
    apt-get install -y -qq docker-compose-plugin > /dev/null 2>&1
fi
ok "Docker Compose: $(docker compose version --short)"

# =============================================================================
# 3. Deploy user
# =============================================================================
log "[3/10] Setting up deploy user '$DEPLOY_USER'..."

if id "$DEPLOY_USER" &>/dev/null; then
    ok "User '$DEPLOY_USER' already exists"
else
    useradd -m -s /bin/bash "$DEPLOY_USER"
    ok "User '$DEPLOY_USER' created"
fi

usermod -aG docker "$DEPLOY_USER"
ok "User added to docker group"

# =============================================================================
# 4. Firewall
# =============================================================================
log "[4/10] Configuring firewall (UFW)..."

ufw --force reset > /dev/null 2>&1
ufw default deny incoming > /dev/null 2>&1
ufw default allow outgoing > /dev/null 2>&1
ufw allow ssh > /dev/null 2>&1
ufw allow 80/tcp > /dev/null 2>&1
ufw allow 443/tcp > /dev/null 2>&1
ufw --force enable > /dev/null 2>&1

ok "Firewall configured: SSH (22), HTTP (80), HTTPS (443) open"
warn "PostgreSQL (5432) is NOT exposed externally"

# --- SSH hardening ------------------------------------------------------------
log "Hardening SSH (disabling password authentication)..."

sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?KbdInteractiveAuthentication.*/KbdInteractiveAuthentication no/' /etc/ssh/sshd_config

if [ -f /root/.ssh/authorized_keys ] && [ -s /root/.ssh/authorized_keys ]; then
    systemctl restart sshd
    ok "SSH password authentication disabled (key-only access)"
else
    warn "No SSH authorized_keys found — skipping SSH hardening to avoid lockout"
    warn "Run 'ssh-copy-id root@VPS_IP' from your local machine first, then re-run this section"
fi

# =============================================================================
# 5. Clone repository
# =============================================================================
log "[5/10] Cloning repository..."

mkdir -p "$PROJECT_DIR"

if [ -d "$PROJECT_DIR/.git" ]; then
    ok "Repository already cloned at $PROJECT_DIR"
    cd "$PROJECT_DIR"
    git pull origin main
else
    git clone "$REPO_URL" "$PROJECT_DIR"
    ok "Cloned to $PROJECT_DIR"
fi

chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$PROJECT_DIR"
cd "$PROJECT_DIR"

# =============================================================================
# 6. Generate .env.prod
# =============================================================================
log "[6/10] Generating .env.prod with strong secrets..."

DB_PASS=$(openssl rand -base64 24)
SECRET=$(openssl rand -hex 32)
WEBHOOK_SECRET=$(openssl rand -hex 20)

if [ -f "$PROJECT_DIR/.env.prod" ]; then
    warn ".env.prod already exists — creating .env.prod.new instead"
    ENV_FILE="$PROJECT_DIR/.env.prod.new"
else
    ENV_FILE="$PROJECT_DIR/.env.prod"
fi

cat > "$ENV_FILE" << EOF
# Generated by bootstrap-vps.sh on $(date '+%Y-%m-%d %H:%M:%S')
# === DATABASE ===
DB_USER=openschool
DB_PASSWORD=$DB_PASS
DB_NAME=openschool
DATABASE_URL=postgresql://openschool:${DB_PASS}@db:5432/openschool

# === SECURITY ===
SECRET_KEY=$SECRET

# === APPLICATION ===
BASE_URL=https://$DOMAIN
ENVIRONMENT=production
ALLOWED_ORIGINS=https://$DOMAIN

# === GITHUB OAUTH ===
GITHUB_CLIENT_ID=$GH_CLIENT_ID
GITHUB_CLIENT_SECRET=$GH_CLIENT_SECRET
GITHUB_WEBHOOK_SECRET=$WEBHOOK_SECRET

# === NGINX DOMAINS (envsubst template) ===
PROD_DOMAIN=$DOMAIN
STAGING_DOMAIN=staging.$DOMAIN
EOF

chmod 600 "$ENV_FILE"
chown "$DEPLOY_USER":"$DEPLOY_USER" "$ENV_FILE"
ok "Generated $ENV_FILE (permissions: 600)"

# Use the generated env file
if [ "$ENV_FILE" = "$PROJECT_DIR/.env.prod" ]; then
    # Also create a .env symlink for docker-compose.yml compatibility
    ln -sf .env.prod "$PROJECT_DIR/.env" 2>/dev/null || true
fi

# =============================================================================
# 7. Start services
# =============================================================================
log "[7/10] Starting services..."

cd "$PROJECT_DIR"
sudo -u "$DEPLOY_USER" docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" up --build -d

# Wait for DB to be ready
log "Waiting for database..."
for i in $(seq 1 30); do
    if sudo -u "$DEPLOY_USER" docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" exec -T db pg_isready -U openschool &>/dev/null; then
        ok "Database ready"
        break
    fi
    if [ "$i" -eq 30 ]; then
        err "Database did not become ready in 30 seconds"
        exit 1
    fi
    sleep 1
done

# =============================================================================
# 8. Migrations + seed data
# =============================================================================
log "[8/10] Running database migrations..."

sudo -u "$DEPLOY_USER" docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" \
    exec -T backend alembic upgrade head
ok "Migrations complete"

if [ "$LOAD_SEED" = "y" ] || [ "$LOAD_SEED" = "Y" ]; then
    log "Loading seed data..."
    sudo -u "$DEPLOY_USER" docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" \
        exec -T db psql -U openschool -d openschool << 'SQL'
INSERT INTO courses (name, description) VALUES
  ('Python Alapok', '13 hetes bevezető kurzus a Python programozásba.'),
  ('Backend FastAPI', '25 hetes backend fejlesztő kurzus FastAPI keretrendszerrel.'),
  ('Projekt Labor', 'A OpenSchool platform felépítése az alapoktól az éles üzemig.')
ON CONFLICT DO NOTHING;
SQL
    ok "Seed data loaded"
fi

# =============================================================================
# 9. SSL
# =============================================================================
if [ "$SETUP_SSL" = "y" ] || [ "$SETUP_SSL" = "Y" ]; then
    log "[9/10] Setting up SSL with Let's Encrypt..."

    apt-get install -y -qq certbot > /dev/null 2>&1

    # Stop nginx temporarily for standalone cert
    sudo -u "$DEPLOY_USER" docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" stop nginx

    if certbot certonly --standalone -d "$DOMAIN" --non-interactive --agree-tos -m "admin@$DOMAIN"; then
        ok "SSL certificate obtained for $DOMAIN"

        # Add cert volume to docker-compose if not already present
        if ! grep -q "letsencrypt" "$PROJECT_DIR/docker-compose.prod.yml"; then
            warn "Add the following to docker-compose.prod.yml nginx volumes manually:"
            echo "      - /etc/letsencrypt:/etc/letsencrypt:ro"
            echo ""
            warn "And update nginx/nginx.conf.template for SSL (see telepitesi-utmutato.md)"
        fi

        # Setup auto-renewal
        if ! [ -f /etc/cron.d/certbot-renew ]; then
            cat > /etc/cron.d/certbot-renew << CRON
0 */12 * * * root certbot renew --quiet --deploy-hook 'cd $PROJECT_DIR && docker compose -f docker-compose.prod.yml restart nginx'
CRON
            ok "Auto-renewal cron job installed"
        fi
    else
        warn "SSL setup failed — you can retry manually: sudo certbot certonly --standalone -d $DOMAIN"
    fi

    # Restart nginx
    sudo -u "$DEPLOY_USER" docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" up -d nginx
else
    log "[9/10] SSL setup skipped"
fi

# =============================================================================
# 10. Provisioning (cron, backups, log rotation)
# =============================================================================
log "[10/10] Running maintenance provisioning..."

chmod +x "$PROJECT_DIR/scripts/maintenance.sh" "$PROJECT_DIR/scripts/setup-cron.sh" "$PROJECT_DIR/scripts/provision.sh"
"$PROJECT_DIR/scripts/provision.sh"

# =============================================================================
# Health check
# =============================================================================
echo ""
log "Final health check..."
sleep 3

if curl -sf http://localhost:8000/health &>/dev/null; then
    ok "Backend /health: responding"
else
    warn "Backend /health: not responding yet (may need a moment)"
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "========================================"
echo -e " ${GREEN}VPS Bootstrap Complete!${NC}"
echo "========================================"
echo ""
echo "  Domain:       $DOMAIN"
echo "  Project:      $PROJECT_DIR"
echo "  User:         $DEPLOY_USER"
echo "  Env file:     $ENV_FILE"
echo "  Backups:      /opt/openschool/backups"
echo "  Cron:         /etc/cron.d/openschool-maintenance"
echo "  Maint log:    /var/log/openschool-maintenance.log"
echo ""
echo "  Next steps:"
echo "  1. Configure DNS: A record '$DOMAIN' → $(curl -4sf ifconfig.me || echo 'VPS_IP')"
if [ "$SETUP_SSL" = "y" ] || [ "$SETUP_SSL" = "Y" ]; then
    echo "  2. Update nginx/nginx.conf.template for SSL (see docs/telepitesi-utmutato.md)"
    echo "  3. Mount /etc/letsencrypt in docker-compose.prod.yml"
fi
echo "  4. Edit /etc/openschool-maintenance.conf (Discord webhook, SSL_DOMAIN)"
echo "  5. Set up GitHub Actions secrets (VPS_HOST, VPS_USER, VPS_SSH_KEY)"
echo "  6. Run: ./scripts/maintenance.sh health"
echo ""
