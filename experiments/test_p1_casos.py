from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta1 import calcular_espectro
from src.pregunta1 import espectro_log
from src.pregunta1 import filtrar_notch


RUTA_IMAGEN = Path("images/profesor/p1/P1.CR2")

CARPETA_SALIDA = Path("results/pregunta1/casos")

LISTA_CENTROS = [
    (0.25, 0),
    (-0.5, -0.5),
    (-0.5, 0),
    (0, -0.5),
]

TIPO_PADDING = "ninguno"
TAM_PADDING = 0

# casos principales elegidos con curvas_barrido.png (ver notas.md):
# angosto, el codo de las curvas y ancho
CASOS = [0.001, 0.005, 0.04]

# misma zona de detalle que en test_p1_filtrado (M43)
ZONA_DETALLE = {
    "fila": 2180,
    "col": 1650,
    "tam": 128,
}

# estrella brillante con el centro saturado (arriba a la derecha)
CENTRO_ESTRELLA = (1090, 3358)
MEDIO_ESTRELLA = 48

# dentro del nucleo saturado la imagen original es plana
# si ahi aparece algo despues de filtrar es un artefacto del filtro
MEDIO_NUCLEO = 6

# zoom del espectro alrededor de dos centros (en ciclos/pixel)
MEDIO_ZOOM_FREC = 0.05


def recortar_detalle(imagen):

    f0 = ZONA_DETALLE["fila"]
    c0 = ZONA_DETALLE["col"]
    tam = ZONA_DETALLE["tam"]

    recorte = imagen[f0:f0 + tam, c0:c0 + tam]

    return recorte


def recortar_estrella(imagen):

    fila = CENTRO_ESTRELLA[0]
    col = CENTRO_ESTRELLA[1]
    m = MEDIO_ESTRELLA

    recorte = imagen[fila - m:fila + m, col - m:col + m]

    return recorte


def std_nucleo(imagen):

    fila = CENTRO_ESTRELLA[0]
    col = CENTRO_ESTRELLA[1]
    m = MEDIO_NUCLEO

    nucleo = imagen[fila - m:fila + m, col - m:col + m]

    return np.std(nucleo)


def recortar_espectro(
    espectro,
    u0,
    v0,
):

    alto = espectro.shape[0]
    ancho = espectro.shape[1]

    frec_u = np.fft.fftshift(np.fft.fftfreq(ancho))
    frec_v = np.fft.fftshift(np.fft.fftfreq(alto))

    col_centro = np.argmin(np.abs(frec_u - u0))
    fila_centro = np.argmin(np.abs(frec_v - v0))

    medio_filas = int(MEDIO_ZOOM_FREC * alto)
    medio_cols = int(MEDIO_ZOOM_FREC * ancho)

    # con % se da la vuelta en los bordes (igual que en los otros scripts)
    filas = []
    for d in range(-medio_filas, medio_filas + 1):
        filas.append((fila_centro + d) % alto)

    columnas = []
    for d in range(-medio_cols, medio_cols + 1):
        columnas.append((col_centro + d) % ancho)

    recorte = espectro[filas, :]
    recorte = recorte[:, columnas]

    extension = [
        frec_u[col_centro] - medio_cols / ancho,
        frec_u[col_centro] + medio_cols / ancho,
        frec_v[fila_centro] + medio_filas / alto,
        frec_v[fila_centro] - medio_filas / alto,
    ]

    return recorte, extension


def preparar_fila(
    nombre,
    imagen_original,
    imagen,
):

    # todo lo que se muestra de un caso, asi no hay que guardar la imagen completa
    espectro = espectro_log(calcular_espectro(imagen))

    zoom_025, ext_025 = recortar_espectro(espectro, 0.25, 0)
    zoom_esquina, ext_esquina = recortar_espectro(espectro, -0.5, -0.5)

    fila = {
        "nombre": nombre,
        "detalle": recortar_detalle(imagen),
        "dif_detalle": recortar_detalle(imagen_original - imagen),
        "estrella": recortar_estrella(imagen),
        "zoom_025": zoom_025,
        "ext_025": ext_025,
        "zoom_esquina": zoom_esquina,
        "ext_esquina": ext_esquina,
        "std_nucleo": std_nucleo(imagen),
        "std_dif": np.std(imagen_original - imagen),
    }

    return fila


