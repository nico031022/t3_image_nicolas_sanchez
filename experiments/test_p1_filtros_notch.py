from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from src.pregunta1 import cargar_imagen
from src.pregunta1 import crear_grilla_frecuencias
from src.pregunta1 import agregar_simetricos
from src.pregunta1 import notch_ideal
from src.pregunta1 import notch_gaussiano


RUTA_IMAGEN = Path("images/profesor/p1/P1.CR2")

CARPETA_SALIDA = Path("results/pregunta1/filtros")

# centros sacados de notas.md (test_p1_picos), el simetrico se agrega solo
# para el par de columnas uso 0.25 (periodo de 4 pixeles) y no 0.2501
LISTA_CENTROS = [
    (0.25, 0),
    (-0.5, -0.5),
    (-0.5, 0),
    (0, -0.5),
]

# anchos solo para ver la forma, el ancho se estudia despues en el barrido
RADIO_PRUEBA = 0.01
SIGMA_PRUEBA = 0.005

# mitad del zoom en ciclos/pixel
MEDIO_ZOOM_FREC = 0.03


def graficar_H_completo(
    H_ideal,
    H_gauss,
    U,
    V,
    carpeta_salida,
):

    extension = [
        U[0, 0],
        U[0, -1],
        V[-1, 0],
        V[0, 0],
    ]

    figura, axes = plt.subplots(
        1,
        2,
        figsize=(13, 5.5),
    )

    axes[0].imshow(
        H_ideal,
        cmap="gray",
        vmin=0,
        vmax=1,
        extent=extension,
    )
    axes[0].set_title(f"Notch ideal, radio = {RADIO_PRUEBA}")

    axes[1].imshow(
        H_gauss,
        cmap="gray",
        vmin=0,
        vmax=1,
        extent=extension,
    )
    axes[1].set_title(f"Notch gaussiano, sigma = {SIGMA_PRUEBA}")

    for axis in axes:
        axis.set_xlabel("u [ciclos/pixel]")
        axis.set_ylabel("v [ciclos/pixel]")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "H_notch_completo.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def recortar_alrededor(
    matriz,
    frec_u,
    frec_v,
    u0,
    v0,
):

    alto = matriz.shape[0]
    ancho = matriz.shape[1]

    # posicion (fila, columna) mas cercana a (u0, v0)
    col_centro = np.argmin(np.abs(frec_u - u0))
    fila_centro = np.argmin(np.abs(frec_v - v0))

    medio_filas = int(MEDIO_ZOOM_FREC * alto)
    medio_cols = int(MEDIO_ZOOM_FREC * ancho)

    # con % se da la vuelta en los bordes, igual que en test_p1_picos
    filas = []
    for d in range(-medio_filas, medio_filas + 1):
        filas.append((fila_centro + d) % alto)

    columnas = []
    for d in range(-medio_cols, medio_cols + 1):
        columnas.append((col_centro + d) % ancho)

    recorte = matriz[filas, :]
    recorte = recorte[:, columnas]

    extension = [
        frec_u[col_centro] - medio_cols / ancho,
        frec_u[col_centro] + medio_cols / ancho,
        frec_v[fila_centro] + medio_filas / alto,
        frec_v[fila_centro] - medio_filas / alto,
    ]

    return recorte, extension


