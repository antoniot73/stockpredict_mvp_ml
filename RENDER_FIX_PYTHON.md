# Corrección Render — Python Runtime

## Problema detectado

Render estaba usando Python 3.14.3 por defecto, lo que provocaba error al instalar pandas 2.2.2.

## Corrección incluida

Este paquete contiene:

```text
runtime.txt
```

con:

```text
python-3.11.9
```

También conserva dependencias compatibles con Python 3.11.

## Pasos

Desde la raíz del proyecto:

```powershell
git add runtime.txt requirements.txt render.yaml RENDER_FIX_PYTHON.md
git commit -m "Fix Render Python runtime"
git push
```

Luego en Render:

```text
Manual Deploy
Clear build cache & deploy
```

El log correcto debe mostrar:

```text
Using Python version 3.11.9
```
