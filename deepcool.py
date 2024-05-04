#!/bin/python3
import subprocess
from enum import Enum
import sys
import time
import hid
import psutil
from random import randint


class DeviceInfo:
    def __init__(self, vendor_id, product_id, simple_mode):
        self.VENDOR_ID = vendor_id
        self.PRODUCT_ID = product_id
        self.SIMPLE_MODE = simple_mode


def get_bar_value(input_value: int) -> int:
    if input_value <= 0:
        return 0
    if input_value >= 99:
        return 10

    return round(input_value, -1) // 10


def celsius_to_fahrenheit(input_value):
    return round(input_value * 1.8 + 32)


class ComplexDataType(Enum):
    start = 0,
    temp = 1,
    usage = 2


def get_data_complex(bar_persent: int = 0, value: int = 0, mode: ComplexDataType = ComplexDataType.usage):
    base_data = [0] * 64
    base_data[0] = 16

    if mode == ComplexDataType.start:
        base_data[1] = 170
        return base_data
    elif mode == ComplexDataType.usage:
        base_data[1] = 76
    elif mode == ComplexDataType.temp:
        base_data[1] = 19

    base_data[2] = get_bar_value(bar_persent)
    numbers = [int(char) for char in str(value)]
    if len(numbers) == 1:
        base_data[5] = numbers[0]
    elif len(numbers) == 2:
        base_data[4] = numbers[0]
        base_data[5] = numbers[1]
    elif len(numbers) == 3:
        base_data[3] = numbers[0]
        base_data[4] = numbers[1]
        base_data[5] = numbers[2]
    return base_data


def get_data_simple(bar_persent: int = 0, temp_c: int = 0, use_fahrenheit: bool = False):
    simple_data = bytearray()
    if use_fahrenheit:
        simple_data.extend(map(ord, f"_HLXDATA({bar_persent},{celsius_to_fahrenheit(temp_c)},0,0,F)"))
    else:
        simple_data.extend(map(ord, f"_HLXDATA({bar_persent},{temp_c},0,0,C)"))
    return simple_data


class GpuVendor(Enum):
    unknown = 0,
    nvidia_prop = 1


def get_gpu_temperature(gpu_vendor: GpuVendor = GpuVendor.unknown):
    if gpu_vendor == GpuVendor.unknown:
        return 0

    if gpu_vendor == GpuVendor.nvidia_prop:
        try:
            return int(subprocess.check_output(['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader']))
        except Exception as e:
            print("Error call 'nvidia-smi' command:", e)
            print("Return 0")
            return 0


def get_gpu_usage(gpu_vendor: GpuVendor = GpuVendor.unknown):
    if gpu_vendor == GpuVendor.unknown:
        return 0

    if gpu_vendor == GpuVendor.nvidia_prop:
        try:
            data_gpu_usage = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.total,memory.used',
                                                      '--format=csv,noheader,nounits']).decode('UTF-8')
            split_data = data_gpu_usage.split(", ")
            return round(int(split_data[1]) * 100 / int(split_data[0]))
        except Exception as e:
            print("Error call 'nvidia-smi' command:", e)
            print("Return 0")
            return 0


def get_temperature(is_test: bool = False, sensor: str = 'k10temp', sensor_index: int = 0,
                    gpu_vendor: GpuVendor = GpuVendor.unknown):
    if is_test:
        return randint(45, 95)

    if gpu_vendor == GpuVendor.unknown:
        try:
            temp_sensor = round(psutil.sensors_temperatures()[sensor][sensor_index].current)
        except KeyError:
            temp_sensor = 0
        return temp_sensor

    return get_gpu_temperature(gpu_vendor=gpu_vendor)


def get_usage(is_test: bool = False, gpu_vendor: GpuVendor = GpuVendor.unknown):
    if is_test:
        return randint(0, 100)
    if gpu_vendor == GpuVendor.unknown:
        return round(psutil.cpu_percent())

    return get_gpu_usage(gpu_vendor)


