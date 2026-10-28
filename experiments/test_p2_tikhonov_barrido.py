from pathlib import Path
import time

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta2 import cargar_psf
from src.pregunta2 import psf_a_otf
from src.pregunta2 import degradar
from src.pregunta2 import calcular_rmse
from src.pregunta2 import tikhonov_gd


RUTA_IMAGEN = Path("images/profesor/p2/cameraman.jpg")
RUTA_PSF = Path("images/profesor/p2/psf.png")

CARPETA_SALIDA = Path("results/pregunta2/tikhonov")

SIGMA = 0.01
SEMILLA = 0

# K_opt de Wiener para sigma = 0.01 (test_p2_wiener_barrido)
K_OPT = 4.64e-3

# lambda: K_opt y un orden de magnitud a cada lado, mas lambda = 0
LISTA_LAMBDAS = [0, K_OPT / 10, K_OPT, K_OPT * 10]

# tau: el limite es 2 / (1 + lambda) (~1.99 con K_opt, ~1.91 con K_opt x 10)
# 0.5 lento, 1.0 seguro, 1.9 cerca del limite, 2.05 pasado el limite
LISTA_TAUS = [0.5, 1.0, 1.9, 2.05]

# barrido de tau con lambda = K_opt, barrido de lambda con tau = 1
LAMBDA_FIJO = K_OPT
TAU_FIJO = 1.0

# con lambda = K_opt y tau = 1 la frecuencia mas lenta baja e veces cada 1 / (tau lambda) ~ 215 iteraciones
# con 3000 alcanza para converger, y con K_opt / 10 o lambda = 0 se ve que no alcanza
MAX_ITER = 3000

# tol chica para que corra hasta el final y despues mirar distintos tol con la lista de cambios
TOL_CORRIDA = 1e-7
LISTA_TOL = [1e-3, 1e-4, 1e-5, 1e-6, 1e-7]

ZOOM_FILAS = (30, 110)
ZOOM_COLS = (100, 200)


def correr(
    y,
    H,
    lam,
    tau,
    x,
):

    inicio = time.time()

    x_est, lista_costo, lista_rmse, lista_cambio, n_iter = tikhonov_gd(
        y,
        H,
        lam,
        tau,
        MAX_ITER,
        TOL_CORRIDA,
        x,
    )

    tiempo = time.time() - inicio

    corrida = {
        "lam": lam,
        "tau": tau,
        "x_est": x_est,
        "costo": np.array(lista_costo),
        "rmse": np.array(lista_rmse),
        "cambio": np.array(lista_cambio),
        "n_iter": n_iter,
        "tiempo": tiempo,
    }

    return corrida


def linea_resumen(corrida):

    rmse = corrida["rmse"]
    i_min = np.argmin(rmse)

    if corrida["cambio"][-1] < TOL_CORRIDA:
        motivo = "tol"
    else:
        motivo = "max_iter"

    linea = (
        f"{corrida['lam']:<10.2e} {corrida['tau']:<6} {corrida['n_iter']:<6} {motivo:<9} "
        f"{corrida['costo'][-1]:<12.4g} {rmse[-1]:<11.4g} {rmse[i_min]:<9.4f} {i_min:<8} {corrida['tiempo']:.1f} s"
    )

    return linea


def tabla_tol(corrida):

    lineas = []

    for tol in LISTA_TOL:

        # primera iteracion donde el cambio queda bajo tol (cambio[k] es de la iteracion k + 1)
        bajo_tol = np.where(corrida["cambio"] < tol)[0]

        if len(bajo_tol) == 0:
            lineas.append(f"    tol = {tol:<8g} no se cumple en {MAX_ITER} iteraciones")
            continue

        k_parada = bajo_tol[0] + 1

        lineas.append(f"    tol = {tol:<8g} para en la iteracion {k_parada:<6} RMSE = {corrida['rmse'][k_parada]:.4f}")

    return lineas


