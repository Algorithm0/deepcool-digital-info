#!/bin/python3

# This script should help configure the specified device
# Iterate through the variation data as the developer indicated to you to get the result

# We want to see something like this:
# Left side of the screen                                    Right side of the screen
#      8 squares                                                     2 squares
#         36 C                                                          33 C

# Running this script without changes should show the correct left screen


from deepcool import *

# Constant data
# VENDOR_ID = 0x3633
# PRODUCT_ID = 0x0005
VENDOR_ID = 0x34d3
PRODUCT_ID = 0x1100
BEGIN_SECOND_DATA = 6

# Varible data
SEND_START = False  # 'False' or 'True'
SEND_MODE = False  # 'False' or 'True'
SHIFT = -1  # -1..40


def get_data_complex_dual_test_start(shift: int = -1):
    data = get_data_complex(mode=ComplexDataType.start)
    if shift >= 0:
        data[BEGIN_SECOND_DATA + shift] = 170

    return data


def get_data_complex_dual_test(shift: int = -1, send_mode: bool = True):
    base_data = get_data_complex(bar_persent=81, value=36, mode=ComplexDataType.temp)
    if shift < 0:
        return base_data

    local_shift = BEGIN_SECOND_DATA + shift
    if send_mode:
        base_data[local_shift] = 19
        local_shift += 1

    bar_persent2 = 19
    value2 = 33
    base_data[2] = get_bar_value(bar_persent2)
    numbers = [int(char) for char in str(value2)]
    if len(numbers) == 1:
        base_data[local_shift + 2] = numbers[0]
    elif len(numbers) == 2:
        base_data[local_shift + 1] = numbers[0]
        base_data[local_shift + 2] = numbers[1]
    elif len(numbers) == 3:
        base_data[local_shift] = numbers[0]
        base_data[local_shift + 1] = numbers[1]
        base_data[local_shift + 2] = numbers[2]

    return base_data


if __name__ == "__main__":
    try:
        hidDevice = hid.device()
        hidDevice.open(VENDOR_ID, PRODUCT_ID)
        hidDevice.set_nonblocking(1)
        if SEND_START:
            hidDevice.write(get_data_complex_dual_test_start(SHIFT))
        else:
            hidDevice.write(get_data_complex_dual_test_start(-1))
        while True:
            hidDevice.set_nonblocking(1)
            hidDevice.write(get_data_complex_dual_test(shift=SHIFT, send_mode=SEND_MODE))
            time.sleep(2)
    except IOError as ex:
        print(ex)
        print("Failed to open device for writing. Either you are using the wrong device (incorrect "
              "VENDOR_ID/PRODUCT_ID), or you need superuser rights.")
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    finally:
        if 'hidDevice' in locals():
            hidDevice.close()