if __name__ == "__main__":
    import argparse

    CUR_DEVICE = "CUSTOM"
    SENSOR = 'k10temp'
    SENSOR_INDEX = 0
    INTERVAL = 1
    COMPLEX_INTERVAL = INTERVAL
    GPU_VENDOR = GpuVendor.unknown

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
    parser.add_argument('-i', '--interval', type=int, nargs='?', help='display refresh timing in seconds',
                        default=INTERVAL)
    parser.add_argument('--complex-interval', type=int, nargs='?', help='display refresh timing in seconds between '
                                                                        'temperature and use (only for complex mode)',
                        default=COMPLEX_INTERVAL)
    parser.add_argument('-j', '--json-devices', nargs='?',
                        help='path to the device configuration file in the form of a '
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
    parser.add_argument('-g', '--use-gpu',
                        action='store_true', help="Display information about the NVIDIA GPU "
                                                  "instead of the CPU (only the proprietary driver "
                                                  "is supported). Some flags that are responsible "
                                                  "for setting the temperature sensor will be "
                                                  "ignored.")
    parser.add_argument('--disable-temp', action='store_false', help="Turns off the temperature display (only for "
                                                                     "complex mode)")
    parser.add_argument('--disable-usage', action='store_false', help="Turns off usage display (complex mode only)")

    args = parser.parse_args()
    INTERVAL = args.interval
    COMPLEX_INTERVAL = args.complex_interval
    SENSOR = args.sensor
    SENSOR_INDEX = args.sensor_index
    CUR_DEVICE = args.device
    TST_MODE = args.test
    COMPLEX_SHOW_TEMP = args.disable_temp
    COMPLEX_SHOW_USAGE = args.disable_usage
    if args.use_gpu:
        GPU_VENDOR = GpuVendor.nvidia_prop

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
                for device in json_devices:
                    DEVICES[device] = DeviceInfo(json_devices[device]["vendor_id"], json_devices[device]["product_id"],
                                                 json_devices[device]["simple"])
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

    try:
        hidDevice = hid.device()
        hidDevice.open(DEVICES[CUR_DEVICE].VENDOR_ID, DEVICES[CUR_DEVICE].PRODUCT_ID)
        hidDevice.set_nonblocking(1)
        if not DEVICES[CUR_DEVICE].SIMPLE_MODE:
            hidDevice.write(get_data_complex(mode=ComplexDataType.start))
        while True:
            usage_now = get_usage(is_test=TST_MODE, gpu_vendor=GPU_VENDOR)
            temp_now = get_temperature(is_test=TST_MODE, sensor=SENSOR, sensor_index=SENSOR_INDEX,
                                       gpu_vendor=GPU_VENDOR)

            if DEVICES[CUR_DEVICE].SIMPLE_MODE:
                data = get_data_simple(bar_persent=usage_now, temp_c=temp_now)
                hidDevice.write(data)
            else:
                hidDevice.set_nonblocking(1)
                if COMPLEX_SHOW_TEMP:
                    temp_data = get_data_complex(bar_persent=usage_now, value=temp_now, mode=ComplexDataType.temp)
                    hidDevice.write(temp_data)

                if COMPLEX_SHOW_TEMP and COMPLEX_SHOW_USAGE:
                    time.sleep(COMPLEX_INTERVAL)
                    usage_now = get_usage(is_test=TST_MODE, gpu_vendor=GPU_VENDOR)

                if COMPLEX_SHOW_USAGE:
                    usage_data = get_data_complex(bar_persent=usage_now, value=usage_now, mode=ComplexDataType.usage)
                    hidDevice.write(usage_data)

            time.sleep(INTERVAL)
    except IOError as ex:
        print(ex)
        print(
            "Failed to open device for writing. Either you are using the wrong device (incorrect VENDOR_ID/PRODUCT_ID),"
            "or you need superuser rights.")
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    finally:
        if 'hidDevice' in locals():
            hidDevice.close()
