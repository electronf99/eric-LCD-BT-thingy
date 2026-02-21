# main.py — start the BLE UART with ericbt-<3char> name
import time
from ble_uart import BLEUART
from machine import Pin, SoftI2C
from pico_i2c_lcd import I2cLcd
import json

# Define the LCD I2C address and dimensions
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16

adv_name = ""

i2c = SoftI2C(scl=Pin(8), sda=Pin(7), freq=500_000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
lcd.backlight_off()
lcd.clear()
lcd.move_to(0,0)

def update_display(data):

    print(data)
    
    if "BL" in data:
        if data["BL"] == "off":
            lcd.backlight_off()
        else:
            lcd.backlight_on()

    lcd.clear()
    if "LCD0" in data:
        lcd.move_to(0,0)
        lcd.putstr(data["LCD0"])
    if "LCD1" in data:
        lcd.move_to(0,1)
        lcd.putstr(data["LCD1"])

    

def on_receive(rx: bytes, conn_handle: int):

    data = {}
    text = rx.decode("utf-8").strip()
    data = json.loads(text)

    update_display(data)    

    return ("OK:" + text).encode()


def on_disconnect(conn_handle: int):
    print("Display: Disconnectcccced")
    lcd.clear()
    lcd.move_to(0,0)
    lcd.putstr(f"{adv_name}")
    




def main():
    
    global adv_name
    
    ble = BLEUART(base_name="ericbt", include_uuid_in_scan_resp=True, addr_public=True)
    
    adv_name = ble.adv_name

    ble.set_on_disconnect(on_disconnect)
    ble.set_on_receive(on_receive)
    
    lcd.clear()
    lcd.putstr(f"{adv_name}")
    
    while True:
        time.sleep_ms(200)

if __name__ == "__main__":
    main()