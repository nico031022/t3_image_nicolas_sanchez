from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta2 import cargar_psf
from src.pregunta2 import psf_a_otf
from src.pregunta2 import aplicar_H


RUTA_IMAGEN = Path("images/profesor/p2/cameraman.jpg")
RUTA_PSF = Path("images/profesor/p2/psf.png")

CARPETA_SALIDA = Path("results/pregunta2/otf")


def revisar_psf(
    psf_original,
    psf,
    lineas,
):

    alto_psf = psf.shape[0]
    ancho_psf = psf.shape[1]

    lineas.append(f"PSF: tamano {psf.shape}")
    lineas.append(f"  suma antes de normalizar: {np.sum(psf_original):.4f}")
    lineas.append(f"  suma despues de normalizar: {np.sum(psf):.6f}")

    fila_max, col_max = np.unravel_index(np.argmax(psf), psf.shape)
    lineas.append(f"  maximo: {np.max(psf):.5f} en (fila, col) = ({fila_max}, {col_max})")

    # centro de masa de la psf
    filas, cols = np.meshgrid(
        np.arange(alto_psf),
        np.arange(ancho_psf),
        indexing="ij",
    )
    centro_fila = np.sum(psf * filas)
    centro_col = np.sum(psf * cols)
    lineas.append(f"  centro de masa: ({centro_fila:.3f}, {centro_col:.3f})")
    lineas.append(f"  centro usado en psf_a_otf: ({alto_psf // 2}, {ancho_psf // 2})")

    # si la psf fuera simetrica seria igual a ella misma girada en 180 grados
    psf_girada = psf[::-1, ::-1]
    dif_simetria = np.max(np.abs(psf - psf_girada))
    lineas.append(f"  max |h - h girada 180|: {dif_simetria:.2e} ({100 * dif_simetria / np.max(psf):.2f} % del maximo)")


def revisar_H(
    H,
    lineas,
):

    modulo = np.abs(H)

    lineas.append("H = fft2 de la psf centrada en (0, 0):")
    lineas.append(f"  H(0, 0) = {H[0, 0]:.6f}")
    lineas.append(f"  max |H| = {np.max(modulo):.6f}, min |H| = {np.min(modulo):.2e}")
    lineas.append(f"  min |H|^2 = {np.min(modulo**2):.2e}")
    lineas.append(f"  max |parte imaginaria de H| = {np.max(np.abs(np.imag(H))):.2e}")

    for umbral in [0.1, 0.01, 0.001]:
        porcentaje = 100 * np.mean(modulo < umbral)
        lineas.append(f"  frecuencias con |H| < {umbral}: {porcentaje:.2f} %")


def convolucion_a_mano(
    x,
    psf,
):

    alto_psf = psf.shape[0]
    ancho_psf = psf.shape[1]

    centro_fila = alto_psf // 2
    centro_col = ancho_psf // 2

    resultado = np.zeros(x.shape)

    # suma de copias desplazadas de x, cada una por su peso de la psf
    # np.roll da la vuelta en los bordes, o sea convolucion circular
    for i in range(alto_psf):
        for j in range(ancho_psf):

            desplazamiento = (i - centro_fila, j - centro_col)

            x_movida = np.roll(
                x,
                desplazamiento,
                axis=(0, 1),
            )

            resultado = resultado + psf[i, j] * x_movida

    return resultado


def otf_sin_centrar(
    psf,
    alto,
    ancho,
):

    # igual que psf_a_otf pero sin el np.roll (error a proposito)
    alto_psf = psf.shape[0]
    ancho_psf = psf.shape[1]

    psf_grande = np.zeros((alto, ancho))
    psf_grande[0:alto_psf, 0:ancho_psf] = psf

    H = np.fft.fft2(psf_grande)

    return H


