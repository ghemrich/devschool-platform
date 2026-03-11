#!/bin/bash
# =============================================================================
# Install cron jobs for OpenSchool Platform maintenance
# Usage: sudo ./scripts/setup-cron.sh [--remove]
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MAINTENANCE_SCRIPT="$SCRIPT_DIR/maintenance.sh"
CRON_ID="# openschool-maintenance"
CRON_FILE="/etc/cron.d/openschool-maintenance"

if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root (sudo)."
    exit 1
fi

remove_cron() {
    if [ -f "$CRON_FILE" ]; then
        rm -f "$CRON_FILE"
        echo "Removed cron file: $CRON_FILE"
    else
        echo "No cron file found at $CRON_FILE"
    fi
}

install_cron() {
    # Ensure maintenance script is executable
    chmod +x "$MAINTENANCE_SCRIPT"

    # Detect the user who owns the project directory
    local run_user
    run_user=$(stat -c '%U' "$PROJECT_DIR")

    cat > "$CRON_FILE" << EOF
# =============================================================================
# OpenSchool Platform — Automated Maintenance
# Installed by: setup-cron.sh
# Project: $PROJECT_DIR
# =============================================================================
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# --- Daily: 2:00 AM — backup + health check + log scan ---
0 2 * * * $run_user $MAINTENANCE_SCRIPT full-daily >> /var/log/openschool-maintenance.log 2>&1

# --- Weekly: Sunday 3:00 AM — disk check + docker cleanup + db stats ---
0 3 * * 0 $run_user $MAINTENANCE_SCRIPT full-weekly >> /var/log/openschool-maintenance.log 2>&1

# --- Monthly: 1st of month 4:00 AM — SSL + security audit ---
0 4 1 * * $run_user $MAINTENANCE_SCRIPT full-monthly >> /var/log/openschool-maintenance.log 2>&1

EOF

    chmod 644 "$CRON_FILE"

    # Setup log rotation
    cat > /etc/logrotate.d/openschool-maintenance << 'LOGROTATE'
/var/log/openschool-maintenance.log {
    weekly
    rotate 12
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
LOGROTATE

    echo "Cron jobs installed at: $CRON_FILE"
    echo "Log rotation configured at: /etc/logrotate.d/openschool-maintenance"
    echo ""
    echo "Installed schedule:"
    echo "  Daily   02:00  — backup, health check, log scan"
    echo "  Weekly  Sun 03:00 — + disk check, docker cleanup, db stats"
    echo "  Monthly 1st 04:00 — + SSL check, security audit"
    echo ""
    echo "Logs → /var/log/openschool-maintenance.log"
    echo ""
    echo "Verify with: cat $CRON_FILE"
}

case "${1:-install}" in
    install)
        install_cron
        ;;
    --remove|remove)
        remove_cron
        ;;
    *)
        echo "Usage: $0 [install|--remove]"
        exit 1
        ;;
esac
