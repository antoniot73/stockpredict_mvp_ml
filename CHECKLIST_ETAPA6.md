# Checklist de pruebas locales — Etapa 6

## 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 2. Ejecutar pruebas unitarias

```bash
pytest -q
```

Resultado esperado:

```text
10 passed
```

## 3. Ejecutar smoke test

```bash
python smoke_test.py
```

Resultado esperado:

```text
Resultado: OK
```

## 4. Ejecutar Streamlit local

```bash
streamlit run app/main.py
```

Validar visualmente:

- KPIs cargan correctamente.
- Alertas aparecen sin error.
- Clasificación ABC se muestra.
- Tabla de política permite filtrar.
- Pronóstico por SKU funciona.
- Botones CSV descargan archivos.

## 5. Criterios de aceptación

- No hay errores de importación.
- No hay errores por rutas.
- No hay errores de validación con datos semilla.
- La app abre localmente.
- Los módulos principales tienen pruebas.
- El proyecto queda listo para preparar Render.
