# Temperature display for Deepcool Digital USB-devices on Linux
This project provides support for **Deepcool Digital** for Linux OS. The Python script is tailored exclusively for the developer’s equipment; work on other devices is not guaranteed, but you can always make your own changes.

## Dependencies
- python3
- python3-hidapi (*Look for this package in the repositories of your OS, the module can also be installed via PIP, but then it must be installed by the root user*)
- python3-psutil (*It is better to install the package from other repositories as well. It is necessary to read the processor temperature. You can use something of your own if you want to use other sensors (for example, a GPU sensor).*)

## Сonfiguration
You can find your device using the utility _lsusb_ (`lsusb -v`). You need to find VendorID and ProductID. Enter this data at the beginning of the Python script in the appropriate fields. After that, test your device by running the script as root.
```shell
sudo python3 deepcool-digital-info.py
```
If you get some output on the display, but the data is incorrect, then you will have to fiddle with how to obtain the temperature data. Study this place in the script and change it so that it works.
```python
def get_temperature():
    if platform == "linux" or platform == "linux2":
        #In this case, a method is called that returns the temperature of my processor.
        import psutil
        return psutil.sensors_temperatures()['k10temp'][0].current
        ...
```

## Installation and Update
When you got what you wanted, just run the internal script. The service will turn on automatically after your PC starts and restart after it sleeps.
```shell
./install.sh
```

## Tested Configuration
- Fedora 39, AMD Rayzen 7 7800X3D, Deepcool ch510 Mesh Digital