"""Pruebas unitarias para carga y validación de datos."""

from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from modules.data_loader import prepare_seed_data, validate_inventory_data, validate_sales_data


def build_valid_inventory() -> pd.DataFrame:
    """
    Construye inventario mínimo válido para pruebas.

    Returns:
        DataFrame de inventario.
    """
    return pd.DataFrame(
        {
            "sku": ["SKU001"],
            "product_name": ["Producto prueba"],
            "category": ["Prueba"],
            "current_stock": [100],
            "unit_cost": [10.5],
            "lead_time_days": [5],
            "service_level": [0.95],
        }
    )


def build_valid_sales() -> pd.DataFrame:
    """
    Construye ventas mínimas válidas para pruebas.

    Returns:
        DataFrame de ventas.
    """
    return pd.DataFrame(
        {
            "date": ["2025-01-01", "2025-01-02"],
            "sku": ["SKU001", "SKU001"],
            "units_sold": [10, 12],
        }
    )


def test_validate_inventory_data_accepts_valid_inventory() -> None:
    """Valida que un inventario correcto sea aceptado."""
    inventory_df = build_valid_inventory()
    assert validate_inventory_data(inventory_df) is True


def test_validate_sales_data_accepts_valid_sales() -> None:
    """Valida que ventas correctas sean aceptadas."""
    sales_df = build_valid_sales()
    assert validate_sales_data(sales_df) is True


def test_prepare_seed_data_rejects_unknown_sku() -> None:
    """Valida que ventas con SKU inexistente sean rechazadas."""
    inventory_df = build_valid_inventory()
    sales_df = build_valid_sales()
    sales_df.loc[0, "sku"] = "SKU999"

    with pytest.raises(ValueError):
        prepare_seed_data(inventory_df, sales_df)
