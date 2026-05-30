# Etapa 9 — Despliegue Final de StockPredict MVP en Render

## Objetivo

Publicar StockPredict MVP como aplicación web funcional en Render Free usando GitHub como repositorio fuente.

## 1. Validación local final

Ejecutar desde la raíz del proyecto:

```powershell
python --version
python -m pytest -q tests
python smoke_test.py
python check_deploy_files.py
streamlit run app/main.py
```

Criterio mínimo:

```text
Python 3.11.x
pytest -> passed
smoke_test.py -> Resultado: OK
check_deploy_files.py -> Resultado: OK
Streamlit -> abre sin errores
```

## 2. Subir proyecto a GitHub

Si el repositorio no existe:

```powershell
git init
git add .
git commit -m "StockPredict MVP final"
git branch -M main
git remote add origin URL_DEL_REPOSITORIO
git push -u origin main
```

Si ya existe:

```powershell
git add .
git commit -m "Etapa 9 despliegue final"
git push
```

## 3. Crear Web Service en Render

1. Entrar a Render.
2. Seleccionar `New +`.
3. Seleccionar `Web Service`.
4. Conectar GitHub.
5. Seleccionar el repositorio de StockPredict.
6. Configurar:

```text
Name: stockpredict-mvp
Environment: Python
Branch: main
Plan: Free
```

## 4. Comandos de Render

### Build Command

```bash
pip install --upgrade pip setuptools wheel && pip install -r requirements.txt
```

### Start Command

```bash
streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0
```

## 5. Variables de entorno

No se requieren variables de entorno para esta versión MVP.

## 6. Validación en Render

Cuando Render finalice el despliegue, abrir la URL pública y validar:

- Dashboard carga correctamente.
- Datos semilla aparecen.
- KPIs visibles.
- Alertas visibles.
- Política de inventario funcional.
- Clasificación ABC funcional.
- Pronóstico estadístico funcional.
- Pestaña Machine Learning funcional.
- Descargas CSV funcionales.

## 7. Consideraciones Render Free

Render Free puede suspender la aplicación por inactividad. Al volver a abrirla, puede tardar algunos segundos o minutos en reactivarse.

## 8. Resultado esperado

Al completar esta etapa, StockPredict quedará publicado como MVP web accesible mediante URL pública.
