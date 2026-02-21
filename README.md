# BLE Thingy for Eric's Wacky LCD

More stuff built with things laying around (including some of the code).

I used the wierd jumbo LCD, one of the many LCD I2C piggybacks laying around and a mini waveshare esp32 I had in my box of development boards. 
* Had to cut pins 15 and 16 off the piggyback and were those pins beck to the other end of the LCD pins.
* Wired thge esp to the piggyback and glued the ESP to the back of the LCD.

The code is mostly a combination of code used in other projects and stuff written by copilot.

## Eric's not quite right jumbo LCD1602 with BL pins at the wrong end.

Using ESP32 Micropython and a PC based python sender

## ESP32 Micropython BLE reciever

Upload the following files to the esp:
* ble_uart.py
* pico_i2c_lcd.py
* lcd_api.py

Upload ericBTThingy to the esp32 (as main.py if you want it to autostart)

## PC Python BLE senderS

On the pc end:
* install bluetooth stuff if not already
* install bleak (pip3 install bleak)

The sender code sends a dict like this:

```
{"LCD0": "", "LCD1": "", "BL" : "on"}
```

Values are the LCD text you want and allows you to turn the backlight on or off.

Power on the ESP and then run sender/ericBLESender.py on the pc.

It should eventually connect and start sending data.

>I write and test code inside vscode however you can connect to the esp using mpremote to upload file, run a > file and connect to watch the running code or access the REPL.


## Threaded Collector

Other stuff like this I have uses a threaded collector in the python on the PC to collect data in the background (eg from a router) and have the main code retrieve it's values from there.


