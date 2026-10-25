import streamlit as st

from services.access_control import require_module_access
from services.pdf_tools import (
    MAX_UPLOAD_BYTES,
    MAX_PDF_FILES,
    ConversionUnavailableError,
    PdfToolError,
    docx_to_pdf,
    merge_pdfs,
    pdf_to_docx,
    split_pdf,
    validate_upload,
)

require_module_access("pdf_toolbox")

st.title("PDF Toolbox", icon=":material/picture_as_pdf:")
st.write(
    "Une y divide PDF o convierte entre PDF y Word. Los archivos se procesan "
    "en memoria o en carpetas temporales que se eliminan al terminar."
)
st.caption(
    "Límite por archivo: 20 MB; unión: hasta 20 archivos y 40 MB en total. "
    "Conversión a Word: el formato puede cambiar."
)


def show_output(key: str, filename: str, mime: str):
    result = st.session_state.get(key)
    if result:
        st.download_button(
            f"Descargar {filename}",
            data=result,
            file_name=filename,
            mime=mime,
            key=f"download_{key}",
            icon=":material/download:",
        )


def show_tool_error(error: PdfToolError):
    st.error(str(error))


def clear_output(key: str):
    st.session_state.pop(key, None)


merge_tab, split_tab, pdf_word_tab, word_pdf_tab = st.tabs(
    ["Unir PDF", "Dividir PDF", "PDF a Word", "Word a PDF"]
)

with merge_tab:
    st.subheader("Unir varios PDF")
    merge_files = st.file_uploader(
        "Selecciona dos o más archivos PDF en el orden deseado",
        type=["pdf"],
        accept_multiple_files=True,
        max_upload_size=20,
        key="merge_pdf_files",
        on_change=clear_output,
        args=("merged_pdf",),
    )
    if merge_files:
        if any(file.size > MAX_UPLOAD_BYTES for file in merge_files):
            st.error("Cada archivo debe pesar 20 MB o menos.")
        elif len(merge_files) > MAX_PDF_FILES:
            st.error(f"Selecciona como máximo {MAX_PDF_FILES} archivos PDF.")
        else:
            labels = {
                f"{index + 1}. {file.name}": file
                for index, file in enumerate(merge_files)
            }
            ordered_labels = st.multiselect(
                "Orden del documento combinado",
                options=list(labels),
                default=[],
                help="Selecciona los archivos de uno en uno en el orden que quieras combinar.",
                key="merge_pdf_order",
                on_change=clear_output,
                args=("merged_pdf",),
            )
            if st.button("Unir PDF", key="merge_pdf_button"):
                try:
                    documents = [
                        (label, validate_upload(labels[label], kind="pdf"))
                        for label in ordered_labels
                    ]
                    st.session_state["merged_pdf"] = merge_pdfs(documents)
                except PdfToolError as error:
                    show_tool_error(error)
            show_output("merged_pdf", "documento-unido.pdf", "application/pdf")

with split_tab:
    st.subheader("Extraer páginas")
    split_file = st.file_uploader(
        "Selecciona un PDF",
        type=["pdf"],
        max_upload_size=20,
        key="split_pdf_file",
        on_change=clear_output,
        args=("split_pdf",),
    )
    page_ranges = st.text_input(
        "Páginas o rangos",
        placeholder="Ejemplo: 1-3,5",
        help="Empieza por la página 1; cada página se añade una sola vez.",
    )
    if split_file:
        if split_file.size > MAX_UPLOAD_BYTES:
            st.error("El archivo debe pesar 20 MB o menos.")
        elif st.button("Dividir PDF", key="split_pdf_button"):
            try:
                st.session_state["split_pdf"] = split_pdf(
                    validate_upload(split_file, kind="pdf"),
                    page_ranges,
                )
            except PdfToolError as error:
                show_tool_error(error)
    show_output("split_pdf", "paginas-extraidas.pdf", "application/pdf")

with pdf_word_tab:
    st.subheader("Convertir PDF a Word")
    st.info(
        "La conversión extrae texto y reconstruye párrafos editables. No conserva "
        "exactamente el diseño, tablas ni imágenes del PDF. No hay OCR para PDF escaneados."
    )
    pdf_file = st.file_uploader(
        "Selecciona un PDF con texto seleccionable",
        type=["pdf"],
        max_upload_size=20,
        key="pdf_to_word_file",
        on_change=clear_output,
        args=("pdf_to_docx",),
    )
    if pdf_file:
        if pdf_file.size > MAX_UPLOAD_BYTES:
            st.error("El archivo debe pesar 20 MB o menos.")
        elif st.button("Convertir a DOCX", key="pdf_to_word_button"):
            try:
                st.session_state["pdf_to_docx"] = pdf_to_docx(
                    validate_upload(pdf_file, kind="pdf")
                )
            except PdfToolError as error:
                show_tool_error(error)
    show_output(
        "pdf_to_docx",
        "documento-convertido.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

with word_pdf_tab:
    st.subheader("Convertir Word a PDF")
    st.caption(
        "Requiere LibreOffice Writer instalado en el servidor. La conversión "
        "puede variar respecto al diseño original."
    )
    word_file = st.file_uploader(
        "Selecciona un documento DOCX",
        type=["docx"],
        max_upload_size=20,
        key="word_to_pdf_file",
        on_change=clear_output,
        args=("word_to_pdf",),
    )
    if word_file:
        if word_file.size > MAX_UPLOAD_BYTES:
            st.error("El archivo debe pesar 20 MB o menos.")
        elif st.button("Convertir a PDF", key="word_to_pdf_button"):
            try:
                st.session_state["word_to_pdf"] = docx_to_pdf(
                    validate_upload(word_file, kind="docx")
                )
            except ConversionUnavailableError as error:
                st.warning(str(error))
            except PdfToolError as error:
                show_tool_error(error)
    show_output("word_to_pdf", "documento-convertido.pdf", "application/pdf")
