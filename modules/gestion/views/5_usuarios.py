import pandas as pd
import streamlit as st
from services.db import init_connection

st.title("🔐 Gestión de Usuarios y Roles")
st.markdown("Administra los accesos y roles del personal dentro del sistema.")

supabase = init_connection()

with st.expander("➕ Registrar Nuevo Usuario"):
  with st.form("form_usuario"):
    roles_res = supabase.table("roles").select("id, nombre, descripcion").execute()
    roles_list = roles_res.data if roles_res.data else []
    roles_map = {r["nombre"]: r["id"] for r in roles_list}

    nombre_usuario = st.text_input("Nombre Completo")
    email_usuario = st.text_input("Correo Electrónico")
    
    if roles_map:
      rol_sel = st.selectbox("Rol Asignado", options=list(roles_map.keys()))
    else:
      rol_sel = None
      st.warning("No hay roles definidos en la base de datos.")

    submitted_user = st.form_submit_button("Guardar Usuario")
    if submitted_user:
      if nombre_usuario and email_usuario and rol_sel:
        data_user = {
            "nombre": nombre_usuario,
            "email": email_usuario,
            "role_id": roles_map[rol_sel],
            "activo": True
        }
        res = supabase.table("usuarios").insert(data_user).execute()
        if res.data:
          st.success("¡Usuario registrado con éxito!")
          st.rerun()
        else:
          st.error("Error al registrar el usuario.")
      else:
        st.warning("Por favor completa todos los campos obligatorios.")

st.markdown("---")
st.subheader("Directorio de Usuarios del Sistema")

user_res = supabase.table("usuarios").select("id, nombre, email, activo, role_id").execute()
usuarios_list = user_res.data if user_res.data else []

roles_res = supabase.table("roles").select("id, nombre").execute()
roles_map = {r["id"]: r["nombre"] for r in roles_res.data} if roles_res.data else {}

if usuarios_list:
  df_users = pd.DataFrame(usuarios_list)
  df_users["Rol"] = df_users["role_id"].map(lambda x: roles_map.get(x, "Sin Rol"))
  st.dataframe(df_users[["id", "nombre", "email", "Rol", "activo"]], use_container_width=True)
else:
  st.info("No hay usuarios registrados en el sistema.")