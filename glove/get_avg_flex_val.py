'''
* Average Flexion  Value Utility Script
*
* usage: python3 get_avg_flex_val.py
'''

# Import Utility Libraries
import time
# Import MCP3008 Libraries
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# Create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# Create the cs (chip select)
cs = digitalio.DigitalInOut(board.D5)

# Create the MCP3008 object
mcp = MCP.MCP3008(spi, cs)

# Create an analog input channel on pin P#
# Edit MCP.P# to get values for different fingers
chan = AnalogIn(mcp, MCP.P0)

# Get 60 flexion readings at 2 Hz
i = 0;
sum = 0;
while i < 60:
    sum += chan.voltage
    i += 1
    time.sleep(0.5)

# Print average flexion value
print('Average: ' + str(sum/60) + 'V')
