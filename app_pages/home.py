import streamlit as st

st.title("Hub de aplicaciones", icon=":material/apps:")
st.write(
    "Abre una de las aplicaciones habilitadas para tu usuario."
)

modules = st.session_state.get("accessible_modules", [])
if not modules:
    st.info("Tu usuario no tiene módulos asignados. Solicita acceso al administrador.")

columns = st.columns(2)

for index, module in enumerate(modules):
    with columns[index % len(columns)]:
        with st.container(border=True):
            st.subheader(module["title"], icon=module["icon"])
            st.write(module["description"])
            st.page_link(
                module["entrypoint"],
                label="Abrir módulo",
                icon=":material/arrow_forward:",
                width="stretch",
            )
