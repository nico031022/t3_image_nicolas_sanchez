from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta1 import calcular_espectro
from src.pregunta1 import espectro_log


RUTA_IMAGEN = Path("images/profesor/p1/P1.CR2")

CARPETA_SALIDA = Path("results/pregunta1/picos")

# elegido mirando perfil_radial.png (test_p1_perfiles)
RADIO_EXCLUIR = 0.05

# por los perfiles se esperan 5 picos: 3 del mosaico de Bayer y el par de +-0.25
N_ESPERADOS = 5

# busco el doble para ver donde se corta
N_PICOS = 2 * N_ESPERADOS

# pixeles que se borran alrededor de cada pico encontrado
VENTANA_SUPRESION = 3

# mitad del tamano de cada zoom (en pixeles del espectro)
MEDIO_ZOOM = 15

# otros radios para revisar que los picos no cambian
RADIOS_PRUEBA = [0.02, 0.05, 0.1, 0.2]


def buscar_picos(
    magnitud_rel,
    distancia,
    frec_u,
    frec_v,
    radio_excluir,
    n_picos,
):

    alto = magnitud_rel.shape[0]
    ancho = magnitud_rel.shape[1]

    copia = magnitud_rel.copy()

    # no buscar cerca del centro (ahi esta el contenido de la imagen)
    copia[distancia < radio_excluir] = 0

    lista_picos = []

    for k in range(n_picos):

        indice = np.argmax(copia)
        fila, col = np.unravel_index(indice, copia.shape)

        pico = {
            "fila": fila,
            "col": col,
            "u": frec_u[col],
            "v": frec_v[fila],
            "valor": magnitud_rel[fila, col],
        }

        lista_picos.append(pico)

        # borrar alrededor del pico para no encontrarlo otra vez
        # el espectro es periodico, con % se pasa al otro lado del borde
        for df in range(-VENTANA_SUPRESION, VENTANA_SUPRESION + 1):
            for dc in range(-VENTANA_SUPRESION, VENTANA_SUPRESION + 1):

                f = (fila + df) % alto
                c = (col + dc) % ancho

                copia[f, c] = 0

    return lista_picos


def guardar_tabla_picos(
    lista_picos,
    carpeta_salida,
):

    lineas = []
    lineas.append(f"Radio excluido: {RADIO_EXCLUIR}, N_PICOS = {N_PICOS}")
    lineas.append(" k        u          v      |F|/mediana")

    for k in range(len(lista_picos)):

        pico = lista_picos[k]

        linea = f"{k + 1:2d}   {pico['u']:+.4f}    {pico['v']:+.4f}    {pico['valor']:9.1f}"
        lineas.append(linea)

    for linea in lineas:
        print(linea)

    ruta_salida = carpeta_salida / "picos_encontrados.txt"

    with open(ruta_salida, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_salida}")


