# Deepcool Digital on Linux
This project provides support for **Deepcool Digital** usb-devices (HID) for Linux OS.<br>
Project is based on _python3_, _systemd_ and _bash_ scripts.<br>
The number of supported devices is expanding with the help of the community, so write boldly!

## Python package dependencies

### Base
- `hidapi`
- `psutil`
- `json5`
- `subprocess`

### Configurator
- `stat`
- `subprocess`, `subprocess.Popen`
- `click`

### Some information about installing packages
It is not recommended to use PIP as an installer of these dependencies, since here you can miss the user access
(for example, the superuser from whom this service will be launched may not have access to them).
For this reason, it is better to follow the installation path from your distribution's repository. For example,
for Fedora it looks something like this:
~~~shell
sudo dnf install python-json5 python-hidapi python-psutil
~~~

## Configuration and Install
For configuration, it is now enough to run the configurator script as a superuser. Just make sure that the dependencies
of at least the configurator itself are satisfied.

So. You want to install this project for yourself. Just do this:
~~~shell
git clone https://github.com/Algorithm0/deepcool-digital-info.git
cd deepcool-digital-info
sudo ./configurator.py
~~~
Carefully monitor the output of the configurator when setting up your equipment. I hope everything works out for you!

## What does this thing do?
- [x] Displays CPU temperature on tested devices
- [x] Displays CPU usage information on tested devices
- [ ] Displays GPU temperature on tested devices
  - [x] Nvidia (proprietary driver with `nvidia-smi`)
- [ ] Displays GPU usage information on tested devices
  - [x] Nvidia (proprietary driver with `nvidia-smi`)
- [x] Launches when the computer starts up
- [x] Restarts after sleep
- [ ] Works with multiple devices
- [ ] Has a visual interface
- [ ] Can display temperature in Fahrenheit
- [x] Allows you to configure usage/temperature switching

## What devices are supported?
Unfortunately, it is impossible to try the configuration of a particular device without having it in hand. 
But you can always try your device! Run the configurator and maybe you will get something!
If you were able to configure your device, which was not previously on the list, then please write about it 
[here](https://github.com/Algorithm0/deepcool-digital-info/issues/2).

A list of currently supported devices can be found [here](devices.json5).

## Deposits
 - https://github.com/raghulkrishna - implementation of the dual mode algorithm 
(marked as `complex` in the configurator)