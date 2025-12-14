#!/bin/bash
# install_service.sh
# Installs the DAUT MCP systemd service
# Usage: sudo ./install_service.sh

if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root (sudo ./install_service.sh)"
  exit 1
fi

SERVICE_NAME="daut-mcp.service"
SRC_FILE="daut-mcp.service"
DEST_FILE="/etc/systemd/system/$SERVICE_NAME"

echo "Installing $SERVICE_NAME..."

# Copy service file
cp $SRC_FILE $DEST_FILE

# Reload systemd
systemctl daemon-reload

# Enable and start
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

echo "✅ Service installed and started!"
echo "Check status via: systemctl status $SERVICE_NAME"
echo "View logs via: journalctl -u $SERVICE_NAME -f"
