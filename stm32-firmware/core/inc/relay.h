/* Core/Inc/relay.h
 *
 * Relay control abstraction: toggles a GPIO to switch VBUS.
 * Keep logic simple: Allow vs Disconnect.
 */

#ifndef __RELAY_H
#define __RELAY_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

/* Initialize relay hardware (GPIO config) if needed */
void Relay_Init(void);

/* Connect (allow) USB VBUS through relay */
void Relay_AllowUSB(void);

/* Disconnect USB VBUS immediately (cut) */
void Relay_DisconnectUSB(void);

/* Helper: return current relay state (0 = disconnected, 1 = allowed) */
uint8_t Relay_GetState(void);

#ifdef __cplusplus
}
#endif

#endif /* __RELAY_H */