def graficar_casos(
    tipo,
    filas,
    lim_diferencia,
    carpeta_salida,
):

    # escalas comunes sacadas de la imagen ruidosa (primera fila)
    detalle_min = np.percentile(filas[0]["detalle"], 1)
    detalle_max = np.percentile(filas[0]["detalle"], 99.5)

    espectro_min = min(np.min(filas[0]["zoom_025"]), np.min(filas[0]["zoom_esquina"]))
    espectro_max = max(np.max(filas[0]["zoom_025"]), np.max(filas[0]["zoom_esquina"]))

    figura, axes = plt.subplots(
        len(filas),
        5,
        figsize=(22, 4.4 * len(filas)),
    )

    for i in range(len(filas)):

        fila = filas[i]

        axes[i, 0].imshow(
            fila["detalle"],
            cmap="gray",
            vmin=detalle_min,
            vmax=detalle_max,
            interpolation="nearest",
        )
        axes[i, 0].set_title(f"{fila['nombre']}: zoom M43")

        if i == 0:
            axes[i, 1].axis("off")
        else:
            axes[i, 1].imshow(
                fila["dif_detalle"],
                cmap="gray",
                vmin=-lim_diferencia,
                vmax=lim_diferencia,
                interpolation="nearest",
            )
            axes[i, 1].set_title(f"diferencia (escala +-{lim_diferencia:.3f})")

        # escala angosta para ver lo que pasa dentro del nucleo saturado
        axes[i, 2].imshow(
            fila["estrella"],
            cmap="gray",
            vmin=0.6,
            vmax=1.2,
            interpolation="nearest",
        )
        axes[i, 2].set_title(f"estrella [0.6, 1.2], std nucleo = {fila['std_nucleo']:.4f}")

        axes[i, 3].imshow(
            fila["zoom_025"],
            cmap="gray",
            vmin=espectro_min,
            vmax=espectro_max,
            extent=fila["ext_025"],
            aspect="auto",
        )
        axes[i, 3].set_title("log(1 + |F|) cerca de (0.25, 0)")

        axes[i, 4].imshow(
            fila["zoom_esquina"],
            cmap="gray",
            vmin=espectro_min,
            vmax=espectro_max,
            extent=fila["ext_esquina"],
            aspect="auto",
        )
        axes[i, 4].set_title("log(1 + |F|) cerca de (-0.5, -0.5)")

        for j in range(3):
            axes[i, j].axis("off")

        axes[i, 3].tick_params(labelsize=7)
        axes[i, 4].tick_params(labelsize=7)

    figura.suptitle(f"Notch {tipo}: casos principales (padding: {TIPO_PADDING})", fontsize=14)

    figura.tight_layout()

    ruta_salida = carpeta_salida / f"casos_{tipo}.png"

    figura.savefig(
        ruta_salida,
        dpi=110,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def guardar_tabla(
    filas_por_tipo,
    carpeta_salida,
):

    lineas = []
    lineas.append("caso                      std nucleo estrella   std diferencia")

    for tipo in ["ideal", "gaussiano"]:
        for fila in filas_por_tipo[tipo]:

            # la ruidosa esta en los dos, se escribe una sola vez
            if tipo == "gaussiano" and fila["nombre"] == "ruidosa":
                continue

            linea =f"{fila['nombre']:25s} {fila['std_nucleo']:12.4f}       {fila['std_dif']:10.5f}"
            lineas.append(linea)

    print("")
    for linea in lineas:
        print(linea)

    ruta_salida = carpeta_salida / "casos_tabla.txt"

    with open(ruta_salida, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_salida}")


def main():

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    imagen = cargar_imagen(RUTA_IMAGEN)

    print(f"Imagen: {RUTA_IMAGEN}, tamano {imagen.shape}")

    filas_por_tipo = {}

    for tipo in ["ideal", "gaussiano"]:

        if tipo == "ideal":
            nombre_parametro = "radio"
        else:
            nombre_parametro = "sigma"

        # primera fila: la imagen ruidosa
        filas = []
        filas.append(preparar_fila("ruidosa", imagen, imagen))

        for ancho in CASOS:

            print(f"Notch {tipo}, {nombre_parametro} = {ancho}")

            imagen_filtrada = filtrar_notch(
                imagen,
                tipo,
                LISTA_CENTROS,
                ancho,
                TIPO_PADDING,
                TAM_PADDING,
            )

            nombre = f"{tipo} {nombre_parametro}={ancho}"

            filas.append(preparar_fila(nombre, imagen, imagen_filtrada))

        filas_por_tipo[tipo] = filas

    # misma escala de diferencia para todos los casos de los dos filtros
    lim_diferencia = 0
    for tipo in ["ideal", "gaussiano"]:
        for fila in filas_por_tipo[tipo][1:]:
            lim = np.percentile(np.abs(fila["dif_detalle"]), 99.5)
            if lim > lim_diferencia:
                lim_diferencia = lim

    guardar_tabla(
        filas_por_tipo,
        CARPETA_SALIDA,
    )

    for tipo in ["ideal", "gaussiano"]:
        graficar_casos(
            tipo,
            filas_por_tipo[tipo],
            lim_diferencia,
            CARPETA_SALIDA,
        )


if __name__ == "__main__":
    main()
