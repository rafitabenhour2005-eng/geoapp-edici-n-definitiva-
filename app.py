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
        "data/areas_con_mayor_presencia_incendios.gpkg"
    )

    return reserva, incendios


reserva, incendios = cargar_datos()

# =====================================================
# DEPURACIÓN (Paso 1)
# =====================================================

st.subheader("Información de las capas")

st.write("Número de polígonos de la reserva:", len(reserva))
st.write("Número de polígonos de incendios:", len(incendios))

st.write("CRS de la reserva:", reserva.crs)
st.write("CRS de incendios:", incendios.crs)

# =====================================================
# DEPURACIÓN (Paso 2)
# =====================================================

st.subheader("Extensión espacial")

st.write("Reserva (bounds):")
st.write(reserva.total_bounds)

st.write("Incendios (bounds):")
st.write(incendios.total_bounds)

# =====================================================
# Verificar CRS
# =====================================================

if reserva.crs is None:
    st.error("La capa de la reserva no tiene un sistema de coordenadas.")
    st.stop()

if incendios.crs is None:
    st.error("La capa de incendios no tiene un sistema de coordenadas.")
    st.stop()

# =====================================================
# Calcular áreas
# =====================================================

reserva_utm = reserva.to_crs("EPSG:32616")
incendios_utm = incendios.to_crs("EPSG:32616")

area_reserva = reserva_utm.area.sum() / 10000

incendios_utm["area_ha"] = incendios_utm.area / 10000

area_incendios = incendios_utm["area_ha"].sum()

porcentaje = (area_incendios / area_reserva) * 100

# =====================================================
# Barra lateral
# =====================================================

st.sidebar.header("Capas")

mostrar_reserva = st.sidebar.checkbox(
    "Reserva de la Biosfera",
    value=True
)

mostrar_incendios = st.sidebar.checkbox(
    "Áreas con incendios",
    value=True
)

# =====================================================
# Crear mapa
# =====================================================

mapa = leafmap.Map()

mapa.add_basemap("SATELLITE")

if mostrar_reserva:
    mapa.add_gdf(
        reserva.to_crs(4326),
        layer_name="Reserva",
        style={
            "color": "green",
            "weight": 2,
            "fillOpacity": 0.1
        }
    )

if mostrar_incendios:
    mapa.add_gdf(
        incendios.to_crs(4326),
        layer_name="Incendios",
        style={
            "color": "red",
            "fillColor": "red",
            "fillOpacity": 0.6,
            "weight": 1
        }
    )

mapa.zoom_to_gdf(reserva.to_crs(4326))

mapa.to_streamlit(height=700)

# =====================================================
# Indicadores
# =====================================================

st.header("📊 Indicadores")

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
    f"{porcentaje:.2f}%"
)

# =====================================================
# Gráfico
# =====================================================

st.header("Área por polígono")

incendios_utm["poligono"] = range(
    1,
    len(incendios_utm) + 1
)

fig = px.bar(
    incendios_utm,
    x="poligono",
    y="area_ha",
    color="area_ha",
    title="Área de cada polígono"
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
    "📥 Descargar CSV",
    csv,
    file_name="areas_mayor_presencia_incendios.csv",
    mime="text/csv"
)
