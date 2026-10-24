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

### Filtros notch (`src/pregunta1.py`, `test_p1_filtros_notch`)

- Coordenadas: `crear_grilla_frecuencias` da U y V en ciclos/pixel con `fftfreq` + `fftshift`, en el mismo orden que el espectro centrado. Centros y anchos se dan en ciclos/pixel, así no dependen del tamaño (sirve para cuando haya padding).
- Distancia a un centro (`distancia_a_centro`): como el espectro es periódico con periodo 1, se usa `du = min(|u − u0|, 1 − |u − u0|)` y lo mismo en v. Así el notch en −0.5 también tapa el lado de +0.5 (en el zoom de la esquina el agujero queda completo).
- Simétricos (`agregar_simetricos`): por cada centro (u0, v0) se agrega (−u0, −v0). Si cada coordenada es 0 o ±0.5 el simétrico es el mismo punto (picos de Bayer) y no se agrega otra vez; en el gaussiano un agujero repetido quedaría como (1 − g)², más ancho.
- Ideal: H = 1 y se pone 0 donde D ≤ radio. Gaussiano: producto de 1 − exp(−D²/(2σ²)) por cada centro (pasa altos gaussiano de la clase 14 con D medido desde el notch). La única diferencia entre los dos es cómo se usa D: corte duro contra un umbral o caída suave.
- Para el par de columnas se usa u0 = 0.25 (periodo exacto de 4 pixeles) y no 0.2501 (el pixel más cercano).
- Revisión con radio = 0.01 y σ = 0.005 (solo para ver la forma):
  - H(0, 0) = 1 en los dos, entonces no se cambia el promedio de la imagen.
  - max |H(u, v) − H(−u, −v)| = 0 (ideal) y ~7e-15 (gaussiano): H es simétrico, la imagen filtrada debería salir real.
  - Se elimina (H < 0.5) el 0.16 % del espectro con el ideal y el 0.05 % con el gaussiano.
- Por ahora los agujeros son circulares (un solo ancho). Ver en el barrido si alcanza para el pico de 0.25, que es más largo en u.

### Filtrado completo (`filtrar_notch`, `test_p1_filtrado`)

- Cadena: padding → `fft2` + `fftshift` → H del tamaño de la imagen con padding → F · H (espectro complejo) → `ifftshift` + `ifft2` → parte real → recorte. Por ahora sin padding, radio = 0.01 y σ = 0.005 (los mismos de prueba).
- La parte imaginaria máxima después de la ifft es ~5e-16 en los dos filtros (error numérico), o sea la imagen filtrada sale real porque H es simétrico.
- El promedio de la imagen no cambia (0.091652 antes y después), porque H(0, 0) = 1.
- En los picos, |F|/mediana pasa de 325–1474 a 0 con el ideal. Con el gaussiano queda ~0.09 en ±0.25: el fondo del agujero gaussiano es 0 solo justo en el centro y el pico está en 0.2501, no en 0.25.
- Perfil del cielo (filas 100–400, columnas 2400–3200, mediana por columna y por fila):
  - Antes: un salto cada 4 columnas (columnas 2, 6, 10, …) y las filas alternan cada 2. Es el patrón que se veía en el espectro.
  - Después: los dos filtros dejan el perfil plano.
- Zoom en la zona de M43 (filas 2180–2308, columnas 1650–1778): la grilla del mosaico casi desaparece, pero en la parte más brillante de la nebulosa todavía se ve un poco. Ahí el color cambia más y el pico de Bayer es más ancho que el agujero. Mirar esto en el barrido de anchos.
- Los pixeles calientes (puntos blancos sueltos) siguen ahí, no son periódicos y el notch no los toca.
- La diferencia a imagen completa se ve casi gris uniforme porque al achicar la figura la grilla se promedia; hay que mirarla con zoom.
- Correr el script toma ~20 s y usa ~2.3 GB de memoria (varias matrices de 2856 × 4290).

### Barrido de anchos: métricas (`test_p1_barrido`)

- Anchos: 0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.04 (radio en el ideal, σ en el gaussiano). Sin padding.
- Por qué estos anchos:
  - Mínimo 0.0005: la resolución en frecuencia es 1/N (clase 11), o sea 1/4290 ≈ 0.00023 en u y 1/2856 ≈ 0.00035 en v. Con un radio menor a ~1 pixel el agujero casi no tapa nada. 0.0005 son ~2 pixeles en u y ~1.4 en v.
  - Máximo 0.04: los centros están separados al menos 0.25, así que el radio tiene que quedar bien bajo 0.125 para que los agujeros no se junten. Además el agujero en 0.25 con radio 0.04 llega hasta 0.21, lejos de donde está el contenido de la imagen (D < 0.1 en el perfil radial). Es un caso claramente ancho pero todavía razonable.
  - Entre medio cada valor es ~el doble del anterior (escala logarítmica, valores redondos 1-2-5), porque el efecto del ancho va por factores y no por sumas.
  - Revisando después: el codo de las curvas (~0.005) quedó al medio del rango y en los extremos se ve "muy angosto, queda ruido" y "muy ancho, se pierde imagen", así que el rango alcanza.