def graficar_espectro_con_picos(
    espectro,
    lista_picos,
    frec_u,
    frec_v,
    carpeta_salida,
):

    extension = [
        frec_u[0],
        frec_u[-1],
        frec_v[-1],
        frec_v[0],
    ]

    figura, axis = plt.subplots(
        1,
        1,
        figsize=(9, 8),
    )

    axis.imshow(
        espectro,
        cmap="gray",
        extent=extension,
    )

    # los picos son de un pixel y no se ven, por eso se marcan con circulos
    # rojo: los esperados, cian: el resto
    for k in range(len(lista_picos)):

        pico = lista_picos[k]

        if k < N_ESPERADOS:

            axis.plot(
                pico["u"],
                pico["v"],
                "o",
                markerfacecolor="none",
                markeredgecolor="red",
                markersize=14,
            )

            # el numero se corre hacia el centro para que no quede fuera
            if pico["u"] > 0:
                x_texto = pico["u"] - 0.05
            else:
                x_texto = pico["u"] + 0.02

            if pico["v"] < 0:
                y_texto = pico["v"] + 0.05
            else:
                y_texto = pico["v"] - 0.02

            axis.text(
                x_texto,
                y_texto,
                str(k + 1),
                color="red",
                fontsize=12,
            )

        else:

            axis.plot(
                pico["u"],
                pico["v"],
                "o",
                markerfacecolor="none",
                markeredgecolor="cyan",
                markersize=7,
            )

    # circulo del radio excluido
    angulos = np.linspace(0, 2 * np.pi, 200)

    axis.plot(
        RADIO_EXCLUIR * np.cos(angulos),
        RADIO_EXCLUIR * np.sin(angulos),
        "--",
        color="yellow",
        linewidth=1,
    )

    axis.set_title(
        f"log(1 + |F|), radio excluido = {RADIO_EXCLUIR}\n"
        f"rojo: picos 1 a {N_ESPERADOS}, cian: picos {N_ESPERADOS + 1} a {len(lista_picos)}"
    )
    axis.set_xlabel("u [ciclos/pixel]")
    axis.set_ylabel("v [ciclos/pixel]")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "espectro_con_picos.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_zoom_picos(
    espectro,
    lista_picos,
    carpeta_salida,
):

    alto = espectro.shape[0]
    ancho = espectro.shape[1]

    # misma escala para todos los zoom
    valor_min = np.min(espectro)
    valor_max = np.max(espectro)

    n_columnas = 5
    n_filas = int(np.ceil(len(lista_picos) / n_columnas))

    figura, axes = plt.subplots(
        n_filas,
        n_columnas,
        figsize=(3.2 * n_columnas, 3.4 * n_filas),
    )

    axes = axes.ravel()

    for k in range(len(lista_picos)):

        pico = lista_picos[k]

        # indices alrededor del pico, con % para dar la vuelta en los bordes
        filas = []
        for d in range(-MEDIO_ZOOM, MEDIO_ZOOM + 1):
            filas.append((pico["fila"] + d) % alto)

        columnas = []
        for d in range(-MEDIO_ZOOM, MEDIO_ZOOM + 1):
            columnas.append((pico["col"] + d) % ancho)

        recorte = espectro[filas, :]
        recorte = recorte[:, columnas]

        # ejes en ciclos/pixel (pueden pasar de 0.5 por la vuelta en el borde)
        extension = [
            pico["u"] - MEDIO_ZOOM / ancho,
            pico["u"] + MEDIO_ZOOM / ancho,
            pico["v"] + MEDIO_ZOOM / alto,
            pico["v"] - MEDIO_ZOOM / alto,
        ]

        axes[k].imshow(
            recorte,
            cmap="gray",
            vmin=valor_min,
            vmax=valor_max,
            extent=extension,
            interpolation="nearest",
            aspect="auto",
        )

        axes[k].set_title(
            f"{k + 1}: ({pico['u']:+.4f}, {pico['v']:+.4f})\n|F|/mediana = {pico['valor']:.0f}",
            fontsize=9,
        )
        axes[k].tick_params(labelsize=7)

    # apagar los ejes que sobran
    for k in range(len(lista_picos), len(axes)):
        axes[k].axis("off")

    figura.suptitle(f"Zoom de {2 * MEDIO_ZOOM + 1} x {2 * MEDIO_ZOOM + 1} pixeles alrededor de cada pico (misma escala)")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "zoom_picos.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def revisar_otros_radios(
    magnitud_rel,
    distancia,
    frec_u,
    frec_v,
    lista_picos,
):

    # solo comparo los picos esperados
    n_comparar = N_ESPERADOS

    referencia = []
    for k in range(n_comparar):
        referencia.append((round(lista_picos[k]["u"], 4), round(lista_picos[k]["v"], 4)))

    print("")
    print(f"Revision con otros radios (primeros {n_comparar} picos):")

    for radio in RADIOS_PRUEBA:

        picos_radio = buscar_picos(
            magnitud_rel,
            distancia,
            frec_u,
            frec_v,
            radio,
            n_comparar,
        )

        posiciones = []
        for k in range(n_comparar):
            posiciones.append((round(picos_radio[k]["u"], 4), round(picos_radio[k]["v"], 4)))

        if posiciones == referencia:
            resultado = "iguales"
        else:
            resultado = "DISTINTOS"

        print(f"  radio = {radio:.2f}: {resultado}")

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

    # igual que en test_p1_perfiles: el fondo queda cerca de 1
    mediana = np.median(magnitud)
    magnitud_rel = magnitud / mediana

    espectro = espectro_log(F)

    frec_u = np.fft.fftshift(np.fft.fftfreq(ancho))
    frec_v = np.fft.fftshift(np.fft.fftfreq(alto))

    U, V = np.meshgrid(
        frec_u,
        frec_v,
    )

    distancia = np.sqrt(U**2 + V**2)

    lista_picos = buscar_picos(
        magnitud_rel,
        distancia,
        frec_u,
        frec_v,
        RADIO_EXCLUIR,
        N_PICOS,
    )

    guardar_tabla_picos(
        lista_picos,
        CARPETA_SALIDA,
    )

    revisar_otros_radios(
        magnitud_rel,
        distancia,
        frec_u,
        frec_v,
        lista_picos,
    )

    graficar_espectro_con_picos(
        espectro,
        lista_picos,
        frec_u,
        frec_v,
        CARPETA_SALIDA,
    )

    graficar_zoom_picos(
        espectro,
        lista_picos,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
