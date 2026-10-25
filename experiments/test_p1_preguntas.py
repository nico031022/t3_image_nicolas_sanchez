from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta1 import aplicar_padding
from src.pregunta1 import recortar_padding
from src.pregunta1 import calcular_espectro
from src.pregunta1 import espectro_log
from src.pregunta1 import crear_grilla_frecuencias
from src.pregunta1 import distancia_a_centro
from src.pregunta1 import notch_gaussiano
from src.pregunta1 import filtrar_notch


RUTA_IMAGEN = Path("images/profesor/p1/P1.CR2")

CARPETA_SALIDA = Path("results/pregunta1/preguntas")

# configuracion final (test_p1_final)
LISTA_CENTROS = [
    (0.25, 0),
    (-0.5, -0.5),
    (-0.5, 0),
    (0, -0.5),
]
SIGMA = 0.03
TIPO_PADDING = "reflejo"
TAM_PADDING = 128

# para la pregunta 6: solo los de Bayer (cada uno es su propio simetrico)
CENTROS_BAYER = [
    (-0.5, -0.5),
    (-0.5, 0),
    (0, -0.5),
]

# misma zona de cielo que en los otros scripts
ZONA_CIELO = {
    "fila_inicio": 100,
    "fila_fin": 400,
    "col_inicio": 2400,
    "col_fin": 3200,
}

N_PERFIL = 40

# misma zona de M43 que en los otros scripts
ZONA_DETALLE = {
    "fila": 2180,
    "col": 1650,
    "tam": 128,
}


def volver_al_espacio(
    F_filtrado,
    alto,
    ancho,
):

    # igual que los pasos 5 y 6 de filtrar_notch, pero sin sacar la parte real
    F_orden_fft = np.fft.ifftshift(F_filtrado)
    resultado = np.fft.ifft2(F_orden_fft)

    resultado = recortar_padding(
        resultado,
        alto,
        ancho,
        TAM_PADDING,
    )

    return resultado


def buscar_indice(
    frecuencias,
    valor,
):

    # pixel con la frecuencia mas cercana a valor
    indice = np.argmin(np.abs(frecuencias - valor))

    return indice


def texto_complejo(z):

    texto = f"{z.real:+12.4f} {z.imag:+12.4f}j   |.| = {np.abs(z):10.4f}   fase = {np.angle(z):+.4f} rad"

    return texto


def pregunta_3(
    imagen,
    imagen_pad,
    lineas,
):

    alto = imagen.shape[0]
    ancho = imagen.shape[1]

    lineas.append("PREGUNTA 3: padding y recorte")
    lineas.append(f"  imagen original:   {alto} x {ancho}")
    lineas.append(f"  padding {TIPO_PADDING} de {TAM_PADDING} pixeles por lado -> {imagen_pad.shape[0]} x {imagen_pad.shape[1]}")
    lineas.append(f"  recorte: filas [{TAM_PADDING}, {TAM_PADDING + alto}), columnas [{TAM_PADDING}, {TAM_PADDING + ancho})")

    recorte = recortar_padding(
        imagen_pad,
        alto,
        ancho,
        TAM_PADDING,
    )

    igual = np.array_equal(recorte, imagen)

    lineas.append(f"  el recorte de la imagen con padding es igual a la original: {igual}")

    # que valores pone el reflejo: la columna -1 es la columna 1, la -2 es la 2, etc.
    lineas.append(f"  columna -1 (reflejo) == columna 1 original: {np.array_equal(imagen_pad[TAM_PADDING:TAM_PADDING + alto, TAM_PADDING - 1], imagen[:, 1])}")
    lineas.append(f"  columna -2 (reflejo) == columna 2 original: {np.array_equal(imagen_pad[TAM_PADDING:TAM_PADDING + alto, TAM_PADDING - 2], imagen[:, 2])}")
    lineas.append("")


