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

### Barrido con padding y artefactos (`test_p1_barrido_padding`)

- Antes de elegir la configuración final se repite el barrido con el padding elegido (reflejo 128) y se agrega la métrica de artefactos de `test_p1_casos`, pero en varias zonas saturadas y no solo en una estrella.
- Zonas saturadas: en `saturados.png` (imagen > 1, el 0.73 % de los pixeles) se ven el núcleo de la nebulosa, la estrella grande de arriba a la derecha, una estrella más arriba y la estrella de M43. Se usa una ventana chica en cada una (24, 12, 8 y 8 pixeles de lado) y se revisó que las cuatro quedan 100 % saturadas.
- Anchos: 0.005, 0.01, 0.015, 0.02, 0.03 y 0.04, porque en `test_p1_casos` los artefactos cambiaban mucho entre 0.005 y 0.04.
- Criterio (antes de mirar los números): el residuo en las zonas brillantes ya llega al piso cerca de 0.005 (barrido anterior), así que más ancho no saca más ruido. Lo que queda por decidir es el compromiso entre artefactos (bajan al ensanchar) y lo que se le saca a la imagen (sube al ensanchar).

| filtro | ancho | zonas brill. | artefactos (prom. 4 zonas) | std diferencia |
|---|---|---|---|---|
| ruidosa | — | 449.1 | 0.0036 | — |
| ideal | 0.005 | 16.7 | 0.0313 | 0.01909 |
| ideal | 0.01 | 16.6 | 0.0565 | 0.01939 |
| ideal | 0.015 | 17.5 | 0.0568 | 0.01953 |
| ideal | 0.02 | 16.7 | 0.0437 | 0.01967 |
| ideal | 0.03 | 16.9 | 0.0455 | 0.01993 |
| ideal | 0.04 | 17.0 | 0.0172 | 0.02024 |
| gaussiano | 0.005 | 18.8 | 0.0340 | 0.01897 |
| gaussiano | 0.01 | 16.9 | 0.0434 | 0.01926 |
| gaussiano | 0.015 | 16.7 | 0.0360 | 0.01944 |
| gaussiano | 0.02 | 16.8 | 0.0263 | 0.01958 |
| gaussiano | 0.03 | 17.2 | 0.0125 | 0.01986 |
| gaussiano | 0.04 | 17.6 | 0.0059 | 0.02018 |

- Zonas brillantes: todos entre 16.6 y 18.8, o sea todos en el piso (la imagen ruidosa da 449). Por esto no se puede elegir entre ellos.
- Artefactos:
  - El ideal sube y baja sin orden (ringing del borde duro del agujero) y en su mejor caso (0.04) deja 0.017, ~3 veces más que el gaussiano con el mismo ancho. El gaussiano baja de forma ordenada desde 0.01.
  - En el núcleo de la nebulosa (la zona saturada más grande) el gaussiano no deja nada desde 0.01. En las estrellas chicas cuesta más (con 0.03: 0.026 y 0.023; con 0.04: ~0.012), porque la zona plana es chica y el borde de la estrella queda cerca.
- Lo que se saca: sube con el ancho en los dos; el gaussiano siempre saca un poco menos que el ideal.
- Con esto el filtro final debería ser el gaussiano: mismo residuo, menos artefactos y saca menos imagen. El ancho queda entre 0.03 y 0.04:
  - 0.03: artefactos 0.0125 (la estrella grande y el núcleo quedan limpios, en las estrellas chicas queda algo) y saca un poco menos de imagen.
  - 0.04: artefactos 0.0059 (la mitad), pero saca más imagen (0.02018 contra 0.01986) y es el borde del rango probado.
  - Se decide en la configuración final.

### Configuración final (`test_p1_final`)

- **Notch gaussiano, σ = 0.03, padding reflejo de 128 pixeles por lado**, centros (0.25, 0), (−0.5, −0.5), (−0.5, 0), (0, −0.5) + simétricos.
- Por qué:
  - Gaussiano y no ideal: el residuo es el mismo, pero el ideal mete artefactos que suben y bajan con el ancho (ringing) y siempre saca un poco más de imagen.
  - σ = 0.03: desde σ ≈ 0.005 el residuo del patrón ya no baja, así que ensanchar solo sirve para bajar los artefactos en las zonas saturadas, a costa de sacar más información de la imagen. Con 0.03 el núcleo de la nebulosa y la estrella grande quedan sin artefactos y se saca menos imagen que con 0.04. Además 0.03 queda dentro del rango probado (hay datos a los dos lados), en cambio 0.04 es el borde.
  - Reflejo 128: es el único padding que mejora un borde sin empeorar los otros, y 128 alcanza para el gaussiano.

