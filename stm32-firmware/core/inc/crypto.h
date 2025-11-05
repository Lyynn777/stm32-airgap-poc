/* Core/Inc/crypto.h
 *
 * Crypto & scan interfaces (stubs for now).
 * Replace stubbed functions with real AES/SHA and scanning logic later.
 */

#ifndef __CRYPTO_H
#define __CRYPTO_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stddef.h>

/* Simple API prototypes used by main.c */

/* Scans files on the USB drive for quick heuristics.
 * Return: 0 = safe, 1 = malware detected
 * Implement actual scanning or delegate to PC agent later.
 */
uint8_t File_Scan_For_Threats(void);

/* Encrypt the file on the USB and stream to the PC.
 * This is a high-level stub. Implement chunked AES + SHA streaming.
 */
void Encrypt_And_Send_To_PC(void);

#ifdef __cplusplus
}
#endif

#endif /* __CRYPTO_H */
