from sys import platform
import time
# use package hidapi!
import hid

VENDOR_ID = 0x34d3
PRODUCT_ID = 0x1100
INTERVAL = 1

def get_temperature():
    if platform == "linux" or platform == "linux2":
        #In this case, a method is called that returns the temperature of my processor.
        import psutil
        return psutil.sensors_temperatures()['k10temp'][0].current
    else:
        #out fake temp
        return 60

try:
    h = hid.device()
    h.open(VENDOR_ID, PRODUCT_ID)

    h.set_nonblocking(1)

    while True:
        temp = get_temperature()
        b = bytearray()
        b.extend(map(ord, f"_HLXDATA({temp},{temp},0,0,C)"))
        h.write(b)
        time.sleep(INTERVAL)

except IOError as ex:
   print(ex)
   print("Failed to open device for writing. Either you are using the wrong device (incorrect VENDOR_ID/PRODUCT_ID), or you need superuser rights.")
