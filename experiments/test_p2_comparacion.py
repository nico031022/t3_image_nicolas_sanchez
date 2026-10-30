from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta2 import cargar_psf
from src.pregunta2 import psf_a_otf
from src.pregunta2 import degradar
from src.pregunta2 import calcular_rmse
from src.pregunta2 import wiener
from src.pregunta2 import tikhonov_gd


RUTA_IMAGEN = Path("images/profesor/p2/cameraman.jpg")
RUTA_PSF = Path("images/profesor/p2/psf.png")

CARPETA_SALIDA = Path("results/pregunta2/comparacion")

SEMILLA = 0

# niveles elegidos y su K_opt de Wiener (test_p2_wiener_barrido)
LISTA_SIGMAS = [0.01, 0.05]
LISTA_K_OPT = [4.64e-3, 2.93e-2]

# tau mas rapido que fue estable en test_p2_tikhonov_barrido
TAU = 1.9

# tol muy chica para acercarse lo mas posible a la solucion cerrada
TOL = 1e-9
MAX_ITER = 3000

ZOOM_FILAS = (30, 110)
ZOOM_COLS = (100, 200)


def mejor_iteracion(
    y,
    H,
    lam,
    x,
):

    # corrida completa guardando el RMSE contra x
    x_final, lista_costo, lista_rmse, lista_cambio, n_iter = tikhonov_gd(
        y,
        H,
        lam,
        TAU,
        MAX_ITER,
        TOL,
        x,
    )

    # lista_rmse[k] es el RMSE despues de k iteraciones (k = 0 es y)
    k_mejor = int(np.argmin(lista_rmse))

    # se repite parando justo en k_mejor (el metodo es determinista, sale la misma imagen)
    x_mejor, _, _, _, _ = tikhonov_gd(
        y,
        H,
        lam,
        TAU,
        k_mejor,
        TOL,
    )

    resultado = {
        "x_final": x_final,
        "n_iter": n_iter,
        "rmse_final": lista_rmse[-1],
        "x_mejor": x_mejor,
        "k_mejor": k_mejor,
        "rmse_mejor": lista_rmse[k_mejor],
    }

    return resultado


