#!/usr/bin/env bash
set -euo pipefail

REMOTE="fjania@fjania.com"
REMOTE_PATH="/home/fjania/sites/fjania.com/workshop/router-bits"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

rsync -avz --delete \
  --exclude='deploy.sh' \
  --exclude='bit-images-backup/' \
  --exclude='.DS_Store' \
  "$LOCAL_DIR/" "$REMOTE:$REMOTE_PATH/"

ssh "$REMOTE" "find $REMOTE_PATH -type f -exec chmod 644 {} + && find $REMOTE_PATH -type d -exec chmod 755 {} +"

echo "Deployed to $REMOTE:$REMOTE_PATH"
