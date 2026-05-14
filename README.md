# Consolidador Amazon — Proyecto I

Trabajo formativo para el curso **Proyecto I** de la **Especialización en Data & IA**. El proyecto toma cuatro archivos `.xlsx` con datos de productos de Amazon, los consolida en un único DataFrame y descubre automáticamente qué columnas son equivalentes entre sí, aunque vengan con nombres distintos en español o inglés (`categoria` ↔ `category`, `nombre_producto` ↔ `product_name`, etc.).

La parte interesante no es la EDA en sí, sino **cómo se reconcilian los campos heterogéneos sin un mapeo manual**: cada columna se trata como un documento de texto, se vectoriza con TF-IDF y un par de algoritmos de clustering deciden cuáles son variantes del mismo concepto.

Sobre esa lógica se monta una pequeña API en FastAPI con una interfaz web para subir archivos y ver los resultados en vivo. Todo se puede correr con Docker.

---

## Conceptos del curso y cómo se aplican

### Modularización

Seguimos un marco de cuatro niveles, escalando solo cuando un requerimiento concreto lo justifica. La idea es no sobre-diseñar: el código vive en el nivel mínimo que cubra el caso de uso.

| Nivel | Cuándo | Artefactos |
|---|---|---|
| 1 — Notebook | Exploración inicial | `consolidado.ipynb` |
| 2 — Modular local | Lógica reutilizable y testeable | `src/`, `main.py` |
| 3 — API local | Exponer el modelo a otros consumidores | `app.py` |
| 4 — Producción containerizada | Despliegue reproducible | `Dockerfile`, `docker-compose.yml` |

El reparto actual:

- `src/carga.py` — lectura iterativa de `.xlsx`, etiquetado por archivo de origen y reparación de mojibake en los textos.
- `src/clustering.py` — construcción de documentos por columna, TF-IDF, K-means, similitud coseno con union-find y tabla de similitudes.
- `main.py` — orquestador para correr el pipeline en consola.
- `app.py` — capa HTTP (FastAPI) con los endpoints `/subir`, `/reiniciar`, `/estado` y `/`.
- `templates/index.html` — frontend HTML con CSS classless (Pico.css) y JS vanilla.
- `consolidado.ipynb` — superficie narrativa. Solo importa, llama y muestra; no contiene lógica que no esté ya en `src/`.

### Uso de Git y GitHub

GitHub forma parte de la evaluación, así que el flujo es deliberado:

- Cada commit corresponde a un microtopic (una idea pequeña y reviewable de manera independiente): añadir un helper, ajustar el umbral, reorganizar el layout, reparar la codificación, etc. Se evitan mega-commits que mezclan cambios sin relación.
- Mensajes en imperativo y en español, explicando el *qué* y el *por qué* en lugar del *cómo*.
- Una operación o feature completa = un PR independiente.

### FastAPI

Se usó FastAPI por tres razones concretas:

1. **Manejo trivial de `UploadFile`** para recibir el `.xlsx` desde el navegador.
2. **Tipado y validación** automáticos en los endpoints.
3. **Arranque mínimo** con `uvicorn`, ideal para un demo de un solo usuario.

El estado del DataFrame acumulado vive en memoria del proceso: es un demo, no requiere base de datos ni sesiones.

### Docker

El contenedor empaqueta Python 3.12, las dependencias y el código. Quien evalúe el proyecto puede levantar todo con un único comando, sin instalar Python ni preocuparse por su versión local. La imagen base es `python:3.12-slim`, expone el puerto 8000 y arranca `uvicorn` como `CMD` por defecto.

`docker-compose.yml` envuelve el `docker run` con su mapeo de puerto y política de reinicio, dejando el comando final corto.

### Clustering: K-means y umbral de similitud

El núcleo conceptual del proyecto. Cada columna del DataFrame se transforma en un documento (sus valores no nulos unidos como texto), se vectoriza con **TF-IDF** y luego se aplican dos enfoques complementarios:

1. **K-means con K fijo (K = 17).** Se asume que conocemos de antemano el número de conceptos. Funciona como baseline pedagógico y permite visualizar la idea, pero falla cuando dos columnas comparten vocabulario superficial (por ejemplo, `user_id` y `review_id`, ambos alfanuméricos).

