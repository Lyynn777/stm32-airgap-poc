/* main.c - STM32 USB Malware Gatekeeper Firmware (Skeleton) */

#include "main.h"
#include "usb_host.h"
#include "fingerprint.h"
#include "relay.h"
#include "crypto.h"
#include <stdio.h>

UART_HandleTypeDef huart1; // UART for debugging + fingerprint
USBH_HandleTypeDef hUsbHostHS;

void SystemClock_Config(void);
void MX_GPIO_Init(void);
void MX_USART1_UART_Init(void);

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    MX_GPIO_Init();
    MX_USART1_UART_Init();

    UART_Send("System Booted\r\n");
    UART_Send("Initializing USB Host...\r\n");

    USBH_Init(&hUsbHostHS, USBH_UserProcess, 0);
    USBH_RegisterClass(&hUsbHostHS, USBH_MSC_CLASS);
    USBH_Start(&hUsbHostHS);

    Relay_DisconnectUSB(); // initially protect system

    while (1)
    {
        USBH_Process(&hUsbHostHS);
        
        if(USB_Device_Connected())
        {
            UART_Send("USB Drive Detected\r\n");

            Relay_AllowUSB();  // connect USB to PC

            UART_Send("Waiting for fingerprint auth...\r\n");

            if(Fingerprint_Authenticate())
            {
                UART_Send("Fingerprint Auth Success\r\n");
                UART_Send("Scanning USB Files...\r\n");

                if(File_Scan_For_Threats()) 
                {
                    UART_Send("Threat detected! Disconnecting USB\r\n");
                    Relay_DisconnectUSB();
                }
                else
                {
                    UART_Send("No threat. Transferring & Encrypting...\r\n");
                    Encrypt_And_Send_To_PC();
                }
            }
            else
            {
                UART_Send("Fingerprint Failed. Disconnecting USB\r\n");
                Relay_DisconnectUSB();
            }
        }
    }
}
