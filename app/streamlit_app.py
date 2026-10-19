import plotly.express as px
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import requests
import os

# ------------------------------------------------------------
# 1. CONFIGURACIÓN GENERAL
# ------------------------------------------------------------

st.set_page_config(
    page_title="Taxis NYC | Decisiones basadas en datos",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


# 13.7.2 — CLIENTE HTTP FASTAPI

def obtener_url_api():
    """
    Obtiene la dirección de FastAPI.

    En Colab utiliza localhost.
    En producción podrá configurarse mediante
    la variable de entorno API_URL o st.secrets.
    """
    url = os.environ.get("API_URL")

    if not url:
        try:
            url = st.secrets.get("API_URL")
        except Exception:
            url = None

    return (url or "http://127.0.0.1:8000").rstrip("/")


@st.cache_data(ttl=300, show_spinner=False)
def consultar_info_api(url_api):
    """
    Consulta las zonas, fechas y cuantiles disponibles.
    La respuesta se almacena temporalmente en caché.
    """
    respuesta = requests.get(
        f"{url_api}/info",
        timeout=30
    )
    respuesta.raise_for_status()
    return respuesta.json()


@st.cache_data(ttl=300, show_spinner=False)
def consultar_pronostico_api(url_api, zona_id, fecha):
    """
    Solicita a FastAPI los 24 pronósticos horarios
    para una zona y fecha específicas.
    """
    respuesta = requests.get(
        f"{url_api}/pronostico",
        params={
            "zona_id": int(zona_id),
            "fecha": str(fecha)
        },
        timeout=60
    )
    respuesta.raise_for_status()
    return respuesta.json()


def convertir_pronostico_dataframe(respuesta_api):
    """
    Convierte la respuesta JSON de FastAPI
    en un DataFrame para los gráficos de Streamlit.
    """
    registros = []

    for registro in respuesta_api["pronosticos"]:
        fila = {
            "hora": pd.to_datetime(registro["hora"]),
            "real": registro.get("real"),
            "hace_una_semana": registro.get(
                "hace_una_semana"
            )
        }

        fila.update(registro["cuantiles"])
        registros.append(fila)

    return pd.DataFrame(registros)



# ------------------------------------------------------------
# 2. CARGA DE DATOS
# ------------------------------------------------------------

@st.cache_data
def cargar_datos():

    zonas = pd.read_csv(
        DATA_DIR / "zonas_pronostico.csv"
    )

    segmentos = pd.read_csv(
        DATA_DIR / "segmentos_zonas.csv"
    )

    despacho = pd.read_csv(
        DATA_DIR / "plan_despacho_2024-02-01.csv",
        parse_dates=["hora"]
    )

    ficha = (
        DATA_DIR / "model_card.md"
    ).read_text(encoding="utf-8")

    return zonas, segmentos, despacho, ficha


zonas, segmentos, despacho, ficha = cargar_datos()

# ------------------------------------------------------------
# 3. BARRA LATERAL
# ------------------------------------------------------------

with st.sidebar:

    st.title("🚕 Taxis NYC")

    st.caption(
        "Una app para quien toma decisiones"
    )

    st.divider()

    pagina = st.radio(
        "Explorar módulos",
        [
            "Inicio",
            "Pronóstico de demanda",
            "Segmentación de zonas",
            "Decisiones de despacho",
            "Ficha del modelo"
        ]
    )

    st.divider()

    # MEJORA 13.3 — STREAMLIT AVANZADO
    if st.button("Verificar datos cargados"):
        st.toast(
            f"Datos disponibles: "
            f"{despacho['PULocationID'].nunique()} zonas "
            f"y {len(despacho):,} pronósticos.",
            icon="✅"
        )

    st.caption(
        "Datos históricos: enero de 2024"
    )

    st.caption(
        "Pronóstico futuro: 1 de febrero de 2024"
    )

# ------------------------------------------------------------
# 4. PÁGINA DE INICIO
# ------------------------------------------------------------

if pagina == "Inicio":

    st.title("Taxis NYC")
    st.subheader(
        "Inteligencia de datos para decisiones de despacho"
    )

    st.write(
        "Esta aplicación integra pronósticos "
        "probabilísticos, segmentación de zonas "
        "y análisis de costos operativos para "
        "apoyar la planificación de taxis "
        "en Nueva York."
    )

    st.divider()

    # Indicadores principales.
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Zonas pronosticadas",
        despacho["PULocationID"].nunique()
    )

    col2.metric(
        "Zonas segmentadas",
        segmentos["PULocationID"].nunique()
    )

    col3.metric(
        "Segmentos operativos",
        segmentos["cluster"].nunique()
    )

    col4.metric(
        "Pronósticos futuros",
        len(despacho)
    )

    st.divider()

    st.subheader("¿Qué puedes explorar?")

    col_a, col_b = st.columns(2)

    with col_a:

        st.markdown(
            "#### 📈 Pronóstico de demanda"
        )

        st.write(
            "Consulta los cuantiles de demanda "
            "por zona y hora."
        )

        st.markdown(
            "#### 🗺️ Segmentación de zonas"
        )

        st.write(
            "Explora los perfiles operativos "
            "identificados mediante KMeans."
        )

    with col_b:

        st.markdown(
            "#### 🚖 Decisiones de despacho"
        )

        st.write(
            "Compara recomendaciones de taxis "
            "según diferentes costos operativos."
        )

        st.markdown(
            "#### 📄 Ficha del modelo"
        )

        st.write(
            "Revisa métricas, supuestos "
            "y limitaciones del sistema."
        )

    st.info(
        "Los resultados son simulaciones "
        "de apoyo a decisiones y no representan "
        "asignaciones reales de vehículos."
    )

    with st.popover("¿Cómo interpretar los resultados?"):
        st.markdown(
            "**Pronóstico:** demanda estimada por hora y zona.\n\n"
            "**Segmentación:** perfiles operativos similares "
            "identificados con KMeans.\n\n"
            "**Despacho:** recomendaciones simuladas según "
            "los costos definidos por el usuario.\n\n"
            "La herramienta apoya decisiones; "
            "no ejecuta asignaciones reales."
        )