| métrica | ruidosa | filtrada |
|---|---|---|
| cielo, std mediana por columna | 0.00881 | 0.00238 |
| cielo, std mediana por fila | 0.00839 | 0.00114 |
| zonas brillantes, \|F\| en picos / mediana | 449.1 | 17.2 |
| artefactos, núcleo nebulosa | 0.0036 | 0.0000 |
| artefactos, estrella grande | 0.0036 | 0.0016 |
| artefactos, estrella arriba | 0.0036 | 0.0260 |
| artefactos, estrella M43 | 0.0036 | 0.0226 |
| std de la diferencia | — | 0.01986 |
| promedio | 0.091652 | 0.091652 |

- Parte imaginaria máxima después de la ifft: ~1e-15. Filtrar tarda ~3.6 s.
- En los zoom: en M43 la grilla casi desaparece y se mantiene el degradado de la nebulosa; en el cielo queda limpio. En la estrella grande el centro queda plano, pero en el borde del disco saturado y en el halo todavía se ve algo de grilla.
- Limitaciones:
  - Quedan artefactos en las estrellas saturadas chicas (std ~0.025) y un poco de grilla alrededor de las estrellas brillantes. El mosaico de Bayer no es un ruido sumado sino el color de la escena multiplicado por un patrón, y donde el color cambia muy rápido un notch no lo puede sacar entero sin sacar también la imagen. Las zonas saturadas son solo el 0.73 % de la imagen y ahí no había información real.
  - El borde derecho sigue con algo del patrón de 4 columnas (ver padding).

### Apoyo para las preguntas guiadas (`test_p1_preguntas`)

- Se usa la configuración final (gaussiano σ = 0.03, reflejo 128). La cadena se hace a mano paso a paso (padding, fft, H, F · H, ifft, recorte) para tener F y H en la mano. Revisión: la cadena a mano da exactamente lo mismo que `filtrar_notch` (diferencia máxima 0).
- Todos los números quedan en `results/pregunta1/preguntas/preguntas_guiadas.txt`.

**P1 (simetría)**
- Una sinusoide real es cos θ = (e^{jθ} + e^{−jθ})/2, o sea dos exponenciales con frecuencias opuestas, por eso aparecen dos picos en ±(u0, v0). En general, para una imagen real F(−u, −v) = conj(F(u, v)).
- En los datos: |F(−u, −v) − conj(F(u, v))| ≈ 1e-11 en el pico de 0.25 (con |F| ≈ 34669, error numérico).
- En el pico de Bayer (−0.5, −0.5) el simétrico es el mismo pixel, y F sale real (−156862.94 + 0j).
- En el código: `agregar_simetricos` agrega (−u0, −v0) por cada centro, salvo si cada coordenada es 0 o ±0.5.

**P2 (coordenadas y distancia)**
- `crear_grilla_frecuencias` arma U y V en ciclos/pixel con `fftfreq` + `fftshift`, en el mismo orden que el espectro centrado.
- `distancia_a_centro` calcula du = |U − u0| y dv = |V − v0|, los pasa a `min(d, 1 − d)` porque el espectro es periódico con periodo 1, y D = √(du² + dv²).
- La distancia es la misma para los dos filtros. Lo que cambia es cómo se usa D: el ideal compara D ≤ radio (pone 0 o 1), el gaussiano calcula 1 − exp(−D²/(2σ²)) (cae suave). Si hay varios centros se multiplican los H de cada uno.

**P3 (padding y recorte)**
- 2856 × 4290 → reflejo de 128 por lado → 3112 × 4546.
- El reflejo pone fuera de la imagen los pixeles de adentro en espejo sin repetir el borde (`np.pad` con `mode="reflect"`): la columna −1 es la columna 1, la −2 es la 2, etc. (verificado en el script).
- Después de la ifft se toma filas [128, 2984) y columnas [128, 4418) (`recortar_padding`). El recorte de la imagen con padding es igual a la original (verificado).

