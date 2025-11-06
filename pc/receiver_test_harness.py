"""
receiver.py - PC-side controller that listens to STM32 over serial,
receives framed encrypted data chunks, verifies hash, and issues ALLOW/CUT.
"""

import serial
import struct
import hashlib
import time
import sys

START_MARK = 0xAA
END_MARK = 0x55

def read_frame(ser):
    """Read one UART frame starting with 0xAA marker."""
    # Wait for start marker
    b = ser.read(1)
    if not b or b[0] != START_MARK:
        return None
    hdr = ser.read(4)
    if len(hdr) != 4:
        return None
    length = struct.unpack(">I", hdr)[0]
    data = ser.read(length)
    tail = ser.read(1)
    if len(tail) != 1 or tail[0] != END_MARK:
        print("[WARN] Bad tail marker")
    return data

def main():
    if len(sys.argv) < 2:
        print("Usage: python receiver.py <COM_PORT>")
        print("Example: python receiver.py COM5")
        return

    port = sys.argv[1]
    ser = serial.Serial(port, 115200, timeout=1)
    print(f"[INFO] Listening on {port}")

    ciphertext = b''
    file_counter = 0
    current_hash_expected = None

    while True:
        line = ser.readline().decode(errors='ignore').strip()
        if not line:
            continue

        if line.startswith("EVENT:USB_INSERTED"):
            print("[STM32] USB Inserted")
            ciphertext = b''
            current_hash_expected = None

        elif line == "CHUNK_START":
            print("[STM32] Beginning file stream...")
            while True:
                frame = read_frame(ser)
                if frame:
                    ciphertext += frame
                else:
                    # timeout or broken
                    break

        elif line.startswith("HASH:"):
            current_hash_expected = line.split("HASH:")[1].strip()
            print(f"[STM32] Expected HASH: {current_hash_expected}")

            # Compute actual hash from received ciphertext
            h = hashlib.sha256(ciphertext).hexdigest()
            print(f"[PC] Calculated HASH: {h}")

            if h != current_hash_expected:
                print("[!] HASH mismatch! Sending CUT")
                ser.write(b"CUT\n")
            else:
                print("[OK] HASH match. Sending ALLOW")
                ser.write(b"ALLOW\n")

            # Save file for reference
            file_counter += 1
            with open(f"received_{file_counter}.bin", "wb") as f:
                f.write(ciphertext)
            ciphertext = b''

        elif line.startswith("ACTION:RELAY_CUT"):
            print("[STM32] Relay CUT acknowledged.")

        elif line.startswith("ACTION:RELAY_ALLOW"):
            print("[STM32] Relay ALLOW acknowledged.")

        elif line.startswith("STATUS:COMPLETE"):
            print("[STM32] Transfer complete.\n")

        elif "ERROR" in line:
            print(f"[STM32 ERROR] {line}")

        time.sleep(0.05)

if __name__ == "__main__":
    main()
