"""Servicios demostrativos de Machine Learning para StockPredict MVP.

Incluye:
- ML supervisado: RandomForestRegressor para predicción de demanda diaria.
- ML no supervisado: KMeans para segmentación automática de SKU.
"""

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


@dataclass
class SupervisedMLResult:
    """
    Resultado del modelo supervisado de demanda.

    Attributes:
        model: Modelo entrenado.
        metrics: Métricas de evaluación.
        predictions_df: DataFrame con predicciones de validación.
        feature_importance_df: Importancia de variables.
    """

    model: RandomForestRegressor
    metrics: dict[str, float]
    predictions_df: pd.DataFrame
    feature_importance_df: pd.DataFrame


@dataclass
class ClusteringMLResult:
    """
    Resultado del modelo no supervisado de segmentación SKU.

    Attributes:
        model: Modelo KMeans entrenado.
        scaler: Escalador usado.
        clustered_df: DataFrame con clústeres asignados.
        cluster_profile_df: Perfil promedio por clúster.
    """

    model: KMeans
    scaler: StandardScaler
    clustered_df: pd.DataFrame
    cluster_profile_df: pd.DataFrame


def create_supervised_features(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea variables predictoras para modelo supervisado de demanda.

    Args:
        sales_df: DataFrame de ventas con date, sku y units_sold.

    Returns:
        DataFrame con variables de calendario, rezagos y medias móviles.

    Raises:
        ValueError: Si faltan columnas requeridas.
    """
    required_columns = {"date", "sku", "units_sold"}
    missing_columns = required_columns.difference(sales_df.columns)
    if missing_columns:
        raise ValueError(f"Faltan columnas para ML supervisado: {sorted(missing_columns)}")

    df = sales_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce")

    if df["date"].isna().any() or df["units_sold"].isna().any():
        raise ValueError("Ventas contiene fechas o unidades inválidas para ML.")

    df = df.sort_values(["sku", "date"]).reset_index(drop=True)

    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    df["sku_code"] = df["sku"].astype("category").cat.codes

    df["lag_1"] = df.groupby("sku")["units_sold"].shift(1)
    df["lag_7"] = df.groupby("sku")["units_sold"].shift(7)
    df["rolling_mean_7"] = (
        df.groupby("sku")["units_sold"]
        .shift(1)
        .rolling(window=7, min_periods=3)
        .mean()
        .reset_index(level=0, drop=True)
    )
    df["rolling_mean_30"] = (
        df.groupby("sku")["units_sold"]
        .shift(1)
        .rolling(window=30, min_periods=7)
        .mean()
        .reset_index(level=0, drop=True)
    )

    df = df.dropna().reset_index(drop=True)
    logger.info("Features supervisadas creadas: %d registros.", len(df))
    return df


def train_demand_random_forest(sales_df: pd.DataFrame, random_state: int = 42) -> SupervisedMLResult:
    """
    Entrena RandomForestRegressor para predecir unidades vendidas.

    Args:
        sales_df: DataFrame histórico de ventas.
        random_state: Semilla de reproducibilidad.

    Returns:
        Resultado del modelo supervisado.
    """
    feature_df = create_supervised_features(sales_df)

    feature_columns = [
        "sku_code",
        "day_of_week",
        "day_of_month",
        "month",
        "is_weekend",
        "lag_1",
        "lag_7",
        "rolling_mean_7",
        "rolling_mean_30",
    ]

    X = feature_df[feature_columns]
    y = feature_df["units_sold"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=random_state,
        shuffle=True,
    )

    model = RandomForestRegressor(
        n_estimators=120,
        max_depth=12,
        min_samples_leaf=2,
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = r2_score(y_test, y_pred)

    metrics = {
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4),
        "r2": round(float(r2), 4),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
    }

    predictions_df = pd.DataFrame(
        {
            "real_units": y_test.values,
            "predicted_units": np.round(y_pred, 2),
        }
    )
    predictions_df["absolute_error"] = (predictions_df["real_units"] - predictions_df["predicted_units"]).abs()

    feature_importance_df = pd.DataFrame(
        {
            "feature": feature_columns,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)
    feature_importance_df["importance"] = feature_importance_df["importance"].round(4)

    logger.info("RandomForestRegressor entrenado. MAE=%.4f RMSE=%.4f R2=%.4f", mae, rmse, r2)

    return SupervisedMLResult(
        model=model,
        metrics=metrics,
        predictions_df=predictions_df,
        feature_importance_df=feature_importance_df,
    )


def predict_next_day_for_sku(
    sales_df: pd.DataFrame,
    sku: str,
    model: RandomForestRegressor,
) -> float:
    """
    Predice la demanda del siguiente día para un SKU usando el modelo ML.

    Args:
        sales_df: DataFrame histórico de ventas.
        sku: SKU seleccionado.
        model: Modelo RandomForest entrenado.

    Returns:
        Predicción de unidades para el siguiente día.

    Raises:
        ValueError: Si no hay suficientes datos del SKU.
    """
    feature_df = create_supervised_features(sales_df)
    sku_df = feature_df[feature_df["sku"] == sku].sort_values("date")

    if sku_df.empty:
        raise ValueError(f"No hay suficientes datos para predecir el SKU {sku}.")

    last_row = sku_df.iloc[-1]
    next_date = pd.to_datetime(last_row["date"]) + pd.Timedelta(days=1)

    feature_row = pd.DataFrame(
        {
            "sku_code": [last_row["sku_code"]],
            "day_of_week": [next_date.dayofweek],
            "day_of_month": [next_date.day],
            "month": [next_date.month],
            "is_weekend": [int(next_date.dayofweek in [5, 6])],
            "lag_1": [last_row["units_sold"]],
            "lag_7": [last_row["lag_7"]],
            "rolling_mean_7": [sku_df["units_sold"].tail(7).mean()],
            "rolling_mean_30": [sku_df["units_sold"].tail(30).mean()],
        }
    )

    prediction = float(model.predict(feature_row)[0])
    return round(max(prediction, 0.0), 2)


def prepare_clustering_features(policy_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara variables para segmentación no supervisada de SKU.

    Args:
        policy_df: DataFrame de política de inventario.

    Returns:
        DataFrame con variables numéricas para clustering.

    Raises:
        ValueError: Si faltan columnas necesarias.
    """
    required_columns = {
        "sku",
        "product_name",
        "category",
        "avg_daily_demand",
        "std_daily_demand",
        "total_units_sold",
        "stock_value",
        "coverage_days",
        "reorder_point",
    }
    missing_columns = required_columns.difference(policy_df.columns)
    if missing_columns:
        raise ValueError(f"Faltan columnas para KMeans: {sorted(missing_columns)}")

    feature_df = policy_df[
        [
            "sku",
            "product_name",
            "category",
            "avg_daily_demand",
            "std_daily_demand",
            "total_units_sold",
            "stock_value",
            "coverage_days",
            "reorder_point",
        ]
    ].copy()

    numeric_columns = [
        "avg_daily_demand",
        "std_daily_demand",
        "total_units_sold",
        "stock_value",
        "coverage_days",
        "reorder_point",
    ]

    for column in numeric_columns:
        feature_df[column] = pd.to_numeric(feature_df[column], errors="coerce")

    if feature_df[numeric_columns].isna().any().any():
        raise ValueError("Existen valores no numéricos para clustering.")

    return feature_df


def interpret_cluster(row: pd.Series, demand_median: float, value_median: float) -> str:
    """
    Interpreta clúster de SKU desde una perspectiva logística.

    Args:
        row: Fila con perfil promedio del clúster.
        demand_median: Mediana global de demanda.
        value_median: Mediana global de valor.

    Returns:
        Etiqueta interpretativa.
    """
    if row["avg_daily_demand"] >= demand_median and row["stock_value"] >= value_median:
        return "Alta rotación / Alto valor"
    if row["avg_daily_demand"] >= demand_median:
        return "Alta rotación / Valor medio"
    if row["stock_value"] >= value_median:
        return "Baja rotación / Alto capital"
    return "Baja rotación / Bajo valor"


def train_sku_kmeans(policy_df: pd.DataFrame, n_clusters: int = 3, random_state: int = 42) -> ClusteringMLResult:
    """
    Entrena KMeans para segmentar SKU según comportamiento logístico.

    Args:
        policy_df: DataFrame de política de inventario.
        n_clusters: Número de clústeres.
        random_state: Semilla de reproducibilidad.

    Returns:
        Resultado de clustering.
    """
    if n_clusters < 2:
        raise ValueError("KMeans requiere al menos 2 clústeres.")

    feature_df = prepare_clustering_features(policy_df)

    numeric_columns = [
        "avg_daily_demand",
        "std_daily_demand",
        "total_units_sold",
        "stock_value",
        "coverage_days",
        "reorder_point",
    ]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(feature_df[numeric_columns])

    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=20)
    clusters = model.fit_predict(X_scaled)

    clustered_df = feature_df.copy()
    clustered_df["ml_cluster"] = clusters

    cluster_profile_df = (
        clustered_df.groupby("ml_cluster", as_index=False)
        .agg(
            sku_count=("sku", "count"),
            avg_daily_demand=("avg_daily_demand", "mean"),
            std_daily_demand=("std_daily_demand", "mean"),
            total_units_sold=("total_units_sold", "mean"),
            stock_value=("stock_value", "mean"),
            coverage_days=("coverage_days", "mean"),
            reorder_point=("reorder_point", "mean"),
        )
    )

    demand_median = float(cluster_profile_df["avg_daily_demand"].median())
    value_median = float(cluster_profile_df["stock_value"].median())

    labels: list[str] = []
    for _, row in cluster_profile_df.iterrows():
        labels.append(interpret_cluster(row, demand_median, value_median))

    cluster_profile_df["cluster_label"] = labels

    clustered_df = clustered_df.merge(
        cluster_profile_df[["ml_cluster", "cluster_label"]],
        on="ml_cluster",
        how="left",
    )

    round_columns = [
        "avg_daily_demand",
        "std_daily_demand",
        "total_units_sold",
        "stock_value",
        "coverage_days",
        "reorder_point",
    ]
    clustered_df[round_columns] = clustered_df[round_columns].round(2)
    cluster_profile_df[round_columns] = cluster_profile_df[round_columns].round(2)

    logger.info("KMeans entrenado con %d clústeres.", n_clusters)

    return ClusteringMLResult(
        model=model,
        scaler=scaler,
        clustered_df=clustered_df,
        cluster_profile_df=cluster_profile_df,
    )
