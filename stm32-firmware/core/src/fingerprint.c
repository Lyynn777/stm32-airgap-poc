#include "fingerprint.h"
#include "main.h"

uint8_t Fingerprint_Authenticate(void)
{
    UART_Send("[FP] Scan Finger\n");
    // TODO: Add fingerprint sensor protocol
    return 1; // pretend success now
}
