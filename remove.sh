#!/bin/bash

usage()
{
  echo "Usage: $0 [-h|--help]"
  echo ""
  echo "This script completely removes the installation of this project on your system"
}

while [[ $# -gt 0 ]]; do
    case $1 in
    -h|--help)
      usage
      exit 0
    ;;
  esac
done

sudo systemctl stop deepcool-temp.service --no-warn
sudo systemctl disable deepcool-temp.service --no-warn
sudo systemctl disable deepcool-temp-restart.service --no-warn
sudo rm -f /lib/systemd/system/deepcool-temp.service
sudo rm -f /lib/systemd/system/deepcool-temp-restart.service
sudo rm -f /usr/local/bin/deepcool-digital-info.py
sudo rm -f /usr/bin/deepcool-digital-info.py
sudo rm -f /usr/local/share/applications/deepcool-devices.json5