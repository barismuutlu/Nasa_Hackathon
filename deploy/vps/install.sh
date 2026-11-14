#!/usr/bin/env bash
# First-time install on the VPS (Ubuntu 24.04, run as a sudo-capable user from anywhere):
#   curl -fsSL https://raw.githubusercontent.com/barismuutlu/Nasa_Hackathon/main/deploy/vps/install.sh | bash
# or, after cloning:  bash deploy/vps/install.sh
# Does NOT touch Apache: enabling the vhost and the certificate are separate, manual steps (see README.md).
set -euo pipefail

REPO=https://github.com/barismuutlu/Nasa_Hackathon.git
BRANCH=${BRANCH:-main}
APP_DIR=/opt/firecal

sudo apt-get update -qq
sudo apt-get install -y -qq git python3.12 python3.12-venv

id firecal >/dev/null 2>&1 || sudo useradd --system --home-dir "$APP_DIR" --shell /usr/sbin/nologin firecal
sudo mkdir -p "$APP_DIR"
sudo chown firecal:firecal "$APP_DIR"

if [ -d "$APP_DIR/.git" ]; then
  sudo -u firecal git -C "$APP_DIR" fetch --quiet origin "$BRANCH"
  sudo -u firecal git -C "$APP_DIR" checkout --quiet "$BRANCH"
  sudo -u firecal git -C "$APP_DIR" pull --quiet --ff-only origin "$BRANCH"
else
  sudo -u firecal git clone --quiet --branch "$BRANCH" "$REPO" "$APP_DIR"
fi

sudo -u firecal python3.12 -m venv "$APP_DIR/.venv"
sudo -u firecal "$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
sudo -u firecal "$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
sudo -u firecal mkdir -p "$APP_DIR/.streamlit-home"

test -f "$APP_DIR/data/deploy/hotspots_deploy.parquet" || { echo "data/deploy/hotspots_deploy.parquet missing"; exit 1; }

sudo cp "$APP_DIR/deploy/vps/firecal.service" /etc/systemd/system/firecal.service
sudo systemctl daemon-reload
sudo systemctl enable --now firecal

sleep 6
bash "$APP_DIR/deploy/vps/check.sh"
echo "Next: Apache vhost + certificate → deploy/vps/README.md, step 3."
