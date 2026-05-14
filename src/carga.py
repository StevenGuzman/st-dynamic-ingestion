from io import BytesIO
from pathlib import Path

import ftfy
import pandas as pd


def _reparar_codificacion(df):
    """Corrige mojibake en columnas de texto. Los .xlsx vienen con doble
    codificación (UTF-8 leído como cp1252 y re-guardado): `₹` aparece como
    `â‚¹`, comillas y otros caracteres también. `ftfy.fix_text` revierte
    el patrón sin alterar cadenas ya correctas."""
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].map(lambda s: ftfy.fix_text(s) if isinstance(s, str) else s)
    return df


def cargar_archivo(nombre, contenido):
    """Lee un único .xlsx (ruta o bytes) y añade la columna `archivo_origen`.

    `contenido` puede ser una ruta, un objeto file-like o bytes; útil para
    integrarse con uploads HTTP donde el archivo llega en memoria."""
    fuente = BytesIO(contenido) if isinstance(contenido, (bytes, bytearray)) else contenido
    df = pd.read_excel(fuente)
    df['archivo_origen'] = nombre
    return _reparar_codificacion(df)


def cargar_archivos(data_dir):
    """Lee iterativamente todos los .xlsx de `data_dir`, etiqueta cada fila
    con `archivo_origen` y concatena en un único DataFrame."""
    frames = [cargar_archivo(p.name, p) for p in sorted(Path(data_dir).glob('*.xlsx'))]
    return pd.concat(frames, ignore_index=True)