def graficar_H_zoom(
    H_ideal,
    H_gauss,
    U,
    V,
    carpeta_salida,
):

    frec_u = U[0, :]
    frec_v = V[:, 0]

    # un centro normal y uno en la esquina (borde del espectro)
    centros_zoom = [
        (0.25, 0),
        (-0.5, -0.5),
    ]

    filtros = [
        ("ideal", H_ideal),
        ("gaussiano", H_gauss),
    ]

    figura, axes = plt.subplots(
        2,
        2,
        figsize=(10, 9),
    )

    for i in range(len(filtros)):

        nombre = filtros[i][0]
        H = filtros[i][1]

        for j in range(len(centros_zoom)):

            u0 = centros_zoom[j][0]
            v0 = centros_zoom[j][1]

            recorte, extension = recortar_alrededor(
                H,
                frec_u,
                frec_v,
                u0,
                v0,
            )

            axes[i, j].imshow(
                recorte,
                cmap="gray",
                vmin=0,
                vmax=1,
                extent=extension,
                interpolation="nearest",
            )
            axes[i, j].set_title(f"{nombre}, zoom en ({u0}, {v0})")
            axes[i, j].set_xlabel("u [ciclos/pixel]")
            axes[i, j].set_ylabel("v [ciclos/pixel]")

    figura.suptitle("En la esquina el notch sigue al otro lado del borde")

    figura.tight_layout()

    ruta_salida = carpeta_salida / "H_notch_zoom.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def graficar_H_perfil(
    H_ideal,
    H_gauss,
    U,
    carpeta_salida,
):

    alto = H_ideal.shape[0]

    # fila v = 0
    fila_centro = alto // 2

    frec_u = U[0, :]

    # solo la zona alrededor de u = 0.25
    zona = (frec_u > 0.2) & (frec_u < 0.3)

    figura, axis = plt.subplots(
        1,
        1,
        figsize=(9, 4.5),
    )

    axis.plot(
        frec_u[zona],
        H_ideal[fila_centro, zona],
        label=f"ideal, radio = {RADIO_PRUEBA}",
    )

    axis.plot(
        frec_u[zona],
        H_gauss[fila_centro, zona],
        label=f"gaussiano, sigma = {SIGMA_PRUEBA}",
    )

    axis.axvline(
        0.25,
        color="gray",
        linestyle="--",
        linewidth=1,
    )

    axis.set_title("Corte de H en v = 0 alrededor de u = 0.25")
    axis.set_xlabel("u [ciclos/pixel]")
    axis.set_ylabel("H(u, 0)")
    axis.grid(alpha=0.3)
    axis.legend()

    figura.tight_layout()

    ruta_salida = carpeta_salida / "H_notch_perfil.png"

    figura.savefig(
        ruta_salida,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(figura)

    print(f"Guardado: {ruta_salida}")


def revisar_filtro(
    nombre,
    H,
    H_negativo,
):

    alto = H.shape[0]
    ancho = H.shape[1]

    # con fftshift la frecuencia cero esta en (alto // 2, ancho // 2)
    valor_centro = H[alto // 2, ancho // 2]

    diferencia_simetria = np.max(np.abs(H - H_negativo))

    porcentaje_eliminado = 100 * np.mean(H < 0.5)

    print(f"Notch {nombre}:")
    print(f"  H(0, 0) = {valor_centro}")
    print(f"  max |H(u, v) - H(-u, -v)| = {diferencia_simetria}")
    print(f"  min H = {np.min(H):.4f}, max H = {np.max(H):.4f}")
    print(f"  pixeles con H < 0.5: {porcentaje_eliminado:.3f} %")


def main():

    CARPETA_SALIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    imagen = cargar_imagen(RUTA_IMAGEN)

    alto = imagen.shape[0]
    ancho = imagen.shape[1]

    print(f"Imagen: {RUTA_IMAGEN}, tamano {imagen.shape}")

    U, V = crear_grilla_frecuencias(
        alto,
        ancho,
    )

    print("Centros con sus simetricos:")
    for centro in agregar_simetricos(LISTA_CENTROS):
        print(f"  {centro}")
    print("")

    H_ideal = notch_ideal(
        U,
        V,
        LISTA_CENTROS,
        RADIO_PRUEBA,
    )

    H_gauss = notch_gaussiano(
        U,
        V,
        LISTA_CENTROS,
        SIGMA_PRUEBA,
    )

    # para revisar la simetria se calcula el mismo filtro en (-u, -v)
    H_ideal_negativo = notch_ideal(
        -U,
        -V,
        LISTA_CENTROS,
        RADIO_PRUEBA,
    )

    H_gauss_negativo = notch_gaussiano(
        -U,
        -V,
        LISTA_CENTROS,
        SIGMA_PRUEBA,
    )

    revisar_filtro(
        "ideal",
        H_ideal,
        H_ideal_negativo,
    )

    revisar_filtro(
        "gaussiano",
        H_gauss,
        H_gauss_negativo,
    )

    print("")

    graficar_H_completo(
        H_ideal,
        H_gauss,
        U,
        V,
        CARPETA_SALIDA,
    )

    graficar_H_zoom(
        H_ideal,
        H_gauss,
        U,
        V,
        CARPETA_SALIDA,
    )

    graficar_H_perfil(
        H_ideal,
        H_gauss,
        U,
        CARPETA_SALIDA,
    )


if __name__ == "__main__":
    main()
