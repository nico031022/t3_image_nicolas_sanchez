from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta2 import cargar_psf
from src.pregunta2 import psf_a_otf
from src.pregunta2 import aplicar_H
from src.pregunta2 import degradar
from src.pregunta2 import calcular_rmse
from src.pregunta2 import costo_tikhonov
from src.pregunta2 import tikhonov_gd


RUTA_IMAGEN = Path("images/profesor/p2/cameraman.jpg")
RUTA_PSF = Path("images/profesor/p2/psf.png")

CARPETA_SALIDA = Path("results/pregunta2/preguntas")

SIGMA = 0.01
SEMILLA = 0

# mismos valores que antes (K_opt de Wiener para sigma = 0.01, tau seguro)
LAMBDA = 4.64e-3
TAU = 1.0
MAX_ITER = 1000
TOL = 1e-7

ZOOM_FILAS = (30, 110)
ZOOM_COLS = (100, 200)


def tikhonov_gd_con_H(
    y,
    H,
    lam,
    tau,
    max_iter,
    tol,
    x_real,
):

    # copia de tikhonov_gd pero usando H en vez de Ht (error a proposito)
    x = y.copy()

    lista_costo = [costo_tikhonov(x, y, H, lam)]
    lista_rmse = [calcular_rmse(x, x_real)]

    n_iter = 0

    for k in range(max_iter):

        residuo = aplicar_H(x, H) - y
        grad_fidelidad = aplicar_H(residuo, H)    # aqui deberia ir aplicar_Ht
        grad_regularizacion = lam * x

        gradiente = grad_fidelidad + grad_regularizacion

        x_nuevo = x - tau * gradiente

        costo = costo_tikhonov(x_nuevo, y, H, lam)
        cambio = np.linalg.norm(x_nuevo - x) / np.linalg.norm(x)

        x = x_nuevo
        n_iter = k + 1

        lista_costo.append(costo)
        lista_rmse.append(calcular_rmse(x, x_real))

        if not np.isfinite(costo):
            print(f"  diverge en la iteracion {n_iter}")
            break

        if cambio < tol:
            break

    return x, lista_costo, lista_rmse, n_iter


