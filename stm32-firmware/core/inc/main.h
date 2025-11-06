#ifndef MAIN_H
#define MAIN_H

#include "stm32f4xx_hal.h"

void UART_Send(char *msg);
uint8_t USB_Device_Connected(void);
uint8_t File_Scan_For_Threats(void);
void Encrypt_And_Send_To_PC(void);

#endif
