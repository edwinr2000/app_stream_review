from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from services.access_control import require_module_access
from services.pdf_generator import generar_pdf_fecha_hora

require_module_access("reloj_pdf")

zona_horaria = ZoneInfo("America/Bogota")
ahora = datetime.now(zona_horaria)

st.title("Imprimir fecha y hora", icon=":material/print:")
st.write("Crea un comprobante PDF con la fecha y hora actuales de Bogotá.")
st.metric("Fecha y hora", ahora.strftime("%d/%m/%Y %I:%M:%S %p"))

if st.button("Generar PDF", icon=":material/picture_as_pdf:"):
    pdf = generar_pdf_fecha_hora(ahora)
    st.download_button(
        "Descargar PDF",
        data=pdf,
        file_name=f"fecha-hora-{ahora:%Y%m%d-%H%M%S}.pdf",
        mime="application/pdf",
        icon=":material/download:",
    )
