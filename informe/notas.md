# Notas T3

## P1

### Lectura de la imagen

- `P1.CR2` es un RAW de Canon (14 bits). Se lee con `rawpy` el mosaico de Bayer sin interpolar (`raw_image_visible`), de 2856 × 4290.
- Se normaliza con el nivel de negro (promedio de los 4 canales) y el nivel de blanco del sensor.

### Exploración del espectro (`test_p1_perfiles`)

- |F| se divide por la mediana del espectro para que el fondo quede cerca de 1.
- Fila v = 0: picos en u = ±0.25 (~325 veces la mediana) y en u = −0.5 (~1250).
- Columna u = 0: pico en v = −0.5 (~1200). En v = ±0.25 no aparece nada, entonces el patrón de 0.25 es solo horizontal (se repite cada 4 columnas).
- Perfil radial: la media baja rápido hasta D ≈ 0.1 y después queda plana (~1). Desde D = 0.05 hacia afuera el máximo del contenido de la imagen es menor a ~18.
- Hay máximos aislados en D ≈ 0.25, 0.5 y 0.71 (la esquina u = v = −0.5).
- Los picos en ±0.5 serían del mosaico de Bayer (patrón 2 × 2, clase 2).
- En u = +0.5 la curva sube pero no hay pico: como el ancho es par, u = −0.5 y u = +0.5 son la misma frecuencia y el pico aparece solo en un lado. Ojo con esto al hacer los notch.

- Siguiente paso: buscar los picos sin mirar el centro. Por el perfil radial cualquier radio de exclusión entre ~0.05 y 0.2 debería servir. Probar con 0.05 y revisar que los picos no cambien con otros radios.

### Búsqueda de picos (`test_p1_picos`)

- Radio excluido 0.05, se buscan 10 picos (el doble de los 5 esperados). Después de cada pico se borra una ventana de 7 × 7 alrededor, usando `%` para dar la vuelta en los bordes (si no, el pico de la esquina aparece otra vez al otro lado).
- Picos encontrados:

| k | u | v | \|F\|/mediana |
|---|---|---|---|
| 1 | −0.5000 | −0.5000 | 1474 |
| 2 | −0.5000 | 0 | 1255 |
| 3 | 0 | −0.5000 | 1211 |
| 4 | −0.2501 | 0 | 325 |
| 5 | +0.2501 | 0 | 325 |
| 6–10 | junto a los anteriores | | ≤ 57 |

- Hay un salto claro entre el pico 5 (325) y el 6 (57). Los picos 6 a 10 quedan a ~4 pixeles de los picos 1, 3, 4 y 5, o sea son parte del mismo pico y no componentes nuevas.
- Con radios 0.02, 0.05, 0.1 y 0.2 los 5 primeros picos son iguales, entonces el radio no es crítico.
- Los picos 1, 2 y 3 aparecen una sola vez: como alto y ancho son pares, −0.5 y +0.5 son la misma frecuencia y el pico es su propio simétrico.
- Los picos 4 y 5 son un par simétrico (u = ±0.25). En el zoom se ve una línea horizontal en v = 0: el pico se reparte en varios pixeles en u porque 4290 no es múltiplo de 4 y 0.25 cae entre dos muestras. El notch de este par va a tener que ser más ancho en u. Revisar si con padding (ancho múltiplo de 4) el pico queda en un solo pixel.

### Centros para los notch (a usar en el siguiente commit)

- (−0.5, −0.5), (−0.5, 0), (0, −0.5): mosaico de Bayer.
- (±0.25, 0): patrón que se repite cada 4 columnas.
