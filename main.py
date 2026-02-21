import time
from ble_uart import BLEUART
from machine import Pin, SoftI2C
from pico_i2c_lcd import I2cLcd
import json

# Define the LCD I2C address and dimensions
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

# To hold the caluclated unique BT device name
adv_name = ""
connected = False

# Setup I2C LCD device

i2c = SoftI2C(scl=Pin(8), sda=Pin(7), freq=500_000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
lcd.backlight_on()
lcd.clear()
lcd.move_to(0,0)


# Update display outside of recv callback
def update_display(data):

    print(data)
    
    if "BL" in data:
        if data["BL"] == "off":
            lcd.backlight_off()
        else:
            lcd.backlight_on()

    #lcd.clear()
    if "LCD0" in data:
        lcd.move_to(0,0)
        lcd.putstr(data["LCD0"])
    if "LCD1" in data:
        lcd.move_to(0,1)
        lcd.putstr(data["LCD1"])

    

# recieve data callback funcion
def on_receive(rx: bytes, conn_handle: int):

    data = {}
    text = rx.decode("utf-8").strip()
    data = json.loads(text)

    update_display(data)    

    return ("OK:" + text).encode()


# ble disconnect callback function
def on_disconnect(conn_handle: int):

    global connected
    connected = False

    print("Disconnected")
    lcd.clear()
    lcd.move_to(0,0)
    lcd.putstr(f"{adv_name}")



def on_connect(conn_handle: int):
    global connected
    connected = True
    # Optional: brief status flash
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("Connected")


## Setup and advertise. Set disconnect and recieve callbacks.
## Main loop
def main():
    
    global adv_name
    
    ble = BLEUART(base_name="ericbt", include_uuid_in_scan_resp=True, addr_public=True)
    adv_name = ble.adv_name

    ble.set_on_connect(on_connect)
    ble.set_on_disconnect(on_disconnect)
    ble.set_on_receive(on_receive)
    
    lcd.clear()
    lcd.putstr(f"Wait {adv_name}")
    
    s = "https://github.com/electronf99/eric-LCD-BT-thingy "
    i = 0

    while True:
        time.sleep_ms(200)
        if not connected:
            i = (i + 1) % len(s)
            rotated = s[i:] + s[:i]
            lcd.move_to(0,1)
            lcd.putstr(rotated[:16])

if __name__ == "__main__":
    main()