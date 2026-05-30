"""Pruebas unitarias para servicios analíticos."""

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from modules.analytics_service import (
    build_alerts_table,
    build_category_summary,
    calculate_abc_classification,
)


def build_policy_df() -> pd.DataFrame:
    """
    Construye política de inventario de prueba.

    Returns:
        DataFrame de política.
    """
    return pd.DataFrame(
        {
            "sku": ["SKU001", "SKU002", "SKU003"],
            "product_name": ["A", "B", "C"],
            "category": ["Cat1", "Cat1", "Cat2"],
            "unit_cost": [10.0, 5.0, 1.0],
            "total_units_sold": [100, 50, 10],
            "current_stock": [20, 40, 80],
            "stock_value": [200.0, 200.0, 80.0],
            "reorder_point": [30.0, 35.0, 20.0],
            "safety_stock": [10.0, 8.0, 5.0],
            "coverage_days": [2.0, 5.0, 20.0],
            "inventory_status": ["Reorden urgente", "Precaución", "Normal"],
        }
    )


def test_calculate_abc_classification_adds_class() -> None:
    """Valida clasificación ABC."""
    abc_df = calculate_abc_classification(build_policy_df())
    assert "abc_class" in abc_df.columns
    assert set(abc_df["abc_class"]).issubset({"A", "B", "C"})


def test_build_category_summary_groups_categories() -> None:
    """Valida resumen por categoría."""
    summary_df = build_category_summary(build_policy_df())
    assert len(summary_df) == 2
    assert "stock_value" in summary_df.columns


def test_build_alerts_table_excludes_normal() -> None:
    """Valida que alertas excluyan SKU normales."""
    alerts_df = build_alerts_table(build_policy_df())
    assert "Normal" not in alerts_df["inventory_status"].tolist()
