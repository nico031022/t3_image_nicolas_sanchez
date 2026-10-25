from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from src.pregunta1 import cargar_imagen
from src.pregunta1 import filtrar_notch


RUTA_IMAGEN = Path("images/profesor/p1/P1.CR2")

CARPETA_SALIDA = Path("results/pregunta1/barrido_padding")

LISTA_CENTROS = [
    (0.25, 0),
    (-0.5, -0.5),
    (-0.5, 0),
    (0, -0.5),
]

# padding elegido en test_p1_padding
TIPO_PADDING = "reflejo"
TAM_PADDING = 128

# en test_p1_casos los artefactos cambian mucho entre 0.005 y 0.04,
# por eso ahora se miran mas valores en ese rango
LISTA_ANCHOS = [0.005, 0.01, 0.015, 0.02, 0.03, 0.04]

# igual que en test_p1_barrido
FACTOR_GAUSS = np.sqrt(2 * np.log(2))

# zonas saturadas (vistas en saturados.png): (fila, columna, mitad de la ventana)
# la ventana es chica para que quede entera dentro de la parte saturada
NUCLEOS = [
    ("nucleo nebulosa", 1907, 1953, 12),
    ("estrella grande", 1089, 3357, 6),
    ("estrella arriba", 677, 3424, 4),
    ("estrella M43", 2278, 1738, 4),
]

# igual que en test_p1_barrido
TAM_ZONA = 256
ZONAS_BRILLANTES = [
    (1920, 2176),
    (1536, 1536),
    (1408, 1792),
    (1792, 1408),
]