**P4 (espectro complejo)**
- (a) F · H; (b) H solo en la magnitud y la fase sin tocar: |F| · H · e^{j∠F}; (c) H en la magnitud y también en la fase: |F| · H · e^{j·H·∠F}.
- (a) y (b) son iguales (diferencia máxima ~9e-16): como H es real y ≥ 0, multiplicar F por H solo cambia la magnitud. Por eso se multiplica el espectro complejo directamente: es lo que dice el teorema de convolución y no hay que separar nada.
- (c) es distinto (diferencia máxima 0.035): donde 0 < H < 1 la fase cambia y esas componentes se corren de lugar (la fase dice dónde está cada onda, cápsula semana 8). En `fase_vs_complejo.png` a simple vista se parece, pero la resta muestra grilla corrida alrededor de la nebulosa.

**P5 (seguimiento de una frecuencia)**

| punto | F antes | H | F · H |
|---|---|---|---|
| pico (u = +0.24989, v = 0) | −2699.49 − 34564.10j (\|F\| = 34669.4, fase −1.6487) | 0.000007 | −0.0181 − 0.2323j (\|F\| = 0.233, fase −1.6487) |
| borde del agujero (u = +0.28003, v = 0) | −66.09 + 133.60j (\|F\| = 149.05, fase +2.0302) | 0.394 | −26.04 + 52.64j (\|F\| = 58.73, fase +2.0302) |
| Bayer (−0.5, −0.5) | −156862.94 + 0j | 0.000000 | ~0 |

- En los tres casos la fase no cambia, solo la magnitud (se multiplica por H). En el borde del agujero H = 0.394 ≈ 1 − e^{−1/2}, porque está justo a una distancia σ del centro.
- Ojo: el pico de 0.25 queda en u = 0.24989 y no en 0.25 porque 4546 no es múltiplo de 4. El simétrico se buscó con la frecuencia del pixel (−0.24989), y +0.5 se trató como −0.5 (no existe en la grilla).

**P6 (un solo notch del par)**
- H con los agujeros de Bayer y un solo agujero en +0.25 (sin el de −0.25).
- Parte imaginaria máxima después de la ifft: 1.8e-2, contra 1.2e-15 con el par completo. Como H ya no es simétrico, F · H deja de cumplir F(−u, −v) = conj(F(u, v)) y la imagen sale compleja.
- La parte imaginaria tiene rayas verticales cada 4 columnas, es la exponencial que quedó en −0.25.
- Cielo, std de la mediana por columna: ruidosa 0.00881, par completo 0.00238, un solo notch 0.00356. En el perfil se ve que el patrón de 4 columnas sigue ahí, más chico: de cos θ = (e^{jθ} + e^{−jθ})/2 se sacó una exponencial y la parte real de la que queda es un coseno con la mitad de amplitud.

## P2

### Datos y modelo de degradación (`src/pregunta2.py`, `test_p2_otf`)

