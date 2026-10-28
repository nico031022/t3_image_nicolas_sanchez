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

CARPETA_SALIDA = Path("results/pregunta2/wiener")

# niveles elegidos en test_p2_degradacion
LISTA_SIGMAS = [0.01, 0.05]

SEMILLA = 0

# mismo rango que el panel de Wiener de la capsula
LISTA_K = np.logspace(-7, 1, 61)

# para mostrar poca y mucha regularizacion: dos ordenes de magnitud a cada lado
FACTOR_K = 100

# mismo zoom que en test_p2_degradacion
ZOOM_FILAS = (30, 110)
ZOOM_COLS = (100, 200)

ANCHO_ANILLO = 0.01


def perfil_radial(
    potencia,
):

    # copiada de test_p2_degradacion
    frec_u = np.fft.fftfreq(potencia.shape[1])
    frec_v = np.fft.fftfreq(potencia.shape[0])

    U, V = np.meshgrid(
        frec_u,
        frec_v,
    )

    distancia = np.sqrt(U**2 + V**2)

    n_anillos = int(np.ceil(np.max(distancia) / ANCHO_ANILLO))

    radios = []
    medias = []

    for i in range(n_anillos):

        r_inicio = i * ANCHO_ANILLO
        r_fin = (i + 1) * ANCHO_ANILLO

        en_anillo = (distancia >= r_inicio) & (distancia < r_fin)

        if np.sum(en_anillo) == 0:
            continue

        radios.append((r_inicio + r_fin) / 2)
        medias.append(np.mean(potencia[en_anillo]))

    return np.array(radios), np.array(medias)


