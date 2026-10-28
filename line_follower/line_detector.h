// Detección de línea por filas de escaneo (portable, sin dependencias de Arduino/ESP32).
// Extraído de muhammad-fawaz/line-following-esp32cam (src/main.cpp).
//
// Entrada: imagen en escala de grises de 8 bits (width*height bytes, fila por fila).
// La línea es CLARA sobre fondo oscuro (pixel > threshold). Para línea oscura use `invert = true`.
#pragma once
#include <stdint.h>
#include <math.h>

namespace linefollow {

struct DetectorConfig {
  int  threshold   = 190;           // umbral de binarización (0-255)
  int  rows[3]     = {70, 90, 110}; // filas de escaneo: arriba (anticipa), centro (posición), abajo
  int  bandHalf    = 2;             // cada fila se promedia con +-bandHalf filas vecinas
  bool invert      = false;         // true => línea oscura sobre fondo claro
  float deadband   = 3.0f;          // |error| menor que esto se toma como 0 (px)
};

struct LineResult {
  bool  found      = false;  // false => línea perdida
  float position   = -1.0f;  // centroide X de la fila central en px (0..width-1), -1 si no hay línea
  float error      = 0.0f;   // position - width/2  (+ = línea a la derecha del centro), con zona muerta
  float angleDeg   = 0.0f;   // ángulo de la línea (+ = curva a la derecha), 0 si falta fila superior/inferior
  float severity   = 0.0f;   // 0..1, qué tan cerrada es la curva (error + ángulo), útil para bajar velocidad
};

class LineDetector {
 public:
  DetectorConfig cfg;

  LineDetector() {}
  explicit LineDetector(const DetectorConfig& c) : cfg(c) {}

  // Centroide X (px) de los pixeles de línea en la banda centrada en `row`. -1 si no hay ninguno.
  float centroidAtRow(const uint8_t* img, int width, int height, int row) const {
    long sumX = 0;
    int count = 0;
    for (int r = row - cfg.bandHalf; r <= row + cfg.bandHalf; r++) {
      if (r < 0 || r >= height) continue;
      const uint8_t* line = img + (long)r * width;
      for (int x = 0; x < width; x++) {
        bool on = cfg.invert ? (line[x] < cfg.threshold) : (line[x] > cfg.threshold);
        if (on) { sumX += x; count++; }
      }
    }
    return count == 0 ? -1.0f : (float)sumX / count;
  }

  // Ángulo (grados) de la línea comparando el centroide de la fila superior con la inferior.
  // 0 = recta, + = curva a la derecha, - = a la izquierda. Devuelve 0 si falta alguna fila.
  float angleDeg(const uint8_t* img, int width, int height) const {
    float top = centroidAtRow(img, width, height, cfg.rows[0]);
    float bot = centroidAtRow(img, width, height, cfg.rows[2]);
    if (top < 0 || bot < 0) return 0.0f;
    float dx = top - bot;
    float dy = (float)(cfg.rows[2] - cfg.rows[0]);
    return atan2f(dx, dy) * (180.0f / (float)M_PI);
  }

  LineResult detect(const uint8_t* img, int width, int height) const {
    LineResult r;
    r.position = centroidAtRow(img, width, height, cfg.rows[1]);
    if (r.position < 0) return r;  // línea perdida
    r.found = true;

    r.error = r.position - width / 2.0f;
    if (fabsf(r.error) < cfg.deadband) r.error = 0.0f;

    r.angleDeg = angleDeg(img, width, height);

    float s = fabsf(r.error) / (width / 2.0f) + fabsf(r.angleDeg) / 45.0f;
    r.severity = s < 0.0f ? 0.0f : (s > 1.0f ? 1.0f : s);
    return r;
  }
};

}  // namespace linefollow
