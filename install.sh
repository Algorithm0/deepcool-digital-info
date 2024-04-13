#!/bin/bash

usage()
{
  echo "Usage: $0 [APP OPTIONS]"
  echo ""
  echo "This script will install this project. You can tell this script with which arguments to call the program itself."
  echo ""
  echo "APP OPTIONS             - Specify with which options the program (deepcool-digital-info.py) should be launched"
}

while [[ $# -gt 0 ]]; do
    case $1 in
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
sudo sed -i "s|ExecStart= /usr/bin/python3 /usr/bin/deepcool-digital-info.py|ExecStart= /usr/bin/python3 /usr/bin/deepcool-digital-info.py ${ARGS}|g" /lib/systemd/system/deepcool-temp.service
sudo cp -f deepcool-temp-restart.service /lib/systemd/system/
sudo cp -f deepcool-digital-info.py /usr/bin/deepcool-digital-info.py
sudo systemctl enable deepcool-temp.service
sudo systemctl enable deepcool-temp-restart.service
sudo systemctl start deepcool-temp.service