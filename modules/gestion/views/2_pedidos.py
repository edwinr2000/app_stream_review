from datetime import datetime
import pandas as pd
import streamlit as st
from services.db import init_connection
from services.pdf_generator import generar_pdf_pedido

st.title("🛒 Gestión de Pedidos y Facturación")

supabase = init_connection()

tab_lista, tab_crear = st.tabs(["📄 Listado, Estados y Facturación", "➕ Crear Nuevo Pedido"])

with tab_lista:
  st.subheader("Pedidos Registrados y Ciclo de Vida")
  
  estados_res = supabase.table("estados_pedido").select("id, nombre, codigo").execute()
  estados_map = {e["id"]: e["nombre"] for e in estados_res.data} if estados_res.data else {}
  estados_inv_map = {e["nombre"]: e["id"] for e in estados_res.data} if estados_res.data else {}
  estados_code_map = {e["id"]: e["codigo"] for e in estados_res.data} if estados_res.data else {}

  # Casilla para mostrar u ocultar pedidos finalizados / cerrados / anulados
  ver_todos = st.checkbox("Mostrar historial completo (incluyendo cerrados, entregados y anulados)", value=False)

  res_pedidos = (
      supabase.table("pedidos")
      .select("id, fecha_pedido, subtotal, impuestos, total, observaciones, cliente_id, estado_id")
      .order("id", desc=True)
      .execute()
  )
  pedidos = res_pedidos.data if res_pedidos.data else []

  if pedidos and not ver_todos:
    pedidos = [
        p for p in pedidos 
        if estados_code_map.get(p["estado_id"], "").upper() not in ["CERRADO", "ANULADO", "CANCELADO", "ENTREGADO"]
    ]

  if not pedidos:
    st.info("No hay pedidos activos registrados en este momento. Activa la casilla superior para consultar el historial cerrado.")
  else:
    df_pedidos = pd.DataFrame(pedidos)
    clientes_res = supabase.table("clientes").select("id, nombre_empresa, contacto_nombre, email, direccion, ciudad").execute()
    clientes_map = {c["id"]: c for c in clientes_res.data} if clientes_res.data else {}

    df_pedidos["Cliente"] = df_pedidos["cliente_id"].map(lambda x: clientes_map.get(x, {}).get("nombre_empresa", "N/A"))
    df_pedidos["Estado"] = df_pedidos["estado_id"].map(lambda x: estados_map.get(x, "Desconocido"))

    st.dataframe(
        df_pedidos[["id", "Cliente", "Estado", "fecha_pedido", "subtotal", "total"]],
        use_container_width=True,
    )

    st.markdown("---")
    col_acc1, col_acc2 = st.columns(2)

    pedido_ids = [p["id"] for p in pedidos]

    with col_acc1:
      st.subheader("⚙️ Actualizar Estado del Pedido")
      selected_id_status = st.selectbox("Seleccione ID de pedido a modificar:", pedido_ids, key="sel_status")

      if selected_id_status:
        pedido_actual = next((p for p in pedidos if p["id"] == selected_id_status), None)
        estado_actual_id = pedido_actual["estado_id"]
        nombre_estado_actual = estados_map.get(estado_actual_id, "Desconocido")

        st.write(f"Estado Actual: **{nombre_estado_actual}**")

        nuevo_estado_nombre = st.selectbox("Cambiar a:", options=list(estados_inv_map.keys()), key="new_status_sel")
        
        if st.button("Actualizar Estado"):
          nuevo_estado_id = estados_inv_map[nuevo_estado_nombre]
          upd_res = supabase.table("pedidos").update({"estado_id": nuevo_estado_id}).eq("id", selected_id_status).execute()
          if upd_res.data:
            st.success(f"¡Pedido #{selected_id_status} actualizado a '{nuevo_estado_nombre}'!")
            st.rerun()
          else:
            st.error("Error al actualizar el estado.")

    with col_acc2:
      st.subheader("📥 Descargar Comprobante PDF")
      selected_id_pdf = st.selectbox("Seleccione ID de pedido para PDF:", pedido_ids, key="sel_pdf")

      if selected_id_pdf:
        pedido_info = next((p for p in pedidos if p["id"] == selected_id_pdf), None)
        cliente_info = clientes_map.get(pedido_info["cliente_id"], {})

        detalle_res = (
            supabase.table("detalle_pedidos")
            .select("cantidad, precio_unitario, subtotal_linea, producto_id")
            .eq("pedido_id", selected_id_pdf)
            .execute()
        )
        detalles = detalle_res.data if detalle_res.data else []
        prod_res = supabase.table("productos").select("id, nombre").execute()
        prod_map = {pr["id"]: pr["nombre"] for pr in prod_res.data} if prod_res.data else {}

        for d in detalles:
          d["producto_nombre"] = prod_map.get(d["producto_id"], "Producto Genérico")

        df_detalle = pd.DataFrame(detalles)

        if not df_detalle.empty:
          pdf_bytes = generar_pdf_pedido(selected_id_pdf, pedido_info, df_detalle, cliente_info)
          st.download_button(
              label="📄 Descargar Factura en PDF",
              data=pdf_bytes,
              file_name=f"factura_pedido_{selected_id_pdf}.pdf",
              mime="application/pdf",
          )
        else:
          st.warning("El pedido no tiene ítems asociados.")

