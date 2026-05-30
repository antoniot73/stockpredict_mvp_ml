"""Verifica que existan los archivos mínimos para despliegue en Render."""

from pathlib import Path


def main() -> None:
    """
    Ejecuta validación de archivos mínimos para Render.

    Returns:
        None.

    Raises:
        SystemExit: Si falta algún archivo requerido.
    """
    required_files = [
        "runtime.txt",
        "render.yaml",
        "Procfile",
        ".streamlit/config.toml",
        "requirements.txt",
        "app/main.py",
        "app/modules/data_loader.py",
        "app/modules/inventory_service.py",
        "app/modules/forecast_service.py",
        "app/modules/analytics_service.py",
        "app/modules/ml_service.py",
        "data/inventory_seed.csv",
        "data/sales_seed.csv",
        "smoke_test.py",
    ]

    missing_files = [file for file in required_files if not Path(file).exists()]

    print("=== VALIDACIÓN DE ARCHIVOS RENDER ===")
    if missing_files:
        print("Archivos faltantes:")
        for file in missing_files:
            print(f"- {file}")
        raise SystemExit(1)

    print("Todos los archivos necesarios están presentes.")
    print("Resultado: OK")


if __name__ == "__main__":
    main()
