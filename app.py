from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from src.carga import cargar_archivo
from src.clustering import (
    clusterizar_kmeans,
    construir_documentos,
    contar_unicas,
    vectorizar,
)


META = {'archivo_origen'}
UMBRAL = 0.85

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / 'templates'))

app = FastAPI(title='Consolidador Amazon — clustering de columnas')

# Estado en memoria: el DataFrame acumulado entre uploads y los nombres de los
# archivos ya incorporados. Es un demo de un solo usuario, no requiere sesiones.
_df_acumulado: pd.DataFrame | None = None
_archivos: list[str] = []


def _resetear():
    global _df_acumulado, _archivos
    _df_acumulado = None
    _archivos = []


def _resumen(df: pd.DataFrame) -> dict:
    head = df.head(10).fillna('').astype(str).to_dict(orient='records')
    info = [
        {
            'columna': col,
            'tipo': str(df[col].dtype),
            'no_nulos': int(df[col].notna().sum()),
            'nulos': int(df[col].isna().sum()),
        }
        for col in df.columns
    ]

    documentos, etiquetas = construir_documentos(df, meta=META)
    clusters: dict[str, list[str]] = {}
    fusiones: list[dict] = []
    k_real = 0

    # K-means requiere al menos 2 columnas con contenido para que la similitud
    # coseno tenga pares que comparar.
    if len(etiquetas) >= 2:
        X = vectorizar(documentos)
        k_real, pares, _ = contar_unicas(X, etiquetas, umbral=UMBRAL)
        clusters_raw = clusterizar_kmeans(X, etiquetas, k=k_real)
        clusters = {str(cid): cols for cid, cols in sorted(clusters_raw.items())}
        fusiones = [
            {'a': a, 'b': b, 'sim': round(s, 4)}
            for a, b, s in sorted(pares, key=lambda p: -p[2])
        ]
    elif len(etiquetas) == 1:
        k_real = 1
        clusters = {'0': etiquetas}

    return {
        'archivos': list(_archivos),
        'filas': int(df.shape[0]),
        'columnas': int(df.shape[1]),
        'head': head,
        'info': info,
        'k_real': k_real,
        'clusters': clusters,
        'fusiones': fusiones,
        'umbral': UMBRAL,
    }


@app.get('/', response_class=HTMLResponse)
def indice(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.post('/subir')
async def subir(file: UploadFile = File(...)):
    global _df_acumulado, _archivos

    if not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(status_code=400, detail='Solo se aceptan archivos .xlsx')

    contenido = await file.read()
    try:
        df_nuevo = cargar_archivo(file.filename, contenido)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'No se pudo leer el archivo: {exc}')

    if _df_acumulado is None:
        _df_acumulado = df_nuevo
    else:
        _df_acumulado = pd.concat([_df_acumulado, df_nuevo], ignore_index=True)
    _archivos.append(file.filename)

    return JSONResponse(_resumen(_df_acumulado))


@app.post('/reiniciar')
def reiniciar():
    _resetear()
    return {'ok': True}


@app.get('/estado')
def estado():
    if _df_acumulado is None:
        return {'archivos': [], 'filas': 0, 'columnas': 0}
    return _resumen(_df_acumulado)
