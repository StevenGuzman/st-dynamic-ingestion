from collections import defaultdict

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


TOKEN_PATTERN = r'(?u)\b\w[\w\.&\-]+\b'


def construir_documentos(df, meta=None, n_muestra=150):
    """Cada columna del DataFrame se convierte en un 'documento' concatenando
    sus valores no nulos. Las columnas en `meta` se excluyen."""
    meta = meta or set()
    documentos, etiquetas = [], []
    for columna in df.columns:
        if columna in meta:
            continue
        valores = df[columna].dropna().astype(str).head(n_muestra).tolist()
        if valores:
            documentos.append(' '.join(valores))
            etiquetas.append(columna)
    return documentos, etiquetas


def vectorizar(documentos, max_features=3000):
    """Vectoriza los documentos con TF-IDF y devuelve la matriz dispersa."""
    vectorizador = TfidfVectorizer(
        max_features=max_features,
        token_pattern=TOKEN_PATTERN,
        lowercase=True,
    )
    return vectorizador.fit_transform(documentos)


def clusterizar_kmeans(X, etiquetas, k, random_state=42, n_init=20):
    """Aplica K-means y devuelve un diccionario `cluster_id -> [columnas]`."""
    modelo = KMeans(n_clusters=k, n_init=n_init, random_state=random_state)
    asignaciones = modelo.fit_predict(X)
    clusters = defaultdict(list)
    for columna, cluster in zip(etiquetas, asignaciones):
        clusters[int(cluster)].append(columna)
    return dict(clusters)


def contar_unicas(X, etiquetas, umbral=0.85):
    """Cuenta variables únicas: similitud coseno + union-find sobre pares
    `sim >= umbral`. Devuelve `(K_real, pares_fusionados, matriz_similitud)`."""
    S = cosine_similarity(X)
    padre = list(range(len(etiquetas)))

    def encontrar(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    pares_fusionados = []
    for i in range(len(etiquetas)):
        for j in range(i + 1, len(etiquetas)):
            if S[i, j] >= umbral:
                pares_fusionados.append((etiquetas[i], etiquetas[j], float(S[i, j])))
                ri, rj = encontrar(i), encontrar(j)
                if ri != rj:
                    padre[ri] = rj

    k_real = len({encontrar(i) for i in range(len(etiquetas))})
    return k_real, pares_fusionados, S


def tabla_similitudes(S, etiquetas, umbral=0.85):
    """DataFrame con todas las combinaciones de columnas, su similitud y si
    cae sobre el umbral. Ordenado desc por similitud."""
    n = len(etiquetas)
    filas = [(etiquetas[i], etiquetas[j], float(S[i, j]))
             for i in range(n) for j in range(i + 1, n)]
    return (pd.DataFrame(filas, columns=['columna_a', 'columna_b', 'similitud'])
              .assign(fusiona=lambda d: d['similitud'] >= umbral)
              .sort_values('similitud', ascending=False)
              .reset_index(drop=True))
