"""Aplicación principal de StockPredict MVP en Streamlit."""

import logging

import pandas as pd
import plotly.express as px
import streamlit as st

from modules.analytics_service import (
    build_alerts_table,
    build_category_summary,
    build_executive_summary,
    calculate_abc_classification,
)
from modules.config import APP_TITLE, INVENTORY_FILE, SALES_FILE
from modules.data_loader import load_csv_file, prepare_seed_data
from modules.forecast_service import (
    build_daily_series,
    build_forecast_summary,
    combine_history_and_forecast,
    forecast_demand,
)
from modules.inventory_service import calculate_inventory_policy, summarize_inventory_policy
from modules.logger_config import configure_logger
from modules.ml_service import (
    predict_next_day_for_sku,
    train_demand_random_forest,
    train_sku_kmeans,
)

logger = logging.getLogger(__name__)


def configure_page() -> None:
    """
    Configura la página principal de Streamlit.

    Returns:
        None.
    """
    st.set_page_config(page_title=APP_TITLE, page_icon="📦", layout="wide")


def render_header() -> None:
    """
    Renderiza el encabezado de la aplicación.

    Returns:
        None.
    """
    st.title("📦 StockPredict MVP")
    st.caption("Inventarios, reorden, forecast estadístico y demostración de Machine Learning")


