# line_follower — detección de línea + PID (portable)

Extraído de [muhammad-fawaz/line-following-esp32cam](https://github.com/muhammad-fawaz/line-following-esp32cam) (`src/main.cpp`).
Solo C++ header-only, sin Arduino/ESP32/cámara: recibe un buffer en escala de grises.

- `line_detector.h` — `LineDetector::detect(img, w, h)` → `LineResult {found, position, error, angleDeg, severity}`
  - Centroide X de píxeles > umbral en 3 filas (arriba/centro/abajo), cada una promediada en una banda de ±2 filas.
  - `error` = centroide fila central − w/2; `angleDeg` = atan2(x_arriba − x_abajo, filas) en grados.
- `pid_controller.h` — `LinePid::update(LineResult)` → `Control {steering, speed}`
  - `steering = Kp_pos·error + Kp_ang·ángulo + Ki·∫error + Kd·Δerror` (Kp_pos=1.2, Kp_ang=0.45, Ki=0, Kd=0.5, anti-windup ±100).
  - Velocidad baja de 110 a 40 según `severity`; línea perdida → pivota hacia el último lado visto.
  - `mixMotors()` convierte a PWM izquierdo/derecho.
- `examples/esp32cam_example.cpp` — uso en ESP32-CAM; `test_host.cpp` — prueba en PC (`g++ -std=c++11 test_host.cpp`).

Cambios respecto al original: bordes de imagen protegidos, `invert` para línea oscura, parámetros en structs.
Ojo: el derivativo es por frame (sin dt), igual que el original.
