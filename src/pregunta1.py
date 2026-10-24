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


def crear_grilla_frecuencias(
    alto,
    ancho,
):

    # frecuencias en ciclos por pixel, en el mismo orden que el espectro con fftshift
    frec_v = np.fft.fftshift(np.fft.fftfreq(alto))
    frec_u = np.fft.fftshift(np.fft.fftfreq(ancho))

    U, V = np.meshgrid(
        frec_u,
        frec_v,
    )

    return U, V


def distancia_a_centro(
    U,
    V,
    u0,
    v0,
):

    du = np.abs(U - u0)
    dv = np.abs(V - v0)

    # el espectro es periodico con periodo 1 (ciclos/pixel)
    # asi un notch en -0.5 tambien tapa lo que esta cerca de +0.5
    du = np.minimum(du, 1 - du)
    dv = np.minimum(dv, 1 - dv)

    D = np.sqrt(du**2 + dv**2)

    return D


def agregar_simetricos(lista_centros):

    lista_completa = []

    for centro in lista_centros:

        u0 = centro[0]
        v0 = centro[1]

        lista_completa.append((u0, v0))

        # si cada coordenada es 0 o +-0.5, el simetrico es el mismo punto
        # (pasa con los picos de Bayer) y no hay que agregarlo dos veces
        u_especial = (u0 == 0) or (abs(u0) == 0.5)
        v_especial = (v0 == 0) or (abs(v0) == 0.5)

        if u_especial and v_especial:
            continue

        lista_completa.append((-u0, -v0))

    return lista_completa


def notch_ideal(
    U,
    V,
    lista_centros,
    radio,
):

    H = np.ones(U.shape)

    centros = agregar_simetricos(lista_centros)

    for centro in centros:

        D = distancia_a_centro(
            U,
            V,
            centro[0],
            centro[1],
        )

        # dentro del radio se elimina todo
        H[D <= radio] = 0

    return H


def notch_gaussiano(
    U,
    V,
    lista_centros,
    sigma,
):

    H = np.ones(U.shape)

    centros = agregar_simetricos(lista_centros)

    for centro in centros:

        D = distancia_a_centro(
            U,
            V,
            centro[0],
            centro[1],
        )

        # pasa altos gaussiano centrado en el notch (clase 14)
        H_centro = 1 - np.exp(-D**2 / (2 * sigma**2))

        H = H * H_centro

    return H


def filtrar_notch(
    imagen,
    tipo_filtro,
    lista_centros,
    ancho_notch,
    tipo_padding,
    tam_padding,
):

    alto = imagen.shape[0]
    ancho = imagen.shape[1]

    # sin padding no hay que recortar nada
    if tipo_padding == "ninguno":
        tam_padding = 0

    # 1. padding
    imagen_pad = aplicar_padding(
        imagen,
        tipo_padding,
        tam_padding,
    )

    # 2. fft2 + fftshift
    F = calcular_espectro(imagen_pad)

    # 3. filtro del mismo tamano que la imagen con padding
    alto_pad = imagen_pad.shape[0]
    ancho_pad = imagen_pad.shape[1]

    U, V = crear_grilla_frecuencias(
        alto_pad,
        ancho_pad,
    )

    if tipo_filtro == "ideal":
        H = notch_ideal(
            U,
            V,
            lista_centros,
            ancho_notch,
        )
    elif tipo_filtro == "gaussiano":
        H = notch_gaussiano(
            U,
            V,
            lista_centros,
            ancho_notch,
        )
    else:
        raise ValueError(f"tipo_filtro no valido: {tipo_filtro}")

    # 4. multiplicar el espectro complejo por H
    F_filtrado = F * H

    # 5. volver al orden de la fft y transformada inversa
    F_filtrado = np.fft.ifftshift(F_filtrado)
    resultado = np.fft.ifft2(F_filtrado)

    # la parte imaginaria deberia ser casi cero porque H es simetrico
    max_imag = np.max(np.abs(np.imag(resultado)))
    print(f"  parte imaginaria maxima: {max_imag:.2e}")

    imagen_filtrada_pad = np.real(resultado)

    # 6. recortar al tamano original
    imagen_filtrada = recortar_padding(
        imagen_filtrada_pad,
        alto,
        ancho,
        tam_padding,
    )

    return imagen_filtrada
