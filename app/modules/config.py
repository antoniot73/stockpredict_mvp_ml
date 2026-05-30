"""Configuración general de StockPredict MVP."""

from pathlib import Path

BASE_DIR: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = BASE_DIR / "data"
INVENTORY_FILE: Path = DATA_DIR / "inventory_seed.csv"
SALES_FILE: Path = DATA_DIR / "sales_seed.csv"
APP_TITLE: str = "StockPredict MVP"
