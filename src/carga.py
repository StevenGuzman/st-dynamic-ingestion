from io import BytesIO
from pathlib import Path

import pandas as pd


def cargar_archivos(data_dir):
    """Lee iterativamente todos los .xlsx de `data_dir`, etiqueta cada fila
    con `archivo_origen` y concatena en un único DataFrame."""
    frames = []
    for archivo in sorted(Path(data_dir).glob('*.xlsx')):
        df = pd.read_excel(archivo)
        df['archivo_origen'] = archivo.name
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def cargar_archivo(nombre, contenido):
    """Lee un único .xlsx (ruta o bytes) y añade la columna `archivo_origen`.

    `contenido` puede ser una ruta, un objeto file-like o bytes; útil para
    integrarse con uploads HTTP donde el archivo llega en memoria."""
    fuente = BytesIO(contenido) if isinstance(contenido, (bytes, bytearray)) else contenido
    df = pd.read_excel(fuente)
    df['archivo_origen'] = nombre
    return df
