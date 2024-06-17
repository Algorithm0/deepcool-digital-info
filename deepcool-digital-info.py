#!/bin/python3

import sys
import time
import hid
import psutil
import argparse

CUR_DEVICE = "CUSTOM"
SENSOR = 'k10temp'
SENSOR_INDEX = 0
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
    "AG400": DeviceInfo(vendor_id=0x3633, product_id=0x0008, simple_mode=False),
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
parser.add_argument('-z', '--sensor-index', default=SENSOR_INDEX, nargs='?', type=int)
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
SENSOR_INDEX = args.sensor_index
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


def сelsius_to_fahrenheit(input_value):
    return round(input_value * 1.8 + 32)


def get_data_complex(value=0, mode='util'):
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
    # AG400
    # moving [16, 19, 5, 0, 4, 5, ....]
    # to     [16, 19, 5, 4, 5, 0, ....]
    if CUR_DEVICE == "AG400":
        temp_first_digit = base_data[4]
        temp_second_digit = base_data[5]

        base_data[5] = base_data[3]
        base_data[3] = temp_first_digit
        base_data[4] = temp_second_digit
    return base_data


def get_data_simple(usage: int = 0, temp_c: int = 0, use_fahrenheit: bool = False):
    simple_data = bytearray()
    if use_fahrenheit:
        simple_data.extend(map(ord, f"_HLXDATA({usage},{сelsius_to_fahrenheit(temp_c)},0,0,F)"))
    else:
        simple_data.extend(map(ord, f"_HLXDATA({usage},{temp_c},0,0,C)"))
    return simple_data


def get_cpu_temperature(label="CPU"):
    sensors = psutil.sensors_temperatures()
    for sensor_label, sensor_list in sensors.items():
        for sensor in sensor_list:
            if sensor.label == label:
                return sensor.current
    return 0


def get_temperature(is_test: bool = False):
    if is_test:
        return randint(45, 95)

    try:
        temp_sensor = round(psutil.sensors_temperatures()[SENSOR][SENSOR_INDEX].current)
    except KeyError:
        temp_sensor = get_cpu_temperature()
    return temp_sensor


def get_usage(is_test: bool = False):
    if is_test:
        return randint(0, 100)

    return round(psutil.cpu_percent())


try:
    hidDevice = hid.device()
    hidDevice.open(DEVICES[CUR_DEVICE].VENDOR_ID, DEVICES[CUR_DEVICE].PRODUCT_ID)
    hidDevice.set_nonblocking(1)
    if not DEVICES[CUR_DEVICE].SIMPLE_MODE:
        hidDevice.write(get_data_complex(mode="start"))
    while True:
        if DEVICES[CUR_DEVICE].SIMPLE_MODE:
            data = get_data_simple(usage=get_usage(TST_MODE), temp_c=get_temperature(TST_MODE))
            hidDevice.write(data)
            time.sleep(INTERVAL)
            continue

        hidDevice.set_nonblocking(1)
        temp = get_data_complex(value=get_temperature(TST_MODE), mode='temp')
        hidDevice.write(temp)
        time.sleep(INTERVAL)
        utils = get_data_complex(value=get_usage(TST_MODE), mode='util')
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
