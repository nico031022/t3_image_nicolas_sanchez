from pathlib import Path
import time

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta1 import calcular_espectro
from src.pregunta1 import espectro_log
from src.pregunta1 import filtrar_notch


RUTA_IMAGEN = Path("images/profesor/p1/P1.CR2")

CARPETA_SALIDA = Path("results/pregunta1/final")

# centros de test_p1_picos, el simetrico se agrega solo
LISTA_CENTROS = [
    (0.25, 0),
    (-0.5, -0.5),
    (-0.5, 0),
    (0, -0.5),
]

# configuracion final (ver notas.md)
FILTRO_FINAL = "gaussiano"     # test_p1_barrido_padding: menos artefactos que el ideal
ANCHO_FINAL = 0.03             # compromiso entre artefactos e imagen que se saca
TIPO_PADDING = "reflejo"       # test_p1_padding
TAM_PADDING = 128              # test_p1_padding

# zonas para los zoom: (nombre, fila, columna, tamano)
ZONAS_ZOOM = [
    ("M43", 2180, 1650, 128),
    ("estrella grande", 1042, 3310, 96),
    ("cielo", 100, 2400, 128),
]

# misma zona de cielo que en los otros scripts
ZONA_CIELO = {
    "fila_inicio": 100,
    "fila_fin": 400,
    "col_inicio": 2400,
    "col_fin": 3200,
}

N_PERFIL = 40

# mismas zonas que en test_p1_barrido_padding
NUCLEOS = [
    ("nucleo nebulosa", 1907, 1953, 12),
    ("estrella grande", 1089, 3357, 6),
    ("estrella arriba", 677, 3424, 4),
    ("estrella M43", 2278, 1738, 4),
]

TAM_ZONA = 256
ZONAS_BRILLANTES = [
    (1920, 2176),
    (1536, 1536),
    (1408, 1792),
    (1792, 1408),
]


def texto_parametros():

    texto = f"notch {FILTRO_FINAL}, sigma = {ANCHO_FINAL}, padding {TIPO_PADDING} {TAM_PADDING}"

    return texto


def residuo_cielo(imagen):

    # copiada de test_p1_barrido
    f0 = ZONA_CIELO["fila_inicio"]
    f1 = ZONA_CIELO["fila_fin"]
    c0 = ZONA_CIELO["col_inicio"]
    c1 = ZONA_CIELO["col_fin"]

    cielo = imagen[f0:f1, c0:c1]

    std_columnas = np.std(np.median(cielo, axis=0))
    std_filas = np.std(np.median(cielo, axis=1))

    return std_columnas, std_filas


def residuo_zonas_brillantes(imagen):

    # copiada de test_p1_barrido
    centro = TAM_ZONA // 2
    cuarto = TAM_ZONA // 4

    valores = []

    for zona in ZONAS_BRILLANTES:

        fila = zona[0]
        col = zona[1]

        recorte = imagen[fila:fila + TAM_ZONA, col:col + TAM_ZONA]
        recorte = recorte - np.mean(recorte)

        magnitud = np.abs(np.fft.fftshift(np.fft.fft2(recorte)))

        en_picos = 0
        en_picos = en_picos + magnitud[0, 0]
        en_picos = en_picos + magnitud[centro, 0]
        en_picos = en_picos + magnitud[0, centro]
        en_picos = en_picos + magnitud[centro, centro + cuarto]
        en_picos = en_picos + magnitud[centro, centro - cuarto]

        valores.append(en_picos / np.median(magnitud))

    return np.mean(valores)


def artefactos_nucleos(imagen):

    # copiada de test_p1_barrido_padding
    valores = []

    for nombre, fila, col, m in NUCLEOS:

        ventana = imagen[fila - m:fila + m, col - m:col + m]
        valores.append(np.std(ventana))

    return valores