def graficar_distancia(
    curvas,
    carpeta_salida,
):

    figura, axis = plt.subplots(
        1,
        1,
        figsize=(10, 5.5),
    )

    for j in range(len(curvas)):

        sigma, lam, distancias = curvas[j]

        iteraciones = np.arange(len(distancias))

        axis.semilogy(
            iteraciones,
            distancias,
            color=f"C{j}",
            label=f"sigma = {sigma}, lambda = K = {lam}",
        )

        # la frecuencia mas lenta se achica (1 - tau lambda) por iteracion
        referencia = distancias[0] * (1 - TAU * lam)**iteraciones

        axis.semilogy(
            iteraciones,
            referencia,
            color=f"C{j}",
            linestyle="--",
            linewidth=1,
            label=f"(1 - tau lambda)^k = {1 - TAU * lam:.4f}^k",
        )

    axis.set_title(f"RMSE entre la iteracion k y la solucion cerrada (tau = {TAU}, tol = {TOL})")
    axis.set_xlabel("iteracion k")
    axis.set_ylabel("RMSE(x_k, x_cerrada)")
    axis.grid(alpha=0.3, which="both")
    axis.legend(fontsize=9)

    figura.tight_layout()

    ruta_salida = carpeta_salida / "distancia_a_cerrada.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_mejores(
    x,
    filas,
    carpeta_salida,
):

    f0, f1 = ZOOM_FILAS
    c0, c1 = ZOOM_COLS

    n_columnas = len(filas[0])

    figura, axes = plt.subplots(
        2 * len(filas),
        n_columnas,
        figsize=(3.8 * n_columnas, 7 * len(filas)),
    )

    for i in range(len(filas)):

        for j in range(n_columnas):

            imagen, titulo = filas[i][j]

            axes[2 * i, j].imshow(imagen, cmap="gray", vmin=0, vmax=1)
            axes[2 * i, j].set_title(titulo, fontsize=9)

            axes[2 * i + 1, j].imshow(
                imagen[f0:f1, c0:c1],
                cmap="gray",
                vmin=0,
                vmax=1,
                interpolation="nearest",
            )
            axes[2 * i + 1, j].set_title(f"zoom filas {f0}-{f1}, col {c0}-{c1}", fontsize=8)

    for axis in axes.flatten():
        axis.set_xticks([])
        axis.set_yticks([])

    figura.suptitle(f"Mejores reconstrucciones, escala [0, 1] (Tikhonov con tau = {TAU})")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "mejores_reconstrucciones.png"

    figura.savefig(
        ruta_salida,
        dpi=130,
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

    lineas = []
    lineas.append(f"tau = {TAU}, tol = {TOL}, max_iter = {MAX_ITER}")

    curvas = []
    filas = []

    for i in range(len(LISTA_SIGMAS)):

        sigma = LISTA_SIGMAS[i]
        K = LISTA_K_OPT[i]

        y = degradar(
            x,
            H,
            sigma,
            SEMILLA,
        )

        lineas.append("")
        lineas.append(f"sigma = {sigma}, K_opt = {K}, RMSE degradada y = {calcular_rmse(y, x):.4f}")

        # 1. lambda = K: solucion cerrada (Wiener) vs iterativa
        print(f"sigma = {sigma}, lambda = {K}")

        x_cerrada = wiener(y, H, K)

        # pasando x_cerrada como x_real, la lista de RMSE es la distancia a la solucion cerrada
        x_iter, _, distancias, _, n_iter = tikhonov_gd(
            y,
            H,
            K,
            TAU,
            MAX_ITER,
            TOL,
            x_cerrada,
        )

        curvas.append((sigma, K, distancias))

        lineas.append(f"  lambda = K = {K}:")
        lineas.append(f"    cerrada (Wiener K):           RMSE = {calcular_rmse(x_cerrada, x):.5f}")
        lineas.append(f"    iterativa convergida:         RMSE = {calcular_rmse(x_iter, x):.5f} ({n_iter} iteraciones)")
        lineas.append(f"    iterativa vs cerrada:         RMSE = {calcular_rmse(x_iter, x_cerrada):.2e}, max |dif| = {np.max(np.abs(x_iter - x_cerrada)):.2e}")

        mejor_K = mejor_iteracion(y, H, K, x)

        lineas.append(f"    iterativa mejor (min RMSE):   RMSE = {mejor_K['rmse_mejor']:.5f} en la iteracion {mejor_K['k_mejor']}")
        lineas.append(f"    mejor vs cerrada:             RMSE = {calcular_rmse(mejor_K['x_mejor'], x_cerrada):.2e}, max |dif| = {np.max(np.abs(mejor_K['x_mejor'] - x_cerrada)):.2e}")

        # 2. lambda = 0: solucion cerrada (filtro inverso) vs iterativa
        print(f"sigma = {sigma}, lambda = 0")

        x_inversa = wiener(y, H, 0)

        mejor_0 = mejor_iteracion(y, H, 0, x)

        lineas.append("  lambda = 0:")
        lineas.append(f"    cerrada (filtro inverso):     RMSE = {calcular_rmse(x_inversa, x):.4g}")
        lineas.append(f"    iterativa mejor (min RMSE):   RMSE = {mejor_0['rmse_mejor']:.5f} en la iteracion {mejor_0['k_mejor']}")
        lineas.append(f"    iterativa en la ultima ({mejor_0['n_iter']}):  RMSE = {mejor_0['rmse_final']:.5f}")
        lineas.append(f"    mejor vs cerrada:             RMSE = {calcular_rmse(mejor_0['x_mejor'], x_inversa):.4g}")

        fila = [
            (x, "x (ideal)"),
            (y, f"degradada y, sigma = {sigma}\nRMSE = {calcular_rmse(y, x):.4f}"),
            (x_cerrada, f"Wiener K = {K}\nRMSE = {calcular_rmse(x_cerrada, x):.4f}"),
            (mejor_K["x_mejor"], f"Tikhonov lambda = {K}, iter {mejor_K['k_mejor']}\nRMSE = {mejor_K['rmse_mejor']:.4f}"),
            (mejor_0["x_mejor"], f"Tikhonov lambda = 0, iter {mejor_0['k_mejor']}\nRMSE = {mejor_0['rmse_mejor']:.4f}"),
        ]

        filas.append(fila)

    print("")
    for linea in lineas:
        print(linea)
    print("")

    ruta_txt = CARPETA_SALIDA / "comparacion.txt"

    with open(ruta_txt, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_txt}")

    graficar_distancia(
        curvas,
        CARPETA_SALIDA,
    )

    graficar_mejores(
        x,
        filas,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