- `cameraman.jpg` es de 256 × 256 con 3 canales iguales, se pasa a gris con `cargar_imagen` de la P1 (queda en [0, 1]).
- `psf.png` es de 15 × 15. Sumaba 35.45 (en [0, 1]), entonces se divide por su suma para que sume 1 (`cargar_psf`). Así H(0, 0) = 1 y la degradación no cambia el promedio de la imagen (0.465586 antes y después).
- El máximo de la PSF está en (7, 7) y su centro de masa en (7.002, 7.006), entonces el centro que se usa es (15 // 2, 15 // 2) = (7, 7).
- La PSF no es exactamente simétrica: max |h − h girada 180°| = 2.2e-4 (0.78 % del máximo). Por eso H tiene una parte imaginaria chica (máx 1.3e-3). Esto importa para la pregunta de Hᵀ.
- Modelo: convolución circular, hecha en frecuencia con `aplicar_H`. Se usa el mismo en toda la P2.
  - Es lo que hace la cápsula de la semana 10 (`psf2otf` y `convolucionar`).
  - En la clase 17 la solución cerrada de Tikhonov queda como Wiener en Fourier porque H es una convolución que la DFT diagonaliza, y eso es exacto solo con convolución circular. Así se puede comparar la solución iterativa con la cerrada sin que el borde meta diferencias.
  - Limitación: una foto real no es periódica (clase 16: la solución es muy sensible a la condición de borde). En h * x se ve que el cielo de la primera fila se oscurece (hasta 0.23 menos que en x) con las piernas oscuras de la última fila, porque la convolución da la vuelta. Como la imagen degradada se genera con el mismo modelo, esto no aparece como error en la restauración.
- H (`psf_a_otf`, igual que `psf2otf` de la cápsula): la PSF se pone en la esquina de una imagen de ceros de 256 × 256, se mueve con `np.roll` (−7, −7) para que su centro quede en el pixel (0, 0) y se hace `fft2` sin `fftshift`, así queda en el mismo orden que `fft2(x)`.
- Revisiones:
  - Convolución con fft vs a mano (suma de 225 copias de x movidas con `np.roll`): diferencia máxima ~1e-15. Multiplicar por H es la convolución circular.
  - Sin el `np.roll` el resultado es la imagen borrosa correcta movida 7 pixeles abajo y a la derecha (diferencia ~5e-16 con la correcta movida). La diferencia con la correcta llega a 0.76 en los bordes de los objetos (`centrado_psf.png`).
- |H|: máximo 1 en (0, 0), mínimo 2e-6 (|H|² mínimo 4e-12). Es un pasa bajos: cae a casi cero en ~0.17 ciclos/pixel en u y ~0.2 en v (la PSF es un poco elíptica) y después quedan lóbulos chicos.
  - |H| < 0.1 en el 93 % de las frecuencias, < 0.01 en el 78 % y < 0.001 en el 48 %.
  - En esas frecuencias Y / H amplificaría el ruido entre 10 y más de 10⁴ veces (`perfiles_H.png`).
  - Para K: |H|² va de 1 a 4e-12, así que el barrido de K tiene que cubrir muchos órdenes de magnitud (la cápsula usa de 1e-7 a 10).

### Niveles de ruido (`degradar`, `test_p2_degradacion`)

- `degradar`: y = h * x + σ · ruido normal, con `np.random.default_rng(semilla)` como en la cápsula. Semilla 0 fija en toda la P2, así el ruido es el mismo en todos los experimentos.
- No se recorta y a [0, 1]: si se recorta, el ruido ya no es gaussiano ni sumado y deja de cumplir el modelo g = Hf + n de la clase 17.
- RMSE = √MSE (MSE de la clase 16). SNR = Σ|F|² / Σ|N|² (clase 16).
- Niveles probados: 0.002, 0.01 y 0.05 de la cápsula (poco, moderado y mucho ruido) y 0.005 y 0.02 entre medio (factor ~2.5 entre seguidos).

| σ | RMSE(y, x) | SNR | SNR [dB] | cruce [ciclos/pixel] | y fuera de [0, 1] |
|---|---|---|---|---|---|
| 0.002 | 0.0801 | 69191 | 48.4 | 0.205 | 0 % |
| 0.005 | 0.0802 | 11071 | 40.4 | 0.185 | 0 % |
| 0.01 | 0.0807 | 2768 | 34.4 | 0.165 | 0 % |
| 0.02 | 0.0825 | 692 | 28.4 | 0.155 | 0.10 % |
| 0.05 | 0.0944 | 111 | 20.4 | 0.125 | 2.13 % |

- Sin ruido RMSE(h * x, x) = 0.0801: hasta σ = 0.02 casi todo el error de y es por el desenfoque, recién con 0.05 el ruido suma bastante.
- A la vista (`degradadas.png`): con 0.002 y 0.005 no se ve ruido; con 0.01 se nota un poco en el zoom (el cielo se ve granulado); con 0.02 se ve claro y con 0.05 mucho.
- `senal_vs_ruido.png` es como el gráfico de la clase 16 (señal que cae y ruido plano): el ruido blanco tiene en promedio σ² · M · N en cada frecuencia, y se compara con el promedio de |H X|² en anillos.
  - "Cruce" = primer anillo donde |H X|² queda bajo el ruido. Más allá de esa frecuencia domina el ruido y no se puede recuperar la imagen, Wiener debería apagar esas frecuencias.
  - El cruce se mueve poco (0.205 → 0.125) aunque σ cambie 25 veces, porque |H X|² cae muy rápido entre 0.1 y 0.2 (ahí H llega a su primer cero).
  - Pasado ~0.2 la señal borrosa es menor a 1e-1 y en la mayoría menor a 1e-3: esas frecuencias se pierden con cualquier σ de los probados.

### Niveles elegidos

- Se usan **σ = 0.01** (ruido moderado) y **σ = 0.05** (mucho ruido) en el resto de la P2.
  - Son dos de los niveles de la cápsula; 0.01 es además el valor por defecto del panel de Wiener de la cápsula.
  - Son claramente distintos: SNR 34.4 dB vs 20.4 dB (25 veces), cruce 0.165 vs 0.125. Con 0.01 el ruido apenas se ve y el error de y es casi todo desenfoque; con 0.05 el ruido se ve fuerte y aporta una parte importante del error.
  - 0.002 casi no tiene ruido (48 dB). Lo que pasa con poco ruido y el filtro inverso se muestra aparte en la parte A.

### Parte A: filtro de Wiener y filtro inverso (`wiener`, `test_p2_wiener_inversa`)

- `wiener(y, H, K)`: Y = fft2(y), X̂ = H* · Y / (|H|² + K), x̂ = parte real de ifft2(X̂). Es la fórmula del enunciado y de la clase 16 (Wiener paramétrico con R = K). H sale de `psf_a_otf`, sin fftshift, igual que Y.
- Con K = 0 queda H* / |H|² = 1 / H, o sea el filtro inverso, entonces no hace falta otra función. Como min |H|² = 4e-12 (no es 0) no se divide por cero.

**Filtro inverso (K = 0)**

| σ | RMSE(x̂, x) | min x̂ | max x̂ |
|---|---|---|---|
| 0 | 4.8e-13 | ~0 | 1 |
| 0.01 | 42.3 | −155 | 172 |
| 0.05 | 211 | −778 | 860 |

- Sin ruido la división recupera x exacta (error de redondeo). El problema no es dividir por H, es el ruido.
- Con ruido: X̂ = (H X + N) / H = X + N / H. El error es solo el término N / H, y su RMSE es igual al RMSE total (42.3 y 211). Sube 5 veces cuando σ sube 5 veces, es lineal en el ruido.
- En `inversa_espectros.png` (σ = 0.01, misma escala): |N| es plano (~10^0.4 ≈ σ · √(M·N) = 2.56). 1/|H| es chico al centro pero llega a 10^5 – 10^6 en los ceros de H (el anillo en ~0.17–0.2 y las curvas de afuera). N / H copia la forma de 1/|H|: el ruido queda amplificado justo donde H es casi 0. La amplificación máxima es 1 / min |H| = 5e5.
- Por eso la imagen sale como ruido de alta frecuencia de amplitud ~±150 (σ = 0.01): las frecuencias altas, donde casi no hay señal (ver cruce en niveles de ruido), quedan llenas de ruido multiplicado por miles.

**Por qué K evita la amplificación (pregunta guiada)**
- La ganancia de Wiener es |W| = |H| / (|H|² + K).
  - Si |H|² ≫ K: |W| ≈ 1 / |H|, igual que el inverso (frecuencias bajas, clase 16: "para frecuencias bajas W = 1/H").
  - Si |H|² ≪ K: |W| ≈ |H| / K → 0, la frecuencia se apaga en vez de amplificarse ("para frecuencias altas W es bajo").
- Derivando |H| / (|H|² + K) respecto de |H| e igualando a 0: K − |H|² = 0, entonces el máximo está en |H| = √K y vale 1 / (2√K). Con K > 0 ninguna frecuencia se multiplica por más de 1 / (2√K).
- Revisión con la H de la PSF: K = 1e-4 → max |W| = 50.00; K = 1e-3 → 15.81; K = 1e-2 → 5.00, exactamente 1 / (2√K) en los tres (`ganancia_wiener.png`). Esos K son solo para ver la forma; cuál K conviene se busca en el barrido.
- En el eje u (`ganancia_wiener.png`, derecha): donde 1/|H| tiene picos (ceros de H en u ≈ ±0.17), |W| baja a casi 0. Mientras más grande K, más frecuencias se apagan y más angosta la zona donde W ≈ 1/H.
