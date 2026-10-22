from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta1 import calcular_espectro
from src.pregunta1 import espectro_log


RUTA_IMAGEN = Path("images/profesor/p1/P1.CR2")

CARPETA_SALIDA = Path("results/pregunta1/espectro")


def mostrar_espectro(
    imagen,
    carpeta_salida,
):

    alto = imagen.shape[0]
    ancho = imagen.shape[1]

    F = calcular_espectro(imagen)
    espectro = espectro_log(F)

    # ejes del espectro en ciclos por pixel
    frec_u = np.fft.fftshift(np.fft.fftfreq(ancho))
    frec_v = np.fft.fftshift(np.fft.fftfreq(alto))

    extension = [
        frec_u[0],
        frec_u[-1],
        frec_v[-1],
        frec_v[0],
    ]

    # la imagen es muy oscura (cielo de noche), por eso
    # para mostrarla hay que usar como maximo el percentil 99
    max_mostrar = np.percentile(imagen, 99)

    figura, axes = plt.subplots(
        1,
        2,
        figsize=(13, 6),
    )

    axes[0].imshow(
        imagen,
        cmap="gray",
        vmin=0,
        vmax=max_mostrar,
    )
    axes[0].set_title(f"Imagen ruidosa ({alto}x{ancho}), vmax = p99")
    axes[0].axis("off")

    axes[1].imshow(
        espectro,
        cmap="gray",
        extent=extension,
    )
    axes[1].set_title("log(1 + |F(u, v)|)")
    axes[1].set_xlabel("u [ciclos/pixel]")
    axes[1].set_ylabel("v [ciclos/pixel]")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "espectro_imagen_ruidosa.png"

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

    mostrar_espectro(
        imagen,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
