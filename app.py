import streamlit as st
from postgrest.exceptions import APIError

from modules import APP_MODULES
from services.access_control import hash_password, verify_password
from services.db import init_connection

st.set_page_config(page_title="Hub de aplicaciones", layout="wide")


def cerrar_sesion():
  st.session_state.clear()
  st.rerun()


if "supabase" not in st.secrets:
  st.error("Falta la configuración de Supabase en `.streamlit/secrets.toml`.")
  st.stop()

supabase = init_connection()
try:
  accounts_res = (
      supabase.table("app_access_users")
      .select("email")
      .limit(1)
      .execute()
  )
except APIError as error:
  st.error(
      "No se pudo consultar `app_access_users`. Aplica la migración "
      "`supabase/migrations/20261025010000_cuentas_acceso.sql` en Supabase "
      f"y verifica la clave del servidor. Detalle: {error.message}"
  )
  st.stop()
accounts = accounts_res.data or []

if not accounts:
  bootstrap = st.secrets.get("bootstrap", {})
  admin_email = str(bootstrap.get("super_admin_email", "")).strip().lower()
  admin_password = str(bootstrap.get("super_admin_password", ""))
  if admin_email and admin_password:
    try:
      password_hash = hash_password(admin_password)
    except ValueError as error:
      st.error(f"La contraseña inicial no cumple el requisito: {error}")
    else:
      supabase.table("app_access_users").insert(
          {
              "email": admin_email,
              "display_name": "Super administrador",
              "password_hash": password_hash,
              "role": "SUPER_ADMIN",
              "module_ids": [module["id"] for module in APP_MODULES],
              "active": True,
          }
      ).execute()
      st.rerun()

if "authenticated_email" not in st.session_state:
  st.title("Hub de aplicaciones", icon=":material/apps:")
  st.write("Inicia sesión para acceder a las aplicaciones asignadas a tu usuario.")
  if not accounts and (
      not st.secrets.get("bootstrap", {}).get("super_admin_email")
      or not st.secrets.get("bootstrap", {}).get("super_admin_password")
  ):
    st.warning(
        "El superadministrador todavía no está configurado. Agrega correo y "
        "una contraseña inicial de al menos 12 caracteres en [bootstrap] de "
        "`.streamlit/secrets.toml`."
    )
  with st.form("login_app"):
    correo_ingresado = st.text_input("Correo electrónico")
    contrasena = st.text_input("Contraseña", type="password")
    iniciar_sesion = st.form_submit_button("Iniciar sesión", icon=":material/login:")

  if iniciar_sesion:
    if not correo_ingresado.strip() or not contrasena:
      st.error("Escribe tu correo y contraseña.")
      st.stop()

    login_email = correo_ingresado.strip().lower()
    login_res = (
        supabase.table("app_access_users")
        .select("email, display_name, password_hash, role, module_ids, active")
        .eq("email", login_email)
        .limit(1)
        .execute()
    )
    login_accounts = login_res.data or []
    if (
        not login_accounts
        or not login_accounts[0].get("active")
        or not verify_password(contrasena, login_accounts[0]["password_hash"])
    ):
      st.error("Correo o contraseña incorrectos, o cuenta inactiva.")
      st.stop()

    st.session_state["authenticated_email"] = login_email
    st.rerun()
  st.stop()

correo_actual = st.session_state["authenticated_email"]
cuenta_actual_res = (
    supabase.table("app_access_users")
    .select("email, display_name, role, module_ids, active")
    .eq("email", correo_actual)
    .limit(1)
    .execute()
)
cuentas_actuales = cuenta_actual_res.data or []
if not cuentas_actuales or not cuentas_actuales[0].get("active"):
  st.error("La cuenta fue desactivada. Inicia sesión con una cuenta activa.")
  cerrar_sesion()

usuario_actual = cuentas_actuales[0]
rol_actual = usuario_actual["role"]
es_administrador = rol_actual == "SUPER_ADMIN"
ids_permitidos = set(usuario_actual.get("module_ids") or [])
try:
  catalog_res = (
      supabase.table("app_catalog")
      .select("id, enabled")
      .execute()
  )
except APIError as error:
  st.error(
      "No se pudo cargar el catálogo de aplicaciones. Aplica la migración "
      "`supabase/migrations/20261025020000_catalogo_apps.sql` en Supabase. "
      f"Detalle: {error.message}"
  )
  st.stop()

catalog_enabled = {
    item["id"] for item in catalog_res.data or [] if item.get("enabled")
}
modulos_accesibles = [
    module for module in APP_MODULES
    if module["id"] in catalog_enabled
    and (es_administrador or module["id"] in ids_permitidos)
]

with st.sidebar:
  st.markdown("### 👤 Sesión de usuario")
  st.write(f"**{usuario_actual['display_name']}**")
  st.caption(f"{correo_actual} · {rol_actual}")
  if st.button("Cerrar sesión", icon=":material/logout:"):
    cerrar_sesion()

  st.markdown("---")

# --- HUB Y MÓDULOS ---
nav_structure = {
    "": [
        st.Page(
            "app_pages/home.py",
            title="Hub de aplicaciones",
            icon=":material/apps:",
        )
    ]
}

for module in modulos_accesibles:
  nav_structure[module["title"]] = [
      st.Page(
          page["path"],
          title=page["title"],
          icon=page["icon"],
          url_path=page.get("url_path"),
      )
      for page in module["pages"]
      if es_administrador or not page.get("admin_only", False)
  ]

st.session_state["accessible_modules"] = modulos_accesibles
st.session_state["is_app_admin"] = es_administrador
st.session_state["authenticated_email"] = correo_actual
st.session_state["app_catalog"] = catalog_res.data or []

pg = st.navigation(nav_structure)
pg.run()