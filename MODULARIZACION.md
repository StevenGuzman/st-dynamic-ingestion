# Política de modularización

Guía de los niveles de modularización que seguimos en este proyecto. Cada nivel añade artefactos sobre el anterior; **subimos de nivel sólo cuando un requisito nuevo lo justifica**, no antes.

> **Nivel actual del proyecto: 2.**

---

## ¿Por qué modularizar?

Organizar el código en carpetas y módulos lógicos permite:

- Encontrar el código rápidamente.
- Reutilizar funciones entre celdas, scripts y futuras APIs.
- Trabajar en equipo sin conflictos sobre un único archivo monolítico.
- Hacer el despliegue posterior mucho más sencillo.

---

## Nivel 1 — Proyecto mínimo (sin despliegue)

**Para:** aprendizaje, exploración rápida en Jupyter.

```
proyecto/
├── notebooks/
│   ├── 01_exploracion.ipynb
│   ├── 02_preprocessing.ipynb
│   └── 03_entrenamiento.ipynb
├── data/
│   ├── raw/
│   └── processed/
├── requirements.txt
└── README.md
```

| | |
|---|---|
| ✅ Ventajas | Súper simple. Ideal para empezar. Sin fricción para Jupyter. |
| ⚠️ Limitaciones | No escala. Código mezclado en celdas. Difícil de compartir. |

**Recomendación:** usa este nivel sólo mientras tengas menos de tres notebooks.

---

## Nivel 2 — Modular local

**Para:** código validado y reutilizable que sigue corriendo en tu máquina.

```
proyecto/
├── src/
│   ├── __init__.py
│   ├── preprocessing.py     # limpieza y preparación
│   ├── model.py             # entrenamiento / inferencia
│   └── utils.py             # helpers compartidos
├── data/
│   ├── raw/
│   └── processed/
├── models/
│   └── modelo_entrenado.pkl
├── notebooks/
│   └── 01_eda.ipynb
├── main.py                  # orquesta el pipeline
├── requirements.txt
├── .gitignore
└── README.md
```

**`main.py` típico:**

```python
from pathlib import Path
from src.preprocessing import limpiar_datos
from src.model import entrenar_modelo

datos = pd.read_csv('data/raw/datos.csv')
datos_limpios = limpiar_datos(datos)
modelo = entrenar_modelo(datos_limpios)
modelo.save('models/mi_modelo.pkl')
```

| | |
|---|---|
| ✅ Ventajas | Código limpio y testeable. Reutilizable. Pasos claros. |
| ⚠️ Limitaciones | Sólo accesible localmente. Sin interfaz de servicio. |

---

## Nivel 3 — API local

**Para:** exponer el modelo a otras aplicaciones y permitir tests automatizados antes de producción.

Añade sobre Nivel 2:

```
proyecto/
├── ...
├── app.py                   # servidor FastAPI / Flask
├── tests/
│   ├── test_model.py
│   └── test_api.py
├── .env                     # NO subir a Git
└── .env.example
```

**`app.py` típico con FastAPI:**

```python
from fastapi import FastAPI
from src.model import cargar_modelo

app = FastAPI()
modelo = cargar_modelo('models/mi_modelo.pkl')

@app.post("/predecir")
def predecir(datos: dict):
    return {"prediccion": modelo.predict([datos])}

# uvicorn app:app --reload
```

| | |
|---|---|
| ✅ Ventajas | Otras apps pueden consumirlo. Testeo end-to-end. |
| ⚠️ Limitaciones | Sólo accesible en la red local. Se cae cuando reinicias. |

---

## Nivel 4 — Producción en la nube

**Para:** aplicación disponible 24/7 con múltiples usuarios.

Añade sobre Nivel 3:

```
proyecto/
├── ...
├── src/
│   └── logger.py
├── config/
│   ├── settings.py
│   └── aws.py
├── scripts/
│   ├── train.py
│   └── deploy.py
├── Dockerfile
├── docker-compose.yml
└── .github/
    └── workflows/
        └── ci-cd.yml
```

**Arquitectura AWS de referencia:**

```
Cliente HTTP
   ↓
API Gateway
   ↓
EC2 / Fargate (API + modelo)
   ↓
S3 (datos, modelos)  +  RDS (BD)  +  CloudWatch (logs)
```

Servicios habituales: **S3** (datos/modelos), **EC2/Fargate** (cómputo), **RDS** (BD), **CloudWatch** (observabilidad), **SageMaker** (entrenamiento a escala, opcional).

| | |
|---|---|
| ✅ Ventajas | Disponibilidad 24/7. Escalado horizontal. Monitoreo profesional. |
| ⚠️ Limitaciones | Cuesta dinero ($30–$500+/mes). Configuración compleja. Requiere DevOps. |

---

## Comparativa rápida

| Aspecto | Nivel 1 | Nivel 2 | Nivel 3 | Nivel 4 |
|---|---|---|---|---|
| Complejidad | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Disponibilidad | Solo PC | Solo PC | Red local | Internet 24/7 |
| Costo mensual | $0 | $0 | $0 | $30–$500+ |
| Ideal para | Aprendizaje | Proyectos locales | Testing | Usuarios reales |
| Usuarios simultáneos | 1 | 1–5 | 5–20 | 1000+ |

---

## Roadmap recomendado

```
Nivel 1 (notebooks)  →  Nivel 2 (scripts limpios)  →  Nivel 3 (API local)  →  Nivel 4 (producción)
```

- **Inicio del proyecto:** Nivel 1 — itera rápido en notebooks.
- **Código validado:** sube a Nivel 2 — extrae funciones a `src/`.
- **Necesitas exponer el modelo:** Nivel 3 — envuelve en API.
- **Vas a producción real:** Nivel 4 — Docker, cloud, CI/CD.

---

## Checklist por nivel

**Nivel 1 — Mínimo**
- [ ] `notebooks/` con `.ipynb`
- [ ] `data/` con datos
- [ ] `requirements.txt`
- [ ] `README.md` con instrucciones básicas

**Nivel 2 — Local** *(todo lo anterior, más)*
- [ ] `src/` con módulos `.py` separados
- [ ] `main.py` que orquesta el pipeline
- [ ] `models/` para artefactos entrenados
- [ ] `utils.py` con helpers reutilizables

**Nivel 3 — API local** *(todo lo anterior, más)*
- [ ] `app.py` (FastAPI / Flask)
- [ ] `tests/` con tests automáticos
- [ ] `.env.example` con plantilla de configuración
- [ ] Endpoints documentados

**Nivel 4 — Producción** *(todo lo anterior, más)*
- [ ] `Dockerfile`
- [ ] Configuración para el proveedor cloud
- [ ] Variables de entorno reales fuera de Git
- [ ] Suite de tests completa
- [ ] Logging y monitoreo
- [ ] CI/CD (GitHub Actions u otro)

---

> No es necesario empezar en Nivel 4. Cada nivel prepara para el siguiente — empieza donde el proyecto lo requiera y sube cuando un nuevo requisito lo justifique.
