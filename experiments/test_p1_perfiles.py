from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta1 import calcular_espectro


RUTA_IMAGEN = Path("images/profesor/p1/P1.CR2")

CARPETA_SALIDA = Path("results/pregunta1/perfiles")

# ancho de cada anillo para el perfil radial (ciclos/pixel)
ANCHO_ANILLO = 0.01

# anillos mas gruesos solo para imprimir una tabla corta
# (las esquinas del espectro llegan a D = 0.707)
LIMITES_TABLA = [0, 0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3, 0.45, 0.55, 0.71]


def graficar_perfiles_ejes(
    magnitud_rel,
    frec_u,
    frec_v,
    carpeta_salida,
):

    alto = magnitud_rel.shape[0]
    ancho = magnitud_rel.shape[1]

    # con fftshift la frecuencia cero queda en (alto // 2, ancho // 2)
    fila_centro = alto // 2
    col_centro = ancho // 2

    perfil_v0 = magnitud_rel[fila_centro, :]
    perfil_u0 = magnitud_rel[:, col_centro]

    figura, axes = plt.subplots(
        2,
        1,
        figsize=(11, 8),
    )

    axes[0].semilogy(
        frec_u,
        perfil_v0,
        linewidth=0.6,
    )
    axes[0].set_title("Fila v = 0 del espectro")
    axes[0].set_xlabel("u [ciclos/pixel]")
    axes[0].set_ylabel("|F| / mediana")
    axes[0].grid(alpha=0.3)

    axes[1].semilogy(
        frec_v,
        perfil_u0,
        linewidth=0.6,
    )
    axes[1].set_title("Columna u = 0 del espectro")
    axes[1].set_xlabel("v [ciclos/pixel]")
    axes[1].set_ylabel("|F| / mediana")
    axes[1].grid(alpha=0.3)

    figura.tight_layout()

    ruta_salida = carpeta_salida / "perfil_v0_u0.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_perfil_radial(
    magnitud_rel,
    distancia,
    carpeta_salida,
):

    distancia_max = np.max(distancia)
    n_anillos = int(np.ceil(distancia_max / ANCHO_ANILLO))

    radios = []
    medias = []
    maximos = []

    for i in range(n_anillos):

        r_inicio = i * ANCHO_ANILLO
        r_fin = (i + 1) * ANCHO_ANILLO

        en_anillo = (distancia >= r_inicio) & (distancia < r_fin)

        valores = magnitud_rel[en_anillo]

        radios.append((r_inicio + r_fin) / 2)
        medias.append(np.mean(valores))
        maximos.append(np.max(valores))

    figura, axis = plt.subplots(
        1,
        1,
        figsize=(10, 5),
    )

    axis.semilogy(
        radios,
        medias,
        "o-",
        markersize=3,
        label="media del anillo",
    )

    axis.semilogy(
        radios,
        maximos,
        "s-",
        markersize=3,
        label="maximo del anillo",
    )

    axis.set_title(f"Perfil radial de |F| (anillos de {ANCHO_ANILLO} ciclos/pixel)")
    axis.set_xlabel("distancia al centro D [ciclos/pixel]")
    axis.set_ylabel("|F| / mediana")
    axis.grid(alpha=0.3)
    axis.legend()

    figura.tight_layout()

    ruta_salida = carpeta_salida / "perfil_radial.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def imprimir_tabla_anillos(
    magnitud_rel,
    distancia,
):

    print("")
    print("Anillo [ciclos/pixel]   media    maximo")

    for i in range(len(LIMITES_TABLA) - 1):

        r_inicio = LIMITES_TABLA[i]
        r_fin = LIMITES_TABLA[i + 1]

        en_anillo = (distancia >= r_inicio) & (distancia < r_fin)

        valores = magnitud_rel[en_anillo]

        media = np.mean(valores)
        maximo = np.max(valores)

        print(f"[{r_inicio:.2f}, {r_fin:.2f})          {media:7.2f}  {maximo:8.1f}")

    print("")


def main():

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    imagen = cargar_imagen(RUTA_IMAGEN)

    alto = imagen.shape[0]
    ancho = imagen.shape[1]

    print(f"Imagen: {RUTA_IMAGEN}, tamano {imagen.shape}")

    F = calcular_espectro(imagen)
    magnitud = np.abs(F)

    # divido por la mediana para que el fondo del espectro quede cerca de 1
    mediana = np.median(magnitud)
    magnitud_rel = magnitud / mediana

    frec_u = np.fft.fftshift(np.fft.fftfreq(ancho))
    frec_v = np.fft.fftshift(np.fft.fftfreq(alto))

    U, V = np.meshgrid(
        frec_u,
        frec_v,
    )

    distancia = np.sqrt(U**2 + V**2)

    graficar_perfiles_ejes(
        magnitud_rel,
        frec_u,
        frec_v,
        CARPETA_SALIDA,
    )

    graficar_perfil_radial(
        magnitud_rel,
        distancia,
        CARPETA_SALIDA,
    )

    imprimir_tabla_anillos(
        magnitud_rel,
        distancia,
    )


if __name__ == "__main__":
    main()
