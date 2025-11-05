/* Core/Inc/usb_host.h
 *
 * USB Host helper interface (stubbed).
 * Implement real detection using CubeMX USB Host middleware.
 */

#ifndef __USB_HOST_H
#define __USB_HOST_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

/* Returns 1 if a USB MSC device (thumbdrive) is present and ready.
 * Replace stub with middleware-specific check (e.g., application_state == APPLICATION_READY).
 */
uint8_t USB_Device_Connected(void);

/* Optional: callback called by USB Host stack when device connected/disconnected.
 * Prototype kept here for reference; implement in usb_host.c if using callbacks.
 */
void USBH_UserProcess(USBH_HandleTypeDef *phost, uint8_t id);

#ifdef __cplusplus
}
#endif

#endif /* __USB_HOST_H */
