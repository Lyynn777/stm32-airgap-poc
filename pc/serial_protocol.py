"""
serial_test_sender.py - Simulates STM32 firmware sending encrypted data and hash.
Use this to test receiver.py without hardware.

Run:
    python serial_test_sender.py <COM_PORT>
"""

import serial
import struct
import hashlib
import time
import sys
import os

START_MARK = 0xAA
END_MARK = 0x55

def send_frame(ser, data: bytes):
    ser.write(bytes([START_MARK]))
    ser.write(struct.pack(">I", len(data)))
    ser.write(data)
    ser.write(bytes([END_MARK]))

def main():
    if len(sys.argv) < 2:
        print("Usage: python serial_test_sender.py <COM_PORT>")
        print("Example: python serial_test_sender.py COM6")
        return

    port = sys.argv[1]
    ser = serial.Serial(port, 115200, timeout=1)
    print(f"[INFO] Simulating STM32 on {port}")

    # Generate some dummy binary data
    payload = os.urandom(16 * 1024)  # 16 KB random data
    hash_hex = hashlib.sha256(payload).hexdigest()

    # Sequence like STM32 firmware
    ser.write(b"EVENT:USB_INSERTED\n")
    time.sleep(0.5)
    ser.write(b"CHUNK_START\n")

    # Send as 4KB chunks
    for i in range(0, len(payload), 4096):
        chunk = payload[i:i+4096]
        send_frame(ser, chunk)
        time.sleep(0.02)

    ser.write(b"CHUNK_END\n")
    time.sleep(0.2)
    ser.write(f"HASH:{hash_hex}\n".encode())
    ser.write(b"STATUS:COMPLETE\n")
    print("[DONE] Fake transfer sent. Waiting for PC response...")

    while True:
        line = ser.readline().decode(errors='ignore').strip()
        if line:
            print("[RX from PC]", line)
        time.sleep(0.05)

if __name__ == "__main__":
    main()
