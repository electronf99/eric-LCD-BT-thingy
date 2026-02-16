from machine import Pin, SoftI2C
from pico_i2c_lcd import I2cLcd
from time import sleep
import bluetooth

# Define the LCD I2C address and dimensions
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

# Initialize I2C and LCD objects
i2c = SoftI2C(scl=Pin(8), sda=Pin(7), freq=500_000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

ble = bluetooth.BLE()
ble.active(True)
mac = ble.config('mac')[1]
btmac = (''.join('%02X' % b for b in mac))

lcd.clear()
lcd.putstr("Connect BT MAC:")
lcd.move_to(0,1)
lcd.putstr(btmac)
sleep(4)

try:
    while True:

        sleep(2)

except KeyboardInterrupt:
    # Turn off the display
    print("Keyboard interrupt")
    lcd.backlight_off()
    lcd.display_off()