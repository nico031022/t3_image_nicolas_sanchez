from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta1 import calcular_espectro
from src.pregunta1 import espectro_log
from src.pregunta1 import agregar_simetricos
from src.pregunta1 import filtrar_notch


RUTA_IMAGEN = Path("images/profesor/p1/P1.CR2")

CARPETA_SALIDA = Path("results/pregunta1/filtrado")

# mismos centros que en test_p1_filtros_notch
LISTA_CENTROS = [
    (0.25, 0),
    (-0.5, -0.5),
    (-0.5, 0),
    (0, -0.5),
]

# el padding se estudia despues, por ahora sin padding
TIPO_PADDING = "ninguno"
TAM_PADDING = 0

# mismos anchos de prueba que en test_p1_filtros_notch
RADIO = 0.01
SIGMA = 0.005

# zona con detalle (estrellas y nebulosa, cerca de M43), 128 x 128
ZONA_DETALLE = {
    "fila": 2180,
    "col": 1650,
    "tam": 128,
}

# zona de cielo con pocas estrellas para los perfiles
ZONA_CIELO = {
    "fila_inicio": 100,
    "fila_fin": 400,
    "col_inicio": 2400,
    "col_fin": 3200,
}

# cuantas columnas / filas se muestran en los perfiles
N_PERFIL = 40


def revisar_picos(
    imagen,
    imagen_ideal,
    imagen_gauss,
):

    alto = imagen.shape[0]
    ancho = imagen.shape[1]

    frec_u = np.fft.fftshift(np.fft.fftfreq(ancho))
    frec_v = np.fft.fftshift(np.fft.fftfreq(alto))

    magnitud = np.abs(calcular_espectro(imagen))
    magnitud_ideal = np.abs(calcular_espectro(imagen_ideal))
    magnitud_gauss = np.abs(calcular_espectro(imagen_gauss))

    # todo dividido por la mediana del espectro original
    mediana = np.median(magnitud)

    print("")
    print("|F|/mediana en los picos:")
    print("   centro             antes     ideal   gaussiano")

    for centro in agregar_simetricos(LISTA_CENTROS):

        # pixel mas cercano al centro
        col = np.argmin(np.abs(frec_u - centro[0]))
        fila = np.argmin(np.abs(frec_v - centro[1]))

        antes = magnitud[fila, col] / mediana
        ideal = magnitud_ideal[fila, col] / mediana
        gauss = magnitud_gauss[fila, col] / mediana

        print(f"   {str(centro):16s} {antes:8.1f}  {ideal:8.2f}  {gauss:8.2f}")

    print("")


