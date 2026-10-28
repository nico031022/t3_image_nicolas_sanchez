from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta2 import cargar_psf
from src.pregunta2 import psf_a_otf
from src.pregunta2 import aplicar_H
from src.pregunta2 import degradar
from src.pregunta2 import calcular_rmse
from src.pregunta2 import wiener


RUTA_IMAGEN = Path("images/profesor/p2/cameraman.jpg")
RUTA_PSF = Path("images/profesor/p2/psf.png")

CARPETA_SALIDA = Path("results/pregunta2/inversa")

# sin ruido + los dos niveles elegidos en test_p2_degradacion
LISTA_SIGMAS = [0, 0.01, 0.05]

SEMILLA = 0

# nivel usado para mirar los espectros
SIGMA_ESPECTROS = 0.01

# K solo para ver la forma de la ganancia, el barrido de K va despues
K_PRUEBA = [1e-4, 1e-3, 1e-2]


def graficar_resultados(
    lista_x_inv,
    lista_rmse,
    carpeta_salida,
):

    n = len(LISTA_SIGMAS)

    figura, axes = plt.subplots(
        2,
        n,
        figsize=(5 * n, 10),
    )

    for j in range(n):

        x_inv = lista_x_inv[j]

        axes[0, j].imshow(x_inv, cmap="gray", vmin=0, vmax=1)
        axes[0, j].set_title(f"K = 0, sigma = {LISTA_SIGMAS[j]}\nRMSE = {lista_rmse[j]:.3g}, escala [0, 1]")

        im = axes[1, j].imshow(x_inv, cmap="gray")
        axes[1, j].set_title(f"misma imagen, escala min-max\n[{np.min(x_inv):.3g}, {np.max(x_inv):.3g}]")
        figura.colorbar(im, ax=axes[1, j], fraction=0.046)

    for axis in axes.flatten():
        axis.set_xticks([])
        axis.set_yticks([])

    figura.suptitle("Filtro inverso Y / H (Wiener con K = 0)")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "inversa_resultados.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_espectros(
    N,
    H,
    carpeta_salida,
):

    # fftshift solo para mostrar
    log_N = np.log10(np.abs(np.fft.fftshift(N)))
    log_inv_H = np.log10(1 / np.abs(np.fft.fftshift(H)))
    log_N_H = np.log10(np.abs(np.fft.fftshift(N / H)))

    paneles = [
        (log_N, "log10 |N| (ruido)"),
        (log_inv_H, "log10 |1 / H|"),
        (log_N_H, "log10 |N / H| (ruido despues de dividir)"),
    ]

    frec_u = np.fft.fftshift(np.fft.fftfreq(H.shape[1]))
    frec_v = np.fft.fftshift(np.fft.fftfreq(H.shape[0]))

    extension = [
        frec_u[0],
        frec_u[-1],
        frec_v[-1],
        frec_v[0],
    ]

    figura, axes = plt.subplots(
        1,
        3,
        figsize=(18, 5.5),
    )

    for j in range(3):

        im = axes[j].imshow(
            paneles[j][0],
            cmap="magma",
            vmin=-1,
            vmax=8,
            extent=extension,
        )
        axes[j].set_title(paneles[j][1])
        axes[j].set_xlabel("u [ciclos/pixel]")
        axes[j].set_ylabel("v [ciclos/pixel]")
        figura.colorbar(im, ax=axes[j], fraction=0.046)

    figura.suptitle(f"sigma = {SIGMA_ESPECTROS}, misma escala de colores en los 3")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "inversa_espectros.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_ganancia(
    H,
    carpeta_salida,
):

    figura, axes = plt.subplots(
        1,
        2,
        figsize=(15, 5.5),
    )

    # 1. ganancia |W| en funcion de |H|
    modulo_H = np.logspace(-6, 0, 500)

    axes[0].loglog(modulo_H, 1 / modulo_H, "k--", label="1 / |H| (inverso)")

    for k in range(len(K_PRUEBA)):

        K = K_PRUEBA[k]
        ganancia = modulo_H / (modulo_H**2 + K)

        axes[0].loglog(modulo_H, ganancia, color=f"C{k}", label=f"|W|, K = {K:g}")

        # maximo en |H| = raiz(K), vale 1 / (2 raiz(K))
        axes[0].plot(
            np.sqrt(K),
            1 / (2 * np.sqrt(K)),
            "o",
            color=f"C{k}",
        )

    axes[0].set_title("Ganancia |W| = |H| / (|H|^2 + K) (puntos: maximo)")
    axes[0].set_xlabel("|H|")
    axes[0].set_ylabel("ganancia")

    # 2. lo mismo pero en el eje u de nuestra H
    frec_u = np.fft.fftshift(np.fft.fftfreq(H.shape[1]))
    perfil_H = np.abs(np.fft.fftshift(H)[H.shape[0] // 2, :])

    axes[1].semilogy(frec_u, 1 / perfil_H, "k--", label="1 / |H(u, 0)|")

    for k in range(len(K_PRUEBA)):

        K = K_PRUEBA[k]
        perfil_W = perfil_H / (perfil_H**2 + K)

        axes[1].semilogy(frec_u, perfil_W, color=f"C{k}", label=f"|W(u, 0)|, K = {K:g}")

    axes[1].set_title("Ganancia en el eje u con la H de la PSF")
    axes[1].set_xlabel("u [ciclos/pixel]")

    for axis in axes:
        axis.grid(alpha=0.3, which="both")
        axis.legend(fontsize=8)

    figura.tight_layout()

    ruta_salida = carpeta_salida / "ganancia_wiener.png"

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

    H = psf_a_otf(
        psf,
        x.shape[0],
        x.shape[1],
    )

    y_borrosa = aplicar_H(x, H)

    lineas = []
    lineas.append(f"min |H|^2 = {np.min(np.abs(H)**2):.2e} (no es 0, con K = 0 no se divide por 0)")
    lineas.append(f"maxima amplificacion 1 / min |H| = {1 / np.min(np.abs(H)):.3g}")
    lineas.append("")

    # 1. filtro inverso con y sin ruido
    lineas.append("Filtro inverso (K = 0):")
    lineas.append("sigma    RMSE(x_inv, x)   min x_inv     max x_inv     RMSE del termino N/H")

    lista_x_inv = []
    lista_rmse = []

    for sigma in LISTA_SIGMAS:

        y = degradar(
            x,
            H,
            sigma,
            SEMILLA,
        )

        x_inv = wiener(
            y,
            H,
            0,
        )

        # X_inv = (H X + N) / H = X + N / H, el error es solo el ruido dividido por H
        N = np.fft.fft2(y - y_borrosa)
        termino_ruido = np.real(np.fft.ifft2(N / H))

        rmse = calcular_rmse(x_inv, x)

        lineas.append(
            f"{sigma:<8} {rmse:<16.4g} {np.min(x_inv):<13.4g} {np.max(x_inv):<13.4g} "
            f"{np.sqrt(np.mean(termino_ruido**2)):.4g}"
        )

        lista_x_inv.append(x_inv)
        lista_rmse.append(rmse)

        if sigma == SIGMA_ESPECTROS:
            N_espectros = N

    # 2. maximo de la ganancia de wiener con la H real
    lineas.append("")
    lineas.append("Ganancia de Wiener con la H de la PSF:")
    lineas.append("K        max |W| en la grilla   1 / (2 raiz(K))")

    for K in K_PRUEBA:

        W = np.abs(H) / (np.abs(H)**2 + K)

        lineas.append(f"{K:<8g} {np.max(W):<22.2f} {1 / (2 * np.sqrt(K)):.2f}")

    print("")
    for linea in lineas:
        print(linea)
    print("")

    ruta_txt = CARPETA_SALIDA / "inversa.txt"

    with open(ruta_txt, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_txt}")

    graficar_resultados(
        lista_x_inv,
        lista_rmse,
        CARPETA_SALIDA,
    )

    graficar_espectros(
        N_espectros,
        H,
        CARPETA_SALIDA,
    )

    graficar_ganancia(
        H,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
