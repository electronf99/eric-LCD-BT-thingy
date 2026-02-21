# ble_uart.py — ESP32 MicroPython BLE UART service with 4-char MAC-based suffix
# This is code mostly generateed by Copilot

import bluetooth
import struct
import time
from micropython import const

# Nordic UART Service (NUS) UUIDs
_UART_SERVICE_UUID      = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX_CHAR_UUID      = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")  # write
_UART_TX_CHAR_UUID      = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")  # notify

# IRQ events
_IRQ_CENTRAL_CONNECT    = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE        = const(3)

# Properties
_FLAG_READ              = const(0x0002)
_FLAG_WRITE             = const(0x0008)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_NOTIFY            = const(0x0010)

_MAX_ADV_BYTES          = const(31)

# ---- base62 helpers (no slicing, no rjust) ----
_B62_ALPH_STR = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

def _u16_to_base62(v: int) -> str:
    if v == 0:
        return "0"
    s = ""
    while v:
        v, r = divmod(v, 62)
        s = _B62_ALPH_STR[r] + s
    return s

def _pad_left_zeros(s: str, width: int) -> str:
    if not isinstance(s, str):
        s = str(s)
    while len(s) < width:
        s = "0" + s
    return s

def _make_suffix_from_mac(mac: bytes) -> str:
    if not isinstance(mac, (bytes, bytearray)) or len(mac) < 2:
        return "0000"
    last2 = (int(mac[-2]) << 8) | int(mac[-1])
    return _pad_left_zeros(_u16_to_base62(last2), 4)

class BLEUART:
    """
    BLE UART-like service:
      - TX characteristic: Notify + Read (ESP32 -> client)
      - RX characteristic: Write (+ Write Without Response) (client -> ESP32)
    Advertises as 'ericbt-<4char>'.
    """
    def __init__(self, base_name="ericbt", include_uuid_in_scan_resp=True, addr_public=True,
                 rx_buf_size=128):
        self._ble = bluetooth.BLE()
        self._ble.active(True)

        # Prefer a public address
        if addr_public:
            try:
                self._ble.config(addr_mode=bluetooth.ADDR_PUBLIC)
            except Exception:
                pass

        # BLE MAC (port dependent)
        mac = None
        try:
            mac_val = self._ble.config("mac")
            if isinstance(mac_val, (bytes, bytearray)):
                mac = bytes(mac_val)
            elif isinstance(mac_val, tuple) and len(mac_val) == 2:
                mac = bytes(mac_val[1])
        except Exception:
            mac = None

        if mac is None:
            try:
                import network
                mac = bytes(network.WLAN(network.STA_IF).config("mac"))
            except Exception:
                mac = b"\x00\x00\x00\x00\x00\x00"

        suffix = _make_suffix_from_mac(mac)
        adv_name = "{}-{}".format(base_name, suffix)
        self.adv_name = adv_name

        self._ble.irq(self._irq)

        # Register service & characteristics
        self._rx = (_UART_RX_CHAR_UUID, _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE)
        self._tx = (_UART_TX_CHAR_UUID, _FLAG_NOTIFY | _FLAG_READ)
        self._service = (_UART_SERVICE_UUID, (self._tx, self._rx))
        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services((self._service,))

        # Allow larger writes & long writes
        try:
            self._ble.gatts_set_buffer(self._rx_handle, rx_buf_size, True)
        except AttributeError:
            pass

        # Prefer MTU (client still decides)
        try:
            self._ble.config(mtu=rx_buf_size)
        except Exception:
            pass

        self._connections = set()
        self._on_receive = None
        self._on_connect = None          # NEW
        self._on_disconnect = None       # NEW

        # Advertising payloads
        self._adv = self._build_adv_payload(name=adv_name)
        self._resp = self._build_scan_resp_payload(services=[_UART_SERVICE_UUID]) if include_uuid_in_scan_resp else None

        self._advertise()

        try:
            mac_str = ":".join("{:02X}".format(int(b)) for b in mac)
        except Exception:
            mac_str = "<unknown>"
        print("Advertising as:", adv_name)
        print("BLE MAC:", mac_str)
        print("TX handle:", self._tx_handle, "RX handle:", self._rx_handle)

    # -------- Public API --------
    def set_on_receive(self, handler):
        """handler(data_bytes: bytes, conn_handle: int) -> Optional[bytes]"""
        self._on_receive = handler

    def set_on_connect(self, handler):
        """handler(conn_handle: int) -> None"""
        self._on_connect = handler

    def set_on_disconnect(self, handler):
        """handler(conn_handle: int) -> None"""
        self._on_disconnect = handler

    def notify(self, data: bytes, conn_handle: int = None):
        if conn_handle is None:
            for ch in list(self._connections):
                try:
                    self._ble.gatts_notify(ch, self._tx_handle, data)
                except OSError:
                    pass
        else:
            try:
                self._ble.gatts_notify(conn_handle, self._tx_handle, data)
            except OSError:
                pass

    def advertise_stop(self):
        try:
            self._ble.gap_advertise(None)
        except Exception:
            pass

    # -------- IRQ handler --------
    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print("Central connected:", conn_handle)
            if self._on_connect:
                try:
                    self._on_connect(conn_handle)
                except Exception as e:
                    print("on_connect error:", e)

        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.discard(conn_handle)
            print("Central disconnected:", conn_handle)
            if self._on_disconnect:
                try:
                    self._on_disconnect(conn_handle)
                except Exception as e:
                    print("on_disconnect error:", e)
            self._advertise()

        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if value_handle == self._rx_handle:
                incoming = self._ble.gatts_read(self._rx_handle)
                if self._on_receive:
                    try:
                        resp = self._on_receive(incoming, conn_handle)
                        if isinstance(resp, (bytes, bytearray)) and len(resp) > 0:
                            self.notify(resp, conn_handle)
                    except Exception as e:
                        print("on_receive error:", e)
                else:
                    self.notify(b"OK:" + incoming, conn_handle)

    # -------- Advertising helpers --------
    def _advertise(self, interval_us=30_000):
        self.advertise_stop()
        try:
            if self._resp:
                self._ble.gap_advertise(interval_us, adv_data=self._adv, resp_data=self._resp)
            else:
                self._ble.gap_advertise(interval_us, adv_data=self._adv)
        except OSError as e:
            print("Advertising failed:", e)
            try:
                name_only = self._build_adv_payload(name="ericbt")
                self._ble.gap_advertise(interval_us, adv_data=name_only)
                print("Fell back to name-only advertising.")
            except OSError as e2:
                print("Fallback advertising also failed:", e2)
                raise

    @staticmethod
    def _append(payload: bytearray, adv_type: int, value: bytes):
        payload.extend(struct.pack("BB", len(value) + 1, adv_type))
        payload.extend(value)

    def _build_adv_payload(self, name=None):
        p = bytearray()
        flags = 0x02 | 0x04
        self._append(p, 0x01, struct.pack("B", flags))
        if name:
            n = name.encode()
            adv_type = 0x09 if len(n) <= 26 else 0x08
            self._append(p, adv_type, n)
        if len(p) > _MAX_ADV_BYTES:
            raise ValueError("adv_data exceeds 31 bytes; shorten name.")
        return p

    def _build_scan_resp_payload(self, services=None):
        p = bytearray()
        if services:
            for u in services:
                self._append(p, 0x07, bytes(u))
        if len(p) > _MAX_ADV_BYTES:
            raise ValueError("resp_data exceeds 31 bytes; remove UUIDs or fields.")
        return p