def graficar_saturados(
    imagen,
    carpeta_salida,
):

    saturados = imagen > 1.0

    porcentaje = 100 * np.mean(saturados)
    print(f"Pixeles saturados (> 1): {porcentaje:.2f} %")

    figura, axis = plt.subplots(
        1,
        1,
        figsize=(13, 9),
    )

    axis.imshow(
        saturados,
        cmap="gray",
        interpolation="nearest",
    )

    # marcar las ventanas elegidas
    for nombre, fila, col, m in NUCLEOS:

        rectangulo = patches.Rectangle(
            (col - 40, fila - 40),
            80,
            80,
            fill=False,
            edgecolor="red",
            linewidth=1.5,
        )
        axis.add_patch(rectangulo)

        axis.text(
            col + 50,
            fila,
            nombre,
            color="red",
            fontsize=9,
        )

    axis.set_title(f"Pixeles saturados (imagen > 1), {porcentaje:.2f} % de la imagen")
    axis.set_xticks(range(0, imagen.shape[1], 250))
    axis.set_yticks(range(0, imagen.shape[0], 250))
    axis.tick_params(labelsize=7)
    axis.grid(color="yellow", alpha=0.3)

    figura.tight_layout()

    ruta_salida = carpeta_salida / "saturados.png"

    figura.savefig(
        ruta_salida,
        dpi=110,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def revisar_ventanas(imagen):

    # todas las ventanas tienen que estar 100 % saturadas
    for nombre, fila, col, m in NUCLEOS:

        ventana = imagen[fila - m:fila + m, col - m:col + m]
        fraccion = np.mean(ventana > 1.0)

        print(f"  {nombre}: ventana {2 * m} x {2 * m}, saturada {100 * fraccion:.0f} %")


def artefactos_nucleos(imagen):

    # en la imagen original las ventanas son planas
    # lo que varie despues de filtrar lo puso el filtro
    valores = []

    for nombre, fila, col, m in NUCLEOS:

        ventana = imagen[fila - m:fila + m, col - m:col + m]
        valores.append(np.std(ventana))

    return valores


def residuo_zonas_brillantes(imagen):

    # copiada de test_p1_barrido
    centro = TAM_ZONA // 2
    cuarto = TAM_ZONA // 4

    valores = []

    for zona in ZONAS_BRILLANTES:

        fila = zona[0]
        col = zona[1]

        recorte = imagen[fila:fila + TAM_ZONA, col:col + TAM_ZONA]
        recorte = recorte - np.mean(recorte)

        magnitud = np.abs(np.fft.fftshift(np.fft.fft2(recorte)))

        en_picos = 0
        en_picos = en_picos + magnitud[0, 0]
        en_picos = en_picos + magnitud[centro, 0]
        en_picos = en_picos + magnitud[0, centro]
        en_picos = en_picos + magnitud[centro, centro + cuarto]
        en_picos = en_picos + magnitud[centro, centro - cuarto]

        valores.append(en_picos / np.median(magnitud))

    return np.mean(valores)


def guardar_tabla(
    referencia,
    resultados,
    carpeta_salida,
):

    nombres = []
    for nucleo in NUCLEOS:
        nombres.append(nucleo[0])

    lineas = []
    lineas.append(f"Padding: {TIPO_PADDING} {TAM_PADDING}")
    lineas.append("artefactos = std dentro de cada zona saturada: " + ", ".join(nombres))
    lineas.append("")
    lineas.append("filtro      ancho   radio H=0.5   zonas brill.   artefactos (4 zonas)                 promedio   std diferencia")

    arts = referencia["artefactos"]
    lineas.append(
        f"ruidosa       -          -          {referencia['brillante']:7.1f}      "
        f"{arts[0]:.4f} {arts[1]:.4f} {arts[2]:.4f} {arts[3]:.4f}       {np.mean(arts):.4f}          -"
    )

    for tipo in ["ideal", "gaussiano"]:

        datos = resultados[tipo]

        for k in range(len(LISTA_ANCHOS)):

            arts = datos["artefactos"][k]

            linea = (
                f"{tipo:10s} {LISTA_ANCHOS[k]:6.3f}    {datos['radio'][k]:7.4f}       "
                f"{datos['brillante'][k]:7.1f}      "
                f"{arts[0]:.4f} {arts[1]:.4f} {arts[2]:.4f} {arts[3]:.4f}       "
                f"{np.mean(arts):.4f}       {datos['std_dif'][k]:.5f}"
            )
            lineas.append(linea)

    print("")
    for linea in lineas:
        print(linea)

    ruta_salida = carpeta_salida / "barrido_padding_tabla.txt"

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
        1,
        3,
        figsize=(19, 5.5),
    )

    for tipo in ["ideal", "gaussiano"]:

        datos = resultados[tipo]

        promedios = []
        for arts in datos["artefactos"]:
            promedios.append(np.mean(arts))

        axes[0].plot(datos["radio"], datos["brillante"], "o-", label=tipo)
        axes[1].plot(datos["radio"], promedios, "o-", label=f"{tipo} (promedio)")
        axes[2].plot(datos["radio"], datos["std_dif"], "o-", label=tipo)

    # cada zona saturada del gaussiano por separado, en linea delgada
    for j in range(len(NUCLEOS)):

        valores = []
        for arts in resultados["gaussiano"]["artefactos"]:
            valores.append(arts[j])

        axes[1].plot(
            resultados["gaussiano"]["radio"],
            valores,
            ":",
            linewidth=1,
            label=f"gaussiano, {NUCLEOS[j][0]}",
        )

    axes[1].axhline(
        np.mean(referencia["artefactos"]),
        color="gray",
        linestyle="--",
        label="ruidosa",
    )

    axes[0].set_title("Zonas brillantes: |F| en las frecuencias del ruido / mediana")
    axes[1].set_title("Artefactos: std dentro de las zonas saturadas")
    axes[2].set_title("std de la diferencia (ruidosa - filtrada)")

    for axis in axes:
        axis.set_xscale("log")
        axis.set_xlabel("radio donde H = 0.5 [ciclos/pixel]")
        axis.grid(alpha=0.3, which="both")
        axis.legend(fontsize=8)

    figura.suptitle(f"Barrido de anchos con padding {TIPO_PADDING} {TAM_PADDING}")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "curvas_barrido_padding.png"

    figura.savefig(
        ruta_salida,
        dpi=140,
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

    # 1. donde esta saturada la imagen
    graficar_saturados(
        imagen,
        CARPETA_SALIDA,
    )

    print("Ventanas dentro de las zonas saturadas:")
    revisar_ventanas(imagen)

    # 2. barrido con el padding elegido
    referencia = {
        "brillante": residuo_zonas_brillantes(imagen),
        "artefactos": artefactos_nucleos(imagen),
    }

    resultados = {}

    for tipo in ["ideal", "gaussiano"]:

        resultados[tipo] = {
            "radio": [],
            "brillante": [],
            "artefactos": [],
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

            resultados[tipo]["radio"].append(radio)
            resultados[tipo]["brillante"].append(residuo_zonas_brillantes(imagen_filtrada))
            resultados[tipo]["artefactos"].append(artefactos_nucleos(imagen_filtrada))
            resultados[tipo]["std_dif"].append(np.std(imagen - imagen_filtrada))

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
