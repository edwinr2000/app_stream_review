import base64
import hashlib
import hmac
import secrets

import streamlit as st
from postgrest.exceptions import APIError

from services.db import init_connection


PASSWORD_HASH_ITERATIONS = 600_000
MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 1024


def account_can_access_module(
    account: dict,
    module_id: str,
    *,
    module_enabled: bool,
    admin_only: bool = False,
) -> bool:
    if not account.get("active") or not module_enabled:
        return False
    is_admin = account.get("role") == "SUPER_ADMIN"
    if admin_only:
        return is_admin
    return is_admin or module_id in (account.get("module_ids") or [])


def hash_password(password: str) -> str:
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"La contraseña debe tener entre {MIN_PASSWORD_LENGTH} y "
            f"{MAX_PASSWORD_LENGTH} caracteres."
        )
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return "$".join(
        (
            "pbkdf2_sha256",
            str(PASSWORD_HASH_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(password_hash).decode("ascii"),
        )
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, encoded_salt, encoded_hash = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iteration_count = int(iterations)
        if not 1 <= iteration_count <= PASSWORD_HASH_ITERATIONS:
            return False
        salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
        expected_hash = base64.urlsafe_b64decode(encoded_hash.encode("ascii"))
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iteration_count,
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual_hash, expected_hash)


def require_module_access(module_id: str, *, admin_only: bool = False) -> None:
    email = st.session_state.get("authenticated_email")
    if not email:
        st.error("Inicia sesión para acceder a esta aplicación.")
        st.stop()

    supabase = init_connection()
    try:
        account_res = (
            supabase.table("app_access_users")
            .select("email, role, module_ids, active")
            .eq("email", email)
            .limit(1)
            .execute()
        )
        catalog_res = (
            supabase.table("app_catalog")
            .select("id, enabled")
            .eq("id", module_id)
            .limit(1)
            .execute()
        )
    except APIError:
        st.error("No fue posible comprobar los permisos de esta aplicación.")
        st.stop()

    accounts = account_res.data or []
    catalog = catalog_res.data or []
    if not accounts or not accounts[0].get("active"):
        st.error("La cuenta no está activa.")
        st.stop()

    account = accounts[0]
    enabled = bool(catalog and catalog[0].get("enabled"))
    if not enabled:
        st.error("Esta aplicación no está disponible.")
        st.stop()
    if admin_only and account.get("role") != "SUPER_ADMIN":
        st.error("Esta sección está disponible solo para el superadministrador.")
        st.stop()
    if not account_can_access_module(
        account,
        module_id,
        module_enabled=enabled,
        admin_only=admin_only,
    ):
        st.error("Tu usuario no tiene permiso para abrir esta aplicación.")
        st.stop()
