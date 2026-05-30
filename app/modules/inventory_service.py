"""Motor de inventario para StockPredict MVP."""

import logging
import math
from typing import Final

import pandas as pd

logger = logging.getLogger(__name__)

SERVICE_LEVEL_Z: Final[dict[float, float]] = {
    0.80: 0.84,
    0.85: 1.04,
    0.90: 1.28,
    0.95: 1.65,
    0.98: 2.05,
    0.99: 2.33,
}


def get_z_score(service_level: float) -> float:
    """
    Obtiene el valor Z aproximado para el nivel de servicio.

    Args:
        service_level: Nivel de servicio entre 0 y 1.

    Returns:
        Valor Z asociado o aproximado.

    Raises:
        ValueError: Si el nivel de servicio no está en rango válido.
    """
    if service_level <= 0 or service_level >= 1:
        raise ValueError("El nivel de servicio debe estar entre 0 y 1.")

    closest_level = min(SERVICE_LEVEL_Z.keys(), key=lambda level: abs(level - service_level))
    return SERVICE_LEVEL_Z[closest_level]


def calculate_sales_metrics(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula métricas históricas de demanda diaria por SKU.

    Args:
        sales_df: DataFrame con columnas sku, date y units_sold.

    Returns:
        DataFrame con demanda promedio, desviación y ventas totales.
    """
    if sales_df.empty:
        raise ValueError("El DataFrame de ventas está vacío.")

    required_columns = {"sku", "date", "units_sold"}
    missing_columns = required_columns.difference(sales_df.columns)
    if missing_columns:
        raise ValueError(f"Faltan columnas de ventas: {sorted(missing_columns)}")

    sales_df = sales_df.copy()
    sales_df["date"] = pd.to_datetime(sales_df["date"], errors="coerce")
    sales_df["units_sold"] = pd.to_numeric(sales_df["units_sold"], errors="coerce")

    if sales_df["date"].isna().any() or sales_df["units_sold"].isna().any():
        raise ValueError("Ventas contiene fechas o unidades inválidas.")

    metrics_df = (
        sales_df.groupby("sku", as_index=False)
        .agg(
            avg_daily_demand=("units_sold", "mean"),
            std_daily_demand=("units_sold", "std"),
            total_units_sold=("units_sold", "sum"),
            max_daily_demand=("units_sold", "max"),
            min_daily_demand=("units_sold", "min"),
            records_count=("units_sold", "count"),
        )
    )

    metrics_df["std_daily_demand"] = metrics_df["std_daily_demand"].fillna(0)
    logger.info("Métricas de demanda calculadas para %d SKU.", len(metrics_df))
    return metrics_df


def classify_inventory_status(row: pd.Series) -> str:
    """
    Clasifica el estado del inventario según stock y punto de reorden.

    Args:
        row: Fila con current_stock, reorder_point y safety_stock.

    Returns:
        Estado textual del inventario.
    """
    current_stock = float(row["current_stock"])
    reorder_point = float(row["reorder_point"])
    safety_stock = float(row["safety_stock"])

    if current_stock <= safety_stock:
        return "Crítico"
    if current_stock <= reorder_point:
        return "Reorden urgente"
    if current_stock <= reorder_point * 1.25:
        return "Precaución"
    return "Normal"


def calculate_inventory_policy(inventory_df: pd.DataFrame, sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula política de inventario por SKU.

    Args:
        inventory_df: DataFrame de inventario.
        sales_df: DataFrame histórico de ventas.

    Returns:
        DataFrame enriquecido con métricas y alertas.

    Raises:
        ValueError: Si los datos no tienen estructura esperada.
    """
    if inventory_df.empty:
        raise ValueError("El DataFrame de inventario está vacío.")

    required_columns = {
        "sku", "product_name", "category", "current_stock",
        "unit_cost", "lead_time_days", "service_level",
    }
    missing_columns = required_columns.difference(inventory_df.columns)
    if missing_columns:
        raise ValueError(f"Faltan columnas de inventario: {sorted(missing_columns)}")

    metrics_df = calculate_sales_metrics(sales_df)
    policy_df = inventory_df.merge(metrics_df, on="sku", how="left")

    if policy_df["avg_daily_demand"].isna().any():
        missing_skus = policy_df.loc[policy_df["avg_daily_demand"].isna(), "sku"].tolist()
        raise ValueError(f"No existen ventas históricas para los SKU: {missing_skus}")

    numeric_columns = [
        "current_stock", "unit_cost", "lead_time_days", "service_level",
        "avg_daily_demand", "std_daily_demand",
    ]

    for column in numeric_columns:
        policy_df[column] = pd.to_numeric(policy_df[column], errors="coerce")

    if policy_df[numeric_columns].isna().any().any():
        raise ValueError("Existen valores no numéricos en columnas de inventario o demanda.")

    z_scores: list[float] = []
    safety_stocks: list[float] = []
    lead_time_demands: list[float] = []
    reorder_points: list[float] = []
    coverage_days: list[float] = []

    for _, row in policy_df.iterrows():
        z_score = get_z_score(float(row["service_level"]))
        lead_time = float(row["lead_time_days"])
        avg_demand = float(row["avg_daily_demand"])
        std_demand = float(row["std_daily_demand"])

        lead_time_demand = avg_demand * lead_time
        safety_stock = z_score * std_demand * math.sqrt(lead_time)
        reorder_point = lead_time_demand + safety_stock
        coverage = float(row["current_stock"]) / avg_demand if avg_demand > 0 else 0.0

        z_scores.append(z_score)
        safety_stocks.append(safety_stock)
        lead_time_demands.append(lead_time_demand)
        reorder_points.append(reorder_point)
        coverage_days.append(coverage)

    policy_df["z_score"] = z_scores
    policy_df["lead_time_demand"] = lead_time_demands
    policy_df["safety_stock"] = safety_stocks
    policy_df["reorder_point"] = reorder_points
    policy_df["coverage_days"] = coverage_days
    policy_df["stock_value"] = policy_df["current_stock"] * policy_df["unit_cost"]
    policy_df["inventory_status"] = policy_df.apply(classify_inventory_status, axis=1)

    rounded_columns = [
        "avg_daily_demand", "std_daily_demand", "lead_time_demand",
        "safety_stock", "reorder_point", "coverage_days", "stock_value",
    ]
    policy_df[rounded_columns] = policy_df[rounded_columns].round(2)

    logger.info("Política de inventario calculada para %d SKU.", len(policy_df))
    return policy_df


def summarize_inventory_policy(policy_df: pd.DataFrame) -> dict[str, float | int]:
    """
    Calcula indicadores ejecutivos de la política de inventario.

    Args:
        policy_df: DataFrame de política de inventario.

    Returns:
        Diccionario con KPIs principales.
    """
    if policy_df.empty:
        raise ValueError("La política de inventario está vacía.")

    return {
        "total_skus": int(len(policy_df)),
        "critical_count": int((policy_df["inventory_status"] == "Crítico").sum()),
        "urgent_count": int((policy_df["inventory_status"] == "Reorden urgente").sum()),
        "warning_count": int((policy_df["inventory_status"] == "Precaución").sum()),
        "total_stock_value": float(policy_df["stock_value"].sum().round(2)),
        "avg_coverage_days": float(policy_df["coverage_days"].mean().round(2)),
    }
