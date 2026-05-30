# StockPredict MVP

## Sistema Inteligente de Gestión de Inventarios, Predicción de Demanda y Demostración de Machine Learning

## Descripción General

StockPredict es una aplicación web desarrollada en Python y Streamlit para la gestión inteligente de inventarios mediante analítica de datos, modelos estadísticos de pronóstico y componentes demostrativos de Machine Learning.

El sistema permite analizar históricos de ventas, calcular inventarios de seguridad, determinar puntos de reorden, generar alertas, clasificar SKU mediante ABC, producir pronósticos y segmentar productos mediante aprendizaje automático.

El proyecto está diseñado como MVP académico y demostrativo, listo para despliegue en Render Free.

## Estado del Proyecto

MVP funcional desarrollado en Python y Streamlit con despliegue compatible en:

- Streamlit Community Cloud.
- Render Free.

Estado actual:

- Gestión de inventarios implementada.
- Analítica ABC implementada.
- Pronóstico estadístico implementado.
- Machine Learning supervisado implementado.
- Machine Learning no supervisado implementado.
- Pruebas locales completadas.
- Proyecto preparado para despliegue en la nube.


## Funcionalidades

- Gestión inicial de inventario con datos semilla.
- Histórico de ventas por SKU.
- Cálculo de demanda promedio.
- Inventario de seguridad.
- Punto de reorden.
- Días de cobertura.
- Alertas operativas.
- Clasificación ABC.
- Pronóstico por media móvil.
- Pronóstico por suavizamiento exponencial.
- ML supervisado con RandomForestRegressor.
- ML no supervisado con KMeans.
- Exportación CSV.
- Dashboard ejecutivo en Streamlit.

## Arquitectura

```text
Usuario
   |
Streamlit
   |
Módulos Python
   |-- data_loader.py
   |-- inventory_service.py
   |-- forecast_service.py
   |-- analytics_service.py
   |-- ml_service.py
   |
CSV semilla
```

## Estructura

```text
stockpredict_mvp/
├── app/
│   ├── main.py
│   └── modules/
│       ├── config.py
│       ├── logger_config.py
│       ├── data_loader.py
│       ├── inventory_service.py
│       ├── forecast_service.py
│       ├── analytics_service.py
│       └── ml_service.py
├── data/
│   ├── inventory_seed.csv
│   └── sales_seed.csv
├── tests/
├── smoke_test.py
├── check_deploy_files.py
├── requirements.txt
├── runtime.txt
├── render.yaml
├── Procfile
├── DEPLOY_RENDER.md
├── CHECKLIST_ETAPA8_RENDER.md
└── .streamlit/
    └── config.toml
```

## Etapas del Proyecto

### Etapa 1 — Estructura base
Arquitectura inicial, Streamlit y datos semilla básicos.

### Etapa 2 — Datos iniciales
20 SKU y 12 meses de ventas simuladas.

### Etapa 3 — Motor de inventario
Inventario de seguridad, punto de reorden, cobertura y alertas.

### Etapa 4 — Predicción estadística
Media móvil y suavizamiento exponencial.

### Etapa 5 — Dashboard ejecutivo
KPIs, gráficos, ABC y exportación CSV.

### Etapa 6 — Pruebas locales
Pytest, smoke test y checklist.

### Etapa 7 — Machine Learning
RandomForestRegressor para predicción y KMeans para segmentación.

### Etapa 8 — Preparación Render
Archivos cloud, validación de despliegue y documentación.

### Etapa 9 — Despliegue final
Publicación del MVP en Render Free.

## Ejecución Local

```bash
pip install -r requirements.txt
streamlit run app/main.py
```

## Pruebas

```bash
python -m pytest -q tests
python smoke_test.py
python check_deploy_files.py
```

## Despliegue

Consultar:

```text
DEPLOY_RENDER.md
```

### Opción adicional — Streamlit Community Cloud

Además de Render Free, StockPredict MVP puede desplegarse en Streamlit Community Cloud, opción recomendada para demostraciones académicas y portafolio profesional porque la aplicación fue desarrollada directamente con Streamlit.

#### Configuración

```text
Repository:
antoniot73/stockpredict_mvp_ml

Branch:
main

Main file path:
app/main.py

App URL sugerida:
stockpredict-mvp-ml
```

#### URL pública

```text
https://stockpredict-mvp-ml.streamlit.app/
```

#### Advanced Settings

Seleccionar:

```text
Python 3.11
```

No se requieren secrets ni variables de entorno para esta versión MVP.

#### Pasos de despliegue

1. Entrar a Streamlit Community Cloud.
2. Iniciar sesión con GitHub.
3. Seleccionar `Deploy an app`.
4. Elegir el repositorio `antoniot73/stockpredict_mvp_ml`.
5. Configurar `main` como rama.
6. Configurar `app/main.py` como archivo principal.
7. Seleccionar Python 3.11 en Advanced Settings.
8. Ejecutar el despliegue.

#### Validación posterior

Después del despliegue, validar:

- Dashboard principal.
- KPIs.
- Clasificación ABC.
- Pronóstico estadístico.
- Pestaña de Machine Learning.
- Descarga de archivos CSV.


## Licencia

Proyecto académico y demostrativo. Definir licencia antes de uso público o comercial.

## Autor

Antonio Nicolás Toro González

Proyecto de Inteligencia Artificial aplicada y Ciencia de Datos.


## Entrega Final

Documentos finales:

```text
ETAPA9_DESPLIEGUE_FINAL.md
CHECKLIST_ETAPA9_FINAL.md
REPORTE_ENTREGA_FINAL.md
```

La Etapa 9 corresponde al despliegue final en Render Free y validación pública del MVP.

También se contempla despliegue alternativo en Streamlit Community Cloud para facilitar demostraciones académicas y publicación rápida del MVP.
