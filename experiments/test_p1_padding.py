from pathlib import Path
import time

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta1 import filtrar_notch


RUTA_IMAGEN = Path("images/profesor/p1/P1.CR2")

CARPETA_SALIDA = Path("results/pregunta1/padding")

LISTA_CENTROS = [
    (0.25, 0),
    (-0.5, -0.5),
    (-0.5, 0),
    (0, -0.5),
]

# los dos filtros con el ancho del codo del barrido (notas.md)
FILTROS = [
    ("ideal", 0.005),
    ("gaussiano", 0.005),
]

TIPOS_PADDING = ["ceros", "reflejo", "borde"]

# lo que saca el notch gaussiano en el espacio tiene una envolvente
# gaussiana con std = 1 / (2 pi sigma) ~ 32 pixeles para sigma = 0.005
# 32 ~ 1 std, 128 ~ 4 std, 256 ~ 8 std
TAMANOS_PADDING = [32, 128, 256]

# ancho de las franjas de borde para medir el patron que queda
ANCHO_FRANJA = 48

# zoom de 64 x 64 en el medio de cada borde
MEDIO_ZOOM = 32

# configuraciones que se muestran con zoom
CONFIGS_ZOOM = [
    ("ninguno", 0),
    ("ceros", 128),
    ("borde", 128),
    ("reflejo", 32),
    ("reflejo", 128),
    ("reflejo", 256),
]

NOMBRES_BORDES = ["izquierda", "derecha", "arriba", "abajo"]


