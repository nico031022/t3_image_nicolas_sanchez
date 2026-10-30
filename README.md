# T3

Este repositorio contiene la Tarea 3: filtrado notch en frecuencia (P1) y deconvolución de Wiener y Tikhonov (P2).

## Instalación

El código está en Python (3.11). Las librerías que se usan son NumPy, Matplotlib, OpenCV y rawpy (rawpy solo se usa para leer la imagen RAW de la P1).

Después de clonar el repositorio, hay que abrir una terminal en la carpeta que contiene este README e instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

Todos los comandos de abajo se ejecutan desde esa misma carpeta, usando `python -m`.

## Organización

- `src/`: implementación de los algoritmos de cada pregunta.
- `experiments/`: scripts para hacer las pruebas y generar las figuras.
- `images/profesor/`: imágenes entregadas por el profesor.
  - `p1/P1.CR2`: imagen RAW con ruido periódico (P1).
  - `p2/cameraman.jpg`: imagen ideal x (P2).
  - `p2/psf.png`: PSF h de 15 × 15 (P2).
- `results/`: figuras y tablas de cada experimento. Cada script guarda sus resultados en una carpeta con su nombre y al volver a ejecutarlo se sobrescriben con los mismos nombres.
- `informe/notas.md`: notas que fui escribiendo durante la tarea, con lo que se observó en cada experimento y por qué se eligió cada parámetro.
- `informe/informe_t3.pdf`: informe de la tarea.

## P1

La implementación está en `src/pregunta1.py`. Las funciones principales son:

- `cargar_imagen`: lee la imagen. El `.CR2` se lee con rawpy como mosaico de Bayer sin interpolar (una sola matriz, en escala de grises) y se normaliza con el nivel de negro y de blanco del sensor.
- `aplicar_padding` y `recortar_padding`: agregan y sacan el padding (`"ninguno"`, `"ceros"`, `"reflejo"` o `"borde"`).
- `crear_grilla_frecuencias` y `distancia_a_centro`: las frecuencias están en ciclos/pixel y la distancia a cada notch considera que el espectro es periódico.
- `notch_ideal` y `notch_gaussiano`: arman H a partir de una lista de centros. El simétrico de cada centro se agrega solo.
- `filtrar_notch`: la cadena completa (padding, FFT, multiplicar por H, IFFT y recorte).

La configuración final es un notch gaussiano con σ = 0.03 ciclos/pixel, centros en (0.25, 0), (−0.5, −0.5), (−0.5, 0) y (0, −0.5) (más sus simétricos) y padding reflejo de 128 pixeles por lado.

Los scripts están en el orden en que se hicieron. Para reproducir todo se pueden correr así:

1. Ver el espectro y buscar los picos del ruido:

```bash
python -m experiments.test_p1_espectro
python -m experiments.test_p1_perfiles
python -m experiments.test_p1_picos
```

2. Revisar los filtros y la cadena de filtrado:

```bash
python -m experiments.test_p1_filtros_notch
python -m experiments.test_p1_filtrado
```

3. Probar distintos anchos de notch y ver los casos principales:

```bash
python -m experiments.test_p1_barrido
python -m experiments.test_p1_casos
```

4. Comparar los tipos y tamaños de padding:

```bash
python -m experiments.test_p1_padding
```

5. Repetir el barrido con el padding elegido (agrega los artefactos en las zonas saturadas) y ver la configuración final:

```bash
python -m experiments.test_p1_barrido_padding
python -m experiments.test_p1_final
```

6. Números y figuras para las preguntas guiadas:

```bash
python -m experiments.test_p1_preguntas
```

Los resultados quedan en `results/pregunta1/`, en una carpeta por script (`espectro`, `perfiles`, `picos`, `filtros`, `filtrado`, `barrido`, `casos`, `padding`, `barrido_padding`, `final` y `preguntas`). Los valores principales de la configuración final están en `results/pregunta1/final/parametros_finales.txt`.

La imagen es grande (2856 × 4290), así que algunos scripts se demoran: la mayoría tarda menos de un minuto y los barridos un poco más. Los que filtran varias veces pueden usar unos 3 GB de memoria.

## P2

La implementación está en `src/pregunta2.py`. Las funciones principales son:

- `cargar_psf`: lee la PSF y la divide por su suma para que sume 1.
- `psf_a_otf`: arma H a partir de la PSF. La pone en una imagen de ceros del tamaño de la imagen, mueve su centro al pixel (0, 0) con `np.roll` y hace la FFT.
- `aplicar_H` y `aplicar_Ht`: aplican H y Hᵀ en frecuencia (multiplicar por H y por su conjugado). Es convolución circular.
- `degradar`: genera la observación y = h * x + ruido gaussiano con una semilla fija.
- `wiener`: el filtro de Wiener simplificado H* Y / (|H|² + K). Con K = 0 es el filtro inverso.
- `tikhonov_gd`: Tikhonov por descenso de gradiente. Se le da λ, τ, el número máximo de iteraciones y el tol del criterio de detención, y guarda por iteración el costo, el RMSE y el cambio relativo.

En toda la pregunta se usa convolución circular, ruido con σ = 0.01 y σ = 0.05 (semilla 0) y los K óptimos de Wiener que salieron en el barrido: 4.64e-3 para σ = 0.01 y 2.93e-2 para σ = 0.05.

Igual que en la P1, los scripts están en el orden en que se hicieron:

1. Ver la PSF y H, revisar el modelo de degradación y elegir los niveles de ruido:

```bash
python -m experiments.test_p2_otf
python -m experiments.test_p2_degradacion
```

2. Filtro inverso y Wiener (barrido de K):

```bash
python -m experiments.test_p2_wiener_inversa
python -m experiments.test_p2_wiener_barrido
```

3. Wiener con una PSF un poco incorrecta:

```bash
python -m experiments.test_p2_psf_incorrecta
```

4. Revisar Tikhonov iterativo y probar distintos λ, τ y criterios de detención:

```bash
python -m experiments.test_p2_tikhonov_check
python -m experiments.test_p2_tikhonov_barrido
```

5. Comparar la solución iterativa con la solución cerrada y ver las mejores reconstrucciones:

```bash
python -m experiments.test_p2_comparacion
```

6. Números y figuras para las preguntas guiadas:

```bash
python -m experiments.test_p2_preguntas
```

Los resultados quedan en `results/pregunta2/`, en una carpeta por script (`otf`, `degradacion`, `inversa`, `wiener`, `psf_incorrecta`, `tikhonov_check`, `tikhonov`, `comparacion` y `preguntas`). Cada carpeta tiene un `.txt` con los números que se imprimen en la terminal.

Los scripts de Wiener tardan unos segundos. Los de Tikhonov iteran miles de veces y se demoran más: `test_p2_tikhonov_barrido` unos 4 a 5 minutos y `test_p2_comparacion` unos 3.
