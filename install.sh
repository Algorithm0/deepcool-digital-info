#!/bin/bash

sudo systemctl stop deepcool-temp.service
sudo cp -f deepcool-temp.service /lib/systemd/system/
sudo cp -f deepcool-temp-restart.service /lib/systemd/system/
sudo cp -f deepcool-digital-info.py /usr/bin/deepcool-digital-info.py
sudo systemctl enable deepcool-temp.service
sudo systemctl enable deepcool-temp-restart.service
sudo systemctl start deepcool-temp.service