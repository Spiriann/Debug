// Ejemplo de uso en ESP32-CAM (PlatformIO + EloquentEsp32cam). Los motores/pines son del proyecto original.
#include <Arduino.h>
#include "eloquent_esp32cam.h"
#include "../pid_controller.h"

using eloq::camera;
using namespace linefollow;

LineDetector detector;
LinePid pid;

void setup() {
  Serial.begin(115200);
  camera.pinout.wrover();
  camera.brownout.disable();
  camera.resolution.qqvga();   // 160x120
  camera.pixformat.grayscale();
  while (!camera.begin().isOk()) delay(2000);
}

void loop() {
  if (!camera.capture().isOk()) return;
  int w = camera.resolution.getWidth(), h = camera.resolution.getHeight();

  LineResult line = detector.detect(camera.frame->buf, w, h);
  Control ctl = pid.update(line);

  int left, right;
  mixMotors(ctl.speed, ctl.steering, 0.90f, left, right);
  // ... escribir left/right a sus motores (ledcWrite, etc.)

  camera.free();
}
