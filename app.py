import streamlit as st
import geopandas as gpd
import leafmap.foliumap as leafmap
import plotly.express as px
from pathlib import Path

# =====================================================
# Configuración de la aplicación
# =====================================================
st.set_page_config(
    page_title="Reserva de la Biosfera de Calakmul",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 Reserva de la Biosfera de Calakmul")
st.markdown("### Áreas con mayor presencia de incendios forestales")

# =====================================================
# Rutas de datos
# =====================================================
DATA_DIR = Path("data")
RESERVA_PATH = DATA_DIR / "area_reserva_calakmul.gpkg"
INCENDIOS_PATH = DATA_DIR / "areas_con_mayor_presencia_de_incendios.gpkg"

# CRS geográfico para visualizar en el mapa
CRS_GEOGRAFICO = "EPSG:4326"

# CRS proyectado en metros, adecuado para Calakmul (UTM zona 16N)
# Se usa SOLO para calcular áreas correctamente (EPSG:3857 distorsiona áreas)
CRS_METROS = "EPSG:32616"

# =====================================================
# Cargar datos
# =====================================================
@st.cache_data
def cargar_datos():
    if not RESERVA_PATH.exists():
        st.error(f"No se encontró el archivo: {RESERVA_PATH}")
        st.stop()
    if not INCENDIOS_PATH.exists():
        st.error(f"No se encontró el archivo: {INCENDIOS_PATH}")
        st.stop()

    reserva = gpd.read_file(RESERVA_PATH)
    incendios = gpd.read_file(INCENDIOS_PATH)

    # Asignar CRS si no lo tienen, o reproyectar al CRS geográfico
    if reserva.crs is None:
        reserva = reserva.set_crs(CRS_GEOGRAFICO)
    else:
        reserva = reserva.to_crs(CRS_GEOGRAFICO)

    if incendios.crs is None:
        incendios = incendios.set_crs(CRS_GEOGRAFICO)
    else:
        incendios = incendios.to_crs(CRS_GEOGRAFICO)

    return reserva, incendios


with st.spinner("Cargando datos geoespaciales..."):
    reserva, incendios = cargar_datos()

# =====================================================
# Calcular áreas en un CRS proyectado (metros)
# =====================================================
reserva_utm = reserva.to_crs(CRS_METROS)
incendios_utm = incendios.to_crs(CRS_METROS)

area_reserva = reserva_utm.area.sum() / 10_000  # m² -> ha
incendios["Área (ha)"] = incendios_utm.area.values / 10_000
area_incendios = incendios["Área (ha)"].sum()
porcentaje = (area_incendios / area_reserva) * 100 if area_reserva > 0 else 0

# =====================================================
# Barra lateral
# =====================================================
st.sidebar.title("🗺️ Capas del mapa")
mostrar_reserva = st.sidebar.checkbox("Reserva de la Biosfera", value=True)
mostrar_incendios = st.sidebar.checkbox("Áreas con incendios", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🛰️ Estilo del mapa base")
basemap = st.sidebar.selectbox(
    "Elige un mapa base",
    ["SATELLITE", "ROADMAP", "TERRAIN", "HYBRID"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Acerca de esta app**

    Visualiza las áreas con mayor presencia de incendios
    forestales dentro de la Reserva de la Biosfera de Calakmul.
    """
)

# =====================================================
# Mapa
# =====================================================
st.header("🗺️ Mapa interactivo")

mapa = leafmap.Map()
mapa.add_basemap(basemap)

if mostrar_reserva:
    mapa.add_gdf(
        reserva,
        layer_name="Reserva de la Biosfera",
        style={"color": "blue", "fillOpacity": 0.05, "weight": 2},
    )

if mostrar_incendios:
    mapa.add_gdf(
        incendios,
        layer_name="Áreas con incendios",
        style={"color": "red", "fillColor": "orange", "fillOpacity": 0.5, "weight": 1},
    )

if not reserva.empty:
    mapa.zoom_to_gdf(reserva)

mapa.to_streamlit(height=700)

# =====================================================
# Indicadores
# =====================================================
st.header("📊 Indicadores")
c1, c2, c3 = st.columns(3)
c1.metric("Número de polígonos", len(incendios))
c2.metric("Área afectada (ha)", f"{area_incendios:,.2f}")
c3.metric("% de la reserva afectada", f"{porcentaje:.2f}%")

# =====================================================
# Gráfico
# =====================================================
st.header("📈 Área por polígono")

tabla_grafico = incendios.drop(columns="geometry").copy()
tabla_grafico["Polígono"] = range(1, len(tabla_grafico) + 1)

fig = px.bar(
    tabla_grafico,
    x="Polígono",
    y="Área (ha)",
    color="Área (ha)",
    title="Área de cada polígono de incendio",
    color_continuous_scale="OrRd",
)
fig.update_layout(xaxis_title="Polígono", yaxis_title="Área (ha)")
st.plotly_chart(fig, use_container_width=True)

# =====================================================
# Tabla
# =====================================================
st.header("📋 Tabla de atributos")
tabla = incendios.drop(columns="geometry")
st.dataframe(tabla, use_container_width=True)

# =====================================================
# Descargar CSV
# =====================================================
csv = tabla.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Descargar tabla CSV",
    data=csv,
    file_name="areas_con_mayor_presencia_de_incendios.csv",
    mime="text/csv",
)
