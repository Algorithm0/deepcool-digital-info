#!/bin/bash

usage()
{
  echo "Usage: $0 [INSTALLER OPTIONS] [APP OPTIONS]"
  echo ""
  echo "This script will install this project. You can tell this script with which arguments to call the program itself."
  echo ""
  echo "INSTALLER OPTIONS:"
  echo "  -u, --user-config     - use device configuration file from user"
  echo "  -h, --help            - show this"
  echo ""
  echo "APP OPTIONS             - specify with which options the program (deepcool-digital-info.py) should be launched"
}

USER_CONFIG=0
while [[ $# -gt 0 ]]; do
    case $1 in
    -u|--user-config)
      USER_CONFIG=1
      shift
    ;;
    -h|--help)
      usage
      exit 0
    ;;
    *)
      ARGS="$ARGS $1"
      shift
    ;;
  esac
done

sudo systemctl stop deepcool-temp.service
sudo cp -f deepcool-temp.service /lib/systemd/system/
sudo sed -i "s|ExecStart= /usr/bin/python3 /usr/local/bin/deepcool-digital-info.py -j /usr/local/share/applications/deepcool-devices.json5|ExecStart= /usr/bin/python3 /usr/local/bin/deepcool-digital-info.py -j /usr/local/share/applications/deepcool-devices.json5${ARGS}|g" /lib/systemd/system/deepcool-temp.service
sudo cp -f deepcool-temp-restart.service /lib/systemd/system/
sudo cp -f deepcool-digital-info.py /usr/local/bin/deepcool-digital-info.py
sudo mkdir -p /usr/local/share/applications

if [ "${USER_CONFIG}" -eq 1 ] && [ -f user-devices.json5 ]; then
  sudo cp -f user-devices.json5 /usr/local/share/applications/deepcool-devices.json5
else
  sudo cp -f devices.json5 /usr/local/share/applications/deepcool-devices.json5
fi

sudo systemctl enable deepcool-temp.service
sudo systemctl enable deepcool-temp-restart.service
sudo systemctl start deepcool-temp.service