def graficar_resultado(
    nombre,
    parametro,
    imagen,
    imagen_filtrada,
    lim_diferencia,
    carpeta_salida,
):

    diferencia = imagen - imagen_filtrada

    # misma escala para la imagen ruidosa y la filtrada
    max_mostrar = np.percentile(imagen, 99)

    espectro_antes = espectro_log(calcular_espectro(imagen))
    espectro_despues = espectro_log(calcular_espectro(imagen_filtrada))
    espectro_diferencia = espectro_log(calcular_espectro(diferencia))

    # misma escala para los tres espectros
    min_espectro = np.min(espectro_antes)
    max_espectro = np.max(espectro_antes)

    figura, axes = plt.subplots(
        2,
        3,
        figsize=(18, 9),
    )

    axes[0, 0].imshow(
        imagen,
        cmap="gray",
        vmin=0,
        vmax=max_mostrar,
    )
    axes[0, 0].set_title("Imagen ruidosa")

    axes[0, 1].imshow(
        imagen_filtrada,
        cmap="gray",
        vmin=0,
        vmax=max_mostrar,
    )
    axes[0, 1].set_title(f"Filtrada, notch {nombre} ({parametro})")

    axes[0, 2].imshow(
        diferencia,
        cmap="gray",
        vmin=-lim_diferencia,
        vmax=lim_diferencia,
    )
    axes[0, 2].set_title(f"Diferencia ruidosa - filtrada (escala +-{lim_diferencia:.3f})")

    axes[1, 0].imshow(
        espectro_antes,
        cmap="gray",
        vmin=min_espectro,
        vmax=max_espectro,
    )
    axes[1, 0].set_title("log(1 + |F|) antes")

    axes[1, 1].imshow(
        espectro_despues,
        cmap="gray",
        vmin=min_espectro,
        vmax=max_espectro,
    )
    axes[1, 1].set_title("log(1 + |F|) despues")

    axes[1, 2].imshow(
        espectro_diferencia,
        cmap="gray",
        vmin=min_espectro,
        vmax=max_espectro,
    )
    axes[1, 2].set_title("log(1 + |F|) de la diferencia (lo que se saco)")

    for axis in axes.ravel():
        axis.axis("off")

    figura.suptitle(f"Padding: {TIPO_PADDING}, centros: {LISTA_CENTROS} + simetricos")

    figura.tight_layout()

    ruta_salida = carpeta_salida / f"resultado_{nombre}.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_zoom_detalle(
    imagen,
    imagen_ideal,
    imagen_gauss,
    lim_diferencia,
    carpeta_salida,
):

    f0 = ZONA_DETALLE["fila"]
    c0 = ZONA_DETALLE["col"]
    tam = ZONA_DETALLE["tam"]

    recorte = imagen[f0:f0 + tam, c0:c0 + tam]
    recorte_ideal = imagen_ideal[f0:f0 + tam, c0:c0 + tam]
    recorte_gauss = imagen_gauss[f0:f0 + tam, c0:c0 + tam]

    dif_ideal = recorte - recorte_ideal
    dif_gauss = recorte - recorte_gauss

    # misma escala para los tres recortes
    min_mostrar = np.percentile(recorte, 1)
    max_mostrar = np.percentile(recorte, 99.5)

    imagenes = [
        recorte,
        recorte_ideal,
        recorte_gauss,
        dif_ideal,
        dif_gauss,
    ]

    titulos = [
        "Ruidosa",
        f"Ideal (radio = {RADIO})",
        f"Gaussiano (sigma = {SIGMA})",
        "Diferencia ideal",
        "Diferencia gaussiano",
    ]

    figura, axes = plt.subplots(
        1,
        5,
        figsize=(22, 5),
    )

    for k in range(5):

        if k < 3:
            vmin = min_mostrar
            vmax = max_mostrar
        else:
            vmin = -lim_diferencia
            vmax = lim_diferencia

        axes[k].imshow(
            imagenes[k],
            cmap="gray",
            vmin=vmin,
            vmax=vmax,
            interpolation="nearest",
        )
        axes[k].set_title(titulos[k])
        axes[k].axis("off")

    figura.suptitle(f"Zoom filas [{f0}, {f0 + tam}), columnas [{c0}, {c0 + tam})")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "zoom_detalle.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_perfil_cielo(
    imagen,
    imagen_ideal,
    imagen_gauss,
    carpeta_salida,
):

    f0 = ZONA_CIELO["fila_inicio"]
    f1 = ZONA_CIELO["fila_fin"]
    c0 = ZONA_CIELO["col_inicio"]
    c1 = ZONA_CIELO["col_fin"]

    imagenes = [
        ("ruidosa", imagen),
        ("ideal", imagen_ideal),
        ("gaussiano", imagen_gauss),
    ]

    figura, axes = plt.subplots(
        2,
        1,
        figsize=(11, 8),
    )

    for nombre, img in imagenes:

        cielo = img[f0:f1, c0:c1]

        # mediana para que las estrellas no molesten
        por_columna = np.median(cielo, axis=0)
        por_fila = np.median(cielo, axis=1)

        axes[0].plot(
            np.arange(N_PERFIL),
            por_columna[:N_PERFIL],
            "o-",
            markersize=3,
            label=nombre,
        )

        axes[1].plot(
            np.arange(N_PERFIL),
            por_fila[:N_PERFIL],
            "o-",
            markersize=3,
            label=nombre,
        )

    axes[0].set_title(f"Mediana de cada columna en el cielo (filas {f0} a {f1})")
    axes[0].set_xlabel(f"columna - {c0}")
    axes[1].set_title(f"Mediana de cada fila en el cielo (columnas {c0} a {c1})")
    axes[1].set_xlabel(f"fila - {f0}")

    for axis in axes:
        axis.set_ylabel("intensidad")
        axis.grid(alpha=0.3)
        axis.legend()

    figura.tight_layout()

    ruta_salida = carpeta_salida / "perfil_cielo.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
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

    print(f"Imagen: {RUTA_IMAGEN}, tamano {imagen.shape}")

    print(f"Notch ideal, radio = {RADIO}")
    imagen_ideal = filtrar_notch(
        imagen,
        "ideal",
        LISTA_CENTROS,
        RADIO,
        TIPO_PADDING,
        TAM_PADDING,
    )

    print(f"Notch gaussiano, sigma = {SIGMA}")
    imagen_gauss = filtrar_notch(
        imagen,
        "gaussiano",
        LISTA_CENTROS,
        SIGMA,
        TIPO_PADDING,
        TAM_PADDING,
    )

    print("")
    print(f"Promedio ruidosa:  {np.mean(imagen):.6f}")
    print(f"Promedio ideal:    {np.mean(imagen_ideal):.6f}")
    print(f"Promedio gaussiano: {np.mean(imagen_gauss):.6f}")

    diferencia_ideal = imagen - imagen_ideal
    diferencia_gauss = imagen - imagen_gauss

    print(f"Desviacion de la diferencia, ideal:     {np.std(diferencia_ideal):.5f}")
    print(f"Desviacion de la diferencia, gaussiano: {np.std(diferencia_gauss):.5f}")

    revisar_picos(
        imagen,
        imagen_ideal,
        imagen_gauss,
    )

    # misma escala de diferencia para los dos filtros
    lim_ideal = np.percentile(np.abs(diferencia_ideal), 99.5)
    lim_gauss = np.percentile(np.abs(diferencia_gauss), 99.5)
    lim_diferencia = max(lim_ideal, lim_gauss)

    graficar_resultado(
        "ideal",
        f"radio = {RADIO}",
        imagen,
        imagen_ideal,
        lim_diferencia,
        CARPETA_SALIDA,
    )

    graficar_resultado(
        "gaussiano",
        f"sigma = {SIGMA}",
        imagen,
        imagen_gauss,
        lim_diferencia,
        CARPETA_SALIDA,
    )

    graficar_zoom_detalle(
        imagen,
        imagen_ideal,
        imagen_gauss,
        lim_diferencia,
        CARPETA_SALIDA,
    )

    graficar_perfil_cielo(
        imagen,
        imagen_ideal,
        imagen_gauss,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
