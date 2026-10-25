import pandas as pd
import streamlit as st
from services.access_control import hash_password, require_module_access
from services.db import init_connection
from modules import APP_MODULES

st.title("🔐 Gestión de Usuarios y Roles")
st.markdown("Administra usuarios, roles y permisos de acceso a cada aplicación.")

require_module_access("gestion", admin_only=True)

supabase = init_connection()
module_titles = {module["id"]: module["title"] for module in APP_MODULES}
catalog_items = (
    supabase.table("app_catalog")
    .select("id, title, enabled")
    .execute()
    .data
    or []
)
catalog_titles = {item["id"]: item["title"] for item in catalog_items}
enabled_module_ids = [
    item["id"] for item in catalog_items if item["enabled"]
]

st.subheader("Catálogo de aplicaciones")
if catalog_items:
  catalog_frame = pd.DataFrame(catalog_items)
  catalog_frame["Disponible"] = catalog_frame["enabled"].map(
      {True: "Sí", False: "No"}
  )
  st.dataframe(
      catalog_frame[["title", "id", "Disponible"]],
      width="stretch",
      hide_index=True,
  )
  with st.expander("Activar o desactivar una aplicación"):
    item_by_title = {item["title"]: item for item in catalog_items}
    selected_title = st.selectbox(
        "Aplicación",
        options=list(item_by_title),
        key="catalog_app_selection",
    )
    selected_app = item_by_title[selected_title]
    with st.form("form_catalog_app"):
      app_enabled = st.checkbox(
          "Aplicación disponible para asignar",
          value=selected_app["enabled"],
          key=f"catalog_enabled_{selected_app['id']}",
      )
      save_app_status = st.form_submit_button("Guardar catálogo")
    if save_app_status:
      if selected_app["id"] == "gestion" and not app_enabled:
        st.error("El módulo Gestión no se puede desactivar porque administra el hub.")
      else:
        supabase.table("app_catalog").update(
            {"enabled": app_enabled}
        ).eq("id", selected_app["id"]).execute()
        st.success("Catálogo actualizado.")
        st.rerun()
else:
  st.warning("El catálogo está vacío. Ejecuta la migración SQL del proyecto.")

st.subheader("Cuentas y acceso a aplicaciones")
access_accounts_res = (
    supabase.table("app_access_users")
    .select("email, display_name, role, module_ids, active")
    .order("email")
    .execute()
)
access_accounts = access_accounts_res.data or []
if access_accounts:
  access_df = pd.DataFrame(access_accounts)
  access_df["Aplicaciones"] = access_df["module_ids"].apply(
      lambda ids: ", ".join(catalog_titles.get(module_id, module_id) for module_id in ids or [])
  )
  st.dataframe(
      access_df[["email", "display_name", "role", "Aplicaciones", "active"]],
      width="stretch",
  )
else:
  st.info("Todavía no hay cuentas de acceso.")

with st.expander("Crear o actualizar una cuenta"):
  account_by_email = {account["email"]: account for account in access_accounts}
  account_choice = st.selectbox(
      "Cuenta para editar",
      options=["Nueva cuenta", *account_by_email],
      key="account_choice",
  )
  selected_account = account_by_email.get(account_choice)
  field_suffix = selected_account["email"] if selected_account else "new"
  password_key = f"account_password_{field_suffix}"
  if st.session_state.pop("clear_account_password", False):
    st.session_state[password_key] = ""

  role_options = ["USER", "SUPER_ADMIN"]
  existing_role = selected_account["role"] if selected_account else "USER"
  default_module_ids = (
      []
      if existing_role == "SUPER_ADMIN"
      else [
          module_id
          for module_id in (selected_account or {}).get("module_ids", [])
          if module_id in enabled_module_ids
      ]
  )

  with st.form("form_cuenta_acceso"):
    cuenta_email = st.text_input(
        "Correo de acceso",
        value=selected_account["email"] if selected_account else "",
        key=f"account_email_{field_suffix}",
    )
    cuenta_nombre = st.text_input(
        "Nombre",
        value=selected_account["display_name"] if selected_account else "",
        key=f"account_name_{field_suffix}",
    )
    cuenta_rol = st.selectbox(
        "Rol",
        options=role_options,
        index=role_options.index(existing_role),
        format_func=lambda role: (
            "Super administrador" if role == "SUPER_ADMIN" else "Usuario"
        ),
        key=f"account_role_{field_suffix}",
    )
    cuenta_modulos = st.multiselect(
        "Aplicaciones permitidas",
        options=enabled_module_ids,
        default=default_module_ids,
        format_func=lambda module_id: catalog_titles.get(
            module_id, module_titles.get(module_id, module_id)
        ),
        disabled=cuenta_rol == "SUPER_ADMIN",
        key=f"account_modules_{field_suffix}",
    )
    cuenta_password = st.text_input(
        "Contraseña inicial (dejar vacía para conservar la actual)",
        type="password",
        key=password_key,
    )
    cuenta_activa = st.checkbox(
        "Cuenta activa",
        value=selected_account["active"] if selected_account else True,
        key=f"account_active_{field_suffix}",
    )
    guardar_cuenta = st.form_submit_button("Guardar cuenta")

  if guardar_cuenta:
    email_normalizado = cuenta_email.strip().lower()
    if not email_normalizado or not cuenta_nombre.strip():
      st.error("El correo y el nombre son obligatorios.")
    else:
      cuenta_existente = next(
          (account for account in access_accounts if account["email"] == email_normalizado),
          None,
      )
      email_admin_actual = st.session_state["authenticated_email"]
      if (
          email_normalizado == email_admin_actual
          and (cuenta_rol != "SUPER_ADMIN" or not cuenta_activa)
      ):
        st.error("No puedes quitarte el rol o desactivar tu propia cuenta.")
        st.stop()

      if (
          cuenta_existente
          and cuenta_existente["role"] == "SUPER_ADMIN"
          and (cuenta_rol != "SUPER_ADMIN" or not cuenta_activa)
      ):
        admins_activos = [
            account
            for account in access_accounts
            if account["role"] == "SUPER_ADMIN" and account["active"]
        ]
        if len(admins_activos) <= 1:
          st.error("Debe permanecer al menos un superadministrador activo.")
          st.stop()

      cuenta_data = {
          "email": email_normalizado,
          "display_name": cuenta_nombre.strip(),
          "role": cuenta_rol,
          "module_ids": (
              enabled_module_ids
              if cuenta_rol == "SUPER_ADMIN"
              else sorted(
                  set(cuenta_modulos)
                  | {
                      module_id
                      for module_id in (cuenta_existente or {}).get("module_ids", [])
                      if module_id not in enabled_module_ids
                  }
              )
          ),
          "active": cuenta_activa,
      }
      if cuenta_password:
        try:
          cuenta_data["password_hash"] = hash_password(cuenta_password)
        except ValueError as error:
          st.error(str(error))
          st.stop()
      elif not cuenta_existente:
        st.error("Debes definir una contraseña inicial para la cuenta nueva.")
        st.stop()
      supabase.table("app_access_users").upsert(
          cuenta_data,
          on_conflict="email",
      ).execute()
      st.session_state["clear_account_password"] = True
      st.success("Cuenta de acceso guardada.")
      st.rerun()

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

  st.markdown("---")
else:
  st.info("No hay usuarios registrados en el sistema.")