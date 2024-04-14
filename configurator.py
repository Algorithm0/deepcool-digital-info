#!/bin/python3
import stat
from subprocess import Popen

import click

print("Hello! This script should help you configure the program.")
print("It is recommended to run the script with superuser rights to ensure that he has access to the necessary "
      "packages, as well as access to USB devices.")
if not click.confirm("Let's try. First, all necessary Python packages will be checked. Begin?", default=True):
    print("Okay, let's continue next time!")
    exit(0)

modulesOk = True
try:
    import psutil
except ImportError:
    print("This project needs 'psutil' module. Please install it first. It is recommended to use the system package "
          "for your OS")
    modulesOk = False

try:
    import hid

    device_list = hid.enumerate(0, 0)
except Exception as e:
    if e == ImportError:
        print("This project needs 'hid' module. Please install it first. It is recommended to use the system package "
              "for your OS")
    else:
        print(f"Error: {e}")
        print(
            "This project needs 'hidapi' module. Please install it first. It is recommended to use the system package "
            "for your OS")
    modulesOk = False

try:
    import argparse
except ImportError:
    print("This project needs 'argparse' module. Please install it first. It is recommended to use the system "
          "package for your OS")
    modulesOk = False

try:
    import os.path
except ImportError:
    print("This project needs 'os.path' module. Please install it first. It is recommended to use the system "
          "package for your OS")
    modulesOk = False

try:
    import json5
except ImportError:
    print("This project needs 'json5' (pyjson5) module. Please install it first. It is recommended to use the system "
          "package for your OS")
    modulesOk = False

try:
    from random import randint
except ImportError:
    print("Failed to import the 'random' module. We won't be able to verify that the program is running. It "
          "seems you will either have to install this module and come back here, or configure everything yourself. "
          "Bye!")
    exit(1)

if not modulesOk:
    print("Do you see this? It looks like you need to install several modules! Install them and come back, "
          "see you later!")
    exit(1)


def selectNum(max, text):
    while True:
        selected = click.prompt(text, type=int)
        if selected == 0:
            print("Bye!")
            exit(0)
        if 1 <= selected <= max:
            break
        else:
            print("Error:", selected, "is not a valid variant.")
    return selected


print("All modules are installed! Great! Well, let's now try to identify your device!")
json_devices_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'devices.json5'))
index = 1
with open(json_devices_file) as f:
    json_devices = json5.load(f)
    try:
        for device in json_devices["devices"]:
            print(index, device["name"])
            index += 1
    except KeyError:
        print("Device configuration file has wrong format")
        exit(1)
print(index, "No my device")
print("0 I think I forgot to turn off the iron! (Go out)")

selected = selectNum(index, 'Please select')

TARGET_ARGS = ""

base_script = os.path.abspath(os.path.join(os.path.dirname(__file__), 'deepcool-digital-info.py'))
check = False
if selected != index:
    running_procs = Popen(
        [base_script, "-j", f"{json_devices_file}", "-d", f"{json_devices["devices"][selected - 1]["name"]}", "-t"])
    check = click.confirm("Wait a little and see what's wrong with your device. Do you see that it shows some random "
                          "data?", default=True)
    running_procs.kill()
    if check:
        print("Hooray! I congratulate you! The worst is over! Let's now make the information meaningful!")
        TARGET_ARGS = f"-d {json_devices["devices"][selected - 1]["name"]}"
    else:
        print("It's a pity... It's really strange. But let's try to move on to manual configuration")

userDeviceName = ""


def tryDevice():
    while True:
        index = 1
        print()
        for hid_device in device_list:
            print(index, hid_device)
            index += 1
            print()

        print(
            "Take a close look at this list. Try, using the method of analysis and screening, to suggest which device "
            "may be what we are looking for. Don't worry, if we miss, nothing should happen (I hope!).")
        print("For example, it is unlikely that the manufacturer_string will contain a well-known brand or the "
              "product_string will hint at a keyboard, mouse or camera.")
        selectedHid = selectNum(index, 'Which number should we choose (enter 0 to exit)')
        print("And so, there we have it. Now tell me which mode are we using? Now everything is set to configurations: "
              "simple and complex. The complex one is usually suitable for devices with two operating modes ("
              "temperature and processor load), and the simple one only for temperature.")
        print("1 complex")
        print("2 simple")
        selectedMode = selectNum(2, 'Please select (enter 0 to exit)')
        if selectedMode == 2:
            running_procs = Popen(
                [base_script, "-v", f"{device_list[selectedHid - 1]['vendor_id']}", "-p",
                 f"{device_list[selectedHid - 1]['product_id']}", "-t", "-m"])
        else:
            running_procs = Popen(
                [base_script, "-v", f"{device_list[selectedHid - 1]['vendor_id']}", "-p",
                 f"{device_list[selectedHid - 1]['product_id']}", "-t"])
        check = click.confirm(
            "Wait a little and see what's wrong with your device. Do you see that it shows some random "
            "data?", default=True)
        running_procs.kill()
        if check:
            print("Hooray! I congratulate you! The worst is over! Let's now make the information meaningful!")
            userDeviceName = click.prompt("Please enter the model number of your device (similar to CH510, AK400). If "
                                          "your device was already on the list, then add some prefix (AK400-2)",
                                          type=str)
            json_devices["devices"].append({'name': userDeviceName,
                                            'vendor_id': device_list[selectedHid - 1]['vendor_id'],
                                            'product_id': device_list[selectedHid - 1]['product_id'],
                                            'simple': (selectedMode == 2)})
            new_json = os.path.abspath(os.path.join(os.path.dirname(__file__), 'user-devices.json5'))
            with open(new_json, "w") as write:
                json5.dump(json_devices, write, sort_keys=True, indent=4)
            os.chmod(new_json, stat.S_IRWXO)
            break
        else:
            print("It's a pity... It's really strange. But let's try to move on to manual configuration")


if selected == index or not check:
    print("Well... We are moving on to a rather difficult part. We will need to try to find your device manually.")
    print("I recommend that you turn off all your USB devices (it would be ideal if, say, you turn off everything "
          "except the mouse and keyboard), and then come back here.")
    print("Moreover, I highly recommend using superuser to get more information in the next step.")
    if click.confirm("Do you want to exit the configuration script?", default=False):
        print("See you!")
        exit(1)
    tryDevice()

print("And so, then everything should be simpler. We will look at the temperature sensors that we were able to detect "
      "and select something suitable.")
