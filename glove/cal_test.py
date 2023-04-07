'''
* BNO055 Calibration Data Recording and Testing Utility Script
*
* usage: python3 cal_test.py <r/w> <filename>
'''

# Import utility libraries
import time, sys
# Import BNO055 library
from Adafruit_BNO055 import BNO055

# Check command line parameters
if (len(sys.argv) !=  3):
    print('Usage: cal_test.py <r/w> <filename>')
    sys.exit(1)
else:
    if (sys.argv[1] == 'r'):
        cal_data = open(sys.argv[2], 'rb')
    elif (sys.argv[1] == 'w'):
        cal_data = open(sys.argv[2], 'wb')
    else:
        print('Usage: cal_test.py <r/w> <filename>')
        sys.exit(1)

# Create and initialize BNO055 device
bno = BNO055.BNO055(serial_port='/dev/serial0', rst=13)

if not bno.begin():
    raise RuntimeError('Failed to initialize BNO055!')
    cal_data.close()

# Get calibration data and write to file if given 'write' parameter
if (sys.argv[1] == 'w'):
    cal_count = 0
    while (cal_count < 3):
        cal_array = bno.get_calibration_status()

        print('Sys_cal=' + str(cal_array[0]) + ' Gyro_cal= ' + str(cal_array[1]) + ' Accel_cal=' + str(cal_array[2]) + ' Mag_cal=' + str(cal_array[3]))

        if (cal_array[0] == cal_array[1] == cal_array[2] == cal_array[3] == 3):
            cal_count += 1
        else:
            cal_count = 0

        if (cal_count > 2):
            cal_data.write(bytes(bno.get_calibration()))
            cal_data.close()

        time.sleep(0.5)
# Read calibration data and check calibration status if given 'read' parameter
elif (sys.argv[1] == 'r'):
    bno.set_calibration(cal_data.read())

    cal_array = bno.get_calibration_status()

    print('System calibration with data file provided:')
    print('Sys_cal=' + str(cal_array[0]) + ' Gyro_cal= ' + str(cal_array[1]) + ' Accel_cal=' + str(cal_array[2]) + ' Mag_cal=' + str(cal_array[3]))

    cal_data.close()
