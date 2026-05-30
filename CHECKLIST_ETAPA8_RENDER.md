# Checklist — Etapa 8 Render Ready

## Local

- [ ] `python --version` muestra Python 3.11.x.
- [ ] `python -m pytest -q tests` pasa sin errores.
- [ ] `python smoke_test.py` muestra `Resultado: OK`.
- [ ] `python check_deploy_files.py` muestra `Resultado: OK`.
- [ ] `streamlit run app/main.py` abre la aplicación.

## App

- [ ] KPIs visibles.
- [ ] Alertas visibles.
- [ ] Política de inventario visible.
- [ ] Clasificación ABC visible.
- [ ] Pronóstico estadístico funcional.
- [ ] Pestaña ML funcional.
- [ ] Descargas CSV funcionales.

## GitHub

- [ ] Repositorio creado.
- [ ] Código subido.
- [ ] Rama principal `main`.
- [ ] Archivos de datos incluidos.

## Render

- [ ] Web Service creado.
- [ ] Plan Free seleccionado.
- [ ] Build Command configurado.
- [ ] Start Command configurado.
- [ ] Deploy finalizado sin errores.

## Criterio de aceptación

La etapa 8 queda aprobada cuando el proyecto está en GitHub y Render puede construirlo sin errores.
