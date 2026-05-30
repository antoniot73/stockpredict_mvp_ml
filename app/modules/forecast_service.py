"""Servicio de predicción ligera de demanda para StockPredict MVP."""

import logging
from typing import Literal

import pandas as pd
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

logger = logging.getLogger(__name__)

ForecastMethod = Literal["media_movil", "suavizamiento_exponencial"]


def build_daily_series(sales_df: pd.DataFrame, sku: str) -> pd.Series:
    """
    Construye una serie diaria continua de ventas para un SKU.

    Args:
        sales_df: DataFrame con columnas date, sku y units_sold.
        sku: Código del producto.

    Returns:
        Serie temporal diaria con unidades vendidas.

    Raises:
        ValueError: Si no hay datos para el SKU.
    """
    required_columns = {"date", "sku", "units_sold"}
    missing_columns = required_columns.difference(sales_df.columns)
    if missing_columns:
        raise ValueError(f"Faltan columnas de ventas: {sorted(missing_columns)}")

    df = sales_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce")
    df = df[df["sku"] == sku]

    if df.empty:
        raise ValueError(f"No existen ventas para el SKU: {sku}")

    daily_df = (
        df.groupby("date", as_index=True)["units_sold"]
        .sum()
        .sort_index()
        .asfreq("D", fill_value=0)
    )

    return daily_df


def forecast_moving_average(series: pd.Series, horizon_days: int, window_days: int = 30) -> pd.DataFrame:
    """
    Genera pronóstico mediante media móvil.

    Args:
        series: Serie temporal histórica diaria.
        horizon_days: Horizonte de predicción en días.
        window_days: Ventana de media móvil.

    Returns:
        DataFrame con fechas futuras y demanda pronosticada.
    """
    if horizon_days <= 0:
        raise ValueError("El horizonte debe ser mayor que cero.")

    if window_days <= 0:
        raise ValueError("La ventana debe ser mayor que cero.")

    effective_window = min(window_days, len(series))
    forecast_value = float(series.tail(effective_window).mean())

    future_dates = pd.date_range(
        start=series.index.max() + pd.Timedelta(days=1),
        periods=horizon_days,
        freq="D",
    )

    return pd.DataFrame(
        {
            "date": future_dates,
            "forecast_units": [round(forecast_value, 2)] * horizon_days,
            "method": "media_movil",
        }
    )


def forecast_simple_exponential_smoothing(
    series: pd.Series,
    horizon_days: int,
    smoothing_level: float = 0.35,
) -> pd.DataFrame:
    """
    Genera pronóstico mediante suavizamiento exponencial simple.

    Args:
        series: Serie temporal histórica diaria.
        horizon_days: Horizonte de predicción en días.
        smoothing_level: Factor alfa entre 0 y 1.

    Returns:
        DataFrame con fechas futuras y demanda pronosticada.
    """
    if horizon_days <= 0:
        raise ValueError("El horizonte debe ser mayor que cero.")

    if smoothing_level <= 0 or smoothing_level >= 1:
        raise ValueError("El parámetro smoothing_level debe estar entre 0 y 1.")

    model = SimpleExpSmoothing(series.astype(float), initialization_method="estimated")
    fitted_model = model.fit(smoothing_level=smoothing_level, optimized=False)
    forecast_values = fitted_model.forecast(horizon_days)

    future_dates = pd.date_range(
        start=series.index.max() + pd.Timedelta(days=1),
        periods=horizon_days,
        freq="D",
    )

    return pd.DataFrame(
        {
            "date": future_dates,
            "forecast_units": forecast_values.round(2).clip(lower=0).values,
            "method": "suavizamiento_exponencial",
        }
    )


def forecast_demand(
    sales_df: pd.DataFrame,
    sku: str,
    horizon_days: int = 30,
    method: ForecastMethod = "media_movil",
    window_days: int = 30,
    smoothing_level: float = 0.35,
) -> pd.DataFrame:
    """
    Ejecuta el pronóstico de demanda para un SKU.

    Args:
        sales_df: DataFrame histórico de ventas.
        sku: Código SKU.
        horizon_days: Horizonte de predicción.
        method: Método de predicción.
        window_days: Ventana para media móvil.
        smoothing_level: Alfa para suavizamiento exponencial.

    Returns:
        DataFrame con pronóstico futuro.

    Raises:
        ValueError: Si el método no está soportado.
    """
    series = build_daily_series(sales_df, sku)

    if method == "media_movil":
        forecast_df = forecast_moving_average(series, horizon_days, window_days)
    elif method == "suavizamiento_exponencial":
        forecast_df = forecast_simple_exponential_smoothing(series, horizon_days, smoothing_level)
    else:
        raise ValueError(f"Método de pronóstico no soportado: {method}")

    forecast_df["sku"] = sku
    logger.info("Pronóstico generado para %s con método %s.", sku, method)
    return forecast_df


def build_forecast_summary(forecast_df: pd.DataFrame) -> dict[str, float]:
    """
    Resume el pronóstico generado.

    Args:
        forecast_df: DataFrame de pronóstico.

    Returns:
        Diccionario con métricas del pronóstico.
    """
    if forecast_df.empty:
        raise ValueError("El pronóstico está vacío.")

    total_forecast = float(forecast_df["forecast_units"].sum().round(2))
    avg_forecast = float(forecast_df["forecast_units"].mean().round(2))
    max_forecast = float(forecast_df["forecast_units"].max().round(2))

    return {
        "forecast_total_units": total_forecast,
        "forecast_avg_daily_units": avg_forecast,
        "forecast_max_daily_units": max_forecast,
    }


def combine_history_and_forecast(series: pd.Series, forecast_df: pd.DataFrame) -> pd.DataFrame:
    """
    Combina histórico y pronóstico para visualización.

    Args:
        series: Serie histórica diaria.
        forecast_df: DataFrame de pronóstico.

    Returns:
        DataFrame en formato largo para graficación.
    """
    history_df = series.reset_index()
    history_df.columns = ["date", "units"]
    history_df["type"] = "Histórico"

    future_df = forecast_df[["date", "forecast_units"]].copy()
    future_df.columns = ["date", "units"]
    future_df["type"] = "Pronóstico"

    return pd.concat([history_df, future_df], ignore_index=True)