- Para comparar los dos filtros se usa el radio donde H = 0.5: en el ideal es el radio y en el gaussiano es σ·√(2 ln 2) ≈ 1.18σ.
- Métricas:
  - Cielo: desviación estándar de la mediana por columna y por fila (misma zona de cielo de antes). Si queda patrón, estas medianas varían mucho.
  - Zonas brillantes: 4 recortes de 256 × 256 en la nebulosa, casi sin pixeles saturados, en (1920, 2176), (1536, 1536), (1408, 1792) y (1792, 1408). En cada uno se suma |F| en las 5 frecuencias del ruido y se divide por la mediana del espectro del recorte. Como 256 es múltiplo de 4, ±0.5 y ±0.25 caen justo en un pixel.
  - std de la diferencia ruidosa − filtrada: cuánto se le saca a la imagen.
- Resultados:
  - Cielo: con el ancho más chico ya baja de 0.0088 a ~0.0023 (columnas) y de 0.0084 a ~0.0011 (filas), y después casi no cambia. En el fondo el ruido es muy angosto en frecuencia. Lo que queda es variación propia del cielo. El ideal es un poco peor en el ancho más chico (el círculo tiene muy pocos pixeles).
  - Zonas brillantes: 449 → ~117 (0.0005) → ~55 (0.001) → ~17 (0.005) y desde ahí queda plano en ~17. En la nebulosa el pico de Bayer es más ancho (el color cambia de un lugar a otro), por eso hace falta un notch más ancho que en el cielo. El piso de ~17 sería contenido de la imagen en esas frecuencias y no ruido.
  - std de la diferencia: sube siempre con el ancho (0.0181 → 0.0202). Lo que se saca por sobre ~0.018 ya no es ruido, es información de la imagen.
  - Con el mismo radio de H = 0.5 el gaussiano saca un poco menos que el ideal y deja el mismo residuo.
- Conclusión por ahora: pasado ~0.005 no se gana nada en ruido y se pierde más imagen. Casos principales para mirar con imágenes: 0.001 (angosto), 0.005 (el codo) y 0.04 (ancho), en los dos filtros.

### Barrido de anchos: casos principales (`test_p1_casos`)

- Casos: 0.001, 0.005 y 0.04 en los dos filtros, sin padding. Por cada caso se muestra un zoom de M43, la diferencia en ese zoom (misma escala ±0.135 para todos), un zoom de la estrella brillante de arriba a la derecha (centro (1090, 3358), núcleo saturado de radio ~25) y el espectro filtrado cerca de (0.25, 0) y de (−0.5, −0.5) (misma escala que el espectro original). A imagen completa los resultados se ven iguales (commit anterior), por eso se usan zooms.
- Para ver artefactos se usa el núcleo saturado de la estrella: en la imagen original es plano (std = 0.0036 en 12 × 12 pixeles), entonces lo que aparezca ahí después de filtrar lo puso el filtro.

| caso | std núcleo | std diferencia |
|---|---|---|
| ruidosa | 0.0036 | — |
| ideal 0.001 | 0.0138 | 0.01840 |
| ideal 0.005 | 0.0645 | 0.01908 |
| ideal 0.04 | 0.0353 | 0.02024 |
| gaussiano 0.001 | 0.0145 | 0.01833 |
| gaussiano 0.005 | 0.0738 | 0.01896 |
| gaussiano 0.04 | 0.0001 | 0.02018 |

- Ruido residual:
  - Con 0.001 la grilla del mosaico se sigue viendo en M43 y en el halo de la estrella. La diferencia es una grilla pareja en todo el zoom: el filtro saca un patrón "promedio" igual en toda la imagen.
  - Con 0.005 la grilla baja en M43 pero todavía se ve en la parte más brillante y en el halo.
  - Con 0.04 casi desaparece en M43, y la diferencia ya no es pareja, sigue la forma de la nebulosa.
  - En el halo de la estrella queda grilla en todos los casos.
- Por qué pasa: el mosaico de Bayer no es un ruido que se suma, es el color de la escena multiplicado por un patrón 2 × 2. Donde el color cambia rápido (estrella, borde de la nebulosa) el pico se abre en el espectro, y un notch angosto solo saca la parte "pareja" del patrón.
- Pérdida de detalle: al ensanchar, la diferencia empieza a mostrar la estructura de la nebulosa (bordes de M43), o sea se está sacando imagen y no solo ruido. Coincide con que la std de la diferencia sube siempre.
- Artefactos:
  - Con 0.001 y 0.005 aparece una grilla dentro del núcleo saturado, donde antes no había nada (std 0.0036 → 0.014 y 0.065–0.074). El filtro le resta el patrón "promedio" de toda la imagen también a una zona que no lo tenía.
  - Con 0.04 el gaussiano deja el núcleo plano (0.0001): con un agujero ancho la parte que se saca está más concentrada en el espacio y sigue lo que pasa localmente.
  - El ideal con 0.04 todavía deja 0.035: el borde duro del agujero produce oscilaciones (ringing, clase 14).
