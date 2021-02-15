#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#include "app.h"

#include "FreeRTOS.h"
#include "task.h"

#include "debug.h"

#include "log.h"
#include "param.h"
#include "pm.h"

#include "app_channel.h"
#include "led.h"
//#include "pm_stm32f4.c"
#include "unistd.h"

const static float bat671723HS25C[10] = {
    3.00, // 00%
    3.78, // 10%
    3.83, // 20%
    3.87, // 30%
    3.89, // 40%
    3.92, // 50%
    3.96, // 60%
    4.00, // 70%
    4.04, // 80%
    4.10  // 90%
};

static int32_t pmBatteryChargeFromVoltage(float voltage)
{
  int charge = 0;

  if (voltage < bat671723HS25C[0])
  {
    return 0;
  }
  if (voltage > bat671723HS25C[9])
  {
    return 9;
  }
  while (voltage > bat671723HS25C[charge])
  {
    charge++;
  }

  return charge;
}

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
