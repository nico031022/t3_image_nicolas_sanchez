from pathlib import Path
import time

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta2 import cargar_psf
from src.pregunta2 import psf_a_otf
from src.pregunta2 import aplicar_H
from src.pregunta2 import aplicar_Ht
from src.pregunta2 import degradar
from src.pregunta2 import calcular_rmse
from src.pregunta2 import tikhonov_gd


RUTA_IMAGEN = Path("images/profesor/p2/cameraman.jpg")
RUTA_PSF = Path("images/profesor/p2/psf.png")

CARPETA_SALIDA = Path("results/pregunta2/tikhonov_check")

SIGMA = 0.01
SEMILLA = 0

# valores de prueba, el barrido de lambda y tau va en el siguiente script
LAMBDA_PRUEBA = 4.64e-3    # K_opt de Wiener para sigma = 0.01
TAU_PRUEBA = 1.0           # cumple 0 < tau < 2 / (1 + lambda)
MAX_ITER_PRUEBA = 2000
TOL_PRUEBA = 1e-6


def prueba_adjunto(
    H,
    lineas,
):

    # <H a, b> tiene que ser igual a <a, Ht b> para cualquier a y b
    rng = np.random.default_rng(1)

    a = rng.standard_normal(H.shape)
    b = rng.standard_normal(H.shape)

    izquierda = np.sum(aplicar_H(a, H) * b)
    derecha = np.sum(a * aplicar_Ht(b, H))

    lineas.append("Prueba del adjunto con a y b aleatorias:")
    lineas.append(f"  <H a, b>  = {izquierda:.10f}")
    lineas.append(f"  <a, Ht b> = {derecha:.10f}")
    lineas.append(f"  diferencia relativa = {abs(izquierda - derecha) / abs(izquierda):.2e}")


def comparar_H_y_Ht(
    psf,
    H,
    y,
    lineas,
):

    # Ht deberia ser la convolucion con la psf girada en 180 grados
    psf_girada = psf[::-1, ::-1]

    H_girada = psf_a_otf(
        psf_girada,
        H.shape[0],
        H.shape[1],
    )

    lineas.append("H transpuesta:")
    lineas.append(f"  max |otf(psf girada) - conj(H)| = {np.max(np.abs(H_girada - np.conj(H))):.2e}")

    # como la psf no es simetrica, usar H en vez de Ht no da lo mismo
    Ht_y = aplicar_Ht(y, H)
    H_y = aplicar_H(y, H)

    lineas.append(f"  max |Ht y - H y| = {np.max(np.abs(Ht_y - H_y)):.2e} (max |H y| = {np.max(np.abs(H_y)):.3f})")


def graficar_prueba(
    lista_costo,
    lista_rmse,
    lista_cambio,
    carpeta_salida,
):

    figura, axes = plt.subplots(
        1,
        3,
        figsize=(18, 5),
    )

    axes[0].semilogy(lista_costo)
    axes[0].set_title("Costo J(x)")

    axes[1].plot(lista_rmse)
    axes[1].set_title("RMSE(x_k, x)")

    # el cambio empieza en la iteracion 1
    iteraciones = np.arange(1, len(lista_cambio) + 1)
    axes[2].semilogy(iteraciones, lista_cambio)
    axes[2].axhline(TOL_PRUEBA, color="gray", linestyle="--", label=f"tol = {TOL_PRUEBA}")
    axes[2].set_title("||x_k+1 - x_k|| / ||x_k||")
    axes[2].legend()

    for axis in axes:
        axis.set_xlabel("iteracion")
        axis.grid(alpha=0.3, which="both")

    figura.suptitle(
        f"Prueba de tikhonov_gd: sigma = {SIGMA}, lambda = {LAMBDA_PRUEBA}, tau = {TAU_PRUEBA}, "
        f"max_iter = {MAX_ITER_PRUEBA}, tol = {TOL_PRUEBA}"
    )

    figura.tight_layout()

    ruta_salida = carpeta_salida / "prueba_tikhonov.png"

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

    y = degradar(
        x,
        H,
        SIGMA,
        SEMILLA,
    )

    lineas = []

    # 1. H y Ht
    prueba_adjunto(
        H,
        lineas,
    )

    comparar_H_y_Ht(
        psf,
        H,
        y,
        lineas,
    )

    # 2. una corrida de prueba
    inicio = time.time()

    x_est, lista_costo, lista_rmse, lista_cambio, n_iter = tikhonov_gd(
        y,
        H,
        LAMBDA_PRUEBA,
        TAU_PRUEBA,
        MAX_ITER_PRUEBA,
        TOL_PRUEBA,
        x,
    )

    tiempo = time.time() - inicio

    # el costo no deberia subir nunca
    diferencias = np.diff(lista_costo)
    n_subidas = np.sum(diferencias > 0)

    lineas.append("")
    lineas.append(f"Corrida de prueba (lambda = {LAMBDA_PRUEBA}, tau = {TAU_PRUEBA}):")
    lineas.append(f"  iteraciones: {n_iter} (max {MAX_ITER_PRUEBA}), tiempo {tiempo:.1f} s")
    lineas.append(f"  ultimo cambio relativo: {lista_cambio[-1]:.2e} (tol {TOL_PRUEBA})")
    lineas.append(f"  costo: inicial {lista_costo[0]:.4f}, final {lista_costo[-1]:.4f}")
    lineas.append(f"  veces que el costo subio: {n_subidas}")
    lineas.append(f"  RMSE: inicial (y) {lista_rmse[0]:.4f}, final {lista_rmse[-1]:.4f}")
    lineas.append(f"  RMSE minimo {np.min(lista_rmse):.4f} en la iteracion {np.argmin(lista_rmse)}")
    lineas.append(f"  RMSE final con calcular_rmse: {calcular_rmse(x_est, x):.4f}")

    print("")
    for linea in lineas:
        print(linea)
    print("")

    ruta_txt = CARPETA_SALIDA / "tikhonov_check.txt"

    with open(ruta_txt, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_txt}")

    graficar_prueba(
        lista_costo,
        lista_rmse,
        lista_cambio,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
