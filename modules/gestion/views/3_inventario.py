import pandas as pd
import streamlit as st
from services.db import init_connection

st.title("📦 Gestión de Productos y Control de Stock")

supabase = init_connection()

tab_prod, tab_stock, tab_cat = st.tabs(["✨ Catálogo de Productos", "📊 Ajuste y Control de Stock", "🏷️ Gestión de Categorías"])

with tab_prod:
  st.subheader("Registrar Nuevo Producto")
  
  # Cargar categorías disponibles
  cat_res = supabase.table("categorias").select("id, nombre").execute()
  cat_list = cat_res.data if cat_res.data else []
  cat_map = {c["nombre"]: c["id"] for c in cat_list}

  with st.form("form_nuevo_producto"):
    nombre_prod = st.text_input("Nombre del Producto")
    sku_prod = st.text_input("SKU (Código único)")
    
    if cat_map:
      cat_sel = st.selectbox("Categoría", options=list(cat_map.keys()))
    else:
      cat_sel = None
      st.warning("No hay categorías registradas. Por favor crea una en la pestaña 'Gestión de Categorías'.")

    precio_prod = st.number_input("Precio Unitario", min_value=0.0, step=1000.0)
    desc_prod = st.text_area("Descripción")

    submitted_prod = st.form_submit_button("Guardar Producto")
    if submitted_prod:
      if nombre_prod and sku_prod and cat_sel:
        data_ins = {
            "nombre": nombre_prod,
            "sku": sku_prod,
            "categoria_id": cat_map.get(cat_sel),
            "precio": precio_prod,
            "stock_actual": 0,
            "descripcion": desc_prod,
        }
        res = supabase.table("productos").insert(data_ins).execute()
        if res.data:
          st.success("¡Producto registrado con éxito!")
          st.rerun()
        else:
          st.error("Error al guardar el producto (¿El SKU ya existe?).")
      else:
        st.warning("Completa los campos obligatorios y asegúrate de seleccionar una categoría.")

  st.markdown("---")
  st.subheader("Catálogo Actual de Productos")
  prod_res = supabase.table("productos").select("*").execute()
  if prod_res.data:
    df_prod = pd.DataFrame(prod_res.data)
    st.dataframe(df_prod[["id", "nombre", "sku", "precio", "stock_actual", "activo"]], use_container_width=True)
  else:
    st.info("No hay productos registrados.")

with tab_stock:
  st.subheader("Modificar y Asignar Stock")
  
  prod_res = supabase.table("productos").select("id, nombre, sku, stock_actual").execute()
  productos_lista = prod_res.data if prod_res.data else []

  if not productos_lista:
    st.info("No hay productos registrados para ajustar stock.")
  else:
    prod_dict = {f"{p['nombre']} (SKU: {p['sku']} - Stock Actual: {p['stock_actual']})": p for p in productos_lista}
    
    sel_prod_str = st.selectbox("Seleccionar Producto", options=list(prod_dict.keys()))
    prod_seleccionado = prod_dict[sel_prod_str]

    st.write(f"Stock actual de **{prod_seleccionado['nombre']}**: `{prod_seleccionado['stock_actual']}` unidades")

    tipo_ajuste = st.radio("Tipo de Ajuste", ["Establecer nuevo stock exacto", "Sumar / Restar unidades (Movimiento)"])
    
    if tipo_ajuste == "Establecer nuevo stock exacto":
      nuevo_stock = st.number_input("Nuevo Stock Total", min_value=0, value=int(prod_seleccionado['stock_actual']), step=1)
      if st.button("Actualizar Stock Total"):
        upd = supabase.table("productos").update({"stock_actual": nuevo_stock}).eq("id", prod_seleccionado["id"]).execute()
        if upd.data:
          st.success("¡Stock actualizado correctamente!")
          st.rerun()
        else:
          st.error("Error al actualizar el stock.")
    else:
      cantidad_mov = st.number_input("Cantidad a sumar (positivo) o restar (negativo)", value=0, step=1)
      if st.button("Aplicar Movimiento"):
        stock_calculado = prod_seleccionado['stock_actual'] + cantidad_mov
        if stock_calculado < 0:
          st.error("El stock resultante no puede ser menor a cero.")
        else:
          upd = supabase.table("productos").update({"stock_actual": stock_calculado}).eq("id", prod_seleccionado["id"]).execute()
          if upd.data:
            st.success(f"¡Movimiento registrado! Nuevo stock: {stock_calculado}")
            st.rerun()
          else:
            st.error("Error al registrar el movimiento.")

with tab_cat:
  st.subheader("Crear Nueva Categoría")
  with st.form("form_nueva_categoria"):
    nombre_cat = st.text_input("Nombre de la Categoría (ej. Hardware, Periféricos)")
    desc_cat = st.text_input("Descripción opcional")
    
    submitted_cat = st.form_submit_button("Guardar Categoría")
    if submitted_cat:
      if nombre_cat:
        res_cat = supabase.table("categorias").insert({"nombre": nombre_cat, "descripcion": desc_cat}).execute()
        if res_cat.data:
          st.success(f"¡Categoría '{nombre_cat}' creada con éxito!")
          st.rerun()
        else:
          st.error("Error al crear la categoría (quizás ya exista).")
      else:
        st.warning("El nombre de la categoría es obligatorio.")

  st.markdown("---")
  st.subheader("Categorías Existentes")
  if cat_list:
    df_cat = pd.DataFrame(cat_list)
    st.dataframe(df_cat, use_container_width=True)
  else:
    st.info("No hay categorías registradas.")