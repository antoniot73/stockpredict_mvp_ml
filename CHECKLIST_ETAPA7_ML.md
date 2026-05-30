# Checklist — Etapa 7 ML

## Validación técnica

Ejecutar:

```powershell
python -m pytest -q tests
python smoke_test.py
streamlit run app/main.py
```

## Validación visual

En la pestaña `🤖 Machine Learning`, comprobar:

- Se muestran métricas MAE, RMSE y R².
- Aparece gráfico de importancia de variables.
- Aparece gráfico real vs predicho.
- Se puede seleccionar un SKU para predicción del siguiente día.
- KMeans genera clústeres.
- Aparece gráfico de segmentación.
- Se puede descargar CSV de segmentación ML.

## Criterio de aceptación

La etapa está validada si:

- Las pruebas pasan.
- El smoke test muestra `Resultado: OK`.
- La pestaña ML carga sin errores.
