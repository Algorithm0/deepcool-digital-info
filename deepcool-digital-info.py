#!/bin/python3

import sys
import time
import hid
import psutil
import argparse

CUR_DEVICE = "CUSTOM"
SENSOR = 'k10temp'
INTERVAL = 1


class DeviceInfo:
    def __init__(self, vendor_id, product_id, simple_mode):
        self.VENDOR_ID = vendor_id
        self.PRODUCT_ID = product_id
        self.SIMPLE_MODE = simple_mode


DEVICES = {
    "CH510": DeviceInfo(vendor_id=0x34d3, product_id=0x1100, simple_mode=True),
    "AK620": DeviceInfo(vendor_id=0x3633, product_id=0x0002, simple_mode=False),
    "AK400": DeviceInfo(vendor_id=0x3633, product_id=0x0001, simple_mode=False),
    "CUSTOM": DeviceInfo(vendor_id=0x0, product_id=0x0000, simple_mode=False)
}

parser = argparse.ArgumentParser(
    prog=sys.argv[0],
    description='This project provides support for Deepcool Digital for Linux OS. The Python script '
                'is tailored exclusively for the developer’s equipment; work on other devices is not '
                'guaranteed, but you can always make your own changes. Use root access to access the '
                'device')
parser.add_argument('-d', '--device', nargs='?',
                    help='select your device name in json (--json-devices req)', default=CUR_DEVICE)
parser.add_argument('-i', '--interval', type=int, nargs='?', help='display refresh timing in seconds', default=INTERVAL)
parser.add_argument('-j', '--json-devices', nargs='?', help='path to the device configuration file in the form of a '
                                                            'json-file', default=None)
parser.add_argument('-s', '--sensor', default=SENSOR, nargs='?', type=str)
parser.add_argument('-m', '--simple', action='store_true',
                    help="specify if using simple data sending mode (if "
                         "your device is on the list, don't worry about "
                         "it)", default=None)
parser.add_argument('-t', '--test', action='store_true',
                    help="send random values to the device, ignoring sensor values")
parser.add_argument('-v', '--vendor', type=lambda x: int(x, 0), nargs='?',
                    help="provide a specific VENDOR_ID (if your device is listed, "
                         "don't worry about it)", default=None)
parser.add_argument('-p', '--product', type=lambda x: int(x, 0), nargs='?',
                    help="provide a specific PRODUCT_ID (if your device is listed, "
                         "don't worry about it)", default=None)

args = parser.parse_args()
INTERVAL = args.interval
SENSOR = args.sensor
CUR_DEVICE = args.device
TST_MODE = args.test

if args.json_devices is not None:
    custom_device = DEVICES["CUSTOM"]
    DEVICES.clear()
    import os.path
    if not os.path.isfile(args.json_devices):
        print("Device configuration file not found")
        exit(1)
    import json5
    with open(args.json_devices) as f:
        json_devices = json5.load(f)
        try:
            for device in json_devices["devices"]:
                DEVICES[device["name"]] = DeviceInfo(device["vendor_id"], device["product_id"], device["simple"])
        except KeyError:
            print("Device configuration file has wrong format")
            exit(1)
    DEVICES["CUSTOM"] = custom_device

if args.simple is not None:
    DEVICES[CUR_DEVICE].SIMPLE_MODE = True
if args.vendor is not None:
    DEVICES[CUR_DEVICE].VENDOR_ID = args.vendor
if args.product is not None:
    DEVICES[CUR_DEVICE].PRODUCT_ID = args.product


if TST_MODE:
    from random import randint


def get_bar_value(input_value):
    return (input_value - 1) // 10 + 1


def get_data(value=0, mode='util'):
    if mode == 'simple':
        simple_data = bytearray()
        simple_data.extend(map(ord, f"_HLXDATA({value},{value},0,0,C)"))
        return simple_data
    base_data = [16, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    numbers = [int(char) for char in str(value)]
    base_data[2] = get_bar_value(value)
    if mode == 'util':
        base_data[1] = 76
    elif mode == 'start':
        base_data[1] = 170
        return base_data
    elif mode == 'temp':
        base_data[1] = 19
    if len(numbers) == 1:
        base_data[5] = numbers[0]
    elif len(numbers) == 2:
        base_data[4] = numbers[0]
        base_data[5] = numbers[1]
    elif len(numbers) == 3:
        base_data[3] = numbers[0]
        base_data[4] = numbers[1]
        base_data[5] = numbers[2]
    elif len(numbers) == 4:
        base_data[3] = numbers[0]
        base_data[4] = numbers[1]
        base_data[5] = numbers[2]
        base_data[6] = numbers[3]
    return base_data


def get_cpu_temperature(label="CPU"):
    sensors = psutil.sensors_temperatures()
    for sensor_label, sensor_list in sensors.items():
        for sensor in sensor_list:
            if sensor.label == label:
                return sensor.current
    return 0


def get_temperature():
    if TST_MODE:
        temp_rand = randint(45, 95)
        if DEVICES[CUR_DEVICE].SIMPLE_MODE:
            return get_data(value=temp_rand, mode='simple')
        else:
            return get_data(value=temp_rand, mode='temp')
    try:
        temp_sensor = round(psutil.sensors_temperatures()[SENSOR][0].current)
    except KeyError:
        temp_sensor = get_cpu_temperature()
    if DEVICES[CUR_DEVICE].SIMPLE_MODE:
        return get_data(value=temp_sensor, mode='simple')
    else:
        return get_data(value=temp_sensor, mode='temp')


def get_utils():
    if TST_MODE:
        return get_data(value=randint(0, 100), mode='util')
    utils_data = round(psutil.cpu_percent())
    return get_data(value=utils_data, mode='util')


try:
    hidDevice = hid.device()
    hidDevice.open(DEVICES[CUR_DEVICE].VENDOR_ID, DEVICES[CUR_DEVICE].PRODUCT_ID)
    hidDevice.set_nonblocking(1)
    if not DEVICES[CUR_DEVICE].SIMPLE_MODE:
        hidDevice.write(get_data(mode="start"))
    while True:
        if DEVICES[CUR_DEVICE].SIMPLE_MODE == "simple":
            temp = get_temperature()
            b = bytearray()
            b.extend(map(ord, f"_HLXDATA({temp},{temp},0,0,C)"))
            hidDevice.write(b)
            time.sleep(INTERVAL)
            continue

        hidDevice.set_nonblocking(1)
        temp = get_temperature()
        hidDevice.write(temp)
        time.sleep(INTERVAL)
        utils = get_utils()
        hidDevice.write(utils)
        time.sleep(INTERVAL)
except IOError as ex:
    print(ex)
    print("Failed to open device for writing. Either you are using the wrong device (incorrect VENDOR_ID/PRODUCT_ID), "
          "or you need superuser rights.")
except KeyboardInterrupt:
    print("\nScript terminated by user.")
finally:
    if 'hidDevice' in locals():
        hidDevice.close()
