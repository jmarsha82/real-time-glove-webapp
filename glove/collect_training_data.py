#! /usr/bin/env python3
'''
* Machine Learning Training Data Collection Script
*
* Usage: python3 collect_training_data.py <output_file> <data classification>
'''

# Import utility libs
import time
import sys
# Import LED lib
from gpiozero import LED
# Import BNO055 lib
from Adafruit_BNO055 import BNO055
# Import MCP3008 libs
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# Create LED
led = LED(12)

# Create and init BNO055 device
bno = BNO055.BNO055(serial_port='/dev/serial0', rst=13)
if not bno.begin():
    raise RuntimeError('Failed to initialize BNO055!')

# Setup MCP3008
## Create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
## Create the cs (chip select)
cs = digitalio.DigitalInOut(board.D5)
## Create the mcp object
mcp = MCP.MCP3008(spi, cs)
## Create analog input channels
chan0 = AnalogIn(mcp, MCP.P0)
chan1 = AnalogIn(mcp, MCP.P1)
chan2 = AnalogIn(mcp, MCP.P2)
chan3 = AnalogIn(mcp, MCP.P3)
chan4 = AnalogIn(mcp, MCP.P4)

# Function to convert received analog voltage to percentage flex
def mapFlexToPercent(x, in_min, in_max):
    out_min = 0
    out_max = 100

    mappedVal = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    # Bounding
    if (mappedVal < out_min):
        mappedVal = out_min
    elif (mappedVal > out_max):
        mappedVal = out_max

    # Flip percent (was 100=no flex, now 100=max flex)
    return (mappedVal-100) * -1

# Open output file as specified by user
output_file = open(str(sys.argv[1]), 'w')

# Get classification of data from command line to tag captured data with
data_class = str(sys.argv[2])

# Calibrate BNO055
cal_data = open('bno055_cal.dat', 'rb')
bno.set_calibration(cal_data.read())
print('Calibration data loaded. Get in position!')

# Wait 10 seconds to allow user to get in position, blinking LED for final 3 seconds
time.sleep(7)
led.blink(0.25, 0.25, None, True)
time.sleep(3)
led.off()

i = 0
# Writes 250 samples of sensor data to file at 4Hz
while i<250:
    # Get sensor data
    imu_orient = bno.read_euler()

    flex_index = mapFlexToPercent(chan0.voltage, 1.87, 2.57)
    flex_mid = mapFlexToPercent(chan1.voltage, 2.02, 2.65)
    flex_ring = mapFlexToPercent(chan2.voltage, 2.18, 2.76)
    flex_pinky = mapFlexToPercent(chan3.voltage, 1.71, 2.54)
    flex_thumb = mapFlexToPercent(chan4.voltage, 1.35, 2.07)

    # Output to file in format "x,y,z,index,middle,ring,pinky,thumb,class"
    output_file.write(str(imu_orient[0]) + ',' + str(imu_orient[1]) + ',' + str(imu_orient[2]) + ',' + str(flex_index) + ',' + str(flex_mid) + ',' + str(flex_ring) + ',' + str(flex_pinky) + ',' + str(flex_thumb) + ',' + data_class + '\n')

    i += 1

    time.sleep(0.25)

output_file.close()
