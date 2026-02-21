#!/usr/bin/env python3
import asyncio
from bleak import BleakClient, BleakScanner
import json
import sys
from datetime import datetime


# --------------------------------------------------------------------
# HARD‑CODED PARAMETERS — EDIT THESE
# --------------------------------------------------------------------
DEVICE_NAME = "ericbt-04Ws"   # <-- CHANGE TO MATCH YOUR ESP32 name

# Nordic UART Service UUIDs (must match your ESP32 MicroPython code)
RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # write
TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # notify
# --------------------------------------------------------------------

async def send(client, payload: bytes):
    
    print(f"Sending {len(payload)} bytes:", repr(payload))
    try:
        await client.write_gatt_char(RX_UUID, payload, response=True)
    except Exception as e:
        print(e)
        print("exiting")
        sys.exit()
    
    # Give ESP32 time to notify back
    await asyncio.sleep(0.05)
    try:
        await client.stop_notify(TX_UUID)
    except Exception:
        pass

async def find_device_by_name(name):
    print(f"Scanning for device named '{name}'...")
    devices = await BleakScanner.discover(timeout=25)
    for d in devices:
        if d.name == name:
            print(f"Found device: {d.name} [{d.address}]")
            return d
    print("Device not found.")
    return None

#################
## Main
#################

async def main():
    device = await find_device_by_name(DEVICE_NAME)
    if not device:
        return
    
    await asyncio.sleep(0.5)

    print("Connecting...")
    async with BleakClient(device.address) as client:
        if not client.is_connected:
            print("Failed to connect.")
            return
        print("Connected!")

        data = {"LCD0": "", "LCD1": "", "BL" : "on"}
        loop_count = 0

        s = "Hello Eric.. https://github.com/electronf99/eric-LCD-BT-thingy "  # A 16-character string (representing 16 bytes)
        i = 0
        #
        # Do Stuff Here..
        #

        while True:

            data_string = json.dumps(data)
            payload = data_string.encode("utf-8")
            
            # No need to throttle, ble class send takes care  of that
            i += 1
            if i == len(s):
                i=0
            rotated_string = s[i:] + s[:i]  # Slice and concatenate
            print(rotated_string)
            data["LCD0"] = rotated_string[:16]

            now = datetime.now().strftime("%H:%M:%S")
            data["LCD1"] = now

            await send(client, payload)
            
            loop_count += 1
            

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)
