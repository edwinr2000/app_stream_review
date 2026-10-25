import pandas as pd
import streamlit as st
from services.db import init_connection

st.title("👥 Gestión de Clientes")

supabase = init_connection()

tab_lista, tab_crear, tab_editar = st.tabs(["📄 Listado de Clientes", "➕ Registrar Cliente", "✏️ Modificar Cliente"])

with tab_lista:
  st.subheader("Directorio de Clientes")
  cli_res = supabase.table("clientes").select("*").execute()
  clientes = cli_res.data if cli_res.data else []

  if clientes:
    df_clientes = pd.DataFrame(clientes)
    st.dataframe(df_clientes, use_container_width=True)
  else:
    st.info("No hay clientes registrados.")

with tab_crear:
  st.subheader("Registrar Nuevo Cliente")
  with st.form("form_nuevo_cliente"):
    nombre_empresa = st.text_input("Nombre de la Empresa")
    contacto_nombre = st.text_input("Nombre del Contacto")
    email = st.text_input("Correo Electrónico")
    telefono = st.text_input("Teléfono")
    direccion = st.text_input("Dirección")
    ciudad = st.text_input("Ciudad")

    submitted = st.form_submit_button("Guardar Cliente")
    if submitted:
      if nombre_empresa and contacto_nombre:
        data = {
            "nombre_empresa": nombre_empresa,
            "contacto_nombre": contacto_nombre,
            "email": email,
            "telefono": telefono,
            "direccion": direccion,
            "ciudad": ciudad
        }
        res = supabase.table("clientes").insert(data).execute()
        if res.data:
          st.success("¡Cliente registrado con éxito!")
          st.rerun()
        else:
          st.error("Error al registrar el cliente.")
      else:
        st.warning("El nombre de la empresa y del contacto son obligatorios.")

with tab_editar:
  st.subheader("Modificar Datos de un Cliente")
  cli_res = supabase.table("clientes").select("*").execute()
  clientes_lista = cli_res.data if cli_res.data else []

  if not clientes_lista:
    st.info("No hay clientes disponibles para modificar.")
  else:
    cli_dict = {f"{c['nombre_empresa']} (Contacto: {c['contacto_nombre']})": c for c in clientes_lista}
    sel_cli_str = st.selectbox("Seleccione el cliente a modificar", options=list(cli_dict.keys()))
    cli_actual = cli_dict[sel_cli_str]

    with st.form("form_editar_cliente"):
      nuevo_nombre_empresa = st.text_input("Nombre de la Empresa", value=cli_actual.get("nombre_empresa", ""))
      nuevo_contacto_nombre = st.text_input("Nombre del Contacto", value=cli_actual.get("contacto_nombre", ""))
      nuevo_email = st.text_input("Correo Electrónico", value=cli_actual.get("email", ""))
      nuevo_telefono = st.text_input("Teléfono", value=cli_actual.get("telefono", ""))
      nuevo_direccion = st.text_input("Dirección", value=cli_actual.get("direccion", ""))
      nuevo_ciudad = st.text_input("Ciudad", value=cli_actual.get("ciudad", ""))

      submitted_edit = st.form_submit_button("Actualizar Cliente")
      if submitted_edit:
        upd_data = {
            "nombre_empresa": nuevo_nombre_empresa,
            "contacto_nombre": nuevo_contacto_nombre,
            "email": nuevo_email,
            "telefono": nuevo_telefono,
            "direccion": nuevo_direccion,
            "ciudad": nuevo_ciudad
        }
        res_upd = supabase.table("clientes").update(upd_data).eq("id", cli_actual["id"]).execute()
        if res_upd.data:
          st.success("¡Cliente actualizado correctamente!")
          st.rerun()
        else:
          st.error("Error al actualizar los datos del cliente.")