#!/usr/bin/env bash
set -euo pipefail

REMOTE="fjania@fjania.com"
REMOTE_PATH="/home/fjania/sites/fjania.com/workshop"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

# Build the Astro site
echo "Building..."
cd "$LOCAL_DIR"
npm run build

# Deploy dist/ output
rsync -avz --delete \
  --exclude='.DS_Store' \
  "$LOCAL_DIR/dist/" "$REMOTE:$REMOTE_PATH/"

ssh "$REMOTE" "find $REMOTE_PATH -type f -exec chmod 644 {} + && find $REMOTE_PATH -type d -exec chmod 755 {} +"

echo "Deployed to $REMOTE:$REMOTE_PATH"
