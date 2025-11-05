#include "main.h"
#include <string.h>

extern UART_HandleTypeDef huart1;

void UART_Send(char *msg)
{
    HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), 100);
}
