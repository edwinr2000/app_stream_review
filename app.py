import streamlit as st
from services.db import init_connection

st.set_page_config(page_title="Sistema de Gestión - ERP", layout="wide")

supabase = init_connection()

# --- CONTROL DE SESIÓN Y ROLES SEGURO EN LA BARRA LATERAL ---
st.sidebar.markdown("### 👤 Sesión de Usuario")

rol_actual = "ADMINISTRADOR"

try:
  usuarios_res = supabase.table("usuarios").select("id, nombre, email, role_id, activo").execute()
  usuarios_lista = usuarios_res.data if usuarios_res.data else []

  roles_res = supabase.table("roles").select("id, nombre").execute()
  roles_map = {r["id"]: r["nombre"] for r in roles_res.data} if roles_res.data else {}

  if usuarios_lista:
    user_options = {f"{u['nombre']} ({roles_map.get(u['role_id'], 'Sin Rol')})": u for u in usuarios_lista}
    
    selected_user_str = st.sidebar.selectbox("Usuario Activo", options=list(user_options.keys()))
    usuario_actual = user_options[selected_user_str]
    rol_actual = roles_map.get(usuario_actual["role_id"], "ADMINISTRADOR").upper()

    st.sidebar.success(f"Rol: **{rol_actual}**")
  else:
    st.sidebar.info("Modo libre (Sin usuarios registrados).")
except Exception:
  st.sidebar.caption("Sesión por defecto (Admin)")

st.sidebar.markdown("---")

# --- DEFINICIÓN DE PÁGINAS ---
dashboard_page = st.Page("views/1_dashboard.py", title="Dashboard", icon="📊")
pedidos_page = st.Page("views/2_pedidos.py", title="Gestión de Pedidos", icon="🛒")
inventario_page = st.Page("views/3_inventario.py", title="Productos y Stock", icon="📦")
clientes_page = st.Page("views/4_clientes.py", title="Clientes", icon="👥")
usuarios_page = st.Page("views/5_usuarios.py", title="Usuarios y Roles", icon="🔐")

nav_structure = {
    "Principal": [dashboard_page],
    "Operaciones": [pedidos_page, inventario_page, clientes_page],
    "Administración": [usuarios_page]
}

pg = st.navigation(nav_structure)
pg.run()