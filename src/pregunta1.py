import numpy as np
import cv2
import rawpy


def cargar_imagen_raw(ruta):

    # abrir el archivo RAW de la camara (.CR2)
    raw = rawpy.imread(str(ruta))

    mosaico = raw.raw_image_visible.copy()

    # niveles de negro y blanco del sensor
    niveles_negro = raw.black_level_per_channel
    nivel_negro = np.mean(niveles_negro)
    nivel_blanco = raw.white_level

    raw.close()

    # pasar a double antes de operar
    imagen = mosaico.astype(np.float64)

    # normalizar: el negro queda en 0 y el blanco en 1
    # no recorto nada: los valores negativos son ruido del sensor
    # y los pixeles saturados quedan un poco sobre 1
    imagen = (imagen - nivel_negro) / (nivel_blanco - nivel_negro)

    return imagen


def cargar_imagen(ruta):

    if str(ruta).lower().endswith(".cr2"):
        imagen = cargar_imagen_raw(ruta)
        return imagen

    imagen = cv2.imread(
        str(ruta),
        cv2.IMREAD_UNCHANGED,
    )

    if imagen is None:
        raise ValueError(f"No se pudo leer la imagen: {ruta}")

    # si viene encolor paso a gris
    if imagen.ndim == 3:
        imagen = cv2.cvtColor(
            imagen,
            cv2.COLOR_BGR2GRAY,
        )

    # dejar la imagen en float entre 0 y 1
    if imagen.dtype == np.uint8:
        max_valor = 255.0
    elif imagen.dtype == np.uint16:
        max_valor = 65535.0
    else:
        max_valor = 1.0

    imagen = imagen.astype(np.float64) / max_valor

    return imagen


def aplicar_padding(
    imagen,
    tipo_padding,
    tam_padding,
):

    # tipo_padding puede ser "ninguno", "ceros", "reflejo" o "borde"
    # tam_padding es cuantos pixeles se agregan en cada borde

    if tipo_padding == "ninguno" or tam_padding == 0:
        return imagen.copy()

    if tam_padding < 0:
        raise ValueError("tam_padding no puede ser negativo")

    if tipo_padding == "ceros":
        modo = "constant"
    elif tipo_padding == "reflejo":
        modo = "reflect"
    elif tipo_padding == "borde":
        modo = "edge"
    else:
        raise ValueError(f"tipo_padding no valido: {tipo_padding}")

    # se agrega lo mismo arriba, abajo, izquierda y derecha
    imagen_pad = np.pad(
        imagen,
        pad_width=tam_padding,
        mode=modo,
    )

    return imagen_pad


def recortar_padding(
    imagen_pad,
    alto_original,
    ancho_original,
    tam_padding,
):

    # la imagen original quedo desplazada tam_padding pixeles en cada eje
    fila_inicio = tam_padding
    fila_fin = tam_padding + alto_original

    col_inicio = tam_padding
    col_fin = tam_padding + ancho_original

    imagen_recortada = imagen_pad[
        fila_inicio:fila_fin,
        col_inicio:col_fin,
    ]

    return imagen_recortada


def calcular_espectro(imagen):

    F = np.fft.fft2(imagen)

    # llevar la frecuencia cero al centro
    F_centrado = np.fft.fftshift(F)

    return F_centrado


def espectro_log(F):

    # log(1 + |F|) para poder ver las frecuencias altas
    magnitud = np.abs(F)
    espectro = np.log(1 + magnitud)

    return espectro




