from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta2 import cargar_psf
from src.pregunta2 import psf_a_otf
from src.pregunta2 import aplicar_H
from src.pregunta2 import degradar
from src.pregunta2 import calcular_rmse


RUTA_IMAGEN = Path("images/profesor/p2/cameraman.jpg")
RUTA_PSF = Path("images/profesor/p2/psf.png")

CARPETA_SALIDA = Path("results/pregunta2/degradacion")

# 0.002, 0.01 y 0.05 son los niveles de la capsula (poco, moderado y mucho ruido)
# 0.005 y 0.02 para que entre dos seguidos haya un factor de ~2.5
LISTA_SIGMAS = [0.002, 0.005, 0.01, 0.02, 0.05]

# misma semilla en toda la P2 (la capsula usa 0)
SEMILLA = 0

# zoom en la cara y la camara (filas, columnas)
ZOOM_FILAS = (30, 110)
ZOOM_COLS = (100, 200)

# ancho de cada anillo para el perfil radial (ciclos/pixel)
ANCHO_ANILLO = 0.01


def calcular_snr(
    x,
    ruido,
):

    # SNR de la clase 16: suma |F|^2 / suma |N|^2
    F = np.fft.fft2(x)
    N = np.fft.fft2(ruido)

    snr = np.sum(np.abs(F)**2) / np.sum(np.abs(N)**2)

    return snr


def perfil_radial(
    potencia,
):

    # distancia de cada frecuencia al centro, sin fftshift (orden de la fft)
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


def frecuencia_de_cruce(
    radios,
    medias_senal,
    nivel_ruido,
):

    # primer anillo donde la senal borrosa queda bajo el ruido
    for i in range(len(radios)):
        if medias_senal[i] < nivel_ruido:
            return radios[i]

    return None


def graficar_degradadas(
    x,
    lista_y,
    lista_rmse,
    carpeta_salida,
):

    n_columnas = len(LISTA_SIGMAS) + 1

    figura, axes = plt.subplots(
        2,
        n_columnas,
        figsize=(4 * n_columnas, 7.5),
    )

    f0, f1 = ZOOM_FILAS
    c0, c1 = ZOOM_COLS

    imagenes = [x] + lista_y
    titulos = ["x (ideal)"]
    for k in range(len(LISTA_SIGMAS)):
        titulos.append(f"y, sigma = {LISTA_SIGMAS[k]}\nRMSE = {lista_rmse[k]:.4f}")

    for j in range(n_columnas):

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

    figura.suptitle(f"Imagen degradada y = h * x + ruido (semilla {SEMILLA}), escala [0, 1]")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "degradadas.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_espectros(
    radios,
    medias_x,
    medias_hx,
    niveles_ruido,
    carpeta_salida,
):

    figura, axis = plt.subplots(
        1,
        1,
        figsize=(10, 6),
    )

    axis.semilogy(radios, medias_x, "k--", label="|X|^2 (imagen ideal)")
    axis.semilogy(radios, medias_hx, "k", linewidth=2, label="|H X|^2 (imagen borrosa)")

    for k in range(len(LISTA_SIGMAS)):
        axis.axhline(
            niveles_ruido[k],
            color=f"C{k}",
            linestyle=":",
            label=f"ruido, sigma = {LISTA_SIGMAS[k]}",
        )

    axis.set_title("Potencia por anillo de frecuencia (promedio) vs nivel del ruido")
    axis.set_xlabel("distancia al centro [ciclos/pixel]")
    axis.set_ylabel("potencia")
    axis.grid(alpha=0.3, which="both")
    axis.legend(fontsize=8)

    figura.tight_layout()

    ruta_salida = carpeta_salida / "senal_vs_ruido.png"

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

    H = psf_a_otf(
        psf,
        alto,
        ancho,
    )

    y_borrosa = aplicar_H(x, H)

    # potencia de la senal antes y despues de la psf
    X = np.fft.fft2(x)
    radios, medias_x = perfil_radial(np.abs(X)**2)
    radios, medias_hx = perfil_radial(np.abs(H * X)**2)

    lineas = []
    lineas.append(f"Sin ruido: RMSE(h * x, x) = {calcular_rmse(y_borrosa, x):.4f}")
    lineas.append("")
    lineas.append("sigma    RMSE(y, x)   SNR        SNR [dB]   std ruido   cruce [ciclos/pixel]   y fuera de [0, 1]")

    lista_y = []
    lista_rmse = []
    niveles_ruido = []

    for sigma in LISTA_SIGMAS:

        y = degradar(
            x,
            H,
            sigma,
            SEMILLA,
        )

        ruido = y - y_borrosa

        rmse = calcular_rmse(y, x)
        snr = calcular_snr(x, ruido)

        # ruido blanco: en cada frecuencia |N|^2 vale en promedio sigma^2 * M * N
        nivel_ruido = sigma**2 * alto * ancho

        cruce = frecuencia_de_cruce(
            radios,
            medias_hx,
            nivel_ruido,
        )

        fuera = 100 * np.mean((y < 0) | (y > 1))

        lineas.append(
            f"{sigma:<8} {rmse:.4f}       {snr:9.1f}  {10 * np.log10(snr):6.1f}     "
            f"{np.std(ruido):.4f}      {cruce:.3f}                  {fuera:.2f} %"
        )

        lista_y.append(y)
        lista_rmse.append(rmse)
        niveles_ruido.append(nivel_ruido)

    print("")
    for linea in lineas:
        print(linea)
    print("")

    ruta_txt = CARPETA_SALIDA / "niveles_ruido.txt"

    with open(ruta_txt, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_txt}")

    graficar_degradadas(
        x,
        lista_y,
        lista_rmse,
        CARPETA_SALIDA,
    )

    graficar_espectros(
        radios,
        medias_x,
        medias_hx,
        niveles_ruido,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