def graficar_datos(
    x,
    psf,
    H,
    carpeta_salida,
):

    figura, axes = plt.subplots(
        1,
        3,
        figsize=(16, 5),
    )

    axes[0].imshow(
        x,
        cmap="gray",
        vmin=0,
        vmax=1,
    )
    axes[0].set_title(f"Imagen ideal x, {x.shape[0]} x {x.shape[1]}")

    im_psf = axes[1].imshow(
        psf,
        cmap="inferno",
        interpolation="nearest",
    )
    axes[1].set_title(f"PSF h, {psf.shape[0]} x {psf.shape[1]}, suma = 1")
    figura.colorbar(im_psf, ax=axes[1], fraction=0.046)

    # fftshift solo para mostrar la frecuencia cero al centro
    frec_u = np.fft.fftshift(np.fft.fftfreq(H.shape[1]))
    frec_v = np.fft.fftshift(np.fft.fftfreq(H.shape[0]))

    extension = [
        frec_u[0],
        frec_u[-1],
        frec_v[-1],
        frec_v[0],
    ]

    im_H = axes[2].imshow(
        np.log10(np.abs(np.fft.fftshift(H))),
        cmap="viridis",
        extent=extension,
    )
    axes[2].set_title("log10 |H(u, v)| (centrada)")
    axes[2].set_xlabel("u [ciclos/pixel]")
    axes[2].set_ylabel("v [ciclos/pixel]")
    figura.colorbar(im_H, ax=axes[2], fraction=0.046)

    figura.tight_layout()

    ruta_salida = carpeta_salida / "imagen_psf_otf.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_perfiles_H(
    H,
    carpeta_salida,
):

    frec_u = np.fft.fftshift(np.fft.fftfreq(H.shape[1]))
    frec_v = np.fft.fftshift(np.fft.fftfreq(H.shape[0]))

    H_centrada = np.fft.fftshift(np.abs(H))

    fila_cero = H.shape[0] // 2
    col_cero = H.shape[1] // 2

    perfil_u = H_centrada[fila_cero, :]
    perfil_v = H_centrada[:, col_cero]

    figura, axes = plt.subplots(
        1,
        2,
        figsize=(14, 4.5),
    )

    axes[0].plot(frec_u, perfil_u, label="|H(u, 0)|")
    axes[0].plot(frec_v, perfil_v, "--", label="|H(0, v)|")
    axes[0].set_title("Cortes de |H| por los ejes")
    axes[0].set_ylabel("|H|")

    axes[1].semilogy(frec_u, 1 / perfil_u, label="1 / |H(u, 0)|")
    axes[1].semilogy(frec_v, 1 / perfil_v, "--", label="1 / |H(0, v)|")
    axes[1].set_title("Cuanto se amplificaria el ruido con Y / H")
    axes[1].set_ylabel("1 / |H|")

    for axis in axes:
        axis.set_xlabel("frecuencia [ciclos/pixel]")
        axis.grid(alpha=0.3, which="both")
        axis.legend()

    figura.tight_layout()

    ruta_salida = carpeta_salida / "perfiles_H.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_centrado(
    x,
    y_bien,
    y_mal,
    carpeta_salida,
):

    figura, axes = plt.subplots(
        1,
        4,
        figsize=(20, 5),
    )

    axes[0].imshow(x, cmap="gray", vmin=0, vmax=1)
    axes[0].set_title("x")

    axes[1].imshow(y_bien, cmap="gray", vmin=0, vmax=1)
    axes[1].set_title("h * x con la psf centrada en (0, 0)")

    axes[2].imshow(y_mal, cmap="gray", vmin=0, vmax=1)
    axes[2].set_title("h * x sin np.roll (psf en la esquina)")

    diferencia = y_mal - y_bien
    limite = np.max(np.abs(diferencia))

    im_dif = axes[3].imshow(
        diferencia,
        cmap="seismic",
        vmin=-limite,
        vmax=limite,
    )
    axes[3].set_title("diferencia (sin roll - con roll)")
    figura.colorbar(im_dif, ax=axes[3], fraction=0.046)

    figura.tight_layout()

    ruta_salida = carpeta_salida / "centrado_psf.png"

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

    alto = x.shape[0]
    ancho = x.shape[1]

    psf_original = cargar_imagen(RUTA_PSF)
    psf = cargar_psf(RUTA_PSF)

    lineas = []

    lineas.append(f"Imagen: {RUTA_IMAGEN}, tamano {x.shape}, min {np.min(x):.3f}, max {np.max(x):.3f}")

    revisar_psf(
        psf_original,
        psf,
        lineas,
    )

    # 1. H a partir de la psf
    H = psf_a_otf(
        psf,
        alto,
        ancho,
    )

    revisar_H(
        H,
        lineas,
    )

    # 2. revisar que multiplicar por H es la convolucion circular
    y_fft = aplicar_H(x, H)
    y_mano = convolucion_a_mano(x, psf)

    lineas.append("Convolucion con fft vs a mano (np.roll):")
    lineas.append(f"  max |diferencia| = {np.max(np.abs(y_fft - y_mano)):.2e}")
    lineas.append(f"  promedio x = {np.mean(x):.6f}, promedio h * x = {np.mean(y_fft):.6f}")

    # 3. que pasa si no se centra la psf
    H_mal = otf_sin_centrar(
        psf,
        alto,
        ancho,
    )

    y_mal = aplicar_H(x, H_mal)

    # si solo es un desplazamiento, deberia ser y_fft movida 7 pixeles
    y_bien_movida = np.roll(
        y_fft,
        (psf.shape[0] // 2, psf.shape[1] // 2),
        axis=(0, 1),
    )

    lineas.append("PSF sin centrar (sin np.roll):")
    lineas.append(f"  max |sin roll - con roll| = {np.max(np.abs(y_mal - y_fft)):.4f}")
    lineas.append(f"  max |sin roll - (con roll movida 7 px)| = {np.max(np.abs(y_mal - y_bien_movida)):.2e}")

    print("")
    for linea in lineas:
        print(linea)
    print("")

    ruta_txt = CARPETA_SALIDA / "resumen_otf.txt"

    with open(ruta_txt, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_txt}")

    graficar_datos(
        x,
        psf,
        H,
        CARPETA_SALIDA,
    )

    graficar_perfiles_H(
        H,
        CARPETA_SALIDA,
    )

    graficar_centrado(
        x,
        y_fft,
        y_mal,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
