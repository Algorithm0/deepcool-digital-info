from sys import platform
import time
# use package hidapi!
import hid

VENDOR_ID = 0x34d3
PRODUCT_ID = 0x1100


if platform == "linux" or platform == "linux2":
    print("linux")
    def get_temperature():
        return 40.3
elif platform == "win32":
    def get_temperature():
        return 60


try:
    h = hid.device()
    h.open(VENDOR_ID, PRODUCT_ID)

    h.set_nonblocking(1)

    while True:
        b = bytearray()
        b.extend(map(ord, f"_HLXDATA(0,{get_temperature()},0,0,C)"))
        h.write(b)
        time.sleep(0.5)

except IOError as ex:
   print(ex)
   print("You probably don't have the hard-coded device.")
   print("Update the h.open() line in this script with the one")
   print("from the enumeration list output above and try again.")
