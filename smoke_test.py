"""Smoke test de StockPredict MVP.

Ejecuta validaciones básicas sin abrir Streamlit.
"""

import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
APP_DIR = PROJECT_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from modules.analytics_service import calculate_abc_classification
from modules.config import INVENTORY_FILE, SALES_FILE
from modules.data_loader import load_csv_file, prepare_seed_data
from modules.forecast_service import forecast_demand
from modules.inventory_service import calculate_inventory_policy, summarize_inventory_policy
from modules.logger_config import configure_logger
from modules.ml_service import train_demand_random_forest, train_sku_kmeans


def main() -> None:
    """
    Ejecuta prueba rápida de carga, cálculos, pronóstico y ML.

    Returns:
        None.
    """
    configure_logger()
    logger = logging.getLogger(__name__)

    inventory_df, sales_df = prepare_seed_data(
        load_csv_file(INVENTORY_FILE),
        load_csv_file(SALES_FILE),
    )
    policy_df = calculate_inventory_policy(inventory_df, sales_df)
    abc_df = calculate_abc_classification(policy_df)
    summary = summarize_inventory_policy(policy_df)

    first_sku = inventory_df["sku"].iloc[0]
    forecast_df = forecast_demand(sales_df, first_sku, horizon_days=7)

    supervised_result = train_demand_random_forest(sales_df)
    clustering_result = train_sku_kmeans(policy_df, n_clusters=3)

    logger.info("Smoke test OK.")
    print("=== STOCKPREDICT SMOKE TEST ===")
    print(f"SKU inventario: {len(inventory_df)}")
    print(f"Registros ventas: {len(sales_df)}")
    print(f"Política calculada: {len(policy_df)} SKU")
    print(f"ABC calculado: {len(abc_df)} SKU")
    print(f"Resumen: {summary}")
    print(f"Pronóstico {first_sku}: {len(forecast_df)} días")
    print(f"ML supervisado MAE: {supervised_result.metrics['mae']}")
    print(f"ML no supervisado clústeres: {len(clustering_result.cluster_profile_df)}")
    print("Resultado: OK")


if __name__ == "__main__":
    main()
