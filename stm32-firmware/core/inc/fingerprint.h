/* Core/Inc/fingerprint.h
 *
 * Fingerprint module interface (TTL UART modules like R305/GT-521).
 * Provide a blocking authenticate API for the main loop.
 */

#ifndef __FINGERPRINT_H
#define __FINGERPRINT_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

/* Initialize fingerprint module if needed (UART, GPIO). Optional */
void Fingerprint_Init(void);

/* Blocking authentication call.
 * Return: 1 = authenticated (match), 0 = not matched / error.
 *
 * NOTE: Implement the UART protocol for your chosen sensor.
 * For early testing you may return 1 always (simulation mode).
 */
uint8_t Fingerprint_Authenticate(void);

#ifdef __cplusplus
}
#endif

#endif /* __FINGERPRINT_H */
