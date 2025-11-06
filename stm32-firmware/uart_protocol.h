// uart_protocol.h
#pragma once
#include <stdint.h>
#include <stddef.h>

/*
 * Simple UART framing protocol used between STM32 and PC controller.
 * Chunk frame format:
 *  [0]       : 0xAA (start marker)
 *  [1..4]    : 32-bit big-endian length (N)
 *  [5..(4+N)]: N bytes of raw ciphertext
 *  [5+N]     : 0x55 (end marker) - optional
 *
 * Control messages are ASCII lines ending in '\n':
 *  - EVENT:USB_INSERTED\n
 *  - AUTH:OK\n
 *  - AUTH:FAIL\n
 *  - HASH:<hex>\n
 *  - STATUS:COMPLETE\n
 *  - ACTION:RELAY_CUT\n
 *
 * PC -> STM32:
 *  - ALLOW\n
 *  - CUT\n
 */

#define UART_START_MARK 0xAA
#define UART_END_MARK   0x55

// keep chunk size moderate for RAM
#define CHUNK_SIZE 4096U

// UART instances (match CubeMX-generated handles in main.c)
extern void uart_send_text(const char *s);
extern void uart_send_chunk(const uint8_t *data, uint32_t len);

// Serial command handler hook
// Call this from UART Rx ISR or polling when a full line is read
extern void handle_serial_command(const char *cmd_line);

