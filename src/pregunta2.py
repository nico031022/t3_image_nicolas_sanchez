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


def degradar(
    x,
    H,
    sigma,
    semilla,
):

    y_borrosa = aplicar_H(x, H)

    # ruido gaussiano de media 0 (igual que en la capsula)
    rng = np.random.default_rng(semilla)
    ruido = sigma * rng.standard_normal(x.shape)

    # no se recorta a [0, 1] para que el ruido siga siendo gaussiano y sumado
    y = y_borrosa + ruido

    return y


def calcular_rmse(
    a,
    b,
):

    rmse = np.sqrt(np.mean((a - b)**2))

    return rmse


def wiener(
    y,
    H,
    K,
):

    Y = np.fft.fft2(y)

    # wiener simplificado: H* Y / (|H|^2 + K)
    # con K = 0 queda H* / |H|^2 = 1 / H (filtro inverso)
    X_estimada = np.conj(H) * Y / (np.abs(H)**2 + K)

    x_estimada = np.real(np.fft.ifft2(X_estimada))

    return x_estimada


def aplicar_Ht(
    x,
    H,
):

    # H transpuesta: en frecuencia es multiplicar por el conjugado de H
    # (es la correlacion con h, o convolucion con h girada en 180 grados)
    X = np.fft.fft2(x)
    resultado = np.fft.ifft2(X * np.conj(H))

    return np.real(resultado)


def costo_tikhonov(
    x,
    y,
    H,
    lam,
):

    residuo = aplicar_H(x, H) - y

    fidelidad = 0.5 * np.sum(residuo**2)
    regularizacion = 0.5 * lam * np.sum(x**2)

    return fidelidad + regularizacion


def tikhonov_gd(
    y,
    H,
    lam,
    tau,
    max_iter,
    tol,
    x_real=None,
):

    # se parte desde la imagen observada (clase 17, Landweber con f0 = g)
    x = y.copy()

    lista_costo = [costo_tikhonov(x, y, H, lam)]
    lista_rmse = []
    lista_cambio = []

    if x_real is not None:
        lista_rmse.append(calcular_rmse(x, x_real))

    n_iter = 0

    for k in range(max_iter):

        # gradiente = Ht (H x - y) + lam x
        residuo = aplicar_H(x, H) - y
        grad_fidelidad = aplicar_Ht(residuo, H)
        grad_regularizacion = lam * x

        gradiente = grad_fidelidad + grad_regularizacion

        x_nuevo = x - tau * gradiente

        costo = costo_tikhonov(x_nuevo, y, H, lam)

        # criterio de detencion (clase 17): cambio relativo entre dos iteraciones seguidas
        cambio = np.linalg.norm(x_nuevo - x) / np.linalg.norm(x)

        x = x_nuevo
        n_iter = k + 1

        lista_costo.append(costo)
        lista_cambio.append(cambio)

        if x_real is not None:
            lista_rmse.append(calcular_rmse(x, x_real))

        if not np.isfinite(costo):
            print(f"  diverge en la iteracion {n_iter}")
            break

        if cambio < tol:
            break

    return x, lista_costo, lista_rmse, lista_cambio, n_iter
