import pandas as pd
import streamlit as st
from supabase import Client, create_client


@st.cache_resource
def init_connection() -> Client:
  """Inicializa y cachea el cliente de Supabase usando st.secrets"""
  url = st.secrets["supabase"]["url"]
  key = st.secrets["supabase"]["key"]
  return create_client(url, key)


def run_query(table_name: str, select_query: str = "*", filters: dict = None):
  """Consulta registros de una tabla de Supabase y los retorna como DataFrame de Pandas"""
  supabase = init_connection()
  try:
    query = supabase.table(table_name).select(select_query)

    # Aplicar filtros opcionales si se envían (ej: {"estado_id": 2})
    if filters:
      for column, value in filters.items():
        query = query.eq(column, value)

    response = query.execute()
    data = response.data

    if not data:
      return pd.DataFrame()

    return pd.DataFrame(data)
  except Exception as e:
    st.error(f"Error consultando la tabla {table_name}: {e}")
    return pd.DataFrame()


def run_custom_sql_query(query_sql: str):
  """Nota: Para consultas complejas con JOINs múltiples, en Supabase se suelen usar Vistas de SQL (Views)."""
  pass