def residuo_bordes(imagen):

    alto = imagen.shape[0]
    ancho = imagen.shape[1]

    a = ANCHO_FRANJA

    # en los bordes izq/der el patron es por columnas, arriba/abajo por filas
    izquierda = np.std(np.median(imagen[:, :a], axis=0))
    derecha = np.std(np.median(imagen[:, ancho - a:], axis=0))
    arriba = np.std(np.median(imagen[:a, :], axis=1))
    abajo = np.std(np.median(imagen[alto - a:, :], axis=1))

    # una franja vertical al medio de la imagen como referencia
    medio = ancho // 2
    centro = np.std(np.median(imagen[:, medio - a // 2:medio + a // 2], axis=0))

    residuo = {
        "izquierda": izquierda,
        "derecha": derecha,
        "arriba": arriba,
        "abajo": abajo,
        "centro": centro,
    }

    return residuo


def recortes_bordes(imagen):

    alto = imagen.shape[0]
    ancho = imagen.shape[1]

    m = MEDIO_ZOOM
    fila_medio = alto // 2
    col_medio = ancho // 2

    recortes = {
        "izquierda": imagen[fila_medio - m:fila_medio + m, 0:2 * m],
        "derecha": imagen[fila_medio - m:fila_medio + m, ancho - 2 * m:ancho],
        "arriba": imagen[0:2 * m, col_medio - m:col_medio + m],
        "abajo": imagen[alto - 2 * m:alto, col_medio - m:col_medio + m],
    }

    return recortes


def guardar_tabla(
    referencia,
    resultados,
    carpeta_salida,
):

    lineas = []
    lineas.append(f"Patron que queda en franjas de {ANCHO_FRANJA} pixeles en cada borde")
    lineas.append("")
    lineas.append("filtro      padding  tam   tamano con padding    izq      der      arr      aba    centro   tiempo [s]")

    r = referencia
    lineas.append(
        f"ruidosa        -       -            -            "
        f"{r['izquierda']:.4f}   {r['derecha']:.4f}   {r['arriba']:.4f}   {r['abajo']:.4f}   {r['centro']:.4f}"
    )

    for fila in resultados:

        r = fila["residuo"]

        linea = (
            f"{fila['filtro']:10s} {fila['padding']:8s} {fila['tam']:4d}   {fila['forma']:18s}   "
            f"{r['izquierda']:.4f}   {r['derecha']:.4f}   {r['arriba']:.4f}   {r['abajo']:.4f}   {r['centro']:.4f}"
            f"     {fila['tiempo']:.1f}"
        )
        lineas.append(linea)

    print("")
    for linea in lineas:
        print(linea)

    ruta_salida = carpeta_salida / "padding_tabla.txt"

    with open(ruta_salida, "w") as archivo:
        for linea in lineas:
            archivo.write(linea + "\n")

    print(f"Guardado: {ruta_salida}")


def graficar_residuo(
    referencia,
    resultados,
    carpeta_salida,
):

    figura, axes = plt.subplots(
        len(FILTROS),
        4,
        figsize=(18, 4.5 * len(FILTROS)),
    )

    for i in range(len(FILTROS)):

        nombre_filtro = FILTROS[i][0]

        for j in range(4):

            borde = NOMBRES_BORDES[j]
            axis = axes[i, j]

            # sin padding y la imagen ruidosa como lineas horizontales
            for fila in resultados:
                if fila["filtro"] == nombre_filtro and fila["padding"] == "ninguno":
                    axis.axhline(
                        fila["residuo"][borde],
                        color="black",
                        linestyle="--",
                        label="sin padding",
                    )

            for tipo in TIPOS_PADDING:

                tamanos = []
                valores = []

                for fila in resultados:
                    if fila["filtro"] == nombre_filtro and fila["padding"] == tipo:
                        tamanos.append(fila["tam"])
                        valores.append(fila["residuo"][borde])

                axis.plot(
                    tamanos,
                    valores,
                    "o-",
                    label=tipo,
                )

            axis.set_title(f"{nombre_filtro}, borde {borde}")
            axis.set_xlabel("pixeles de padding por lado")
            axis.set_ylabel("std de las medianas")
            axis.set_xticks(TAMANOS_PADDING)
            axis.set_ylim(bottom=0)
            axis.grid(alpha=0.3)
            axis.legend(fontsize=8)

    figura.suptitle(f"Patron que queda en los bordes (ruidosa: izq {referencia['izquierda']:.4f}, arriba {referencia['arriba']:.4f})")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "residuo_bordes.png"

    figura.savefig(
        ruta_salida,
        dpi=130,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_zoom_bordes(
    nombre_filtro,
    recortes_ruidosa,
    recortes_por_config,
    carpeta_salida,
):

    filas = []
    filas.append(("ruidosa", recortes_ruidosa))

    for config in CONFIGS_ZOOM:
        filas.append((f"{config[0]} {config[1]}", recortes_por_config[config]))

    figura, axes = plt.subplots(
        len(filas),
        4,
        figsize=(12, 3.1 * len(filas)),
    )

    for j in range(4):

        borde = NOMBRES_BORDES[j]

        # misma escala en toda la columna, sacada de la ruidosa
        vmin = np.percentile(recortes_ruidosa[borde], 1)
        vmax = np.percentile(recortes_ruidosa[borde], 99)

        for i in range(len(filas)):

            nombre = filas[i][0]
            recortes = filas[i][1]

            axes[i, j].imshow(
                recortes[borde],
                cmap="gray",
                vmin=vmin,
                vmax=vmax,
                interpolation="nearest",
            )
            axes[i, j].set_title(f"{nombre}, {borde}", fontsize=9)
            axes[i, j].axis("off")

    figura.suptitle(f"Zoom de 64 x 64 al medio de cada borde, notch {nombre_filtro}")

    figura.tight_layout()

    ruta_salida = carpeta_salida / f"bordes_{nombre_filtro}.png"

    figura.savefig(
        ruta_salida,
        dpi=130,
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

    referencia = residuo_bordes(imagen)
    recortes_ruidosa = recortes_bordes(imagen)

    resultados = []

    for filtro in FILTROS:

        nombre_filtro = filtro[0]
        ancho_notch = filtro[1]

        # primero sin padding y despues cada tipo con cada tamano
        configuraciones = [("ninguno", 0)]
        for tipo in TIPOS_PADDING:
            for tam in TAMANOS_PADDING:
                configuraciones.append((tipo, tam))

        recortes_por_config = {}

        for config in configuraciones:

            tipo = config[0]
            tam = config[1]

            print(f"Notch {nombre_filtro} ({ancho_notch}), padding {tipo} {tam}")

            inicio = time.time()

            imagen_filtrada = filtrar_notch(
                imagen,
                nombre_filtro,
                LISTA_CENTROS,
                ancho_notch,
                tipo,
                tam,
            )

            tiempo = time.time() - inicio

            # tamano de la imagen con padding (solo para la tabla)
            alto_pad = imagen.shape[0] + 2 * tam
            ancho_pad = imagen.shape[1] + 2 * tam

            resultados.append({
                "filtro": nombre_filtro,
                "padding": tipo,
                "tam": tam,
                "forma": f"{alto_pad} x {ancho_pad}",
                "residuo": residuo_bordes(imagen_filtrada),
                "tiempo": tiempo,
            })

            if config in CONFIGS_ZOOM:
                recortes_por_config[config] = recortes_bordes(imagen_filtrada)

        graficar_zoom_bordes(
            nombre_filtro,
            recortes_ruidosa,
            recortes_por_config,
            CARPETA_SALIDA,
        )

    guardar_tabla(
        referencia,
        resultados,
        CARPETA_SALIDA,
    )

    graficar_residuo(
        referencia,
        resultados,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