with tab_crear:
  st.subheader("Asistente de Creación de Pedido")

  cli_res = supabase.table("clientes").select("id, nombre_empresa, contacto_nombre").execute()
  prod_res = supabase.table("productos").select("id, nombre, precio, stock_actual").gt("stock_actual", 0).execute()

  clientes_lista = cli_res.data if cli_res.data else []
  productos_lista = prod_res.data if prod_res.data else []

  if not clientes_lista or not productos_lista:
    st.warning("Necesitas tener al menos un cliente y productos con stock para crear un pedido.")
  else:
    cliente_dict = {f"{c['nombre_empresa']} ({c['contacto_nombre']})": c['id'] for c in clientes_lista}
    
    selected_cliente_str = st.selectbox("Seleccionar Cliente", options=list(cliente_dict.keys()))
    cliente_id = cliente_dict[selected_cliente_str]

    observaciones = st.text_area("Observaciones o notas del pedido")

    st.markdown("### Agregar Productos al Pedido")
    
    if "cart" not in st.session_state:
      st.session_state.cart = []

    prod_dict = {p['name_price']: p for p in [{**item, 'name_price': f"{item['nombre']} - ${item['precio']:,.2f} (Stock: {item['stock_actual']})"} for item in productos_lista]}

    col_p1, col_p2, col_p3 = st.columns([3, 1, 1])
    with col_p1:
      prod_sel = st.selectbox("Producto", options=list(prod_dict.keys()))
    with col_p2:
      cant_sel = st.number_input("Cantidad", min_value=1, value=1, step=1)
    with col_p3:
      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("Agregar Ítem"):
        p_info = prod_dict[prod_sel]
        if cant_sel <= p_info['stock_actual']:
          st.session_state.cart.append({
              "producto_id": p_info["id"],
              "nombre": p_info["nombre"],
              "cantidad": cant_sel,
              "precio_unitario": p_info["precio"],
              "subtotal_linea": cant_sel * p_info["precio"]
          })
          st.success("¡Producto agregado al carrito!")
        else:
          st.error("La cantidad supera el stock disponible.")

    if st.session_state.cart:
      df_cart = pd.DataFrame(st.session_state.cart)
      st.dataframe(df_cart[["nombre", "cantidad", "precio_unitario", "subtotal_linea"]], use_container_width=True)

      subtotal_general = df_cart["subtotal_linea"].sum()
      impuestos_general = subtotal_general * 0.19 
      total_general = subtotal_general + impuestos_general

      st.markdown(f"**Subtotal:** ${subtotal_general:,.2f}")
      st.markdown(f"**IVA (19%):** ${impuestos_general:,.2f}")
      st.markdown(f"**Total a Pagar:** ${total_general:,.2f}")

      if st.button("💾 Guardar y Procesar Pedido"):
        est_res = supabase.table("estados_pedido").select("id").eq("codigo", "PENDIENTE").execute()
        estado_id = est_res.data[0]["id"] if est_res.data else 1

        pedido_data = {
            "cliente_id": cliente_id,
            "estado_id": estado_id,
            "subtotal": subtotal_general,
            "impuestos": impuestos_general,
            "total": total_general,
            "observaciones": observaciones
        }
        res_ped = supabase.table("pedidos").insert(pedido_data).execute()

        if res_ped.data:
          nuevo_pedido_id = res_ped.data[0]["id"]

          for item in st.session_state.cart:
            detalle_data = {
                "pedido_id": nuevo_pedido_id,
                "producto_id": item["producto_id"],
                "cantidad": item["cantidad"],
                "precio_unitario": item["precio_unitario"],
                "subtotal_linea": item["subtotal_linea"]
            }
            supabase.table("detalle_pedidos").insert(detalle_data).execute()

            prod_actual = supabase.table("productos").select("stock_actual").eq("id", item["producto_id"]).execute()
            if prod_actual.data:
              nuevo_stock = prod_actual.data[0]["stock_actual"] - item["cantidad"]
              supabase.table("productos").update({"stock_actual": nuevo_stock}).eq("id", item["producto_id"]).execute()

          st.success(f"¡Pedido #{nuevo_pedido_id} creado y guardado con éxito!")
          st.session_state.cart = []
          st.rerun()
        else:
          st.error("Error al registrar el pedido.")

      if st.button("Limpiar Carrito"):
        st.session_state.cart = []
        st.rerun()