# ------------------------------------------------------------
# 5. MÓDULO DE PRONÓSTICO
# ------------------------------------------------------------


elif pagina == "Pronóstico de demanda":

    st.title("📈 Pronóstico de demanda")

    st.write(
        "Explora los pronósticos horarios de demanda "
        "por zona, compara los resultados con la "
        "demanda real y con la semana anterior."
    )

    # --------------------------------------------------------
    # A. CONSULTAR CATÁLOGO DESDE FASTAPI
    # --------------------------------------------------------

    url_api = obtener_url_api()

    try:
        info_api = consultar_info_api(url_api)

    except requests.RequestException as error:
        st.error(
            "No fue posible consultar FastAPI. "
            "Verifica que el servicio esté disponible."
        )
        st.caption(f"Detalle técnico: {error}")
        st.stop()

    zonas_api = info_api["zonas"]
    fechas_api = info_api["fechas_disponibles"]

    opciones_zona = {
        (
            f'{zona["nombre"]} — {zona["borough"]} '
            f'(ID {zona["zona_id"]})'
        ): int(zona["zona_id"])
        for zona in zonas_api
    }

    # --------------------------------------------------------
    # B. SELECCIÓN DE ZONA Y FECHA
    # --------------------------------------------------------

    columna_zona, columna_fecha = st.columns(2)

    with columna_zona:
        zona_seleccionada = st.selectbox(
            "Selecciona una zona",
            options=list(opciones_zona.keys()),
            key="zona_pronostico_api"
        )

    with columna_fecha:
        fecha_seleccionada = st.selectbox(
            "Selecciona una fecha",
            options=fechas_api,
            index=len(fechas_api) - 1,
            key="fecha_pronostico_api"
        )

    zona_id = opciones_zona[zona_seleccionada]

    # --------------------------------------------------------
    # C. CONSULTAR PRONÓSTICO DESDE FASTAPI
    # --------------------------------------------------------

    try:
        respuesta_api = consultar_pronostico_api(
            url_api,
            zona_id,
            fecha_seleccionada
        )

    except requests.RequestException as error:
        st.error(
            "No fue posible obtener el pronóstico "
            "para la zona y fecha seleccionadas."
        )
        st.caption(f"Detalle técnico: {error}")
        st.stop()

    datos_zona = convertir_pronostico_dataframe(
        respuesta_api
    )

    if datos_zona.empty:
        st.warning(
            "La API no devolvió registros para "
            "esta selección."
        )
        st.stop()

    datos_zona = (
        datos_zona.sort_values("hora").copy()
    )

    # --------------------------------------------------------
    # D. INDICADORES PRINCIPALES
    # --------------------------------------------------------

    demanda_p50 = datos_zona["p50"].sum()
    demanda_p80 = datos_zona["p80"].sum()

    hora_pico = datos_zona.loc[
        datos_zona["p50"].idxmax(),
        "hora"
    ]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Suma de medianas horarias (p50)",
        f"{demanda_p50:,.1f}"
    )

    col2.metric(
        "Suma de cuantiles horarios (p80)",
        f"{demanda_p80:,.1f}"
    )

    col3.metric(
        "Hora de mayor demanda p50",
        hora_pico.strftime("%H:%M")
    )

    st.caption(
        "Las sumas de cuantiles horarios son "
        "indicadores descriptivos; no representan "
        "cuantiles probabilísticos del total diario."
    )

    # --------------------------------------------------------
    # E. GRÁFICO PROBABILÍSTICO Y COMPARACIONES
    # --------------------------------------------------------

    st.subheader(
        "Demanda pronosticada por hora"
    )

    fig = go.Figure()

    # Límite inferior del intervalo.
    fig.add_trace(
        go.Scatter(
            x=datos_zona["hora"],
            y=datos_zona["p10"],
            mode="lines",
            name="p10",
            line=dict(
                color="rgba(65,105,225,0.25)"
            )
        )
    )

    # Límite superior y área de incertidumbre.
    fig.add_trace(
        go.Scatter(
            x=datos_zona["hora"],
            y=datos_zona["p90"],
            mode="lines",
            name="p90",
            fill="tonexty",
            fillcolor="rgba(65,105,225,0.15)",
            line=dict(
                color="rgba(65,105,225,0.25)"
            )
        )
    )

    # Pronóstico central.
    fig.add_trace(
        go.Scatter(
            x=datos_zona["hora"],
            y=datos_zona["p50"],
            mode="lines+markers",
            name="Mediana (p50)",
            line=dict(
                color="#17365D",
                width=3
            )
        )
    )

    # Referencia histórica semanal.
    fig.add_trace(
        go.Scatter(
            x=datos_zona["hora"],
            y=datos_zona["hace_una_semana"],
            mode="lines",
            name="Semana anterior",
            line=dict(
                color="#E69F00",
                width=2,
                dash="dash"
            )
        )
    )

    # Demanda real: solo si existen observaciones.
    if datos_zona["real"].notna().any():

        fig.add_trace(
            go.Scatter(
                x=datos_zona["hora"],
                y=datos_zona["real"],
                mode="lines+markers",
                name="Demanda real",
                line=dict(
                    color="#009E73",
                    width=2
                )
            )
        )

    fig.update_layout(
        xaxis_title="Hora del día",
        yaxis_title="Número de viajes",
        hovermode="x unified",
        height=470,
        legend_title="Series",
        margin=dict(
            l=20, r=20, t=30, b=20
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    if datos_zona["real"].notna().any():

        st.info(
            "Esta fecha pertenece al período de prueba. "
            "Puedes comparar el pronóstico con la demanda "
            "real y con la misma hora de la semana anterior."
        )

    else:

        st.info(
            "Esta fecha corresponde al período futuro. "
            "No existe demanda real disponible; "
            "se muestra la referencia semanal."
        )

    # --------------------------------------------------------
    # F. TABLA INTERACTIVA
    # --------------------------------------------------------

    st.subheader(
        "Detalle de pronósticos horarios"
    )

    columnas_cuantiles = [
        f"p{q}" for q in range(10, 100, 10)
    ]

    vista_cuantiles = st.segmented_control(
        "Nivel de detalle",
        options=[
            "Todos los cuantiles",
            "Cuantiles principales"
        ],
        default="Todos los cuantiles",
        key="vista_cuantiles"
    )

    if vista_cuantiles == "Cuantiles principales":
        columnas_visibles = [
            "p10", "p50", "p90"
        ]
    else:
        columnas_visibles = columnas_cuantiles

    columnas_tabla = (
        ["hora"]
        + columnas_visibles
        + ["real", "hace_una_semana"]
    )

    tabla_pronosticos = datos_zona[
        columnas_tabla
    ].copy()

    tabla_pronosticos["hora"] = (
        tabla_pronosticos["hora"]
        .dt.strftime("%H:%M")
    )

    configuracion_columnas = {
        "hora": st.column_config.TextColumn(
            "Hora",
            help="Hora local de Nueva York."
        ),
        "real": st.column_config.NumberColumn(
            "Demanda real",
            format="%.2f"
        ),
        "hace_una_semana": (
            st.column_config.NumberColumn(
                "Semana anterior",
                format="%.2f"
            )
        )
    }

    for nombre_cuantil in columnas_visibles:
        configuracion_columnas[nombre_cuantil] = (
            st.column_config.NumberColumn(
                nombre_cuantil,
                help=(
                    "Pronóstico horario del cuantil "
                    f"{nombre_cuantil}."
                ),
                format="%.2f"
            )
        )

    st.dataframe(
        tabla_pronosticos.round(2),
        column_config=configuracion_columnas,
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # G. ADVERTENCIA DE ZONA DESCONOCIDA
    # --------------------------------------------------------

    if zona_id == 264:

        st.warning(
            "La zona 264 no tiene ubicación "
            "geográfica identificada. Sus "
            "pronósticos pueden consultarse, "
            "pero no deben interpretarse como "
            "una recomendación de despacho "
            "hacia una ubicación conocida."
        )

    # --------------------------------------------------------
    # H. DESCARGA DE RESULTADOS
    # --------------------------------------------------------

    st.download_button(
        label="Descargar pronóstico de la zona (CSV)",
        data=datos_zona.to_csv(
            index=False
        ).encode("utf-8"),
        file_name=(
            f"pronostico_zona_{zona_id}_"
            f"{fecha_seleccionada}.csv"
        ),
        mime="text/csv"
    )

# ------------------------------------------------------------
# 6. MÓDULO DE SEGMENTACIÓN
# ------------------------------------------------------------


elif pagina == "Segmentación de zonas":

    st.title("🗺️ Segmentación de zonas")

    st.write(
        "Explora los seis perfiles operativos "
        "identificados mediante KMeans en "
        "100 zonas de Nueva York."
    )

    # --------------------------------------------------------
    # A. SELECTOR DE SEGMENTOS
    # --------------------------------------------------------

    nombres_segmentos = sorted(
        segmentos["nombre_cluster"].dropna().unique()
    )

    seleccion_segmentos = st.pills(
        "Selecciona los segmentos que deseas analizar",
        options=nombres_segmentos,
        default=nombres_segmentos,
        selection_mode="multi",
        key="filtro_segmentos"
    )

    datos_filtrados = segmentos[
        segmentos["nombre_cluster"].isin(
            seleccion_segmentos
        )
    ].copy()

    if datos_filtrados.empty:
        st.warning(
            "Selecciona al menos un segmento "
            "para visualizar los resultados."
        )
        st.stop()

    # --------------------------------------------------------
    # B. INDICADORES GENERALES
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Zonas seleccionadas",
        datos_filtrados["PULocationID"].nunique()
    )

    col2.metric(
        "Segmentos seleccionados",
        datos_filtrados["cluster"].nunique()
    )

    col3.metric(
        "Viajes registrados",
        f'{datos_filtrados["total_viajes"].sum():,.0f}'
    )

    col4.metric(
        "Proporción nocturna media",
        f'{datos_filtrados["proporcion_nocturna"].mean():.1%}'
    )

    st.caption(
        "Los viajes corresponden al período histórico "
        "analizado. La proporción nocturna media "
        "es el promedio simple entre zonas."
    )

    st.divider()

    # --------------------------------------------------------
    # C. VISUALIZACIÓN PCA
    # --------------------------------------------------------

    st.subheader(
        "Distribución de zonas en el espacio PCA"
    )

    import plotly.express as px

    fig_pca = px.scatter(
        datos_filtrados,
        x="PCA_1",
        y="PCA_2",
        color="nombre_cluster",
        hover_name="Zone",
        hover_data={
            "Borough": True,
            "total_viajes": ":,.0f",
            "distancia_mediana": ":.2f",
            "tarifa_mediana": ":.2f",
            "PCA_1": ":.2f",
            "PCA_2": ":.2f",
            "nombre_cluster": False
        },
        labels={
            "PCA_1": "Componente principal 1 (38.00%)",
            "PCA_2": "Componente principal 2 (30.56%)",
            "nombre_cluster": "Segmento"
        }
    )

    fig_pca.update_traces(
        marker=dict(size=10, opacity=0.8)
    )

    fig_pca.update_layout(
        height=520,
        legend_title="Segmentos",
        margin=dict(l=20, r=20, t=20, b=20)
    )

    st.plotly_chart(
        fig_pca,
        use_container_width=True
    )

    st.caption(
        "Las dos primeras componentes principales "
        "explican conjuntamente el 68.56% "
        "de la variabilidad."
    )

    # --------------------------------------------------------
    # D. COMPARACIÓN DE PERFILES OPERATIVOS
    # --------------------------------------------------------

    st.subheader(
        "Comparación de perfiles operativos"
    )

    resumen_segmentos = (
        datos_filtrados.groupby(
            ["cluster", "nombre_cluster"],
            observed=True
        )
        .agg(
            zonas=("PULocationID", "nunique"),
            viajes_totales=("total_viajes", "sum"),
            distancia_mediana_promedio=(
                "distancia_mediana", "mean"
            ),
            tarifa_mediana_promedio=(
                "tarifa_mediana", "mean"
            ),
            propina_mediana_promedio=(
                "propina_mediana", "mean"
            ),
            proporcion_nocturna_promedio=(
                "proporcion_nocturna", "mean"
            ),
            proporcion_fin_semana_promedio=(
                "proporcion_fin_semana", "mean"
            )
        )
        .reset_index()
        .sort_values("cluster")
    )

    st.dataframe(
        resumen_segmentos.round(3),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Los promedios de distancia, tarifa y propina "
        "son promedios de las medianas de cada zona; "
        "no son medianas calculadas sobre todos "
        "los viajes de cada segmento."
    )

    # --------------------------------------------------------
    # E. GRÁFICO COMPARATIVO DE ACTIVIDAD
    # --------------------------------------------------------

    st.subheader(
        "Actividad nocturna y de fin de semana"
    )

    comparacion_actividad = resumen_segmentos.melt(
        id_vars=["nombre_cluster"],
        value_vars=[
            "proporcion_nocturna_promedio",
            "proporcion_fin_semana_promedio"
        ],
        var_name="Indicador",
        value_name="Proporción"
    )

    comparacion_actividad["Indicador"] = (
        comparacion_actividad["Indicador"].replace({
            "proporcion_nocturna_promedio":
                "Actividad nocturna",
            "proporcion_fin_semana_promedio":
                "Actividad de fin de semana"
        })
    )

    fig_actividad = px.bar(
        comparacion_actividad,
        x="nombre_cluster",
        y="Proporción",
        color="Indicador",
        barmode="group",
        labels={
            "nombre_cluster": "Segmento"
        }
    )

    fig_actividad.update_layout(
        height=420,
        xaxis_tickangle=-25,
        yaxis_tickformat=".0%",
        margin=dict(l=20, r=20, t=20, b=20)
    )

    st.plotly_chart(
        fig_actividad,
        use_container_width=True
    )

    # --------------------------------------------------------
    # F. CONSULTA DE ZONAS POR SEGMENTO
    # --------------------------------------------------------

    st.subheader(
        "Detalle de las zonas seleccionadas"
    )

    columnas_detalle = [
        "PULocationID",
        "Borough",
        "Zone",
        "nombre_cluster",
        "total_viajes",
        "distancia_mediana",
        "tarifa_mediana",
        "propina_mediana",
        "proporcion_nocturna",
        "proporcion_fin_semana"
    ]

    tabla_zonas = datos_filtrados[
        columnas_detalle
    ].sort_values(
        ["nombre_cluster", "total_viajes"],
        ascending=[True, False]
    )

    st.dataframe(
        tabla_zonas.round(3),
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # G. DESCARGA DE RESULTADOS
    # --------------------------------------------------------

    st.download_button(
        label="Descargar zonas seleccionadas (CSV)",
        data=tabla_zonas.to_csv(
            index=False
        ).encode("utf-8"),
        file_name="segmentacion_zonas_nyc.csv",
        mime="text/csv"
    )

    st.info(
        "La segmentación identifica perfiles "
        "operativos similares. No debe interpretarse "
        "como una clasificación geográfica oficial "
        "ni como una recomendación automática "
        "de asignación de vehículos."
    )

# ------------------------------------------------------------
# 7. MÓDULO DE DESPACHO
# ------------------------------------------------------------


elif pagina == "Decisiones de despacho":

    import numpy as np

    st.title("🚖 Decisiones de despacho")

    st.write(
        "Compara estrategias de asignación de taxis "
        "según pronósticos probabilísticos, demanda "
        "histórica y costos operativos simulados."
    )

    # --------------------------------------------------------
    # A. CONFIGURACIÓN DE COSTOS
    # --------------------------------------------------------

    st.subheader("1. Configuración de costos")

    col_costo1, col_costo2 = st.columns(2)

    with col_costo1:
        costo_perdido = st.number_input(
            "Costo por pasajero no atendido ($)",
            min_value=0.0,
            max_value=1000.0,
            value=40.0,
            step=5.0,
            key="costo_perdido_api"
        )

    with col_costo2:
        costo_ocioso = st.number_input(
            "Costo por taxi ocioso ($)",
            min_value=0.0,
            max_value=1000.0,
            value=10.0,
            step=5.0,
            key="costo_ocioso_api"
        )

    if costo_perdido + costo_ocioso == 0:
        st.warning(
            "Ingresa al menos un costo mayor que cero."
        )
        st.stop()

    cuantil_objetivo = (
        costo_perdido /
        (costo_perdido + costo_ocioso)
    )

    cuantiles_disponibles = [
        q / 100 for q in range(10, 100, 10)
    ]

    cuantil_elegido = min(
        cuantiles_disponibles,
        key=lambda q: abs(q - cuantil_objetivo)
    )

    columna_cuantil = (
        f"p{int(round(cuantil_elegido * 100))}"
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Cuantil objetivo teórico",
        f"{cuantil_objetivo:.0%}"
    )

    col2.metric(
        "Cuantil disponible seleccionado",
        columna_cuantil
    )

    st.caption(
        "El cuantil recomendado es el disponible "
        "más cercano al objetivo teórico. "
        "La recomendación puede cambiar cuando "
        "se modifican los costos."
    )

    st.divider()

    # --------------------------------------------------------
    # B. CONSULTAR ZONAS Y FECHAS DESDE FASTAPI
    # --------------------------------------------------------

    st.subheader("2. Selección de zona y fecha")

    url_api = obtener_url_api()

    try:
        info_api = consultar_info_api(url_api)

    except requests.RequestException as error:
        st.error(
            "No fue posible consultar la API."
        )
        st.caption(f"Detalle técnico: {error}")
        st.stop()

    mapa_zonas = {
        (
            f'{zona["nombre"]} — {zona["borough"]} '
            f'(ID {zona["zona_id"]})'
        ): int(zona["zona_id"])
        for zona in info_api["zonas"]
    }

    col_zona, col_fecha = st.columns(2)

    with col_zona:
        zona_elegida = st.selectbox(
            "Selecciona una zona",
            options=list(mapa_zonas.keys()),
            key="zona_despacho_api"
        )

    with col_fecha:
        fecha_elegida = st.selectbox(
            "Selecciona una fecha",
            options=info_api["fechas_disponibles"],
            index=len(info_api["fechas_disponibles"]) - 1,
            key="fecha_despacho_api"
        )

    zona_id = mapa_zonas[zona_elegida]

    # --------------------------------------------------------
    # C. CONSULTAR PRONÓSTICO
    # --------------------------------------------------------

    try:
        respuesta_api = consultar_pronostico_api(
            url_api,
            zona_id,
            fecha_elegida
        )

    except requests.RequestException as error:
        st.error(
            "No fue posible obtener el pronóstico."
        )
        st.caption(f"Detalle técnico: {error}")
        st.stop()

    datos_zona = convertir_pronostico_dataframe(
        respuesta_api
    )

    if datos_zona.empty:
        st.warning("No hay datos para esta selección.")
        st.stop()

    datos_zona = (
        datos_zona.sort_values("hora").copy()
    )

    # --------------------------------------------------------
    # D. CALCULAR CAPACIDAD POR ESTRATEGIA
    # --------------------------------------------------------

    datos_zona["taxis_simulados"] = np.ceil(
        datos_zona[columna_cuantil]
    ).astype(int)

    datos_zona["taxis_p80"] = np.ceil(
        datos_zona["p80"]
    ).astype(int)

    datos_zona["taxis_p50"] = np.ceil(
        datos_zona["p50"]
    ).astype(int)

    datos_zona["taxis_semana"] = np.ceil(
        datos_zona["hace_una_semana"]
    ).astype(int)

    estrategias = {
        f"Recomendación {columna_cuantil}":
            "taxis_simulados",
        "p80": "taxis_p80",
        "p50": "taxis_p50",
        "Semana anterior": "taxis_semana"
    }

    # --------------------------------------------------------
    # E. INDICADORES DEL PLAN
    # --------------------------------------------------------

    st.subheader("3. Resultados de la simulación")

    total_recomendado = int(
        datos_zona["taxis_simulados"].sum()
    )

    total_p50 = int(
        datos_zona["taxis_p50"].sum()
    )

    total_semana = int(
        datos_zona["taxis_semana"].sum()
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Taxis-hora recomendados",
        f"{total_recomendado:,}"
    )

    col2.metric(
        "Referencia p50",
        f"{total_p50:,}"
    )

    col3.metric(
        "Referencia semana anterior",
        f"{total_semana:,}"
    )

    st.caption(
        "Los totales representan taxis-hora "
        "acumulados durante el día, no vehículos "
        "únicos necesarios."
    )

    # --------------------------------------------------------
    # F. GRÁFICO DE ALTERNATIVAS
    # --------------------------------------------------------

    st.subheader(
        "Comparación horaria de alternativas"
    )

    fig_despacho = go.Figure()

    for nombre, columna in estrategias.items():

        fig_despacho.add_trace(
            go.Scatter(
                x=datos_zona["hora"],
                y=datos_zona[columna],
                mode="lines",
                name=nombre
            )
        )

    fig_despacho.update_layout(
        xaxis_title="Hora",
        yaxis_title="Taxis recomendados",
        hovermode="x unified",
        height=450,
        margin=dict(
            l=20, r=20, t=20, b=20
        )
    )

    st.plotly_chart(
        fig_despacho,
        use_container_width=True
    )

    # --------------------------------------------------------
    # G. EVALUACIÓN DE COSTOS SIMULADOS
    # --------------------------------------------------------

    st.subheader(
        "4. Comparación de costos simulados"
    )

    hay_demanda_real = (
        datos_zona["real"].notna().all()
    )

    if hay_demanda_real:

        resultados = []

        for nombre, columna in estrategias.items():

            demanda = datos_zona["real"].to_numpy(
                dtype=float
            )

            taxis = datos_zona[columna].to_numpy(
                dtype=float
            )

            no_atendidos = np.maximum(
                demanda - taxis,
                0
            )

            ociosos = np.maximum(
                taxis - demanda,
                0
            )

            costo_total = (
                no_atendidos * costo_perdido
                + ociosos * costo_ocioso
            ).sum()

            resultados.append({
                "Estrategia": nombre,
                "Taxis-hora": int(taxis.sum()),
                "Costo simulado ($)": float(costo_total)
            })

        tabla_costos = pd.DataFrame(resultados)

        costo_referencia = float(
            tabla_costos.loc[
                tabla_costos["Estrategia"]
                == "Semana anterior",
                "Costo simulado ($)"
            ].iloc[0]
        )

        if costo_referencia > 0:

            tabla_costos["Variación vs. semana (%)"] = (
                (
                    tabla_costos["Costo simulado ($)"]
                    - costo_referencia
                )
                / costo_referencia
                * 100
            )

        else:

            tabla_costos["Variación vs. semana (%)"] = (
                np.nan
            )

        st.dataframe(
            tabla_costos.round(2),
            use_container_width=True,
            hide_index=True
        )

        mejor = tabla_costos.loc[
            tabla_costos["Costo simulado ($)"].idxmin()
        ]

        st.success(
            "Menor costo simulado para esta zona "
            f"y fecha: {mejor['Estrategia']} "
            f"(${mejor['Costo simulado ($)']:,.2f})."
        )

        st.caption(
            "Evaluación retrospectiva con demanda "
            "observada. Los costos son hipotéticos "
            "y no representan ahorros reales."
        )

    else:

        st.info(
            "Esta fecha no tiene demanda real "
            "disponible. Se muestran recomendaciones "
            "de capacidad, pero no es posible "
            "calcular costos observados."
        )

    # --------------------------------------------------------
    # H. PLAN HORARIO
    # --------------------------------------------------------

    st.subheader("5. Plan horario de despacho")

    columnas_plan = [
        "hora",
        columna_cuantil,
        "taxis_simulados",
        "taxis_p80",
        "taxis_p50",
        "taxis_semana",
        "real"
    ]

    tabla_plan = datos_zona[
        columnas_plan
    ].copy()

    tabla_plan["hora"] = (
        tabla_plan["hora"]
        .dt.strftime("%H:%M")
    )

    tabla_plan = tabla_plan.rename(
        columns={
            columna_cuantil: "Demanda pronosticada",
            "taxis_simulados": "Taxis recomendados",
            "taxis_p80": "Taxis p80",
            "taxis_p50": "Taxis p50",
            "taxis_semana": "Taxis semana anterior",
            "real": "Demanda real"
        }
    )

    st.dataframe(
        tabla_plan.round(2),
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # I. DESCARGA DEL PLAN
    # --------------------------------------------------------

    st.download_button(
        label="Descargar plan simulado (CSV)",
        data=tabla_plan.to_csv(
            index=False
        ).encode("utf-8"),
        file_name=(
            f"plan_despacho_zona_{zona_id}_"
            f"{fecha_elegida}_{columna_cuantil}.csv"
        ),
        mime="text/csv"
    )

    # --------------------------------------------------------
    # J. LIMITACIONES
    # --------------------------------------------------------

    if zona_id == 264:

        st.warning(
            "La zona 264 no tiene ubicación "
            "geográfica identificada. "
            "No debe interpretarse como una "
            "recomendación de despacho real."
        )

    st.caption(
        "El modelo no se vuelve a entrenar al "
        "cambiar los costos. La simulación no "
        "considera tiempos de desplazamiento, "
        "disponibilidad real de vehículos ni "
        "restricciones operativas adicionales."
    )


    # --------------------------------------------------------
    # K. EVALUACIÓN GLOBAL RETROSPECTIVA
    # --------------------------------------------------------

    st.divider()

    with st.expander(
        "📊 Evaluación global de estrategias "
        "(59 zonas · 25–31 enero)",
        expanded=False
    ):

        st.subheader(
            "Evaluación global de estrategias"
        )

        st.write(
            "Comparación retrospectiva de tres "
            "estrategias de despacho durante "
            "siete días y 59 zonas."
        )

        st.info(
            "Esta evaluación utiliza costos "
            "hipotéticos fijos de $40 por "
            "pasajero no atendido y $10 por "
            "taxi-hora ocioso. Los controles "
            "superiores no modifican estos "
            "resultados históricos."
        )

        global_df = pd.read_csv(
            DATA_DIR /
            "evaluacion_global_despacho.csv"
        )

        diario_df = pd.read_csv(
            DATA_DIR /
            "evaluacion_diaria_despacho.csv"
        )

        costo_p80 = float(
            global_df.loc[
                global_df["Estrategia"] == "p80",
                "Costo simulado ($)"
            ].iloc[0]
        )

        costo_p50 = float(
            global_df.loc[
                global_df["Estrategia"] == "p50",
                "Costo simulado ($)"
            ].iloc[0]
        )

        costo_semana = float(
            global_df.loc[
                global_df["Estrategia"]
                == "Semana anterior",
                "Costo simulado ($)"
            ].iloc[0]
        )

        diferencia = costo_semana - costo_p80

        reduccion = (
            diferencia / costo_semana * 100
            if costo_semana > 0
            else 0
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Costo simulado p80",
            f"${costo_p80:,.0f}"
        )

        col2.metric(
            "Costo simulado p50",
            f"${costo_p50:,.0f}"
        )

        col3.metric(
            "Referencia semanal",
            f"${costo_semana:,.0f}"
        )

        st.success(
            f"p80 presentó un costo simulado "
            f"{reduccion:.2f}% menor que "
            f"la referencia semanal, equivalente "
            f"a una diferencia de "
            f"${diferencia:,.0f}."
        )

        # ----------------------------------------------------
        # GRÁFICO 1: COSTOS GLOBALES
        # ----------------------------------------------------

        st.markdown(
            "#### Costos simulados acumulados"
        )

        fig_global = px.bar(
            global_df,
            x="Estrategia",
            y="Costo simulado ($)",
            text="Costo simulado ($)"
        )

        fig_global.update_traces(
            texttemplate="$%{text:,.0f}",
            textposition="outside"
        )

        fig_global.update_layout(
            xaxis_title="Estrategia",
            yaxis_title="Costo simulado ($)",
            showlegend=False,
            height=400
        )

        st.plotly_chart(
            fig_global,
            use_container_width=True
        )

        # ----------------------------------------------------
        # GRÁFICO 2: EVOLUCIÓN DIARIA
        # ----------------------------------------------------

        st.markdown(
            "#### Evolución diaria de costos"
        )

        diario_largo = diario_df.melt(
            id_vars="fecha",
            value_vars=[
                "p80",
                "p50",
                "Semana anterior"
            ],
            var_name="Estrategia",
            value_name="Costo simulado ($)"
        )

        fig_diario = px.line(
            diario_largo,
            x="fecha",
            y="Costo simulado ($)",
            color="Estrategia",
            markers=True
        )

        fig_diario.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Costo simulado ($)",
            hovermode="x unified",
            height=450
        )

        st.plotly_chart(
            fig_diario,
            use_container_width=True
        )

        # ----------------------------------------------------
        # TABLA COMPARATIVA
        # ----------------------------------------------------

        st.markdown(
            "#### Resultados globales detallados"
        )

        st.dataframe(
            global_df.round(2),
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # MEJOR ESTRATEGIA POR DÍA
        # ----------------------------------------------------

        st.markdown(
            "#### Estrategia de menor costo por día"
        )

        diario_df["Mejor estrategia"] = (
            diario_df[
                ["p80", "p50", "Semana anterior"]
            ].idxmin(axis=1)
        )

        st.dataframe(
            diario_df[
                ["fecha", "Mejor estrategia"]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Los resultados son simulaciones "
            "retrospectivas, no ahorros "
            "financieros realizados. "
            "No incluyen tiempos de traslado, "
            "disponibilidad de conductores ni "
            "otras restricciones operativas."
        )

# ------------------------------------------------------------
# 8. FICHA DEL MODELO
# ------------------------------------------------------------

elif pagina == "Ficha del modelo":

    st.title("📄 Ficha del modelo")

    st.markdown(ficha)
