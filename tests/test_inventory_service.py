"""Pruebas unitarias para el motor de inventario."""

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from modules.inventory_service import calculate_inventory_policy, get_z_score, summarize_inventory_policy


def test_get_z_score_returns_expected_near_value() -> None:
    """Valida que el nivel 0.95 use el Z esperado aproximado."""
    assert get_z_score(0.95) == 1.65


def test_calculate_inventory_policy_generates_required_columns() -> None:
    """Valida que la política de inventario calcule columnas clave."""
    inventory_df = pd.DataFrame(
        {
            "sku": ["SKU001"],
            "product_name": ["Producto prueba"],
            "category": ["Prueba"],
            "current_stock": [100],
            "unit_cost": [5.0],
            "lead_time_days": [5],
            "service_level": [0.95],
        }
    )
    sales_df = pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=10, freq="D"),
            "sku": ["SKU001"] * 10,
            "units_sold": [10, 12, 11, 10, 13, 12, 11, 10, 9, 12],
        }
    )

    policy_df = calculate_inventory_policy(inventory_df, sales_df)

    required_columns = {
        "avg_daily_demand",
        "std_daily_demand",
        "safety_stock",
        "lead_time_demand",
        "reorder_point",
        "coverage_days",
        "inventory_status",
    }
    assert required_columns.issubset(policy_df.columns)
    assert policy_df.loc[0, "reorder_point"] > 0


def test_summarize_inventory_policy_returns_kpis() -> None:
    """Valida que el resumen ejecutivo devuelva KPIs."""
    policy_df = pd.DataFrame(
        {
            "inventory_status": ["Normal", "Crítico", "Precaución"],
            "stock_value": [100.0, 50.0, 75.0],
            "coverage_days": [10.0, 2.0, 5.0],
        }
    )

    summary = summarize_inventory_policy(policy_df)

    assert summary["total_skus"] == 3
    assert summary["critical_count"] == 1
    assert summary["total_stock_value"] == 225.0
