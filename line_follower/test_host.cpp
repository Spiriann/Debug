// Prueba en PC: g++ -std=c++11 test_host.cpp -o t && ./t
#include <cstdio>
#include <cstring>
#include "pid_controller.h"
using namespace linefollow;

static void draw(uint8_t* img, int w, int h, float xTop, float xBot, int half) {
  memset(img, 0, w * h);
  for (int y = 0; y < h; y++) {
    float x = xTop + (xBot - xTop) * y / (h - 1);
    for (int dx = -half; dx <= half; dx++) { int px = (int)x + dx; if (px >= 0 && px < w) img[y * w + px] = 255; }
  }
}

int main() {
  const int W = 160, H = 120;
  static uint8_t img[W * H];
  LineDetector det; LinePid pid;
  struct { const char* name; float xt, xb; } cases[] = {
    {"centrada recta", 80, 80}, {"desplazada derecha", 110, 110}, {"curva a la derecha", 100, 70}, {"curva a la izquierda", 60, 90},
  };
  for (auto& c : cases) {
    draw(img, W, H, c.xt, c.xb, 4);
    LineResult r = det.detect(img, W, H); pid.reset(); Control u = pid.update(r);
    printf("%-22s found=%d err=%6.1f ang=%6.1f sev=%.2f -> steer=%7.1f speed=%d\n", c.name, r.found, r.error, r.angleDeg, r.severity, u.steering, u.speed);
  }
  memset(img, 0, sizeof img);
  LineResult r = det.detect(img, W, H); Control u = pid.update(r);
  printf("%-22s found=%d -> steer=%.1f speed=%d\n", "sin línea", r.found, u.steering, u.speed);
  return 0;
}