def graficar_curvas(
    corridas,
    carpeta_salida,
):

    figura, axes = plt.subplots(
        1,
        2,
        figsize=(16, 5.5),
    )

    for j in range(len(corridas)):

        nombre = corridas[j]["nombre"]

        axes[0].semilogy(corridas[j]["costo"], color=f"C{j}", label=nombre)
        axes[1].semilogy(corridas[j]["rmse"], color=f"C{j}", label=nombre)

    axes[0].set_title("Costo J(x_k)")
    axes[1].set_title("RMSE(x_k, x)")

    for axis in axes:
        axis.set_xlabel("iteracion")
        axis.grid(alpha=0.3, which="both")
        axis.legend(fontsize=9)

    figura.suptitle(f"Descenso de gradiente con Ht (correcto) y con H (incorrecto), lambda = {LAMBDA}, tau = {TAU}")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "H_en_vez_de_Ht_curvas.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_imagenes(
    corridas,
    carpeta_salida,
):

    f0, f1 = ZOOM_FILAS
    c0, c1 = ZOOM_COLS

    n = len(corridas)

    figura, axes = plt.subplots(
        2,
        n,
        figsize=(4 * n, 7.5),
    )

    for j in range(n):

        imagen = corridas[j]["x_est"]
        titulo = f"{corridas[j]['nombre']}\n{corridas[j]['n_iter']} it., RMSE = {corridas[j]['rmse'][-1]:.4g}"

        axes[0, j].imshow(imagen, cmap="gray", vmin=0, vmax=1)
        axes[0, j].set_title(titulo, fontsize=9)

        axes[1, j].imshow(
            imagen[f0:f1, c0:c1],
            cmap="gray",
            vmin=0,
            vmax=1,
            interpolation="nearest",
        )
        axes[1, j].set_title(f"zoom filas {f0}-{f1}, col {c0}-{c1}", fontsize=8)

    for axis in axes.flatten():
        axis.set_xticks([])
        axis.set_yticks([])

    figura.suptitle("Ultima iteracion, escala [0, 1]")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "H_en_vez_de_Ht_imagenes.png"

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

    # la psf corrida 1 pixel de test_p2_psf_incorrecta, ahora como psf "real" no simetrica
    psf_corrida = np.roll(
        psf,
        1,
        axis=1,
    )

    lista_psf = [
        ("psf original", psf),
        ("psf corrida 1 px", psf_corrida),
    ]

    lineas = []
    lineas.append(f"sigma = {SIGMA}, lambda = {LAMBDA}, tau = {TAU}, max_iter = {MAX_ITER}, tol = {TOL}")
    lineas.append("y se hace con la misma psf que se usa para restaurar, lo unico malo es H en vez de Ht")

    corridas = []

    for nombre, psf_usada in lista_psf:

        H = psf_a_otf(
            psf_usada,
            x.shape[0],
            x.shape[1],
        )

        y = degradar(
            x,
            H,
            SIGMA,
            SEMILLA,
        )

        asimetria = np.max(np.abs(psf_usada - psf_usada[::-1, ::-1])) / np.max(psf_usada)

        # factor por iteracion en cada frecuencia
        factor_Ht = np.abs(1 - TAU * (np.abs(H)**2 + LAMBDA))
        factor_H = np.abs(1 - TAU * (H**2 + LAMBDA))

        # punto fijo con H: (H^2 + lambda) X = H Y
        Y = np.fft.fft2(y)
        x_punto_fijo = np.real(np.fft.ifft2(H * Y / (H**2 + LAMBDA)))

        lineas.append("")
        lineas.append(f"{nombre}: max |h - h girada| / max h = {100 * asimetria:.2f} %")
        lineas.append(f"  max |1 - tau (|H|^2 + lambda)| (con Ht) = {np.max(factor_Ht):.4f}")
        lineas.append(f"  max |1 - tau (H^2 + lambda)|   (con H)  = {np.max(factor_H):.4f}")
        lineas.append(f"  frecuencias con factor > 1 usando H: {np.sum(factor_H > 1)} de {H.size}")
        lineas.append(f"  min de la parte real de H^2: {np.min(np.real(H**2)):.4f}")
        lineas.append(f"  punto fijo con H, H Y / (H^2 + lambda): RMSE = {calcular_rmse(x_punto_fijo, x):.4g}")

        print(f"{nombre}, con Ht")

        x_bien, costo_bien, rmse_bien, _, n_bien = tikhonov_gd(
            y,
            H,
            LAMBDA,
            TAU,
            MAX_ITER,
            TOL,
            x,
        )

        print(f"{nombre}, con H")

        x_mal, costo_mal, rmse_mal, n_mal = tikhonov_gd_con_H(
            y,
            H,
            LAMBDA,
            TAU,
            MAX_ITER,
            TOL,
            x,
        )

        subidas_bien = np.sum(np.diff(costo_bien) > 0)
        subidas_mal = np.sum(np.diff(costo_mal) > 0)

        lineas.append(f"  con Ht: {n_bien} it., RMSE final = {rmse_bien[-1]:.4f}, el costo subio {subidas_bien} veces")
        lineas.append(f"  con H:  {n_mal} it., RMSE final = {rmse_mal[-1]:.4g}, el costo subio {subidas_mal} veces")
        lineas.append(f"  max |x con H - x con Ht| = {np.max(np.abs(x_mal - x_bien)):.4g}")

        corridas.append({
            "nombre": f"{nombre}, con Ht",
            "x_est": x_bien,
            "costo": costo_bien,
            "rmse": rmse_bien,
            "n_iter": n_bien,
        })

        corridas.append({
            "nombre": f"{nombre}, con H",
            "x_est": x_mal,
            "costo": costo_mal,
            "rmse": rmse_mal,
            "n_iter": n_mal,
        })

    print("")
    for linea in lineas:
        print(linea)
    print("")

    ruta_txt = CARPETA_SALIDA / "H_en_vez_de_Ht.txt"

    with open(ruta_txt, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_txt}")

    graficar_curvas(
        corridas,
        CARPETA_SALIDA,
    )

    graficar_imagenes(
        corridas,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
