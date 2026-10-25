import streamlit as st

from services.access_control import require_module_access
from services.qr_tools import QR_ERROR_LEVELS, generate_qr_png, validate_text_payload, wifi_payload

require_module_access("qr_generator")

st.title("QR Generator", icon=":material/qr_code_2:")
st.write("Genera códigos QR localmente. El contenido no se guarda en la base de datos.")

qr_types = {
    "Texto o URL": "text",
    "Red Wi-Fi": "wifi",
}
qr_type_label = st.selectbox("Tipo de contenido", list(qr_types))

with st.form("form_qr"):
    if qr_types[qr_type_label] == "text":
        content = st.text_area("Texto o URL")
    else:
        ssid = st.text_input("Nombre de la red (SSID)")
        security = st.selectbox(
            "Seguridad",
            options=["WPA/WPA2", "WEP", "Sin contraseña"],
        )
        wifi_password = st.text_input(
            "Contraseña de Wi-Fi",
            type="password",
            disabled=security == "Sin contraseña",
        )
        content = ""

    col_size, col_error = st.columns(2)
    with col_size:
        box_size = st.slider("Tamaño", min_value=4, max_value=12, value=8)
    with col_error:
        correction_label = st.selectbox(
            "Corrección de errores",
            options=list(QR_ERROR_LEVELS),
        )
    generate = st.form_submit_button(
        "Generar QR",
        icon=":material/qr_code_2:",
        key="generate_qr",
    )

if generate:
    st.session_state.pop("generated_qr_content", None)
    st.session_state.pop("generated_qr_png", None)
    st.session_state.pop("generated_qr_settings", None)
    try:
        if qr_types[qr_type_label] == "text":
            qr_content = validate_text_payload(content)
        else:
            qr_content = wifi_payload(ssid, wifi_password, security)
        st.session_state["generated_qr_content"] = qr_content
        st.session_state["generated_qr_png"] = generate_qr_png(
            qr_content,
            error_correction=QR_ERROR_LEVELS[correction_label],
            box_size=box_size,
        )
        st.session_state["generated_qr_settings"] = {
            "box_size": box_size,
            "error_level": correction_label,
        }
    except ValueError as error:
        st.error(str(error))

if st.session_state.get("generated_qr_png"):
    st.image(st.session_state["generated_qr_png"], caption="Vista previa del QR")
    st.caption(
        f"Tamaño por módulo: {st.session_state['generated_qr_settings']['box_size']} · "
        f"Corrección: {st.session_state['generated_qr_settings']['error_level']}"
    )
    st.download_button(
        "Descargar PNG",
        data=st.session_state["generated_qr_png"],
        file_name="codigo-qr.png",
        mime="image/png",
        icon=":material/download:",
    )
