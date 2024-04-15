# Temperature display for Deepcool Digital USB-devices on Linux
This project provides support for **Deepcool Digital** for Linux OS. The Python3 script is tailored
exclusively for the developer’s equipment;
work on other devices is not guaranteed, but you can always make your own changes.

## Python package dependencies

### Base
- `hidapi`
- `psutil`
- `json5`

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
sudo dnf install python-json5 python-hidapi python-hidapi
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

## What do this thing do?
- [x] Displays CPU temperature on tested devices
- [x] Displays CPU usage information on tested devices
- [ ] Displays GPU temperature on tested devices
- [ ] Displays GPU usage information on tested devices
- [x] Launches when the computer starts up
- [x] Restarts after sleep
- [ ] Works with multiple devices
- [ ] Has a visual interface
- [ ] Can display temperature in Fahrenheit
- [ ] Allows you to configure usage/temperature switching

## What devices are supported?
Unfortunately, it is impossible to try the configuration of a particular device without having it in hand. 
But you can always try your device! Run the configurator and maybe you will get something!
If you were able to configure your device, which was not previously on the list, then please write about it 
[here](https://github.com/Algorithm0/deepcool-digital-info/issues/2).

A list of currently supported devices can be found [here](devices.json5).

## Denial of responsibility
All program data has been tested and verified on several configurations, nothing critical has happened. 
But if you have specific equipment, specific behavior or, for example, hands, then I cannot help you.
I'm just giving you a tool. Its use on the highest level of advice.

## Deposits
 - https://github.com/raghulkrishna - implementation of the dual mode algorithm 
(marked as `complex` in the configurator)