from pathlib import Path

import numpy as np
import cv2
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta2 import cargar_psf
from src.pregunta2 import psf_a_otf
from src.pregunta2 import degradar
from src.pregunta2 import calcular_rmse
from src.pregunta2 import wiener


RUTA_IMAGEN = Path("images/profesor/p2/cameraman.jpg")
RUTA_PSF = Path("images/profesor/p2/psf.png")

CARPETA_SALIDA = Path("results/pregunta2/psf_incorrecta")

# con poco ruido se ve mejor el efecto del error en la psf
SIGMA = 0.01

SEMILLA = 0

# K_opt con la psf correcta para sigma = 0.01 (test_p2_wiener_barrido)
K_OPT_CORRECTA = 4.64e-3

# mismo barrido que en test_p2_wiener_barrido
LISTA_K = np.logspace(-7, 1, 61)

# perturbaciones: centro corrido 1 pixel y ancho +-10 %
DESPLAZAMIENTO = 1
FACTOR_ANCHA = 1.1
FACTOR_ANGOSTA = 0.9

ZOOM_FILAS = (30, 110)
ZOOM_COLS = (100, 200)


def crear_psf_desplazada(
    psf,
    desplazamiento,
):

    # la psf corrida a la derecha (como si el centro estuviera mal)
    psf_mal = np.roll(
        psf,
        desplazamiento,
        axis=1,
    )

    return psf_mal


