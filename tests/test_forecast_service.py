"""Pruebas unitarias para el servicio de pronóstico."""

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from modules.forecast_service import build_daily_series, build_forecast_summary, forecast_demand


def build_sales() -> pd.DataFrame:
    """
    Construye ventas de prueba.

    Returns:
        DataFrame de ventas.
    """
    return pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=40, freq="D"),
            "sku": ["SKU001"] * 40,
            "units_sold": [10 + (i % 5) for i in range(40)],
        }
    )


def test_build_daily_series_returns_series() -> None:
    """Valida construcción de serie diaria."""
    series = build_daily_series(build_sales(), "SKU001")
    assert len(series) == 40
    assert series.index.is_monotonic_increasing


def test_forecast_demand_moving_average_returns_horizon() -> None:
    """Valida pronóstico por media móvil."""
    forecast_df = forecast_demand(
        sales_df=build_sales(),
        sku="SKU001",
        horizon_days=14,
        method="media_movil",
        window_days=7,
    )
    assert len(forecast_df) == 14
    assert (forecast_df["forecast_units"] >= 0).all()


def test_build_forecast_summary_returns_values() -> None:
    """Valida resumen del pronóstico."""
    forecast_df = forecast_demand(
        sales_df=build_sales(),
        sku="SKU001",
        horizon_days=7,
        method="media_movil",
        window_days=7,
    )
    summary = build_forecast_summary(forecast_df)
    assert summary["forecast_total_units"] > 0
    assert summary["forecast_avg_daily_units"] > 0
