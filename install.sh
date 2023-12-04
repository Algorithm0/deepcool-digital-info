#!/bin/bash

sudo cp deepcool-temp.service /lib/systemd/system/
sudo cp deepcool-digital-info.py /usr/bin/deepcool-digital-info.py
sudo systemctl enable deepcool-temp.service
sudo systemctl start deepcool-temp.service