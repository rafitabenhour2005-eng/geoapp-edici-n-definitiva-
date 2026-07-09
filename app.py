import streamlit as st
import geopandas as gpd
import leafmap.foliumap as leafmap
import plotly.express as px

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
# Cargar datos
# =====================================================

@st.cache_data
def cargar_datos():

    reserva = gpd.read_file(
        "data/area_reserva_calakmul.gpkg"
    )

    incendios = gpd.read_file(
        "data/areas_con_mayor_presencia_de_incendios.gpkg"
    )

    return reserva, incendios


reserva, incendios = cargar_datos()

# =====================================================
# Convertir a UTM para calcular áreas
# =====================================================

# UTM Zona 16N (Calakmul)
reserva_utm = reserva.to_crs("EPSG:32616")
incendios_utm = incendios.to_crs("EPSG:32616")

# Área de la reserva
area_reserva = reserva_utm.area.sum() / 10000

# Área de incendios
incendios_utm["Área (ha)"] = incendios_utm.area / 10000

area_incendios = incendios_utm["Área (ha)"].sum()

porcentaje = (area_incendios / area_reserva) * 100

# =====================================================
# Barra lateral
# =====================================================

st.sidebar.title("Capas")

mostrar_reserva = st.sidebar.checkbox(
    "Reserva de la Biosfera",
    True
)

mostrar_incendios = st.sidebar.checkbox(
    "Áreas con incendios",
    True
)

# =====================================================
# Crear mapa
# =====================================================

mapa = leafmap.Map()

mapa.add_basemap("SATELLITE")

if mostrar_reserva:

    mapa.add_gdf(
        reserva,
        layer_name="Reserva de la Biosfera"
    )

if mostrar_incendios:

    mapa.add_gdf(
        incendios,
        layer_name="Áreas con incendios"
    )

mapa.zoom_to_gdf(reserva)

mapa.to_streamlit(height=700)

# =====================================================
# Indicadores
# =====================================================

st.header("Indicadores")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Número de polígonos",
    len(incendios)
)

c2.metric(
    "Área afectada (ha)",
    f"{area_incendios:,.2f}"
)

c3.metric(
    "% de la reserva afectada",
    f"{porcentaje:.2f}"
)

# =====================================================
# Gráfico
# =====================================================

st.header("Área por polígono")

incendios_utm["Polígono"] = range(
    1,
    len(incendios_utm) + 1
)

fig = px.bar(
    incendios_utm,
    x="Polígono",
    y="Área (ha)",
    color="Área (ha)",
    title="Área de cada polígono de incendio"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================================
# Tabla
# =====================================================

st.header("Tabla de atributos")

tabla = incendios_utm.drop(columns="geometry")

st.dataframe(
    tabla,
    use_container_width=True
)

# =====================================================
# Descargar CSV
# =====================================================

csv = tabla.to_csv(index=False)

st.download_button(
    label="📥 Descargar tabla CSV",
    data=csv,
    file_name="areas_con_mayor_presencia_de_incendios.csv",
    mime="text/csv"
)
