#!/usr/bin/env python3
import asyncio
from bleak import BleakClient, BleakScanner
import json
import sys
import os
import psutil
from datetime import datetime
import argparse

# --------------------------------------------------------------------
# HARD-CODED PARAMETERS — EDIT THESE
# --------------------------------------------------------------------
DEVICE_NAME = "ericbt-04Ws"   # Your peripheral's advertised name
# If you set this, scanning is skipped entirely:
DEVICE_ADDRESS = None         # e.g. "AA:BB:CC:DD:EE:FF"

# Nordic UART Service UUIDs (must match your peripheral)
NUS_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # write
TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # notify
# --------------------------------------------------------------------

async def send(client, payload: bytes, debug):
    
    if debug:
        print(f"Sending {len(payload)} bytes:", repr(payload))

    try:
        # Write with response to keep ordering/flow control simple
        await client.write_gatt_char(RX_UUID, payload, response=False)
    except Exception as e:
        print("Write failed:", e)
        sys.exit(1)

async def find_device_fast(name: str, service_uuid: str, timeout: float = 5.0):
    """
    Active scan + callback; stop as soon as we see a matching UUID or name.
    Returns a Bleak device or None.
    """
    found = {"dev": None}

    def on_adv(device, adv_data):
        # Prefer UUID match (fast, unambiguous)
        uuids = {u.lower() for u in (adv_data.service_uuids or [])}
        if service_uuid.lower() in uuids:
            found["dev"] = device
            return
        # Fallback: match by local name if present
        if adv_data.local_name == name:
            found["dev"] = device

    scanner = BleakScanner(
        detection_callback=on_adv,
        service_uuids=[service_uuid],   # Helps BlueZ match early
        scanning_mode="active"          # Request scan response (faster metadata)
    )

    await scanner.start()
    try:
        t0 = asyncio.get_running_loop().time()
        while found["dev"] is None and (asyncio.get_running_loop().time() - t0) < timeout:
            await asyncio.sleep(0.05)
    finally:
        await scanner.stop()

    if found["dev"]:
        print(f"Found device: {found['dev'].name} [{found['dev'].address}]")
    else:
        print("Device not found within timeout.")
    return found["dev"]

def get_uptime():

    boot = datetime.fromtimestamp(psutil.boot_time())
    delta = datetime.now() - boot

    # Extract parts
    days = delta.days
    seconds = delta.seconds

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return f"{days} {hours:02d}:{minutes:02d}:{seconds:02d}"


async def main(backlight_off, debug):
    # Fast path: use known MAC to avoid scanning entirely
    if DEVICE_ADDRESS:
        class _Stub:  # lightweight stub with .address
            def __init__(self, address): self.address = address
        device = _Stub(DEVICE_ADDRESS)
    else:
        device = await find_device_fast(DEVICE_NAME, NUS_SERVICE_UUID, timeout=5.0)
        if not device:
            return

    await asyncio.sleep(0.1)  # small settle delay

    print("Connecting...")
    async with BleakClient(device.address) as client:
        if not client.is_connected:
            print("Failed to connect.")
            return
        print("Connected!")
        if backlight_off:
            backlight= "off"
        else:
            backlight = "on"

        data = {"LCD0": "", "LCD1": "", "BL": backlight}

        tick = 0
        cpu = 0

        while True:
            
            
            tick += 1
            if tick % 5 == 0:
                cpu  = psutil.cpu_percent()
                
            data["LCD0"] = f"L1:{os.getloadavg()[0]:.2f} CPU:{cpu:2.0f}%    "[:16]
            data["LCD1"] = f"UP:{get_uptime()}     "[:16]

            payload = json.dumps(data).encode("utf-8")
            await send(client, payload, debug)
            await asyncio.sleep(0.5)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Eric LCD BLE Sender")
    parser.add_argument("--debug", action='store_true',
                        help="Turn on debug")
    parser.add_argument("--backlight-off", action='store_true',
                        help="Turn off Backlight by default")

    args = parser.parse_args()

    try:
        asyncio.run(main(args.backlight_off, args.debug))
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)