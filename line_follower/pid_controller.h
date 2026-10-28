// Controlador PID de seguimiento de línea (portable, sin dependencias de hardware).
// Extraído de muhammad-fawaz/line-following-esp32cam (src/main.cpp, loop()).
//
//   steering = Kp_pos*error + Kp_ang*angulo + Ki*integral + Kd*(error - errorPrevio)
//
// Combina el error de posición (dónde está la línea ahora) con el ángulo (hacia dónde va),
// para anticipar curvas. Nota: como en el original, el término derivativo es por frame (sin dt).
#pragma once
#include "line_detector.h"

namespace linefollow {

struct PidConfig {
  float kpPos = 1.20f;       // ganancia sobre el error de posición (px)
  float kpAng = 0.45f;       // ganancia sobre el ángulo (grados)
  float ki    = 0.00f;
  float kd    = 0.50f;
  float integralLimit = 100.0f;  // anti-windup: |integral| <= limit
  int   baseSpeed = 110;     // velocidad en recta (PWM 0-255)
  int   minSpeed  = 40;      // velocidad mínima en curva cerrada
  float lostPivot = 120.0f;  // giro sobre el eje al perder la línea
};

struct Control {
  float steering = 0.0f;  // + gira a la derecha (motor izq. más rápido), - a la izquierda
  int   speed    = 0;     // velocidad base ya ajustada por severidad de curva
};

class LinePid {
 public:
  PidConfig cfg;

  LinePid() {}
  explicit LinePid(const PidConfig& c) : cfg(c) {}

  void reset() { integral_ = 0; prevError_ = 0; }

  Control update(const LineResult& line) {
    Control c;
    if (!line.found) {
      // Línea perdida: detenerse y pivotar hacia el último lado en que se vio.
      c.speed = 0;
      c.steering = (prevError_ > 0) ? cfg.lostPivot : -cfg.lostPivot;
      return c;
    }

    // Velocidad dinámica: más lenta cuanto más cerrada la curva.
    c.speed = cfg.baseSpeed - (int)(line.severity * (cfg.baseSpeed - cfg.minSpeed));

    integral_ += line.error;
    if (integral_ >  cfg.integralLimit) integral_ =  cfg.integralLimit;
    if (integral_ < -cfg.integralLimit) integral_ = -cfg.integralLimit;

    float derivative = line.error - prevError_;
    c.steering = cfg.kpPos * line.error + cfg.kpAng * line.angleDeg
               + cfg.ki * integral_ + cfg.kd * derivative;
    prevError_ = line.error;
    return c;
  }

 private:
  float integral_  = 0;
  float prevError_ = 0;
};

// Mezcla diferencial: convierte (velocidad, steering) en PWM de cada motor, rango -255..255.
// leftBias compensa diferencias entre motores (0.90 en el original).
inline void mixMotors(int speed, float steering, float leftBias, int& left, int& right) {
  float l = (speed + steering) * leftBias;
  float r = speed - steering;
  left  = (int)(l < -255 ? -255 : (l > 255 ? 255 : l));
  right = (int)(r < -255 ? -255 : (r > 255 ? 255 : r));
}

}  // namespace linefollow