- Comparando los filtros: con el mismo ancho el ruido residual es parecido; la diferencia está en los artefactos, sobre todo con agujeros anchos, donde el gaussiano es mucho mejor.
- Para la configuración final hay un compromiso: un agujero angosto saca poco de imagen pero mete artefactos donde no había patrón; uno ancho gaussiano limpia mejor la grilla y no mete artefactos, pero saca más estructura de la nebulosa. Decidir después de ver el padding.

### Comparación de padding (`test_p1_padding`)

- Filtros: ideal y gaussiano con 0.005 (el codo del barrido). Padding: ninguno, ceros, reflejo y borde, con 32, 128 y 256 pixeles por lado.
- Por qué 32, 128 y 256: lo que saca el notch gaussiano, en el espacio, es la frecuencia del ruido multiplicada por una gaussiana de std s = 1/(2πσ) (la transformada de una gaussiana de std σ en frecuencia). Con σ = 0.005, s ≈ 32 pixeles, y el filtro usa pixeles hasta ~3s ≈ 95 de distancia. Entonces 32 ≈ 1s (debería quedar corto), 128 ≈ 4s (debería alcanzar) y 256 ≈ 8s (sobra). Si se cambia σ, el padding que alcanza sería ~4/(2πσ).
- Métrica: en franjas de 48 pixeles en cada borde, std de la mediana por columna (izquierda/derecha) o por fila (arriba/abajo). Al medio de la imagen da ~0.0005 después de filtrar.

| padding | izq | der | arr | aba |
|---|---|---|---|---|
| ruidosa | 0.0076 | 0.0077 | 0.0088 | 0.0063 |
| ninguno (gauss / ideal) | 0.0030 / 0.0033 | 0.0032 / 0.0035 | 0.0004 | 0.0004 |
| ceros 128 | 0.0029 / 0.0031 | 0.0034 / 0.0037 | 0.0024 / 0.0029 | 0.0028 / 0.0030 |
| borde 128 | 0.0028 / 0.0030 | 0.0032 / 0.0036 | 0.0026 / 0.0030 | 0.0030 / 0.0035 |
| reflejo 32 | 0.0003 / 0.0009 | 0.0031 / 0.0034 | 0.0003 | 0.0004 |
| reflejo 128 | 0.0003 / 0.0004 | 0.0030 / 0.0033 | 0.0003 | 0.0004 |
| reflejo 256 | 0.0003 / 0.0003 | 0.0030 / 0.0033 | 0.0003 | 0.0004 |

- Sin padding: arriba y abajo quedan bien, pero izquierda y derecha no. La FFT toma la imagen como si se repitiera. El alto (2856) es par, así que al pegar el borde de abajo con el de arriba el patrón de Bayer (periodo 2) sigue igual. El ancho (4290) no es múltiplo de 4, entonces al pegar derecha con izquierda el patrón de cada 4 columnas se corta (salta de fase) y cerca de esos bordes no se puede sacar bien. Es lo mismo que hacía que el pico de 0.25 se viera ancho en u.
- Ceros y borde empeoran arriba y abajo (de 0.0004 a ~0.0025–0.0035): lo que se agrega no tiene el patrón y se crea un corte en los cuatro bordes. En el zoom se ven rayas en esos bordes.
- Reflejo arregla el borde izquierdo pero no el derecho. El patrón de cada 4 columnas es simétrico respecto a las columnas pares (0, 2, 4, …). Al reflejar en la columna 0 el patrón sigue bien; en la derecha el espejo queda en la columna 4289, que es impar, y el patrón queda mal pegado. Con el mismo padding en los cuatro lados no se puede arreglar eso. A la derecha reflejo queda igual que sin padding, no peor. (Posible mejora: un padding distinto a cada lado para que el eje del espejo quede en una columna par.)
- Tamaño: con el gaussiano el reflejo ya funciona con 32. El ideal necesita más (izquierda: 0.0009 con 32, 0.0004 con 128, 0.0003 con 256), porque su respuesta en el espacio (tipo jinc, clase 14) baja mucho más lento que una gaussiana.
- Tiempo: con padding de 128 el filtrado tarda ~50 % más (ideal 1.9 s → 2.9 s), con 256 casi igual que con 128.
- Elección para el resto de la pregunta: **reflejo con 128 pixeles por lado**. Es el único que mejora un borde sin empeorar otros, 128 alcanza para los dos filtros (4s del gaussiano) y 256 no mejora más.
