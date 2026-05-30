# Etapa 8 — Preparación para despliegue en Render Free

## Objetivo

Dejar StockPredict MVP listo para publicación en Render Free, incluyendo:

- Configuración de Python.
- Configuración Streamlit cloud.
- Comando de construcción.
- Comando de arranque.
- Validación previa al despliegue.
- Checklist para GitHub y Render.

## 1. Validación local obligatoria

Desde la raíz del proyecto:

```powershell
python --version
python -m pytest -q tests
python smoke_test.py
python check_deploy_files.py
streamlit run app/main.py
```

Resultado esperado:

```text
pytest              -> passed
smoke_test.py       -> Resultado: OK
check_deploy_files  -> Resultado: OK
Streamlit           -> aplicación funcional
```

## 2. Archivos clave para Render

```text
runtime.txt
render.yaml
Procfile
.streamlit/config.toml
requirements.txt
app/main.py
data/inventory_seed.csv
data/sales_seed.csv
```

## 3. Comandos de Render

### Build Command

```bash
pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

### Start Command

```bash
streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0
```

## 4. Subir a GitHub

```powershell
git init
git add .
git commit -m "StockPredict MVP etapa 8 listo para Render"
git branch -M main
git remote add origin URL_DEL_REPOSITORIO
git push -u origin main
```

Si ya existe repositorio:

```powershell
git add .
git commit -m "Etapa 8 render ready"
git push
```

## 5. Crear Web Service en Render

1. Entrar a Render.
2. Seleccionar `New +`.
3. Seleccionar `Web Service`.
4. Conectar el repositorio GitHub.
5. Configurar:

```text
Environment: Python
Plan: Free
Branch: main
Build Command: pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
Start Command: streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0
```

## 6. Validación post-deploy

Verificar en la URL pública:

- Carga el dashboard.
- Cargan datos semilla.
- KPIs visibles.
- Alertas visibles.
- Clasificación ABC visible.
- Pronóstico estadístico funcional.
- Pestaña Machine Learning funcional.
- Descargas CSV funcionales.

## 7. Nota Render Free

En Render Free, la aplicación puede quedar suspendida por inactividad. Al acceder nuevamente, puede tardar en iniciar.
