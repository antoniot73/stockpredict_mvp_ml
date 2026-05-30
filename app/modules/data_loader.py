"""Funciones de carga, validación y preparación de datos semilla."""

from pathlib import Path
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def load_csv_file(path: Path) -> pd.DataFrame:
    """
    Carga un archivo CSV validando existencia y legibilidad.

    Args:
        path: Ruta del archivo CSV.

    Returns:
        DataFrame con el contenido del archivo.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el archivo está vacío o no puede leerse correctamente.
    """
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        logger.exception("Error al leer CSV: %s", path)
        raise ValueError(f"No fue posible leer el archivo: {path}") from exc

    if df.empty:
        raise ValueError(f"El archivo está vacío: {path}")

    logger.info("Archivo cargado correctamente: %s", path)
    return df


def validate_inventory_data(df: pd.DataFrame) -> bool:
    """
    Valida columnas, tipos y rangos mínimos del inventario inicial.

    Args:
        df: DataFrame de inventario.

    Returns:
        True si cumple la estructura mínima.

    Raises:
        ValueError: Si faltan columnas, hay duplicados o valores inválidos.
    """
    required_columns: set[str] = {
        "sku", "product_name", "category", "current_stock",
        "unit_cost", "lead_time_days", "service_level",
    }
    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        raise ValueError(f"Faltan columnas en inventario: {sorted(missing_columns)}")

    if df["sku"].duplicated().any():
        raise ValueError("Existen SKU duplicados en el inventario.")

    numeric_columns: list[str] = ["current_stock", "unit_cost", "lead_time_days", "service_level"]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
        if df[column].isna().any():
            raise ValueError(f"La columna {column} contiene valores no numéricos.")

    if (df["current_stock"] < 0).any():
        raise ValueError("El stock actual no puede ser negativo.")
    if (df["unit_cost"] <= 0).any():
        raise ValueError("El costo unitario debe ser mayor que cero.")
    if (df["lead_time_days"] <= 0).any():
        raise ValueError("El lead time debe ser mayor que cero.")
    if ((df["service_level"] <= 0) | (df["service_level"] >= 1)).any():
        raise ValueError("El nivel de servicio debe estar entre 0 y 1.")

    return True


def validate_sales_data(df: pd.DataFrame) -> bool:
    """
    Valida columnas, tipos y rangos mínimos del histórico de ventas.

    Args:
        df: DataFrame de ventas.

    Returns:
        True si cumple la estructura mínima.

    Raises:
        ValueError: Si faltan columnas o existen valores inválidos.
    """
    required_columns: set[str] = {"date", "sku", "units_sold"}
    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        raise ValueError(f"Faltan columnas en ventas: {sorted(missing_columns)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce")

    if df["date"].isna().any():
        raise ValueError("La columna date contiene fechas inválidas.")
    if df["units_sold"].isna().any():
        raise ValueError("La columna units_sold contiene valores no numéricos.")
    if (df["units_sold"] < 0).any():
        raise ValueError("Las unidades vendidas no pueden ser negativas.")

    return True


def prepare_seed_data(inventory_df: pd.DataFrame, sales_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepara datos semilla después de validar estructura y consistencia referencial.

    Args:
        inventory_df: DataFrame de inventario.
        sales_df: DataFrame de ventas.

    Returns:
        Tupla con inventario y ventas preparados.

    Raises:
        ValueError: Si ventas contiene SKU inexistentes en inventario.
    """
    validate_inventory_data(inventory_df)
    validate_sales_data(sales_df)

    inventory_df = inventory_df.copy()
    sales_df = sales_df.copy()

    inventory_df["sku"] = inventory_df["sku"].astype(str).str.strip()
    sales_df["sku"] = sales_df["sku"].astype(str).str.strip()
    sales_df["date"] = pd.to_datetime(sales_df["date"])

    unknown_skus = set(sales_df["sku"]).difference(set(inventory_df["sku"]))
    if unknown_skus:
        raise ValueError(f"Ventas contiene SKU no registrados: {sorted(unknown_skus)}")

    sales_df = sales_df.sort_values(["sku", "date"]).reset_index(drop=True)
    inventory_df = inventory_df.sort_values("sku").reset_index(drop=True)

    logger.info("Datos semilla preparados correctamente.")
    return inventory_df, sales_df
