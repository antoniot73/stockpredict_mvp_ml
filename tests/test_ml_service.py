"""Pruebas unitarias para servicios de Machine Learning."""

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from modules.inventory_service import calculate_inventory_policy
from modules.ml_service import (
    create_supervised_features,
    predict_next_day_for_sku,
    train_demand_random_forest,
    train_sku_kmeans,
)


def build_sales() -> pd.DataFrame:
    """
    Construye ventas simuladas suficientes para ML.

    Returns:
        DataFrame de ventas.
    """
    dates = pd.date_range("2025-01-01", periods=80, freq="D")
    rows = []
    for sku, base in [("SKU001", 10), ("SKU002", 20), ("SKU003", 5)]:
        for i, date in enumerate(dates):
            rows.append({"date": date, "sku": sku, "units_sold": base + (i % 7)})
    return pd.DataFrame(rows)


def build_inventory() -> pd.DataFrame:
    """
    Construye inventario mínimo para clustering.

    Returns:
        DataFrame de inventario.
    """
    return pd.DataFrame(
        {
            "sku": ["SKU001", "SKU002", "SKU003"],
            "product_name": ["A", "B", "C"],
            "category": ["Cat1", "Cat1", "Cat2"],
            "current_stock": [100, 120, 80],
            "unit_cost": [3.0, 5.0, 2.0],
            "lead_time_days": [5, 7, 3],
            "service_level": [0.95, 0.95, 0.90],
        }
    )


def test_create_supervised_features_has_expected_columns() -> None:
    """Valida creación de variables supervisadas."""
    feature_df = create_supervised_features(build_sales())
    assert "lag_1" in feature_df.columns
    assert "rolling_mean_7" in feature_df.columns
    assert len(feature_df) > 0


def test_train_demand_random_forest_returns_metrics() -> None:
    """Valida entrenamiento supervisado."""
    result = train_demand_random_forest(build_sales())
    assert result.metrics["mae"] >= 0
    assert "importance" in result.feature_importance_df.columns


def test_predict_next_day_for_sku_returns_non_negative() -> None:
    """Valida predicción ML para un SKU."""
    sales_df = build_sales()
    result = train_demand_random_forest(sales_df)
    prediction = predict_next_day_for_sku(sales_df, "SKU001", result.model)
    assert prediction >= 0


def test_train_sku_kmeans_returns_clusters() -> None:
    """Valida clustering KMeans de SKU."""
    policy_df = calculate_inventory_policy(build_inventory(), build_sales())
    result = train_sku_kmeans(policy_df, n_clusters=2)
    assert "ml_cluster" in result.clustered_df.columns
    assert len(result.cluster_profile_df) == 2
