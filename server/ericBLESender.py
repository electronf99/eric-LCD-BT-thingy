#!/usr/bin/env python3
import asyncio
from bleak import BleakClient, BleakScanner
import json

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
    await client.write_gatt_char(RX_UUID, payload, response=True)
    # Give ESP32 time to notify back
    await asyncio.sleep(0.1)
    try:
        await client.stop_notify(TX_UUID)
    except Exception:
        pass
    print("Done.")

async def find_device_by_name(name):
    print(f"Scanning for device named '{name}'...")
    devices = await BleakScanner.discover(timeout=15)
    for d in devices:
        if d.name == name:
            print(f"Found device: {d.name} [{d.address}]")
            return d
    print("Device not found.")
    return None

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

        # Notifications callback
        def on_notify(_, data: bytearray):
            try:
                print("Notify:", data.decode("utf-8"))
            except Exception:
                print("Notify bytes:", bytes(data))

        await client.start_notify(TX_UUID, on_notify)

        data = {"LCD0": "", "LCD1": ""}


        loop_count = 0
        while True:
            data["LCD0"] = str(loop_count)
            data_string = json.dumps(data)
            payload = data_string.encode("utf-8")
            await send(client, payload)
            loop_count += 1

if __name__ == "__main__":
    asyncio.run(main())