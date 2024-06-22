#!/bin/python3
import subprocess
from enum import Enum
import sys
import time

import hid
import psutil
from random import randint


class DeviceInfo:
    def __init__(self, vendor_id, product_id, simple_mode: bool = False, shift: bool = False):
        self.VENDOR_ID = vendor_id
        self.PRODUCT_ID = product_id
        self.SIMPLE_MODE = simple_mode
        self.USE_SHIFT = shift


class GpuVendor(Enum):
    unknown = 0,
    nvidia_prop = 1


def parse_devices_file(devices_file: str) -> dict[str, DeviceInfo]:
    import os.path
    devices = dict[str, DeviceInfo]()

    if not os.path.isfile(devices_file):
        print("Device configuration file not found")
        return devices

    with open(devices_file) as f:
        import json5
        json_devices = json5.load(f)
        try:
            for device in json_devices:
                use_shift = False
                if "use_shift" in json_devices[device]:
                    use_shift = json_devices[device]["use_shift"]
                devices[device] = DeviceInfo(json_devices[device]["vendor_id"], json_devices[device]["product_id"],
                                             json_devices[device]["simple"], use_shift)
        except KeyError:
            print("Device configuration file has wrong format")
    return devices


class Configuration:
    device: DeviceInfo = DeviceInfo(vendor_id=0x0, product_id=0x0000)
    interval: int = 1
    complex_interval: int = 1
    gpu_vendor: GpuVendor = GpuVendor.unknown
    sensor: str = 'k10temp'
    sensor_index: int = 0
    complex_show_temp: bool = True
    complex_show_usage: bool = True

    def set_device_from_json(self, devices_file: str, device_name: str):
        devices = parse_devices_file(devices_file)
        if len(devices) != 0:
            if device_name in devices:
                self.device = devices[device_name]

    def from_json(self, json_config_file: str):
        import os.path
        if not os.path.isfile(json_config_file):
            print("Settings configuration file not found")
            return

        with open(json_config_file) as f:
            import json5
            try:
                json_config = json5.load(f)
            except Exception as e:
                print("Failed to load configuration file:", e)
                return
            if "json-devices" in json_config and "device" in json_config:
                self.set_device_from_json(devices_file=json_config["json-devices"], device_name=json_config["device"])
            if "vendor" in json_config:
                self.device.VENDOR_ID = json_config["vendor"]
            if "product" in json_config:
                self.device.PRODUCT_ID = json_config["product"]
            if "simple" in json_config:
                self.device.SIMPLE_MODE = json_config["simple"]
            if "use-shift" in json_config:
                self.device.USE_SHIFT = json_config["use-shift"]
            if "interval" in json_config:
                self.interval = json_config["interval"]
            if "complex-interval" in json_config:
                self.complex_interval = json_config["complex-interval"]
            if "use-gpu" in json_config:
                self.gpu_vendor = GpuVendor.nvidia_prop
            if "sensor" in json_config:
                self.sensor = json_config["sensor"]
            if "sensor-index" in json_config:
                self.sensor_index = json_config["sensor-index"]
            if "complex-show-temp" in json_config:
                self.complex_show_temp = json_config["complex-show-temp"]
            if "complex-show-usage" in json_config:
                self.complex_show_usage = json_config["complex-show-usage"]


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


def get_data_complex(bar_percent: int = 0, value: int = 0, mode: ComplexDataType = ComplexDataType.usage,
                     use_shift: bool = False) -> list[int]:
    base_data = [0] * 64
    base_data[0] = 16

    if mode == ComplexDataType.start:
        base_data[1] = 170
        return base_data
    elif mode == ComplexDataType.usage:
        base_data[1] = 76
    elif mode == ComplexDataType.temp:
        base_data[1] = 19

    base_data[2] = get_bar_value(bar_percent)
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
    if use_shift:
        # moving [16, 19, 5, 0, 4, 5, ....]
        # to     [16, 19, 5, 4, 5, 0, ....]
        temp_first_digit = base_data[4]
        temp_second_digit = base_data[5]

        base_data[5] = base_data[3]
        base_data[3] = temp_first_digit
        base_data[4] = temp_second_digit
    return base_data


