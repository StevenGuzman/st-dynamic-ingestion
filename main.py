from pathlib import Path

from src.carga import cargar_archivos
from src.clustering import (
    clusterizar_kmeans,
    construir_documentos,
    contar_unicas,
    tabla_similitudes,
    vectorizar,
)


META = {'archivo_origen'}
UMBRAL = 0.85


def main():
    df = cargar_archivos(Path('datos'))
    print(f'Datos consolidados: {df.shape[0]} filas × {df.shape[1]} columnas\n')

    documentos, etiquetas = construir_documentos(df, meta=META)
    X = vectorizar(documentos)

    k_real, fusiones, S = contar_unicas(X, etiquetas, umbral=UMBRAL)
    print(f'K_real (variables únicas detectadas): {k_real}')
    print(f'Pares fusionados (sim >= {UMBRAL}):')
    for a, b, s in sorted(fusiones, key=lambda p: -p[2]):
        print(f'  {a:<22} <-> {b:<22}  sim={s:.3f}')

    clusters = clusterizar_kmeans(X, etiquetas, k=k_real)
    print(f'\nClusters K-means con K={k_real}:')
    for cluster_id in sorted(clusters):
        miembros = clusters[cluster_id]
        print(f'  Cluster {cluster_id} ({len(miembros)}): {miembros}')

    tabla = tabla_similitudes(S, etiquetas, umbral=UMBRAL)
    fusionados = tabla[tabla['fusiona']]
    no_fusionados = tabla[~tabla['fusiona']]
    brecha = fusionados['similitud'].min() - no_fusionados['similitud'].max()
    print(f'\nBrecha del umbral {UMBRAL}: {brecha:+.4f}')


if __name__ == '__main__':
    main()