def graficar_curvas(
    resultados,
    carpeta_salida,
):

    figura, axis = plt.subplots(
        1,
        1,
        figsize=(10, 6),
    )

    for k in range(len(LISTA_SIGMAS)):

        datos = resultados[k]

        axis.semilogx(
            LISTA_K,
            datos["rmse"],
            "o-",
            markersize=3,
            color=f"C{k}",
            label=f"Wiener, sigma = {LISTA_SIGMAS[k]}",
        )

        axis.plot(
            datos["K_opt"],
            datos["rmse_opt"],
            "*",
            markersize=15,
            color=f"C{k}",
            markeredgecolor="k",
        )

        axis.axhline(
            datos["rmse_y"],
            color=f"C{k}",
            linestyle="--",
            linewidth=1,
            label=f"degradada y, sigma = {LISTA_SIGMAS[k]}",
        )

    axis.set_ylim(0, 0.2)
    axis.set_title("RMSE vs K (estrella: optimo)")
    axis.set_xlabel("K")
    axis.set_ylabel("RMSE(x estimada, x)")
    axis.grid(alpha=0.3, which="both")
    axis.legend(fontsize=9)

    figura.tight_layout()

    ruta_salida = carpeta_salida / "rmse_vs_K.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_reconstrucciones(
    datos,
    sigma,
    x,
    H,
    carpeta_salida,
):

    y = datos["y"]
    K_opt = datos["K_opt"]

    lista_K = [K_opt / FACTOR_K, K_opt, K_opt * FACTOR_K]
    nombres = ["K_opt / 100", "K_opt", "K_opt x 100"]

    imagenes = [x, y]
    titulos = ["x (ideal)", f"degradada y\nRMSE = {calcular_rmse(y, x):.4f}"]

    for j in range(len(lista_K)):

        x_est = wiener(
            y,
            H,
            lista_K[j],
        )

        imagenes.append(x_est)
        titulos.append(f"{nombres[j]} = {lista_K[j]:.2e}\nRMSE = {calcular_rmse(x_est, x):.4f}")

    f0, f1 = ZOOM_FILAS
    c0, c1 = ZOOM_COLS

    n = len(imagenes)

    figura, axes = plt.subplots(
        2,
        n,
        figsize=(4 * n, 7.5),
    )

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

    for axis in axes.flatten():
        axis.set_xticks([])
        axis.set_yticks([])

    figura.suptitle(f"Wiener, sigma = {sigma}, escala [0, 1]")

    figura.tight_layout()

    ruta_salida = carpeta_salida / f"reconstrucciones_sigma_{sigma}.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_respuesta(
    resultados,
    H,
    carpeta_salida,
):

    figura, axis = plt.subplots(
        1,
        1,
        figsize=(10, 5.5),
    )

    radios, medias_H = perfil_radial(np.abs(H))
    axis.plot(radios, medias_H, "k", label="|H| (degradacion)")

    for k in range(len(LISTA_SIGMAS)):

        K_opt = resultados[k]["K_opt"]

        # |W H| = |H|^2 / (|H|^2 + K): 1 = se recupera, 0 = se apaga
        respuesta = np.abs(H)**2 / (np.abs(H)**2 + K_opt)

        radios, medias = perfil_radial(respuesta)

        axis.plot(
            radios,
            medias,
            color=f"C{k}",
            linewidth=2,
            label=f"|W H|, sigma = {LISTA_SIGMAS[k]}, K_opt = {K_opt:.2e}",
        )

    axis.set_title("Respuesta efectiva |W H| = |H|^2 / (|H|^2 + K) (promedio por anillo)")
    axis.set_xlabel("distancia al centro [ciclos/pixel]")
    axis.set_ylabel("ganancia")
    axis.set_ylim(-0.02, 1.05)
    axis.grid(alpha=0.3)
    axis.legend()

    figura.tight_layout()

    ruta_salida = carpeta_salida / "respuesta_efectiva.png"

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
    lineas.append(f"K: {len(LISTA_K)} valores entre {LISTA_K[0]:.0e} y {LISTA_K[-1]:.0e} (logspace)")
    lineas.append("")

    resultados = []

    for sigma in LISTA_SIGMAS:

        y = degradar(
            x,
            H,
            sigma,
            SEMILLA,
        )

        lista_rmse = []

        for K in LISTA_K:

            x_est = wiener(
                y,
                H,
                K,
            )

            lista_rmse.append(calcular_rmse(x_est, x))

        lista_rmse = np.array(lista_rmse)

        i_opt = np.argmin(lista_rmse)

        # SNR de la clase 16 (igual que en test_p2_degradacion)
        ruido = y - y_borrosa
        snr = np.sum(np.abs(np.fft.fft2(x))**2) / np.sum(np.abs(np.fft.fft2(ruido))**2)

        datos = {
            "y": y,
            "rmse": lista_rmse,
            "K_opt": LISTA_K[i_opt],
            "rmse_opt": lista_rmse[i_opt],
            "rmse_y": calcular_rmse(y, x),
            "snr": snr,
        }

        resultados.append(datos)

        lineas.append(f"sigma = {sigma}:")
        lineas.append(f"  RMSE degradada y = {datos['rmse_y']:.4f}")
        lineas.append(f"  K_opt = {datos['K_opt']:.3e}, RMSE = {datos['rmse_opt']:.4f}")
        x_poco = wiener(y, H, datos["K_opt"] / FACTOR_K)
        x_mucho = wiener(y, H, datos["K_opt"] * FACTOR_K)
        lineas.append(f"  RMSE con K_opt / 100 = {calcular_rmse(x_poco, x):.4f}, con K_opt x 100 = {calcular_rmse(x_mucho, x):.4f}")
        lineas.append(f"  1 / SNR = {1 / snr:.3e}")

    lineas.append("")
    lineas.append(f"K_opt(0.05) / K_opt(0.01) = {resultados[1]['K_opt'] / resultados[0]['K_opt']:.1f}")
    lineas.append(f"(sigma 0.05 / sigma 0.01)^2 = {(LISTA_SIGMAS[1] / LISTA_SIGMAS[0])**2:.1f}")

    print("")
    for linea in lineas:
        print(linea)
    print("")

    ruta_txt = CARPETA_SALIDA / "wiener_barrido.txt"

    with open(ruta_txt, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_txt}")

    graficar_curvas(
        resultados,
        CARPETA_SALIDA,
    )

    for k in range(len(LISTA_SIGMAS)):

        graficar_reconstrucciones(
            resultados[k],
            LISTA_SIGMAS[k],
            x,
            H,
            CARPETA_SALIDA,
        )

    graficar_respuesta(
        resultados,
        H,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