def get_data_simple(bar_persent: int = 0, temp_c: int = 0, use_fahrenheit: bool = False):
    simple_data = bytearray()
    if use_fahrenheit:
        simple_data.extend(map(ord, f"_HLXDATA({bar_persent},{celsius_to_fahrenheit(temp_c)},0,0,F)"))
    else:
        simple_data.extend(map(ord, f"_HLXDATA({bar_persent},{temp_c},0,0,C)"))
    return simple_data


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

    configuration = Configuration()

    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description='This project provides support for Deepcool Digital for Linux OS. The Python script '
                    'is tailored exclusively for the developer’s equipment; work on other devices is not '
                    'guaranteed, but you can always make your own changes. Use root access to access the '
                    'device')
    parser.add_argument('-d', '--device', nargs='?',
                        help='select your device name in json (--json-devices req)', default=None)
    parser.add_argument('-i', '--interval', type=int, nargs='?', help='display refresh timing in seconds',
                        default=configuration.interval)
    parser.add_argument('--complex-interval', type=int, nargs='?', help='display refresh timing in seconds between '
                                                                        'temperature and use (only for complex mode)',
                        default=configuration.complex_interval)
    parser.add_argument('-j', '--json-devices', nargs='?',
                        help='path to the device configuration file in the form of a '
                             'json-file', default=None)
    parser.add_argument('-s', '--sensor', default=configuration.sensor, nargs='?', type=str)
    parser.add_argument('-z', '--sensor-index', default=configuration.sensor_index, nargs='?', type=int)
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
    parser.add_argument("--use-shift", action='store_true', help="Use if you see '05' instead of '50'")
    parser.add_argument('-c', '--config', type=str, default=None,
                        help='Path to the configuration file. Duplicates most of the arguments. However, arguments in '
                             'conflicts take precedence')

    args = parser.parse_args()

    TST_MODE = args.test
    if args.config is not None:
        configuration.from_json(json_config_file=args.config)

    configuration.interval = args.interval
    configuration.complex_interval = args.complex_interval
    configuration.sensor = args.sensor
    configuration.sensor_index = args.sensor_index
    configuration.complex_show_temp = args.disable_temp
    configuration.complex_show_usage = args.disable_usage

    if args.use_gpu:
        configuration.use_gpu = GpuVendor.nvidia_prop

    if args.json_devices is not None and args.device is not None:
        configuration.set_device_from_json(device_name=args.device, devices_file=args.json_devices)

    if args.simple is not None:
        configuration.device.SIMPLE_MODE = True
    if args.vendor is not None:
        configuration.device.VENDOR_ID = args.vendor
    if args.product is not None:
        configuration.device.PRODUCT_ID = args.product
    if args.use_shift is not None:
        configuration.device.USE_SHIFT = args.use_shift

    try:
        hidDevice = hid.device()
        hidDevice.open(configuration.device.VENDOR_ID, configuration.device.PRODUCT_ID)
        hidDevice.set_nonblocking(1)
        if not configuration.device.SIMPLE_MODE:
            hidDevice.write(get_data_complex(mode=ComplexDataType.start))
        while True:
            usage_now = get_usage(is_test=TST_MODE, gpu_vendor=configuration.gpu_vendor)
            temp_now = get_temperature(is_test=TST_MODE, sensor=configuration.sensor,
                                       sensor_index=configuration.sensor_index,
                                       gpu_vendor=configuration.gpu_vendor)

            if configuration.device.SIMPLE_MODE:
                data = get_data_simple(bar_persent=usage_now, temp_c=temp_now)
                hidDevice.write(data)
            else:
                hidDevice.set_nonblocking(1)
                if configuration.complex_show_temp:
                    temp_data = get_data_complex(bar_percent=usage_now, value=temp_now, mode=ComplexDataType.temp,
                                                 use_shift=configuration.device.USE_SHIFT)
                    hidDevice.write(temp_data)

                if configuration.complex_show_temp and configuration.complex_show_usage:
                    time.sleep(configuration.complex_interval)
                    usage_now = get_usage(is_test=TST_MODE, gpu_vendor=configuration.gpu_vendor)

                if configuration.complex_show_usage:
                    usage_data = get_data_complex(bar_percent=usage_now, value=usage_now, mode=ComplexDataType.usage)
                    hidDevice.write(usage_data)

            time.sleep(configuration.interval)
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
