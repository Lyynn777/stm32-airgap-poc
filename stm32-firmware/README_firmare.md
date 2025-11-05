# stm32-firmware — NUCLEO-F767ZI project skeleton

This folder contains the STM32CubeIDE-friendly firmware skeleton for the STM32-based USB mediator (NUCLEO-F767ZI recommended).
It demonstrates the full firmware pipeline:
- USB Host MSC <-> FATFS file access (chunked)
- Fingerprint verification hook (UART)
- Manual button gating
- AES-encrypt chunks + streaming to PC over UART
- SHA-256 over ciphertext and send final HASH
- Accept `ALLOW` / `CUT` commands from PC; toggle relay accordingly

---

## Files included
- `main.c`                : main firmware logic (paste into CubeIDE)
- `uart_protocol.h`       : framing & helper prototypes
- `crypto_stub.h` / `crypto_stub.c` : crypto API stubs (replace with mbedTLS)
- `README_firmware.md`    : this file

---

## CubeMX settings you must enable
Create a new CubeMX project targeting **NUCLEO-F767ZI** (or equivalent OTG-capable board).
Enable the following peripherals (and generate code):

**Peripherals**
- **USB HOST (FS)** -> Class: **MSC** (Mass Storage Class)  
  - Middleware: **USB Host** + **FatFs**
- **USART1**: Asynchronous, 115200 8N1 (PC comms)
  - PA9 TX, PA10 RX (matches main.c)
- **USART2**: Asynchronous, for Fingerprint module (optional)
  - Configure pins as needed (e.g., PA2 TX, PA3 RX)
- **GPIO**
  - PA0 -> User button (input, Pull-down)  
  - PA1 -> Status LED (output)  
  - PB0 -> Relay control (output)
- Optional: DMA for FatFs / USB if you want performance

**Middleware**
- FatFs: enable logical drive (link with USB Host MSC)
- USB Host: enable MSC class and example usage

After generating code in CubeIDE, replace the auto-generated `main.c` logic with the provided `main.c` (or carefully merge functions).

---

## How to compile & flash
1. Install **STM32CubeIDE** (from ST website).
2. Open the CubeMX project created earlier.
3. Add the provided `crypto_stub.h/c`, `uart_protocol.h`, and replace `main.c` (or merge).
4. Build project: `Project -> Build`.
5. Connect Nucleo board via USB; ensure ST-Link driver is installed.
6. Flash: `Run -> Debug` (or use STM32CubeProgrammer).

---

## Replacing crypto stubs with mbedTLS (recommended)
The provided `crypto_stub.c` contains placeholder, non-secure implementations for AES and SHA-256.
Before any real testing with actual malware or sensitive data, replace these with real crypto:

- Add mbedTLS to the project (Project -> Manage Embedded Software Packages or import mbedTLS sources).
- Replace `aes_init`, `aes_encrypt_stream`, `aes_free` with proper AES-CTR/AES-GCM streaming calls (mbedtls_aes_crypt_ctr or mbedtls_gcm_crypt).
- Replace `sha256_*` with `mbedtls_sha256_*` APIs.
- Update `crypto_stub.h` types to wrap mbedTLS contexts.

---

## UART protocol & PC-side expectation
- STM32 sends framed chunks using START_MARK (0xAA) + 4-byte length + data + END_MARK (0x55).
- After CHUNK_END, STM32 sends `HASH:<hex>\n`.
- PC should compute SHA-256 over received ciphertext and compare; if mismatch send `CUT\n`.
- PC should send `ALLOW\n` to keep connection.

A small Python test helper (`pc/serial_test_sender.py`) is provided elsewhere in the repo for development.

---

## Wiring notes (hardware)
- Use **USB Type-A female breakout**; route VBUS (+5V) through the relay COM/NO contact.
- Relay IN -> Nucleo PB0 (via transistor if relay requires 5V trigger).
- Relay VCC -> 5V supply, GND common with Nucleo GND.
- Fingerprint module TTL TX/RX -> USART2 pins (crossed).
- For safety, test relay with LED first before connecting a real USB thumb drive.

---

## Acceptance tests
1. Build & flash binary. Confirm serial shows `STATUS:READY`.
2. Insert FAT32 USB with `/test.bin`. Observe `EVENT:USB_INSERTED`.
3. Simulate fingerprint (currently stub returns true) and press button -> `AUTH:OK` and `CHUNK_START` / chunks / `HASH:...` / `STATUS:COMPLETE` should appear.
4. Use PC test script to verify hash and send `CUT` / `ALLOW`; STM32 should toggle relay and report `ACTION:RELAY_CUT` or `ACTION:RELAY_ALLOW`.

---

## Next steps (after IDE/hardware ready)
- Replace crypto stubs with mbedTLS (AES-GCM or AES-CTR + HMAC).
- Implement proper USB Host MSC detection using the CubeMX middleware event `APPLICATION_READY`.
- Implement fingerprint UART protocol (enroll & verify).
- Optimize DMA + buffer usage if you need higher throughput.