def graficar_resultado(
    imagen,
    imagen_filtrada,
    carpeta_salida,
):

    diferencia = imagen - imagen_filtrada

    max_mostrar = np.percentile(imagen, 99)
    lim_diferencia = np.percentile(np.abs(diferencia), 99.5)

    espectro_antes = espectro_log(calcular_espectro(imagen))
    espectro_despues = espectro_log(calcular_espectro(imagen_filtrada))
    espectro_diferencia = espectro_log(calcular_espectro(diferencia))

    min_espectro = np.min(espectro_antes)
    max_espectro = np.max(espectro_antes)

    figura, axes = plt.subplots(
        2,
        3,
        figsize=(18, 9),
    )

    axes[0, 0].imshow(imagen, cmap="gray", vmin=0, vmax=max_mostrar)
    axes[0, 0].set_title("Imagen ruidosa")

    axes[0, 1].imshow(imagen_filtrada, cmap="gray", vmin=0, vmax=max_mostrar)
    axes[0, 1].set_title("Imagen filtrada")

    axes[0, 2].imshow(diferencia, cmap="gray", vmin=-lim_diferencia, vmax=lim_diferencia)
    axes[0, 2].set_title(f"Diferencia ruidosa - filtrada (+-{lim_diferencia:.3f})")

    axes[1, 0].imshow(espectro_antes, cmap="gray", vmin=min_espectro, vmax=max_espectro)
    axes[1, 0].set_title("log(1 + |F|) antes")

    axes[1, 1].imshow(espectro_despues, cmap="gray", vmin=min_espectro, vmax=max_espectro)
    axes[1, 1].set_title("log(1 + |F|) despues")

    axes[1, 2].imshow(espectro_diferencia, cmap="gray", vmin=min_espectro, vmax=max_espectro)
    axes[1, 2].set_title("log(1 + |F|) de la diferencia")

    for axis in axes.ravel():
        axis.axis("off")

    figura.suptitle(f"Configuracion final: {texto_parametros()}")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "resultado_final.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_zoom(
    imagen,
    imagen_filtrada,
    carpeta_salida,
):

    diferencia = imagen - imagen_filtrada

    # misma escala de diferencia en todos los zoom
    lim_diferencia = 0
    for nombre, fila, col, tam in ZONAS_ZOOM:
        recorte_dif = diferencia[fila:fila + tam, col:col + tam]
        lim = np.percentile(np.abs(recorte_dif), 99.5)
        if lim > lim_diferencia:
            lim_diferencia = lim

    figura, axes = plt.subplots(
        len(ZONAS_ZOOM),
        3,
        figsize=(13, 4.4 * len(ZONAS_ZOOM)),
    )

    for i in range(len(ZONAS_ZOOM)):

        nombre, fila, col, tam = ZONAS_ZOOM[i]

        recorte = imagen[fila:fila + tam, col:col + tam]
        recorte_filtrado = imagen_filtrada[fila:fila + tam, col:col + tam]
        recorte_dif = diferencia[fila:fila + tam, col:col + tam]

        # misma escala para ruidosa y filtrada en cada fila
        vmin = np.percentile(recorte, 1)
        vmax = np.percentile(recorte, 99.5)

        axes[i, 0].imshow(recorte, cmap="gray", vmin=vmin, vmax=vmax, interpolation="nearest")
        axes[i, 0].set_title(f"{nombre}: ruidosa")

        axes[i, 1].imshow(recorte_filtrado, cmap="gray", vmin=vmin, vmax=vmax, interpolation="nearest")
        axes[i, 1].set_title(f"{nombre}: filtrada")

        axes[i, 2].imshow(recorte_dif, cmap="gray", vmin=-lim_diferencia, vmax=lim_diferencia, interpolation="nearest")
        axes[i, 2].set_title(f"{nombre}: diferencia (+-{lim_diferencia:.3f})")

        for axis in axes[i]:
            axis.axis("off")

        axes[i, 0].text(
            0,
            -0.08,
            f"filas [{fila}, {fila + tam}), columnas [{col}, {col + tam})",
            transform=axes[i, 0].transAxes,
            fontsize=8,
        )

    figura.suptitle(f"Zoom, {texto_parametros()}")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "zoom_final.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_perfil_cielo(
    imagen,
    imagen_filtrada,
    carpeta_salida,
):

    f0 = ZONA_CIELO["fila_inicio"]
    f1 = ZONA_CIELO["fila_fin"]
    c0 = ZONA_CIELO["col_inicio"]
    c1 = ZONA_CIELO["col_fin"]

    figura, axes = plt.subplots(
        2,
        1,
        figsize=(11, 8),
    )

    for nombre, img in [("ruidosa", imagen), ("filtrada", imagen_filtrada)]:

        cielo = img[f0:f1, c0:c1]

        por_columna = np.median(cielo, axis=0)
        por_fila = np.median(cielo, axis=1)

        axes[0].plot(np.arange(N_PERFIL), por_columna[:N_PERFIL], "o-", markersize=3, label=nombre)
        axes[1].plot(np.arange(N_PERFIL), por_fila[:N_PERFIL], "o-", markersize=3, label=nombre)

    axes[0].set_title(f"Mediana de cada columna en el cielo (filas {f0} a {f1})")
    axes[0].set_xlabel(f"columna - {c0}")
    axes[1].set_title(f"Mediana de cada fila en el cielo (columnas {c0} a {c1})")
    axes[1].set_xlabel(f"fila - {f0}")

    for axis in axes:
        axis.set_ylabel("intensidad")
        axis.grid(alpha=0.3)
        axis.legend()

    figura.suptitle(texto_parametros())

    figura.tight_layout()

    ruta_salida = carpeta_salida / "perfil_cielo_final.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def guardar_parametros(
    imagen,
    imagen_filtrada,
    tiempo,
    carpeta_salida,
):

    col_antes, fila_antes = residuo_cielo(imagen)
    col_despues, fila_despues = residuo_cielo(imagen_filtrada)

    brillante_antes = residuo_zonas_brillantes(imagen)
    brillante_despues = residuo_zonas_brillantes(imagen_filtrada)

    art_antes = artefactos_nucleos(imagen)
    art_despues = artefactos_nucleos(imagen_filtrada)

    lineas = []
    lineas.append("Configuracion final P1")
    lineas.append(f"  imagen: {RUTA_IMAGEN}, {imagen.shape[0]} x {imagen.shape[1]}")
    lineas.append(f"  filtro: {FILTRO_FINAL}")
    lineas.append(f"  ancho (sigma): {ANCHO_FINAL} ciclos/pixel")
    lineas.append(f"  centros: {LISTA_CENTROS} + simetricos")
    lineas.append(f"  padding: {TIPO_PADDING}, {TAM_PADDING} pixeles por lado")
    lineas.append(f"  tiempo de filtrado: {tiempo:.1f} s")
    lineas.append("")
    lineas.append("Metricas                                   ruidosa    filtrada")
    lineas.append(f"  cielo, std mediana por columna          {col_antes:.5f}    {col_despues:.5f}")
    lineas.append(f"  cielo, std mediana por fila             {fila_antes:.5f}    {fila_despues:.5f}")
    lineas.append(f"  zonas brillantes, |F| en picos/mediana  {brillante_antes:7.1f}    {brillante_despues:7.1f}")

    for k in range(len(NUCLEOS)):
        nombre = NUCLEOS[k][0]
        lineas.append(f"  artefactos, std en {nombre:16s}    {art_antes[k]:.4f}     {art_despues[k]:.4f}")

    lineas.append(f"  std de la diferencia                       -        {np.std(imagen - imagen_filtrada):.5f}")
    lineas.append(f"  promedio de la imagen                   {np.mean(imagen):.6f}   {np.mean(imagen_filtrada):.6f}")

    print("")
    for linea in lineas:
        print(linea)

    ruta_salida = carpeta_salida / "parametros_finales.txt"

    with open(ruta_salida, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_salida}")


def main():

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    imagen = cargar_imagen(RUTA_IMAGEN)

    print(f"Imagen: {RUTA_IMAGEN}, tamano {imagen.shape}")
    print(f"Filtrando: {texto_parametros()}")

    inicio = time.time()

    imagen_filtrada = filtrar_notch(
        imagen,
        FILTRO_FINAL,
        LISTA_CENTROS,
        ANCHO_FINAL,
        TIPO_PADDING,
        TAM_PADDING,
    )

    tiempo = time.time() - inicio

    guardar_parametros(
        imagen,
        imagen_filtrada,
        tiempo,
        CARPETA_SALIDA,
    )

    graficar_resultado(
        imagen,
        imagen_filtrada,
        CARPETA_SALIDA,
    )

    graficar_zoom(
        imagen,
        imagen_filtrada,
        CARPETA_SALIDA,
    )

    graficar_perfil_cielo(
        imagen,
        imagen_filtrada,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
