## BLE Thingy for Eric's Wacky LCD 

More stuff built with things laying around (including some of the code).

# If you are reading this then you are probabaly Eric.

There is something not quite right about Eric's jumbo LCD1602. The BL pins are at the wrong end, meaning it becomes a heat source not a display device.


## TL;DR:

On the PC end:
* install bluetooth packages
* pip3 install bleak psutil
* clone repo, check the device name on the thingy and update and run sender/sender.py
* run sender.py

# Details

I used the wierd jumbo LCD, one of the many LCD I2C piggybacks laying around and a mini waveshare esp32 I had in my box of development boards. 
* Had to cut pins 15 and 16 off the piggyback and wire those pins beck to the other end of the LCD pins.
* Wired the esp to the piggyback and glued the ESP to the back of the LCD.

The code is mostly a combination of code used in other projects and stuff written by copilot.


## ESP32 Micropython BLE reciever

Upload the following files to the esp:
* ble_uart.py
* pico_i2c_lcd.py
* lcd_api.py

Upload ericBTThingy to the esp32 (as main.py if you want it to autostart)

## PC Python BLE sender

On the pc end:
* install bluetooth stuff if not already
* install bleak (pip3 install bleak)

The sender code sends a dict like this:

```
{"LCD0": "", "LCD1": "", "BL" : "on"}
```

Values are the LCD text you want and allows you to turn the backlight on or off.

Power on the ESP and then run sender/ericBLESender.py on the pc.

```
usage: ericBLESender.py [-h] [--debug] [--backlight-off]

Eric LCD BLE Sender

options:
  -h, --help       show this help message and exit
  --debug          Turn on debug
  --backlight-off  Turn off Backlight by default
```

It should eventually connect and start sending data.

>I write and test code inside vscode however you can connect to the esp using mpremote to upload file, run a > file and connect to watch the running code or access the REPL.


## 📦 Dependencies & Installation

Your Python BLE system requires a few system-level packages and Python libraries.  


### 🟩 Linux (Ubuntu/Debian)

1) **Install Python 3 and pip**
```bash
sudo apt update
sudo apt install -y python3 python3-pip
```

2) **Install required Python packages**
```bash
python3 -m pip install --upgrade pip
python3 -m pip install bleak psutil
```

3) **Install Bluetooth stack & tools**
```bash
sudo apt install -y bluetooth bluez bluez-tools
```

4) **Allow your user to access Bluetooth**
```bash
sudo usermod -aG bluetooth $USER
```
Log out and back in for the group change to take effect.

**Optional:** enable BLE scanning without root
```bash
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(which python3)
```

---

## 🧩 Python Dependencies Summary

Your script depends on:

| Package | Purpose |
|--------|---------|
| **bleak** | Cross-platform BLE (Bluetooth Low Energy) scanning and GATT connection |
| **psutil** | CPU %, load average, boot time, memory, process and system stats |
| **json** | Encoding BLE payloads |
| **asyncio** | Asynchronous BLE communication |

Install with:
```bash
python3 -m pip install bleak psutil
```


## Threaded Collector

For other stuff like this I have usds a threaded collector in the PC python code collect data in the background (eg from a router) and have the main code retrieve it's values from collector.





