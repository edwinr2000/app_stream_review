from datetime import date
import pandas as pd
import streamlit as st
from services.db import init_connection

# --- ENCABEZADO CON LOGO ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
  try:
    st.image("assets/logo.png", width=120)
  except Exception:
    st.write("📌 [Logo]")

with col_titulo:
  st.title("📊 Panel de Control y Analítica")
  st.markdown("Resumen general del rendimiento del negocio y métricas operativas.")

supabase = init_connection()

try:
  # Cargar datos base
  pedidos_res = supabase.table("pedidos").select("id, fecha_pedido, total, subtotal, impuestos, cliente_id, estado_id").execute()
  pedidos = pedidos_res.data if pedidos_res.data else []

  clientes_res = supabase.table("clientes").select("id, nombre_empresa").execute()
  clientes_map = {c["id"]: c["nombre_empresa"] for c in clientes_res.data} if clientes_res.data else {}

  productos_res = supabase.table("productos").select("id, nombre, stock_actual, precio").execute()
  productos = productos_res.data if productos_res.data else []

  estados_res = supabase.table("estados_pedido").select("id, nombre, codigo").execute()
  estados_map = {e["id"]: e["nombre"] for e in estados_res.data} if estados_res.data else {}

  if pedidos:
    df_pedidos = pd.DataFrame(pedidos)
    df_pedidos["Cliente"] = df_pedidos["cliente_id"].map(lambda x: clientes_map.get(x, "Desconocido"))
    df_pedidos["Estado"] = df_pedidos["estado_id"].map(lambda x: estados_map.get(x, "Desconocido"))
    
    # Asegurar formato fecha
    df_pedidos["fecha_dt"] = pd.to_datetime(df_pedidos["fecha_pedido"]).dt.date

    # --- PANEL DE FILTROS EN BARRA LATERAL ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filtros del Dashboard")
    
    min_date = df_pedidos["fecha_dt"].min()
    max_date = df_pedidos["fecha_dt"].max()
    
    rango_fechas = st.sidebar.date_input(
        "Rango de Fechas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    estados_disponibles = list(estados_map.values())
    filtro_estado = st.sidebar.multiselect("Estado de Pedido", options=estados_disponibles, default=estados_disponibles)

    # Aplicar Filtros Globales
    if len(rango_fechas) == 2:
      f_inicio, f_fin = rango_fechas
      df_filtrado = df_pedidos[
          (df_pedidos["fecha_dt"] >= f_inicio) & 
          (df_pedidos["fecha_dt"] <= f_fin) &
          (df_pedidos["Estado"].isin(filtro_estado))
      ]
    else:
      df_filtrado = df_pedidos[df_pedidos["Estado"].isin(filtro_estado)]

    # --- MÉTRICAS (KPIs) DINÁMICAS (Se mueven con los filtros) ---
    total_ventas = df_filtrado["total"].sum() if not df_filtrado.empty else 0.0
    cantidad_pedidos = len(df_filtrado)
    ticket_promedio = total_ventas / cantidad_pedidos if cantidad_pedidos > 0 else 0.0
    clientes_activos_periodo = df_filtrado["cliente_id"].nunique() if not df_filtrado.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
      st.metric("💰 Ventas Totales", f"${total_ventas:,.2f}")
    with col2:
      st.metric("🛒 Total Pedidos", cantidad_pedidos)
    with col3:
      st.metric("📈 Ticket Promedio", f"${ticket_promedio:,.2f}")
    with col4:
      st.metric("👥 Clientes en Periodo", clientes_activos_periodo)

    st.markdown("---")

    st.markdown("### 📈 Tendencias y Distribución")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
      st.subheader("Ventas por Cliente")
      if not df_filtrado.empty:
        df_clientes = df_filtrado.groupby("Cliente")["total"].sum().reset_index()
        st.bar_chart(df_clientes.set_index("Cliente"))
      else:
        st.info("No hay datos para mostrar con los filtros seleccionados.")

    with col_g2:
      st.subheader("Pedidos por Estado")
      if not df_filtrado.empty:
        df_estados = df_filtrado["Estado"].value_counts().reset_index()
        df_estados.columns = ["Estado", "Cantidad"]
        st.bar_chart(df_estados.set_index("Estado"))
      else:
        st.info("No hay datos para mostrar.")

    st.markdown("---")
    st.subheader("⚠️ Alertas de Inventario Crítico")
    if productos:
      df_prod = pd.DataFrame(productos)
      df_criticos = df_prod[df_prod["stock_actual"] <= 5]
      if not df_criticos.empty:
        st.warning("Los siguientes productos tienen stock bajo y requieren reposición:")
        st.dataframe(df_criticos[["nombre", "stock_actual", "precio"]], use_container_width=True)
      else:
        st.success("✅ Los niveles de inventario son óptimos.")
  else:
    st.info("Aún no hay suficientes transacciones registradas para mostrar las métricas.")

except Exception as e:
  st.error(f"Error cargando los datos del dashboard: {e}")