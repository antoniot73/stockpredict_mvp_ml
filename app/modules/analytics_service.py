"""Servicios analíticos para dashboard ejecutivo de StockPredict MVP."""

import logging
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_abc_classification(policy_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula clasificación ABC usando el valor económico de ventas históricas.

    Args:
        policy_df: DataFrame con política de inventario y total_units_sold.

    Returns:
        DataFrame con columnas de contribución acumulada y clase ABC.

    Raises:
        ValueError: Si faltan columnas necesarias.
    """
    required_columns = {"sku", "product_name", "category", "unit_cost", "total_units_sold"}
    missing_columns = required_columns.difference(policy_df.columns)
    if missing_columns:
        raise ValueError(f"Faltan columnas para ABC: {sorted(missing_columns)}")

    abc_df = policy_df.copy()
    abc_df["sales_value"] = abc_df["unit_cost"] * abc_df["total_units_sold"]
    abc_df = abc_df.sort_values("sales_value", ascending=False).reset_index(drop=True)

    total_value = abc_df["sales_value"].sum()
    if total_value <= 0:
        raise ValueError("El valor total de ventas debe ser mayor que cero para ABC.")

    abc_df["value_share"] = abc_df["sales_value"] / total_value
    abc_df["cumulative_share"] = abc_df["value_share"].cumsum()

    classes: list[str] = []
    for share in abc_df["cumulative_share"]:
        if share <= 0.80:
            classes.append("A")
        elif share <= 0.95:
            classes.append("B")
        else:
            classes.append("C")

    abc_df["abc_class"] = classes

    rounded_columns = ["sales_value", "value_share", "cumulative_share"]
    abc_df[rounded_columns] = abc_df[rounded_columns].round(4)

    logger.info("Clasificación ABC calculada para %d SKU.", len(abc_df))
    return abc_df


def build_category_summary(policy_df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye resumen ejecutivo por categoría.

    Args:
        policy_df: DataFrame de política de inventario.

    Returns:
        DataFrame agregado por categoría.
    """
    required_columns = {"category", "current_stock", "stock_value", "total_units_sold", "reorder_point"}
    missing_columns = required_columns.difference(policy_df.columns)
    if missing_columns:
        raise ValueError(f"Faltan columnas para resumen por categoría: {sorted(missing_columns)}")

    summary_df = (
        policy_df.groupby("category", as_index=False)
        .agg(
            sku_count=("sku", "count"),
            total_stock=("current_stock", "sum"),
            stock_value=("stock_value", "sum"),
            total_units_sold=("total_units_sold", "sum"),
            avg_reorder_point=("reorder_point", "mean"),
        )
        .sort_values("stock_value", ascending=False)
    )

    summary_df["stock_value"] = summary_df["stock_value"].round(2)
    summary_df["avg_reorder_point"] = summary_df["avg_reorder_point"].round(2)
    return summary_df


def build_alerts_table(policy_df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye tabla priorizada de alertas operativas.

    Args:
        policy_df: DataFrame de política de inventario.

    Returns:
        DataFrame con SKU que requieren atención.
    """
    priority_map = {
        "Crítico": 1,
        "Reorden urgente": 2,
        "Precaución": 3,
        "Normal": 4,
    }

    alerts_df = policy_df.copy()
    alerts_df["priority"] = alerts_df["inventory_status"].map(priority_map).fillna(5)

    alerts_df = alerts_df[alerts_df["inventory_status"] != "Normal"]
    alerts_df = alerts_df.sort_values(["priority", "coverage_days", "reorder_point"], ascending=[True, True, False])

    visible_columns = [
        "priority",
        "sku",
        "product_name",
        "category",
        "current_stock",
        "reorder_point",
        "safety_stock",
        "coverage_days",
        "inventory_status",
    ]

    return alerts_df[visible_columns].reset_index(drop=True)


def build_executive_summary(policy_df: pd.DataFrame, abc_df: pd.DataFrame) -> dict[str, float | int]:
    """
    Calcula resumen ejecutivo combinado.

    Args:
        policy_df: DataFrame de política de inventario.
        abc_df: DataFrame con clasificación ABC.

    Returns:
        Diccionario con KPIs analíticos.
    """
    return {
        "sku_a": int((abc_df["abc_class"] == "A").sum()),
        "sku_b": int((abc_df["abc_class"] == "B").sum()),
        "sku_c": int((abc_df["abc_class"] == "C").sum()),
        "sales_value_total": float(abc_df["sales_value"].sum().round(2)),
        "normal_skus": int((policy_df["inventory_status"] == "Normal").sum()),
        "attention_skus": int((policy_df["inventory_status"] != "Normal").sum()),
    }