def crear_psf_escalada(
    psf,
    factor,
):

    alto_psf = psf.shape[0]
    ancho_psf = psf.shape[1]

    centro = (ancho_psf // 2, alto_psf // 2)

    # escalar alrededor del centro, sin rotar, y dejarla del mismo tamano
    matriz = cv2.getRotationMatrix2D(centro, 0, factor)

    psf_mal = cv2.warpAffine(
        psf,
        matriz,
        (ancho_psf, alto_psf),
        flags=cv2.INTER_LINEAR,
    )

    # que vuelva a sumar 1
    psf_mal = psf_mal / np.sum(psf_mal)

    return psf_mal


def graficar_psfs(
    lista_psf,
    carpeta_salida,
):

    n = len(lista_psf)

    figura, axes = plt.subplots(
        2,
        n,
        figsize=(4 * n, 7.5),
    )

    psf_correcta = lista_psf[0][1]

    vmax = np.max(psf_correcta)

    for j in range(n):

        nombre = lista_psf[j][0]
        psf_j = lista_psf[j][1]

        axes[0, j].imshow(psf_j, cmap="inferno", vmin=0, vmax=vmax, interpolation="nearest")
        axes[0, j].set_title(nombre)

        diferencia = psf_j - psf_correcta

        axes[1, j].imshow(
            diferencia,
            cmap="seismic",
            vmin=-0.01,
            vmax=0.01,
            interpolation="nearest",
        )
        axes[1, j].set_title("h usada - h correcta")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "psfs.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_curvas(
    lista_psf,
    curvas,
    carpeta_salida,
):

    figura, axis = plt.subplots(
        1,
        1,
        figsize=(10, 6),
    )

    for j in range(len(lista_psf)):

        rmse = curvas[j]
        i_opt = np.argmin(rmse)

        axis.semilogx(
            LISTA_K,
            rmse,
            "o-",
            markersize=3,
            color=f"C{j}",
            label=lista_psf[j][0],
        )

        axis.plot(
            LISTA_K[i_opt],
            rmse[i_opt],
            "*",
            markersize=15,
            color=f"C{j}",
            markeredgecolor="k",
        )

    axis.axvline(
        K_OPT_CORRECTA,
        color="gray",
        linestyle="--",
        label=f"K_opt psf correcta = {K_OPT_CORRECTA}",
    )

    axis.set_ylim(0, 0.2)
    axis.set_title(f"RMSE vs K con PSF correcta e incorrectas (sigma = {SIGMA})")
    axis.set_xlabel("K")
    axis.set_ylabel("RMSE(x estimada, x)")
    axis.grid(alpha=0.3, which="both")
    axis.legend(fontsize=9)

    figura.tight_layout()

    ruta_salida = carpeta_salida / "rmse_vs_K_psf.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_reconstrucciones(
    x,
    lista_psf,
    lista_x_est,
    lista_rmse,
    carpeta_salida,
):

    f0, f1 = ZOOM_FILAS
    c0, c1 = ZOOM_COLS

    n = len(lista_psf) + 1

    figura, axes = plt.subplots(
        3,
        n,
        figsize=(4 * n, 11),
    )

    imagenes = [x] + lista_x_est
    titulos = ["x (ideal)"]
    for j in range(len(lista_psf)):
        titulos.append(f"{lista_psf[j][0]}\nRMSE = {lista_rmse[j]:.4f}")

    for j in range(n):

        axes[0, j].imshow(imagenes[j], cmap="gray", vmin=0, vmax=1)
        axes[0, j].set_title(titulos[j], fontsize=10)

        axes[1, j].imshow(
            imagenes[j][f0:f1, c0:c1],
            cmap="gray",
            vmin=0,
            vmax=1,
            interpolation="nearest",
        )
        axes[1, j].set_title(f"zoom filas {f0}-{f1}, col {c0}-{c1}", fontsize=9)

        error = np.abs(imagenes[j] - x)

        axes[2, j].imshow(error, cmap="magma", vmin=0, vmax=0.3)
        axes[2, j].set_title("|x estimada - x|, escala [0, 0.3]", fontsize=9)

    for axis in axes.flatten():
        axis.set_xticks([])
        axis.set_yticks([])

    figura.suptitle(f"Wiener con K = {K_OPT_CORRECTA} y distintas PSF (y hecha con la correcta, sigma = {SIGMA})")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "reconstrucciones_psf.png"

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

    x = cargar_imagen(RUTA_IMAGEN)
    psf = cargar_psf(RUTA_PSF)

    alto = x.shape[0]
    ancho = x.shape[1]

    # la observacion siempre se hace con la psf correcta
    H = psf_a_otf(
        psf,
        alto,
        ancho,
    )

    y = degradar(
        x,
        H,
        SIGMA,
        SEMILLA,
    )

    lista_psf = [
        ("correcta", psf),
        (f"corrida {DESPLAZAMIENTO} px", crear_psf_desplazada(psf, DESPLAZAMIENTO)),
        (f"ancha x {FACTOR_ANCHA}", crear_psf_escalada(psf, FACTOR_ANCHA)),
        (f"angosta x {FACTOR_ANGOSTA}", crear_psf_escalada(psf, FACTOR_ANGOSTA)),
    ]

    lineas = []
    lineas.append(f"sigma = {SIGMA}, RMSE degradada y = {calcular_rmse(y, x):.4f}")
    lineas.append("")
    lineas.append(f"psf usada         ||h_mal - h|| / ||h||   RMSE con K = {K_OPT_CORRECTA}   K_opt propio   RMSE con K_opt propio")

    lista_x_est = []
    lista_rmse = []
    curvas = []

    for nombre, psf_usada in lista_psf:

        H_usada = psf_a_otf(
            psf_usada,
            alto,
            ancho,
        )

        dif_relativa = np.linalg.norm(psf_usada - psf) / np.linalg.norm(psf)

        # 1. con el K que era optimo para la psf correcta
        x_est = wiener(
            y,
            H_usada,
            K_OPT_CORRECTA,
        )

        rmse = calcular_rmse(x_est, x)

        # 2. barrido de K con esta psf
        rmse_barrido = []
        for K in LISTA_K:
            x_k = wiener(y, H_usada, K)
            rmse_barrido.append(calcular_rmse(x_k, x))

        rmse_barrido = np.array(rmse_barrido)
        i_opt = np.argmin(rmse_barrido)

        lineas.append(
            f"{nombre:<17} {dif_relativa:<23.3f} {rmse:<23.4f} {LISTA_K[i_opt]:<14.2e} {rmse_barrido[i_opt]:.4f}"
        )

        lista_x_est.append(x_est)
        lista_rmse.append(rmse)
        curvas.append(rmse_barrido)

    # con la psf corrida la imagen deberia salir movida 1 pixel al otro lado
    x_corrida = lista_x_est[1]
    x_correcta = lista_x_est[0]

    x_corrida_devuelta = np.roll(
        x_corrida,
        DESPLAZAMIENTO,
        axis=1,
    )

    lineas.append("")
    lineas.append("PSF corrida:")
    lineas.append(f"  max |x_corrida - x_correcta| = {np.max(np.abs(x_corrida - x_correcta)):.4f}")
    lineas.append(f"  max |x_corrida movida {DESPLAZAMIENTO} px - x_correcta| = {np.max(np.abs(x_corrida_devuelta - x_correcta)):.2e}")

    print("")
    for linea in lineas:
        print(linea)
    print("")

    ruta_txt = CARPETA_SALIDA / "psf_incorrecta.txt"

    with open(ruta_txt, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_txt}")

    graficar_psfs(
        lista_psf,
        CARPETA_SALIDA,
    )

    graficar_curvas(
        lista_psf,
        curvas,
        CARPETA_SALIDA,
    )

    graficar_reconstrucciones(
        x,
        lista_psf,
        lista_x_est,
        lista_rmse,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