def pregunta_5(
    F,
    H,
    U,
    V,
    lineas,
):

    frec_u = U[0, :]
    frec_v = V[:, 0]

    F_filtrado = F * H

    # puntos a seguir: (nombre, u, v)
    puntos = [
        ("pico (0.25, 0)", 0.25, 0),
        ("borde del agujero (0.25 + sigma, 0)", 0.25 + SIGMA, 0),
        ("pico de Bayer (-0.5, -0.5)", -0.5, -0.5),
    ]

    lineas.append(f"PREGUNTA 5: valores en algunas frecuencias (gaussiano, sigma = {SIGMA})")

    for nombre, u, v in puntos:

        col = buscar_indice(frec_u, u)
        fila = buscar_indice(frec_v, v)

        u_bin = frec_u[col]
        v_bin = frec_v[fila]

        lineas.append(f"  {nombre}: pixel (fila {fila}, col {col}), u = {u_bin:+.5f}, v = {v_bin:+.5f}")
        lineas.append(f"    F antes   = {texto_complejo(F[fila, col])}")
        lineas.append(f"    H         = {H[fila, col]:.6f}")
        lineas.append(f"    F * H     = {texto_complejo(F_filtrado[fila, col])}")

        # el simetrico se busca con la frecuencia exacta del pixel, no con -0.25
        u_sim = -u_bin
        v_sim = -v_bin

        # en la grilla no existe +0.5, es la misma frecuencia que -0.5
        # (isclose porque fftfreq no da exactamente -0.5 en todos los tamanos)
        if np.isclose(u_sim, 0.5):
            u_sim = -0.5
        if np.isclose(v_sim, 0.5):
            v_sim = -0.5

        col_sim = buscar_indice(frec_u, u_sim)
        fila_sim = buscar_indice(frec_v, v_sim)

        if col_sim == col and fila_sim == fila:
            lineas.append("    su simetrico es el mismo pixel (frecuencia de Nyquist), por eso F tiene que ser real")
        else:
            lineas.append(f"    simetrico: pixel (fila {fila_sim}, col {col_sim}), u = {frec_u[col_sim]:+.5f}, v = {frec_v[fila_sim]:+.5f}")
            lineas.append(f"    F antes   = {texto_complejo(F[fila_sim, col_sim])}")
            lineas.append(f"    H         = {H[fila_sim, col_sim]:.6f}")
            lineas.append(f"    F * H     = {texto_complejo(F_filtrado[fila_sim, col_sim])}")

            diferencia_conj = np.abs(F[fila_sim, col_sim] - np.conj(F[fila, col]))
            lineas.append(f"    |F(-u,-v) - conj(F(u,v))| = {diferencia_conj:.2e}")

        lineas.append("")


