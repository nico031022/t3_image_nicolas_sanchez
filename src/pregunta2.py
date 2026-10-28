import numpy as np

from src.pregunta1 import cargar_imagen


def cargar_psf(ruta):

    psf = cargar_imagen(ruta)

    # que sume 1, asi H(0, 0) = 1 y no cambia el brillo promedio
    psf = psf / np.sum(psf)

    return psf


def psf_a_otf(
    psf,
    alto,
    ancho,
):

    alto_psf = psf.shape[0]
    ancho_psf = psf.shape[1]

    # 1. poner la psf en una imagen de ceros del tamano de la imagen
    psf_grande = np.zeros((alto, ancho))
    psf_grande[0:alto_psf, 0:ancho_psf] = psf

    # 2. mover el centro de la psf al pixel (0, 0) (como psf2otf de la capsula)
    psf_grande = np.roll(
        psf_grande,
        (-(alto_psf // 2), -(ancho_psf // 2)),
        axis=(0, 1),
    )

    # 3. fft, sin fftshift para que quede en el mismo orden que fft2(x)
    H = np.fft.fft2(psf_grande)

    return H


def aplicar_H(
    x,
    H,
):

    # convolucion circular: en frecuencia es una multiplicacion
    X = np.fft.fft2(x)
    resultado = np.fft.ifft2(X * H)

    return np.real(resultado)
