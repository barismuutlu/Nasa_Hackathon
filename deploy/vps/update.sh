#!/usr/bin/env bash
# Deploy the latest commit of the checked-out branch:  bash /opt/firecal/deploy/vps/update.sh
set -euo pipefail
APP_DIR=/opt/firecal
sudo -u firecal git -C "$APP_DIR" pull --ff-only
sudo -u firecal "$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
sudo cp "$APP_DIR/deploy/vps/firecal.service" /etc/systemd/system/firecal.service
sudo systemctl daemon-reload
sudo systemctl restart firecal
sleep 6
bash "$APP_DIR/deploy/vps/check.sh"
