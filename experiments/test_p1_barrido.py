from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta1 import filtrar_notch


RUTA_IMAGEN = Path("images/profesor/p1/P1.CR2")

CARPETA_SALIDA = Path("results/pregunta1/barrido")

LISTA_CENTROS = [
    (0.25, 0),
    (-0.5, -0.5),
    (-0.5, 0),
    (0, -0.5),
]

# el padding se estudia despues
TIPO_PADDING = "ninguno"
TAM_PADDING = 0

# radio (ideal) o sigma (gaussiano), cada uno ~el doble del anterior
LISTA_ANCHOS = [0.0005, 0.001, 0.002, 0.005, 0.01, 0.02, 0.04]

# el gaussiano llega a H = 0.5 en D = sigma * sqrt(2 ln 2) = 1.18 sigma
# se usa para comparar los dos filtros con el mismo "radio"
FACTOR_GAUSS = np.sqrt(2 * np.log(2))

# misma zona de cielo que en test_p1_filtrado
ZONA_CIELO = {
    "fila_inicio": 100,
    "fila_fin": 400,
    "col_inicio": 2400,
    "col_fin": 3200,
}

# zonas brillantes de la nebulosa casi sin pixeles saturados (256 x 256)
TAM_ZONA = 256
ZONAS_BRILLANTES = [
    (1920, 2176),
    (1536, 1536),
    (1408, 1792),
    (1792, 1408),
]


def residuo_cielo(imagen):

    f0 = ZONA_CIELO["fila_inicio"]
    f1 = ZONA_CIELO["fila_fin"]
    c0 = ZONA_CIELO["col_inicio"]
    c1 = ZONA_CIELO["col_fin"]

    cielo = imagen[f0:f1, c0:c1]

    # si queda patron, las medianas por columna o por fila varian mucho
    por_columna = np.median(cielo, axis=0)
    por_fila = np.median(cielo, axis=1)

    std_columnas = np.std(por_columna)
    std_filas = np.std(por_fila)

    return std_columnas, std_filas


def residuo_zonas_brillantes(imagen):

    centro = TAM_ZONA // 2
    cuarto = TAM_ZONA // 4

    valores = []

    for zona in ZONAS_BRILLANTES:

        fila = zona[0]
        col = zona[1]

        recorte = imagen[fila:fila + TAM_ZONA, col:col + TAM_ZONA]
        recorte = recorte - np.mean(recorte)

        magnitud = np.abs(np.fft.fftshift(np.fft.fft2(recorte)))

        # como 256 es par y multiplo de 4 las frecuencias caen justo en un pixel
        # indice 0 = -0.5, indice centro = 0, centro +- cuarto = +-0.25
        en_picos = 0
        en_picos = en_picos + magnitud[0, 0]                 # (-0.5, -0.5)
        en_picos = en_picos + magnitud[centro, 0]            # (-0.5, 0)
        en_picos = en_picos + magnitud[0, centro]            # (0, -0.5)
        en_picos = en_picos + magnitud[centro, centro + cuarto]   # (0.25, 0)
        en_picos = en_picos + magnitud[centro, centro - cuarto]   # (-0.25, 0)

        valores.append(en_picos / np.median(magnitud))

    return np.mean(valores)


def guardar_tabla(
    referencia,
    resultados,
    carpeta_salida,
):

    lineas = []
    lineas.append(f"Padding: {TIPO_PADDING}, centros: {LISTA_CENTROS}")
    lineas.append("")
    lineas.append("filtro      ancho    radio H=0.5   cielo col   cielo fila   zonas brill.   std diferencia")

    linea = (
        f"ruidosa        -          -        "
        f"{referencia['col']:9.5f}   {referencia['fila']:9.5f}     {referencia['brillante']:9.1f}            -"
    )
    lineas.append(linea)

    for tipo in ["ideal", "gaussiano"]:

        datos = resultados[tipo]

        for k in range(len(LISTA_ANCHOS)):

            linea = (
                f"{tipo:10s} {LISTA_ANCHOS[k]:7.4f}   {datos['radio'][k]:8.4f}     "
                f"{datos['col'][k]:9.5f}   {datos['fila'][k]:9.5f}     "
                f"{datos['brillante'][k]:9.1f}       {datos['std_dif'][k]:8.5f}"
            )
            lineas.append(linea)

    print("")
    for linea in lineas:
        print(linea)

    ruta_salida = carpeta_salida / "barrido_metricas.txt"

    with open(ruta_salida, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_salida}")


def graficar_curvas(
    referencia,
    resultados,
    carpeta_salida,
):

    figura, axes = plt.subplots(
        2,
        2,
        figsize=(13, 9),
    )

    metricas = [
        ("col", "Cielo: std de la mediana por columna", axes[0, 0]),
        ("fila", "Cielo: std de la mediana por fila", axes[0, 1]),
        ("brillante", "Zonas brillantes: |F| en las frecuencias del ruido / mediana", axes[1, 0]),
        ("std_dif", "std de la diferencia (ruidosa - filtrada)", axes[1, 1]),
    ]

    for clave, titulo, axis in metricas:

        for tipo in ["ideal", "gaussiano"]:

            axis.plot(
                resultados[tipo]["radio"],
                resultados[tipo][clave],
                "o-",
                label=tipo,
            )

        # valor de la imagen sin filtrar como referencia
        if clave in referencia:
            axis.axhline(
                referencia[clave],
                color="gray",
                linestyle="--",
                label="ruidosa",
            )

        axis.set_xscale("log")
        axis.set_title(titulo, fontsize=10)
        axis.set_xlabel("radio donde H = 0.5 [ciclos/pixel]")
        axis.grid(alpha=0.3, which="both")
        axis.legend()

    figura.suptitle(f"Barrido de anchos de notch (padding: {TIPO_PADDING})")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "curvas_barrido.png"

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

    # metricas de la imagen sin filtrar
    col, fila = residuo_cielo(imagen)

    referencia = {
        "col": col,
        "fila": fila,
        "brillante": residuo_zonas_brillantes(imagen),
    }

    resultados = {}

    for tipo in ["ideal", "gaussiano"]:

        resultados[tipo] = {
            "radio": [],
            "col": [],
            "fila": [],
            "brillante": [],
            "std_dif": [],
        }

        for ancho in LISTA_ANCHOS:

            print(f"Notch {tipo}, ancho = {ancho}")

            imagen_filtrada = filtrar_notch(
                imagen,
                tipo,
                LISTA_CENTROS,
                ancho,
                TIPO_PADDING,
                TAM_PADDING,
            )

            if tipo == "gaussiano":
                radio = FACTOR_GAUSS * ancho
            else:
                radio = ancho

            col, fila = residuo_cielo(imagen_filtrada)
            brillante = residuo_zonas_brillantes(imagen_filtrada)
            std_dif = np.std(imagen - imagen_filtrada)

            resultados[tipo]["radio"].append(radio)
            resultados[tipo]["col"].append(col)
            resultados[tipo]["fila"].append(fila)
            resultados[tipo]["brillante"].append(brillante)
            resultados[tipo]["std_dif"].append(std_dif)

    guardar_tabla(
        referencia,
        resultados,
        CARPETA_SALIDA,
    )

    graficar_curvas(
        referencia,
        resultados,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
