import streamlit as st

from services.access_control import require_module_access
from services.json_tools import JsonInputError, format_json, minify_json, parse_json

require_module_access("json_formatter")

st.title("JSON Formatter", icon=":material/data_object:")
st.write("Valida, indenta y minifica JSON en memoria, sin almacenar su contenido.")


def clear_editor():
    st.session_state["json_source"] = ""
    st.session_state["json_result"] = ""
    st.session_state["json_feedback"] = None


source = st.text_area(
    "JSON de entrada",
    height=260,
    key="json_source",
    placeholder='{"nombre":"Ada","activo":true}',
)

col_validate, col_format, col_minify, col_clear = st.columns(4)
validate_clicked = col_validate.button(
    "Validar", icon=":material/check_circle:", width="stretch", key="json_validate"
)
format_clicked = col_format.button(
    "Formatear",
    icon=":material/format_indent_increase:",
    width="stretch",
    key="json_format",
)
minify_clicked = col_minify.button(
    "Minificar", icon=":material/compress:", width="stretch", key="json_minify"
)
col_clear.button(
    "Limpiar",
    icon=":material/delete:",
    width="stretch",
    key="json_clear",
    on_click=clear_editor,
)

if validate_clicked or format_clicked or minify_clicked:
    try:
        if validate_clicked:
            parse_json(source)
            st.session_state["json_result"] = source
            st.session_state["json_feedback"] = ("success", "El JSON es válido.")
        elif format_clicked:
            st.session_state["json_result"] = format_json(source)
            st.session_state["json_feedback"] = ("success", "JSON formateado.")
        else:
            st.session_state["json_result"] = minify_json(source)
            st.session_state["json_feedback"] = ("success", "JSON minificado.")
    except JsonInputError as error:
        location = (
            f" (línea {error.line}, columna {error.column})"
            if error.line is not None
            else ""
        )
        st.session_state["json_result"] = ""
        st.session_state["json_feedback"] = (
            "error",
            f"JSON inválido{location}: {error}",
        )

feedback = st.session_state.get("json_feedback")
if feedback:
    getattr(st, feedback[0])(feedback[1])

result = st.session_state.get("json_result", "")
if result:
    st.text_area("Resultado (selecciona y copia)", value=result, height=260)
    st.download_button(
        "Descargar resultado",
        data=result.encode("utf-8"),
        file_name="resultado.json",
        mime="application/json",
        icon=":material/download:",
    )