def graficar_curvas(
    corridas,
    nombre_variable,
    titulo,
    nombre_archivo,
    carpeta_salida,
):

    figura, axes = plt.subplots(
        1,
        2,
        figsize=(16, 5.5),
    )

    for j in range(len(corridas)):

        corrida = corridas[j]
        valor = corrida[nombre_variable]

        if nombre_variable == "lam":
            etiqueta = f"lambda = {valor:.2e}"
        else:
            etiqueta = f"tau = {valor}"

        axes[0].semilogy(corrida["costo"], color=f"C{j}", label=etiqueta)
        axes[1].plot(corrida["rmse"], color=f"C{j}", label=etiqueta)

    axes[0].set_title("Costo J(x_k)")
    axes[1].set_title("RMSE(x_k, x)")

    # si una corrida diverge el RMSE se va muy arriba, se corta el eje
    axes[1].set_ylim(0.06, 0.09)

    for axis in axes:
        axis.set_xlabel("iteracion")
        axis.grid(alpha=0.3, which="both")
        axis.legend()

    figura.suptitle(titulo)

    figura.tight_layout()

    ruta_salida = carpeta_salida / nombre_archivo

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_imagenes(
    x,
    y,
    corridas,
    carpeta_salida,
):

    f0, f1 = ZOOM_FILAS
    c0, c1 = ZOOM_COLS

    imagenes = [x, y]
    titulos = ["x (ideal)", f"degradada y\nRMSE = {calcular_rmse(y, x):.4f}"]

    for corrida in corridas:
        imagenes.append(corrida["x_est"])
        titulos.append(
            f"lambda = {corrida['lam']:.2e}, {corrida['n_iter']} it.\nRMSE = {corrida['rmse'][-1]:.4f}"
        )

    n = len(imagenes)

    figura, axes = plt.subplots(
        2,
        n,
        figsize=(3.6 * n, 7),
    )

    for j in range(n):

        axes[0, j].imshow(imagenes[j], cmap="gray", vmin=0, vmax=1)
        axes[0, j].set_title(titulos[j], fontsize=9)

        axes[1, j].imshow(
            imagenes[j][f0:f1, c0:c1],
            cmap="gray",
            vmin=0,
            vmax=1,
            interpolation="nearest",
        )
        axes[1, j].set_title(f"zoom filas {f0}-{f1}, col {c0}-{c1}", fontsize=8)

    for axis in axes.flatten():
        axis.set_xticks([])
        axis.set_yticks([])

    figura.suptitle(f"Tikhonov iterativo, ultima iteracion (tau = {TAU_FIJO}, sigma = {SIGMA}), escala [0, 1]")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "imagenes_lambda.png"

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

    # 1. barrido de tau con lambda = K_opt
    corridas_tau = []

    for tau in LISTA_TAUS:

        print(f"lambda = {LAMBDA_FIJO}, tau = {tau}")

        corridas_tau.append(correr(y, H, LAMBDA_FIJO, tau, x))

    # 2. barrido de lambda con tau = 1 (la de K_opt ya esta hecha)
    corridas_lam = []

    for lam in LISTA_LAMBDAS:

        if lam == LAMBDA_FIJO:
            for corrida in corridas_tau:
                if corrida["tau"] == TAU_FIJO:
                    corridas_lam.append(corrida)
            continue

        print(f"lambda = {lam}, tau = {TAU_FIJO}")

        corridas_lam.append(correr(y, H, lam, TAU_FIJO, x))

    # 3. resumen
    encabezado = "lambda     tau    iter   para por  costo final  RMSE final  RMSE min  en iter  tiempo"

    lineas = []
    lineas.append(f"sigma = {SIGMA}, RMSE degradada y = {calcular_rmse(y, x):.4f}, max_iter = {MAX_ITER}, tol corrida = {TOL_CORRIDA}")
    lineas.append("")
    lineas.append(f"Barrido de tau (lambda = {LAMBDA_FIJO}):")
    lineas.append(encabezado)
    for corrida in corridas_tau:
        lineas.append(linea_resumen(corrida))
        lineas.append(f"    limite 2 / (1 + lambda) = {2 / (1 + corrida['lam']):.4f}")

    lineas.append("")
    lineas.append(f"Barrido de lambda (tau = {TAU_FIJO}):")
    lineas.append(encabezado)
    for corrida in corridas_lam:
        lineas.append(linea_resumen(corrida))

    lineas.append("")
    lineas.append(f"Efecto del criterio de detencion (tau = {TAU_FIJO}):")
    for corrida in corridas_lam:
        lineas.append(f"  lambda = {corrida['lam']:.2e}:")
        lineas = lineas + tabla_tol(corrida)

    print("")
    for linea in lineas:
        print(linea)
    print("")

    ruta_txt = CARPETA_SALIDA / "tikhonov_barrido.txt"

    with open(ruta_txt, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_txt}")

    graficar_curvas(
        corridas_tau,
        "tau",
        f"Barrido de tau, lambda = {LAMBDA_FIJO}, sigma = {SIGMA}",
        "curvas_tau.png",
        CARPETA_SALIDA,
    )

    graficar_curvas(
        corridas_lam,
        "lam",
        f"Barrido de lambda, tau = {TAU_FIJO}, sigma = {SIGMA}",
        "curvas_lambda.png",
        CARPETA_SALIDA,
    )

    graficar_imagenes(
        x,
        y,
        corridas_lam,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
