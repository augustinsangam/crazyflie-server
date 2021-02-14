#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <time.h>

#include "app.h"

#include "FreeRTOS.h"
#include "task.h"

#include "debug.h"

#include "log.h"
#include "param.h"

#include "led.h"
#include "unistd.h"
#include "app_channel.h"
#include "pm.h"

struct testPacketRX
{
  bool setLeds;
} __attribute__((packed));

struct testPacketTX
{
  unsigned long long timestemp;
  float speed;
  float battery;
  float positionX;
  float positionY;
  float positionZ;
  bool flying;
  bool ledOn;

} __attribute__((packed));

void appMain()
{

  ledClearAll();

  DEBUG_PRINT("Waiting for activation ...\n");

  struct testPacketRX rxPacket;
  struct testPacketTX txPacket;

  while (1)
  {

    if (appchannelReceivePacket(&rxPacket, sizeof(rxPacket), 0))
    {
      DEBUG_PRINT("App channel received setLeds: %d\n", (int)rxPacket.setLeds);
      if (rxPacket.setLeds)
      {
        ledSetAll();
        txPacket.ledOn = true;
      }
      else
      {
        ledClearAll();
        txPacket.ledOn = false;
      }
    }

    vTaskDelay(M2T(1000));

    txPacket.timestemp = (unsigned long long)time(NULL);
    txPacket.speed = 0.0;
    txPacket.battery = pmBatteryChargeFromVoltage(pmGetBatteryVoltage()) * 10;
    txPacket.positionX = 0.0;
    txPacket.positionY = 0.0;
    txPacket.positionZ = 0.0;
    txPacket.flying = false;
    DEBUG_PRINT("Sending packets");

    appchannelSendPacket(&txPacket, sizeof(txPacket));
  }
}
