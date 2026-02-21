# BLE Thingy for Eric's Wacky LCD

More stuff built with things laying aroud

## Eric's not quite right jumbo LCD1602 with BL pins at the wrong end.

Using ESP32 Micropython and a PC based python sender

## ESP32 Micropython BLE reciever

Upload the following files to the esp:
* ble_uart.py
* pico_i2c_lcd.py
* lcd_api.py

Upload ericBTThingy to the esp32 (as main if you want it to autostart)

## PC Python BLE sender

On the pc end:
* install bluetooth stuff if not already
* install bleak (pip3 install bleak)

Power on the ESP and then run sender/ericBLESender.py on the pc.

It should eventually connect and start sending data.

I write and test code inside vscode however you can connect to the esp using mpremote to upload file, run a file and connect to watch the running code or access the REPL.

## Threaded Collector

YOu could add a threaded collector to the python on the PC to collect data in the background and have the main code retrieve it's values from there.