2. **Umbral de similitud + union-find.** Se calcula la **similitud coseno** entre todos los pares de vectores TF-IDF. Si dos columnas superan un umbral (`0.85`), se tratan como variantes del mismo campo. Union-find agrupa las componentes conectadas y devuelve el `K_real` — el número de variables efectivamente distintas. Este método se adapta solo: añadir un archivo con una columna nueva sube `K_real`, añadir una variante nueva de una existente lo mantiene.

Para juzgar si el umbral es estable se calcula la **brecha**: la diferencia entre el menor par fusionado y el mayor par no fusionado. Cuanto más grande la brecha, menos sensible es el resultado a mover el umbral.

> Una nota sobre Jaccard: la similitud Jaccard por valores **no funciona** aquí porque cada archivo tiene productos distintos. Los conjuntos de valores entre columnas equivalentes no se solapan. TF-IDF gana porque captura el vocabulario compartido (`Electronics`, `Home&Kitchen`) aunque las filas concretas difieran.

---

## Despliegue paso a paso

### Opción A — Docker (recomendada)

Requisitos: Docker Desktop con el daemon corriendo.

```bash
git clone <url-del-repositorio>
cd "Proyecto I"
docker compose up --build
```

Cuando el contenedor termine de arrancar (`Application startup complete.`), abrir en el navegador:

```
http://localhost:8000
```

Para detenerlo:

```bash
docker compose down
```

### Opción B — entorno virtual local

Requisitos: Python 3.12.

```bash
python -m venv .venv

# Activar el venv (Git Bash en Windows):
source .venv/Scripts/activate

# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app:app --reload
```

Y abrir `http://localhost:8000`.

Si lo que interesa es solo correr el pipeline en consola y ver los clusters por terminal:

```bash
python main.py
```

---

## Cómo probar la aplicación

La carpeta `datos/` ya trae los cuatro archivos de muestra (`Amazon1.xlsx` a `Amazon4.xlsx`). Cada uno introduce variantes distintas, así que el flujo más didáctico es subirlos en orden y ver cómo el detector reacciona.

### Paso 1 — Subir `Amazon1.xlsx`

Pulsa **Subir** con `Amazon1.xlsx`. Vas a ver:

- **17 columnas** detectadas (las 16 oficiales más una extra `envio_dias` que solo trae este archivo).
- **K_real = 17**.
- **0 pares fusionados** — todavía no hay con qué comparar.

### Paso 2 — Subir `Amazon2.xlsx`

Este archivo trae `nombre_producto` en lugar de `product_name`. Esperado:

- **K_real = 17** (sigue siendo el mismo número de variables únicas).
- **2 pares fusionados**:
  - `categoria` ↔ `category` (sim ≈ 0.94)
  - `nombre_producto` ↔ `product_name` (sim ≈ 0.89)

El detector dedujo, por contenido, que son la misma variable aunque tengan nombres distintos.

### Paso 3 — Subir `Amazon3.xlsx`

Introduce `usuario` como variante de `user_name`. Aparece un nuevo par fusionado con similitud alta; `K_real` se mantiene en 17.

### Paso 4 — Subir `Amazon4.xlsx`

Introduce `rankeo` como variante de `rating`. Estado final:

- **4 pares fusionados** en total.
- **`K_real = 17`** — el modelo sostiene que hay 17 variables únicas, aunque el DataFrame consolidado tenga más columnas crudas por las variantes.

### Paso 5 — Reiniciar

El botón **Reiniciar** limpia el estado acumulado. Útil para repetir el flujo o cargar los archivos en otro orden y comprobar que el resultado final es el mismo (es invariante al orden de carga).

### Qué mirar en la pantalla

- En **Campos unificados**, los clusters con dos o más columnas aparecen resaltados; esos son los que el modelo unificó.
- El panel de stats arriba (filas, columnas, K_real, pares fusionados) da el resumen numérico.
- El desplegable **Pares fusionados** lista las similitudes exactas, lo cual permite evaluar si `0.85` es un umbral cómodo (la brecha es de ~0.07, así que es estable en el rango `[0.82, 0.88]`).
- Las secciones **Vista previa** e **Info de campos** muestran respectivamente el `head` y el esquema (tipo y nulos por columna).

---

## Stack

- Python 3.12, pandas, scikit-learn, ftfy.
- FastAPI + Uvicorn (API).
- Jinja2 (templates).
- Pico.css vía CDN (estilos sin frameworks pesados).
- Docker + Docker Compose (despliegue).
