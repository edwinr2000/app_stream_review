from datetime import date

import pandas as pd
import streamlit as st
import plotly.express as px

from services.db import init_connection


# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================

st.set_page_config(
    page_title="InventApp | Dashboard",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# ENCABEZADO
# ============================================================

col_logo, col_titulo = st.columns([1, 5])

with col_logo:

    try:
        st.image(
            "assets/logo.png",
            width=100,
        )

    except Exception:
        st.write("📦")


with col_titulo:

    st.title("Panel de Control")

    st.caption(
        "Resumen ejecutivo del rendimiento comercial, pedidos e inventario."
    )


st.markdown("---")


# ============================================================
# CONEXIÓN
# ============================================================

supabase = init_connection()


try:

    # ============================================================
    # CARGAR PEDIDOS
    # ============================================================

    pedidos_res = (
        supabase
        .table("pedidos")
        .select(
            """
            id,
            fecha_pedido,
            total,
            subtotal,
            impuestos,
            cliente_id,
            estado_id
            """
        )
        .execute()
    )

    pedidos = pedidos_res.data if pedidos_res.data else []


    # ============================================================
    # CLIENTES
    # ============================================================

    clientes_res = (
        supabase
        .table("clientes")
        .select(
            "id, nombre_empresa"
        )
        .execute()
    )


    clientes_map = {

        c["id"]: c["nombre_empresa"]

        for c in clientes_res.data

    } if clientes_res.data else {}


    # ============================================================
    # PRODUCTOS
    # ============================================================

    productos_res = (
        supabase
        .table("productos")
        .select(
            "id, nombre, stock_actual, precio"
        )
        .execute()
    )


    productos = (
        productos_res.data
        if productos_res.data
        else []
    )


    # ============================================================
    # ESTADOS
    # ============================================================

    estados_res = (
        supabase
        .table("estados_pedido")
        .select(
            "id, nombre, codigo"
        )
        .execute()
    )


    estados_map = {

        e["id"]: e["nombre"]

        for e in estados_res.data

    } if estados_res.data else {}


    # ============================================================
    # VALIDAR DATOS
    # ============================================================

    if not pedidos:

        st.info(
            "📭 Aún no hay pedidos registrados para mostrar en el dashboard."
        )

        st.stop()


    # ============================================================
    # DATAFRAME PEDIDOS
    # ============================================================

    df_pedidos = pd.DataFrame(pedidos)


    # Cliente

    df_pedidos["Cliente"] = (

        df_pedidos["cliente_id"]
        .map(
            lambda x: clientes_map.get(
                x,
                "Desconocido",
            )
        )

    )


    # Estado

    df_pedidos["Estado"] = (

        df_pedidos["estado_id"]
        .map(
            lambda x: estados_map.get(
                x,
                "Desconocido",
            )
        )

    )


    # Fecha

    df_pedidos["fecha_dt"] = pd.to_datetime(
        df_pedidos["fecha_pedido"]
    )


    df_pedidos["fecha"] = (
        df_pedidos["fecha_dt"].dt.date
    )


    # ============================================================
    # FILTROS
    # ============================================================

    with st.sidebar:

        st.markdown("## 🔍 Filtros")

        st.markdown("---")


        min_date = df_pedidos["fecha"].min()

        max_date = df_pedidos["fecha"].max()


        rango_fechas = st.date_input(

            "📅 Rango de fechas",

            value=(
                min_date,
                max_date,
            ),

            min_value=min_date,

            max_value=max_date,

        )


        estados_disponibles = sorted(
            df_pedidos["Estado"].unique()
        )


        filtro_estado = st.multiselect(

            "📌 Estado del pedido",

            options=estados_disponibles,

            default=estados_disponibles,

        )


        clientes_disponibles = sorted(
            df_pedidos["Cliente"].unique()
        )


        filtro_cliente = st.multiselect(

            "🏢 Cliente",

            options=clientes_disponibles,

            default=clientes_disponibles,

        )


    # ============================================================
    # APLICAR FILTROS
    # ============================================================

    df_filtrado = df_pedidos.copy()


    if len(rango_fechas) == 2:

        fecha_inicio = rango_fechas[0]

        fecha_fin = rango_fechas[1]


        df_filtrado = df_filtrado[

            (
                df_filtrado["fecha"]
                >= fecha_inicio
            )

            &

            (
                df_filtrado["fecha"]
                <= fecha_fin
            )

        ]


    # Estado

    df_filtrado = df_filtrado[

        df_filtrado["Estado"]
        .isin(filtro_estado)

    ]


    # Cliente

    df_filtrado = df_filtrado[

        df_filtrado["Cliente"]
        .isin(filtro_cliente)

    ]


    # ============================================================
    # KPIs
    # ============================================================

    total_ventas = (

        df_filtrado["total"].sum()

        if not df_filtrado.empty

        else 0

    )


    cantidad_pedidos = len(df_filtrado)


    ticket_promedio = (

        total_ventas / cantidad_pedidos

        if cantidad_pedidos > 0

        else 0

    )


    clientes_activos = (

        df_filtrado["cliente_id"].nunique()

        if not df_filtrado.empty

        else 0

    )


    # ============================================================
    # MÉTRICAS
    # ============================================================

    st.subheader("📌 Resumen General")


    col1, col2, col3, col4 = st.columns(4)


    col1.metric(

        "💰 Ventas Totales",

        f"${total_ventas:,.0f}".replace(",", "."),

    )


    col2.metric(

        "🛒 Pedidos",

        cantidad_pedidos,

    )


    col3.metric(

        "📈 Ticket Promedio",

        f"${ticket_promedio:,.0f}".replace(",", "."),

    )


    col4.metric(

        "👥 Clientes Activos",

        clientes_activos,

    )


    st.markdown("---")


    # ============================================================
    # GRÁFICOS PRINCIPALES
    # ============================================================

    col_g1, col_g2 = st.columns(2)


    # ------------------------------------------------------------
    # VENTAS EN EL TIEMPO
    # ------------------------------------------------------------

    with col_g1:

        st.subheader("📈 Evolución de Ventas")


        if not df_filtrado.empty:

            df_ventas_dia = (

                df_filtrado

                .groupby("fecha_dt")["total"]

                .sum()

                .reset_index()

            )


            fig_ventas = px.line(

                df_ventas_dia,

                x="fecha_dt",

                y="total",

                markers=True,

                labels={

                    "fecha_dt": "Fecha",

                    "total": "Ventas",

                },

            )


            fig_ventas.update_layout(

                height=350,

                margin=dict(

                    l=10,

                    r=10,

                    t=20,

                    b=10,

                ),

                yaxis_tickprefix="$ ",

            )


            st.plotly_chart(

                fig_ventas,

                use_container_width=True,

            )


        else:

            st.info("No hay datos disponibles.")


    # ------------------------------------------------------------
    # ESTADO DE PEDIDOS
    # ------------------------------------------------------------

    with col_g2:

        st.subheader("📦 Distribución de Pedidos")


        if not df_filtrado.empty:


            df_estados = (

                df_filtrado["Estado"]

                .value_counts()

                .reset_index()

            )


            df_estados.columns = [

                "Estado",

                "Cantidad",

            ]


            fig_estados = px.pie(

                df_estados,

                names="Estado",

                values="Cantidad",

                hole=0.55,

            )


            fig_estados.update_layout(

                height=350,

                margin=dict(

                    l=10,

                    r=10,

                    t=20,

                    b=10,

                ),

            )


            st.plotly_chart(

                fig_estados,

                use_container_width=True,

            )


    st.markdown("---")


    # ============================================================
    # TOP CLIENTES
    # ============================================================

    col_clientes, col_inventario = st.columns(2)


    with col_clientes:

        st.subheader("🏆 Top Clientes")


        if not df_filtrado.empty:


            df_clientes = (

                df_filtrado

                .groupby("Cliente")["total"]

                .sum()

                .reset_index()

                .sort_values(

                    "total",

                    ascending=False,

                )

                .head(10)

            )


            fig_clientes = px.bar(

                df_clientes,

                x="total",

                y="Cliente",

                orientation="h",

                labels={

                    "total": "Ventas",

                    "Cliente": "",

                },

            )


            fig_clientes.update_layout(

                height=350,

                yaxis={

                    "categoryorder": "total ascending"

                },

                margin=dict(

                    l=10,

                    r=10,

                    t=20,

                    b=10,

                ),

            )


            st.plotly_chart(

                fig_clientes,

                use_container_width=True,

            )


    # ============================================================
    # RESUMEN INVENTARIO
    # ============================================================

    with col_inventario:

        st.subheader("📦 Estado del Inventario")


        if productos:

            df_prod = pd.DataFrame(productos)


            total_productos = len(df_prod)


            productos_criticos = len(

                df_prod[

                    df_prod["stock_actual"] <= 5

                ]

            )


            productos_sin_stock = len(

                df_prod[

                    df_prod["stock_actual"] == 0

                ]

            )


            inv1, inv2, inv3 = st.columns(3)


            inv1.metric(

                "Productos",

                total_productos,

            )


            inv2.metric(

                "Stock Bajo",

                productos_criticos,

            )


            inv3.metric(

                "Sin Stock",

                productos_sin_stock,

            )


            st.markdown("### ⚠️ Productos Críticos")


            df_criticos = (

                df_prod[

                    df_prod["stock_actual"] <= 5

                ]

                .sort_values(

                    "stock_actual"

                )

            )


            if not df_criticos.empty:

                st.dataframe(

                    df_criticos[

                        [

                            "nombre",

                            "stock_actual",

                            "precio",

                        ]

                    ],

                    use_container_width=True,

                    hide_index=True,

                )


            else:

                st.success(

                    "✅ Inventario en niveles saludables."

                )


    # ============================================================
    # DETALLE DE PEDIDOS
    # ============================================================

    st.markdown("---")

    st.subheader("📋 Últimos Pedidos")


    columnas_mostrar = [

        "id",

        "fecha_pedido",

        "Cliente",

        "Estado",

        "subtotal",

        "impuestos",

        "total",

    ]


    df_ultimos = (

        df_filtrado

        .sort_values(

            "fecha_dt",

            ascending=False,

        )

        .head(10)

    )


    st.dataframe(

        df_ultimos[columnas_mostrar],

        use_container_width=True,

        hide_index=True,

    )


except Exception as e:

    st.error(
        f"❌ Error cargando los datos del dashboard: {e}"
    )