@st.cache_data(show_spinner=False)
def load_application_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Carga datos semilla, calcula política de inventario y clasificación ABC.

    Returns:
        Tupla con inventario, ventas, política de inventario y ABC.
    """
    inventory_raw_df = load_csv_file(INVENTORY_FILE)
    sales_raw_df = load_csv_file(SALES_FILE)
    inventory_df, sales_df = prepare_seed_data(inventory_raw_df, sales_raw_df)
    policy_df = calculate_inventory_policy(inventory_df, sales_df)
    abc_df = calculate_abc_classification(policy_df)
    return inventory_df, sales_df, policy_df, abc_df


@st.cache_resource(show_spinner=False)
def train_cached_random_forest(sales_df: pd.DataFrame):
    """
    Entrena y almacena en caché el modelo Random Forest.

    Args:
        sales_df: DataFrame de ventas.

    Returns:
        Resultado supervisado ML.
    """
    return train_demand_random_forest(sales_df)


@st.cache_resource(show_spinner=False)
def train_cached_kmeans(policy_df: pd.DataFrame, n_clusters: int):
    """
    Entrena y almacena en caché el modelo KMeans.

    Args:
        policy_df: DataFrame de política de inventario.
        n_clusters: Número de clústeres.

    Returns:
        Resultado no supervisado ML.
    """
    return train_sku_kmeans(policy_df, n_clusters=n_clusters)


def render_kpis(policy_df: pd.DataFrame, sales_df: pd.DataFrame, abc_df: pd.DataFrame) -> None:
    """
    Renderiza KPIs principales del sistema.

    Args:
        policy_df: DataFrame de política de inventario.
        sales_df: DataFrame de ventas.
        abc_df: DataFrame de clasificación ABC.

    Returns:
        None.
    """
    inventory_summary = summarize_inventory_policy(policy_df)
    executive_summary = build_executive_summary(policy_df, abc_df)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("SKU", inventory_summary["total_skus"])
    col2.metric("Atención", executive_summary["attention_skus"])
    col3.metric("Críticos", inventory_summary["critical_count"])
    col4.metric("Reorden urgente", inventory_summary["urgent_count"])
    col5.metric("Valor inventario", f"${inventory_summary['total_stock_value']:,.2f}")
    col6.metric("Cobertura prom.", f"{inventory_summary['avg_coverage_days']:.1f} días")

    st.caption(
        f"Histórico: {len(sales_df):,} registros | "
        f"{sales_df['date'].dt.to_period('M').nunique()} meses | "
        f"ABC: A={executive_summary['sku_a']}, B={executive_summary['sku_b']}, C={executive_summary['sku_c']}"
    )


def render_alerts(policy_df: pd.DataFrame) -> None:
    """
    Renderiza alertas operativas priorizadas.

    Args:
        policy_df: DataFrame de política de inventario.

    Returns:
        None.
    """
    st.subheader("🚨 Alertas de inventario")
    alerts_df = build_alerts_table(policy_df)

    if alerts_df.empty:
        st.success("No hay alertas activas. Todos los SKU están en estado normal.")
        return

    st.dataframe(alerts_df, use_container_width=True, hide_index=True)


def render_executive_charts(policy_df: pd.DataFrame, abc_df: pd.DataFrame) -> None:
    """
    Renderiza gráficos ejecutivos principales.

    Args:
        policy_df: DataFrame de política de inventario.
        abc_df: DataFrame con clasificación ABC.

    Returns:
        None.
    """
    st.subheader("📊 Panel ejecutivo")

    col1, col2 = st.columns(2)

    status_counts = (
        policy_df["inventory_status"]
        .value_counts()
        .rename_axis("inventory_status")
        .reset_index(name="count")
    )
    fig_status = px.bar(
        status_counts,
        x="inventory_status",
        y="count",
        title="SKU por estado de inventario",
        text="count",
    )
    col1.plotly_chart(fig_status, use_container_width=True)

    abc_counts = (
        abc_df["abc_class"]
        .value_counts()
        .rename_axis("abc_class")
        .reset_index(name="count")
        .sort_values("abc_class")
    )
    fig_abc = px.pie(
        abc_counts,
        values="count",
        names="abc_class",
        title="Distribución ABC por cantidad de SKU",
        hole=0.35,
    )
    col2.plotly_chart(fig_abc, use_container_width=True)

    category_summary = build_category_summary(policy_df)
    fig_category = px.bar(
        category_summary,
        x="category",
        y="stock_value",
        title="Valor de inventario por categoría",
        text="stock_value",
    )
    st.plotly_chart(fig_category, use_container_width=True)


def render_policy_table(policy_df: pd.DataFrame) -> None:
    """
    Renderiza la tabla principal de política de inventario.

    Args:
        policy_df: DataFrame de política de inventario.

    Returns:
        None.
    """
    st.subheader("📋 Política de inventario por SKU")

    col1, col2 = st.columns(2)
    status_filter = col1.multiselect(
        "Filtrar por estado",
        options=sorted(policy_df["inventory_status"].unique().tolist()),
        default=sorted(policy_df["inventory_status"].unique().tolist()),
    )
    category_filter = col2.multiselect(
        "Filtrar por categoría",
        options=sorted(policy_df["category"].unique().tolist()),
        default=sorted(policy_df["category"].unique().tolist()),
    )

    filtered_df = policy_df[
        policy_df["inventory_status"].isin(status_filter)
        & policy_df["category"].isin(category_filter)
    ]

    visible_columns = [
        "sku", "product_name", "category", "current_stock",
        "avg_daily_demand", "std_daily_demand", "lead_time_days",
        "service_level", "safety_stock", "lead_time_demand",
        "reorder_point", "coverage_days", "stock_value", "inventory_status",
    ]

    st.dataframe(filtered_df[visible_columns], use_container_width=True, hide_index=True)

    csv_data = filtered_df[visible_columns].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar política filtrada CSV",
        data=csv_data,
        file_name="stockpredict_politica_inventario.csv",
        mime="text/csv",
    )


def render_abc_table(abc_df: pd.DataFrame) -> None:
    """
    Renderiza tabla de clasificación ABC.

    Args:
        abc_df: DataFrame con clasificación ABC.

    Returns:
        None.
    """
    st.subheader("🏷️ Clasificación ABC")

    visible_columns = [
        "sku", "product_name", "category", "unit_cost", "total_units_sold",
        "sales_value", "value_share", "cumulative_share", "abc_class",
    ]

    st.dataframe(abc_df[visible_columns], use_container_width=True, hide_index=True)

    csv_data = abc_df[visible_columns].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar ABC CSV",
        data=csv_data,
        file_name="stockpredict_clasificacion_abc.csv",
        mime="text/csv",
    )


def render_sku_detail(policy_df: pd.DataFrame, sales_df: pd.DataFrame) -> None:
    """
    Renderiza análisis detallado por SKU.

    Args:
        policy_df: DataFrame de política de inventario.
        sales_df: DataFrame de ventas.

    Returns:
        None.
    """
    st.subheader("🔎 Detalle y pronóstico por SKU")

    selected_sku = st.selectbox(
        "Seleccione un SKU",
        policy_df["sku"].tolist(),
        format_func=lambda sku: f"{sku} — {policy_df.loc[policy_df['sku'] == sku, 'product_name'].iloc[0]}",
    )

    sku_policy = policy_df[policy_df["sku"] == selected_sku].iloc[0]
    sku_sales = sales_df[sales_df["sku"] == selected_sku]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Stock actual", int(sku_policy["current_stock"]))
    col2.metric("Demanda diaria prom.", f"{sku_policy['avg_daily_demand']:.2f}")
    col3.metric("Punto de reorden", f"{sku_policy['reorder_point']:.2f}")
    col4.metric("Estado", str(sku_policy["inventory_status"]))

    fig_history = px.line(
        sku_sales,
        x="date",
        y="units_sold",
        title=f"Ventas históricas — {selected_sku}",
    )
    st.plotly_chart(fig_history, use_container_width=True)

    with st.expander("Ver cálculo del SKU"):
        st.write(
            {
                "Demanda durante lead time": float(sku_policy["lead_time_demand"]),
                "Inventario de seguridad": float(sku_policy["safety_stock"]),
                "Punto de reorden": float(sku_policy["reorder_point"]),
                "Días de cobertura": float(sku_policy["coverage_days"]),
                "Z utilizado": float(sku_policy["z_score"]),
            }
        )

    render_forecast_panel(selected_sku, sales_df)


def render_forecast_panel(selected_sku: str, sales_df: pd.DataFrame) -> None:
    """
    Renderiza panel de pronóstico de demanda.

    Args:
        selected_sku: SKU seleccionado.
        sales_df: DataFrame histórico de ventas.

    Returns:
        None.
    """
    st.markdown("### Pronóstico estadístico de demanda")

    col1, col2, col3 = st.columns(3)

    method_label = col1.selectbox(
        "Método",
        options=["Media móvil", "Suavizamiento exponencial"],
    )
    horizon_days = col2.slider("Horizonte de predicción (días)", min_value=7, max_value=90, value=30, step=7)
    window_days = col3.slider("Ventana media móvil (días)", min_value=7, max_value=90, value=30, step=7)

    method = "media_movil" if method_label == "Media móvil" else "suavizamiento_exponencial"

    smoothing_level = 0.35
    if method == "suavizamiento_exponencial":
        smoothing_level = st.slider("Alfa suavizamiento exponencial", 0.05, 0.95, 0.35, 0.05)

    series = build_daily_series(sales_df, selected_sku)
    forecast_df = forecast_demand(
        sales_df=sales_df,
        sku=selected_sku,
        horizon_days=horizon_days,
        method=method,
        window_days=window_days,
        smoothing_level=smoothing_level,
    )

    summary = build_forecast_summary(forecast_df)
    c1, c2, c3 = st.columns(3)
    c1.metric("Demanda pronosticada total", f"{summary['forecast_total_units']:.2f}")
    c2.metric("Promedio diario pronosticado", f"{summary['forecast_avg_daily_units']:.2f}")
    c3.metric("Máximo diario pronosticado", f"{summary['forecast_max_daily_units']:.2f}")

    combined_df = combine_history_and_forecast(series.tail(120), forecast_df)

    fig = px.line(
        combined_df,
        x="date",
        y="units",
        color="type",
        markers=False,
        title=f"Histórico reciente y pronóstico — {selected_sku}",
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver tabla de pronóstico"):
        st.dataframe(forecast_df, use_container_width=True, hide_index=True)

    csv_data = forecast_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar pronóstico CSV",
        data=csv_data,
        file_name=f"stockpredict_pronostico_{selected_sku}.csv",
        mime="text/csv",
    )


def render_machine_learning_tab(policy_df: pd.DataFrame, sales_df: pd.DataFrame) -> None:
    """
    Renderiza sección demostrativa de Machine Learning.

    Args:
        policy_df: DataFrame de política de inventario.
        sales_df: DataFrame de ventas.

    Returns:
        None.
    """
    st.subheader("🤖 Demostración de Machine Learning")

    st.markdown(
        """
        Esta sección incorpora ML real al prototipo:
        - **Supervisado:** RandomForestRegressor para estimar demanda diaria.
        - **No supervisado:** KMeans para segmentar SKU por comportamiento logístico.
        """
    )

    st.markdown("### 1. ML Supervisado — Predicción de demanda con Random Forest")

    with st.spinner("Entrenando modelo supervisado..."):
        supervised_result = train_cached_random_forest(sales_df)

    metrics = supervised_result.metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("MAE", metrics["mae"])
    col2.metric("RMSE", metrics["rmse"])
    col3.metric("R²", metrics["r2"])
    col4.metric("Filas prueba", metrics["test_rows"])

    st.caption("MAE y RMSE miden error promedio. R² mide capacidad explicativa del modelo.")

    col_left, col_right = st.columns(2)
    with col_left:
        fig_importance = px.bar(
            supervised_result.feature_importance_df,
            x="importance",
            y="feature",
            orientation="h",
            title="Importancia de variables — Random Forest",
        )
        st.plotly_chart(fig_importance, use_container_width=True)

    with col_right:
        sample_pred_df = supervised_result.predictions_df.head(120)
        fig_pred = px.scatter(
            sample_pred_df,
            x="real_units",
            y="predicted_units",
            title="Ventas reales vs predichas",
            labels={"real_units": "Real", "predicted_units": "Predicho"},
        )
        st.plotly_chart(fig_pred, use_container_width=True)

    selected_sku = st.selectbox(
        "Predicción ML para siguiente día",
        policy_df["sku"].tolist(),
        format_func=lambda sku: f"{sku} — {policy_df.loc[policy_df['sku'] == sku, 'product_name'].iloc[0]}",
        key="ml_sku_prediction",
    )

    next_day_prediction = predict_next_day_for_sku(sales_df, selected_sku, supervised_result.model)
    st.metric("Demanda ML estimada para siguiente día", f"{next_day_prediction:.2f} unidades")

    with st.expander("Ver muestra de predicciones de validación"):
        st.dataframe(supervised_result.predictions_df.head(200), use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 2. ML No Supervisado — Segmentación de SKU con K-Means")

    n_clusters = st.slider("Número de clústeres", min_value=2, max_value=5, value=3)

    with st.spinner("Entrenando KMeans..."):
        clustering_result = train_cached_kmeans(policy_df, n_clusters)

    clustered_df = clustering_result.clustered_df
    profile_df = clustering_result.cluster_profile_df

    fig_cluster = px.scatter(
        clustered_df,
        x="avg_daily_demand",
        y="stock_value",
        color="cluster_label",
        size="total_units_sold",
        hover_data=["sku", "product_name", "category", "coverage_days"],
        title="Segmentación ML de SKU: demanda promedio vs valor de inventario",
    )
    st.plotly_chart(fig_cluster, use_container_width=True)

    st.markdown("#### Perfil de clústeres")
    st.dataframe(profile_df, use_container_width=True, hide_index=True)

    st.markdown("#### SKU segmentados")
    st.dataframe(clustered_df, use_container_width=True, hide_index=True)

    csv_data = clustered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar segmentación ML CSV",
        data=csv_data,
        file_name="stockpredict_segmentacion_ml.csv",
        mime="text/csv",
    )


def render_app() -> None:
    """
    Renderiza la aplicación completa.

    Returns:
        None.
    """
    try:
        _, sales_df, policy_df, abc_df = load_application_data()

        render_kpis(policy_df, sales_df, abc_df)
        st.divider()

        render_alerts(policy_df)
        st.divider()

        render_executive_charts(policy_df, abc_df)
        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs(
            ["Política de inventario", "Clasificación ABC", "Detalle SKU", "🤖 Machine Learning"]
        )
        with tab1:
            render_policy_table(policy_df)
        with tab2:
            render_abc_table(abc_df)
        with tab3:
            render_sku_detail(policy_df, sales_df)
        with tab4:
            render_machine_learning_tab(policy_df, sales_df)

    except FileNotFoundError as exc:
        logger.error("Archivo no encontrado: %s", exc)
        st.error(str(exc))
    except ValueError as exc:
        logger.error("Error de validación: %s", exc)
        st.error(str(exc))
    except Exception as exc:
        logger.exception("Error inesperado en la aplicación")
        st.error(f"Error inesperado: {exc}")


def main() -> None:
    """
    Ejecuta la aplicación principal.

    Returns:
        None.
    """
    configure_logger()
    configure_page()
    render_header()
    render_app()


if __name__ == "__main__":
    main()