def pregunta_6(
    F,
    U,
    V,
    imagen,
    lineas,
    carpeta_salida,
):

    alto = imagen.shape[0]
    ancho = imagen.shape[1]

    # H normal: los dos agujeros del par
    H_par = notch_gaussiano(
        U,
        V,
        LISTA_CENTROS,
        SIGMA,
    )

    # H con un solo agujero en +0.25 (sin su simetrico), armado a mano
    H_uno = notch_gaussiano(
        U,
        V,
        CENTROS_BAYER,
        SIGMA,
    )

    D = distancia_a_centro(
        U,
        V,
        0.25,
        0,
    )

    H_uno = H_uno * (1 - np.exp(-D**2 / (2 * SIGMA**2)))

    resultado_par = volver_al_espacio(F * H_par, alto, ancho)
    resultado_uno = volver_al_espacio(F * H_uno, alto, ancho)

    lineas.append("PREGUNTA 6: sacar solo uno de los dos notch del par +-0.25")
    lineas.append(f"  max |parte imaginaria|, par completo:  {np.max(np.abs(np.imag(resultado_par))):.2e}")
    lineas.append(f"  max |parte imaginaria|, un solo notch: {np.max(np.abs(np.imag(resultado_uno))):.2e}")

    f0 = ZONA_CIELO["fila_inicio"]
    f1 = ZONA_CIELO["fila_fin"]
    c0 = ZONA_CIELO["col_inicio"]
    c1 = ZONA_CIELO["col_fin"]

    imagenes = [
        ("ruidosa", imagen),
        ("par completo", np.real(resultado_par)),
        ("un solo notch (parte real)", np.real(resultado_uno)),
    ]

    perfiles = []

    for nombre, img in imagenes:

        cielo = img[f0:f1, c0:c1]
        por_columna = np.median(cielo, axis=0)
        perfiles.append((nombre, por_columna))

        lineas.append(f"  cielo, std de la mediana por columna, {nombre}: {np.std(por_columna):.5f}")

    lineas.append("")

    # figura: perfil, parte imaginaria y espectro cerca de +-0.25
    figura, axes = plt.subplots(
        2,
        2,
        figsize=(14, 9),
    )

    for nombre, por_columna in perfiles:
        axes[0, 0].plot(np.arange(N_PERFIL), por_columna[:N_PERFIL], "o-", markersize=3, label=nombre)

    axes[0, 0].set_title(f"Mediana de cada columna en el cielo (filas {f0} a {f1})")
    axes[0, 0].set_xlabel(f"columna - {c0}")
    axes[0, 0].grid(alpha=0.3)
    axes[0, 0].legend()

    imag_cielo = np.imag(resultado_uno)[f0:f0 + 64, c0:c0 + 64]
    lim = np.max(np.abs(imag_cielo))

    axes[0, 1].imshow(imag_cielo, cmap="gray", vmin=-lim, vmax=lim, interpolation="nearest")
    axes[0, 1].set_title(f"Parte imaginaria con un solo notch (cielo 64 x 64, +-{lim:.4f})")
    axes[0, 1].axis("off")

    # espectro filtrado alrededor de +0.25 y de -0.25 con un solo notch
    frec_u = U[0, :]
    frec_v = V[:, 0]
    fila_0 = buscar_indice(frec_v, 0)
    medio = int(0.05 * F.shape[1])
    medio_v = int(0.05 * F.shape[0])

    espectro_uno = espectro_log(F * H_uno)
    min_e = np.min(espectro_uno)
    max_e = np.max(espectro_uno)

    for k, u0 in [(0, 0.25), (1, -0.25)]:

        col_0 = buscar_indice(frec_u, u0)
        recorte = espectro_uno[fila_0 - medio_v:fila_0 + medio_v, col_0 - medio:col_0 + medio]

        axes[1, k].imshow(
            recorte,
            cmap="gray",
            vmin=min_e,
            vmax=max_e,
            extent=[frec_u[col_0 - medio], frec_u[col_0 + medio], frec_v[fila_0 + medio_v], frec_v[fila_0 - medio_v]],
            aspect="auto",
        )
        axes[1, k].set_title(f"log(1 + |F H|) cerca de ({u0}, 0), un solo notch")
        axes[1, k].set_xlabel("u [ciclos/pixel]")
        axes[1, k].set_ylabel("v [ciclos/pixel]")

    figura.suptitle(f"Pregunta 6: notch gaussiano sigma = {SIGMA} solo en +0.25 (padding {TIPO_PADDING} {TAM_PADDING})")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "un_solo_notch.png"

    figura.savefig(
        ruta_salida,
        dpi=140,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def pregunta_4(
    F,
    H,
    imagen,
    lineas,
    carpeta_salida,
):

    alto = imagen.shape[0]
    ancho = imagen.shape[1]

    magnitud = np.abs(F)
    fase = np.angle(F)

    # (a) lo correcto: multiplicar el espectro complejo
    resultado_a = volver_al_espacio(F * H, alto, ancho)

    # (b) H solo en la magnitud y la fase igual
    F_b = (H * magnitud) * np.exp(1j * fase)
    resultado_b = volver_al_espacio(F_b, alto, ancho)

    # (c) H en la magnitud y tambien en la fase
    F_c = (H * magnitud) * np.exp(1j * H * fase)
    resultado_c = volver_al_espacio(F_c, alto, ancho)

    lineas.append("PREGUNTA 4: espectro complejo vs magnitud y fase por separado")
    lineas.append(f"  max |(a) - (b)| (H solo en la magnitud): {np.max(np.abs(np.real(resultado_a) - np.real(resultado_b))):.2e}")
    lineas.append(f"  max |(a) - (c)| (H tambien en la fase):  {np.max(np.abs(np.real(resultado_a) - np.real(resultado_c))):.2e}")
    lineas.append(f"  std de (a) - (c): {np.std(np.real(resultado_a) - np.real(resultado_c)):.5f}")
    lineas.append("")

    f0 = ZONA_DETALLE["fila"]
    c0 = ZONA_DETALLE["col"]
    tam = ZONA_DETALLE["tam"]

    recortes = [
        ("ruidosa", imagen[f0:f0 + tam, c0:c0 + tam]),
        ("(a) F * H", np.real(resultado_a)[f0:f0 + tam, c0:c0 + tam]),
        ("(c) H en magnitud y fase", np.real(resultado_c)[f0:f0 + tam, c0:c0 + tam]),
    ]

    vmin = np.percentile(recortes[0][1], 1)
    vmax = np.percentile(recortes[0][1], 99.5)

    # a simple vista (a) y (c) se parecen, por eso se muestra tambien la resta
    resta = recortes[1][1] - recortes[2][1]
    lim = np.max(np.abs(resta))

    figura, axes = plt.subplots(
        1,
        4,
        figsize=(20, 5.3),
    )

    for k in range(3):
        axes[k].imshow(recortes[k][1], cmap="gray", vmin=vmin, vmax=vmax, interpolation="nearest")
        axes[k].set_title(recortes[k][0])
        axes[k].axis("off")

    axes[3].imshow(resta, cmap="gray", vmin=-lim, vmax=lim, interpolation="nearest")
    axes[3].set_title(f"(a) - (c), escala +-{lim:.4f}")
    axes[3].axis("off")

    figura.suptitle(f"Pregunta 4: zoom M43, filas [{f0}, {f0 + tam}), columnas [{c0}, {c0 + tam}), sigma = {SIGMA}")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "fase_vs_complejo.png"

    figura.savefig(
        ruta_salida,
        dpi=140,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def main():

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    imagen = cargar_imagen(RUTA_IMAGEN)

    alto = imagen.shape[0]
    ancho = imagen.shape[1]

    print(f"Imagen: {RUTA_IMAGEN}, tamano {imagen.shape}")

    lineas = []

    # la cadena paso a paso (como en filtrar_notch) para tener F y H a mano
    imagen_pad = aplicar_padding(
        imagen,
        TIPO_PADDING,
        TAM_PADDING,
    )

    pregunta_3(
        imagen,
        imagen_pad,
        lineas,
    )

    F = calcular_espectro(imagen_pad)

    U, V = crear_grilla_frecuencias(
        imagen_pad.shape[0],
        imagen_pad.shape[1],
    )

    H = notch_gaussiano(
        U,
        V,
        LISTA_CENTROS,
        SIGMA,
    )

    # revisar que la cadena a mano da lo mismo que filtrar_notch
    resultado_mano = np.real(volver_al_espacio(F * H, alto, ancho))

    print("filtrar_notch:")
    resultado_funcion = filtrar_notch(
        imagen,
        "gaussiano",
        LISTA_CENTROS,
        SIGMA,
        TIPO_PADDING,
        TAM_PADDING,
    )

    lineas.append("Revision: max |a mano - filtrar_notch| = " + f"{np.max(np.abs(resultado_mano - resultado_funcion)):.2e}")
    lineas.append("")

    pregunta_5(
        F,
        H,
        U,
        V,
        lineas,
    )

    pregunta_6(
        F,
        U,
        V,
        imagen,
        lineas,
        CARPETA_SALIDA,
    )

    pregunta_4(
        F,
        H,
        imagen,
        lineas,
        CARPETA_SALIDA,
    )

    print("")
    for linea in lineas:
        print(linea)

    ruta_salida = CARPETA_SALIDA / "preguntas_guiadas.txt"

    with open(ruta_salida, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_salida}")


if __name__ == "__main__":
    main()
