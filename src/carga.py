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
