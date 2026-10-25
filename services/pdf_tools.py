from __future__ import annotations

from io import BytesIO
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from docx import Document
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PyPdfError


MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_PDF_PAGES = 500
MAX_PDF_FILES = 20
MAX_DOCX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024


class PdfToolError(ValueError):
    pass


class ConversionUnavailableError(PdfToolError):
    pass


def validate_bytes(data: bytes, *, kind: str) -> bytes:
    if len(data) > MAX_UPLOAD_BYTES:
        raise PdfToolError("El archivo supera el límite de 20 MB.")
    if kind == "pdf":
        if not data.startswith(b"%PDF-"):
            raise PdfToolError("El archivo no tiene una cabecera PDF válida.")
    elif kind == "docx":
        if not zipfile.is_zipfile(BytesIO(data)):
            raise PdfToolError("El documento Word no es un archivo DOCX válido.")
        try:
            with zipfile.ZipFile(BytesIO(data)) as archive:
                entries = archive.infolist()
                if sum(entry.file_size for entry in entries) > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise PdfToolError("El documento Word contiene demasiado contenido comprimido.")
                if "word/document.xml" not in {entry.filename for entry in entries}:
                    raise PdfToolError("El archivo DOCX no contiene un documento válido.")
        except (OSError, zipfile.BadZipFile) as error:
            raise PdfToolError("El documento Word está dañado.") from error
    else:
        raise ValueError(f"Unsupported file type: {kind}")
    return data


def validate_upload(upload, *, kind: str) -> bytes:
    return validate_bytes(upload.getvalue(), kind=kind)


def _reader(data: bytes) -> PdfReader:
    try:
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise PdfToolError("El PDF está protegido con contraseña.")
        if not reader.pages:
            raise PdfToolError("El PDF no contiene páginas.")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise PdfToolError(f"El PDF supera el límite de {MAX_PDF_PAGES} páginas.")
        return reader
    except PdfToolError:
        raise
    except (PyPdfError, OSError, ValueError, KeyError, IndexError, TypeError) as error:
        raise PdfToolError("No se pudo leer el PDF. Puede estar dañado o protegido.") from error


def merge_pdfs(documents: list[tuple[str, bytes]]) -> bytes:
    if len(documents) < 2:
        raise PdfToolError("Selecciona al menos dos archivos PDF para unir.")
    if len(documents) > MAX_PDF_FILES:
        raise PdfToolError(f"Selecciona como máximo {MAX_PDF_FILES} archivos PDF.")
    writer = PdfWriter()
    total_pages = 0
    total_bytes = 0
    try:
        for _, data in documents:
            total_bytes += len(data)
            if total_bytes > 40 * 1024 * 1024:
                raise PdfToolError("La carga total no puede superar 40 MB.")
            reader = _reader(data)
            total_pages += len(reader.pages)
            if total_pages > MAX_PDF_PAGES:
                raise PdfToolError(f"El resultado supera el límite de {MAX_PDF_PAGES} páginas.")
            for page in reader.pages:
                writer.add_page(page)
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    except PdfToolError:
        raise
    except (PyPdfError, OSError, ValueError, KeyError, IndexError, TypeError) as error:
        raise PdfToolError("No se pudieron unir esos documentos PDF.") from error
    finally:
        writer.close()


def parse_page_ranges(specification: str, page_count: int) -> list[int]:
    if not specification.strip():
        raise PdfToolError("Escribe los rangos de páginas, por ejemplo 1-3,5.")
    if len(specification) > 2000:
        raise PdfToolError("La lista de rangos es demasiado larga.")
    pages: list[int] = []
    selected = set()
    try:
        for part in specification.split(","):
            token = part.strip()
            if not token:
                raise ValueError
            if "-" in token:
                start_text, end_text = token.split("-", maxsplit=1)
                start, end = int(start_text.strip()), int(end_text.strip())
                if start > end or start < 1 or end > page_count:
                    raise ValueError
                current_pages = range(start, end + 1)
            else:
                page_number = int(token)
                if page_number < 1 or page_number > page_count:
                    raise ValueError
                current_pages = (page_number,)
            for page_number in current_pages:
                if page_number in selected:
                    raise PdfToolError("No repitas páginas en los rangos.")
                selected.add(page_number)
                pages.append(page_number)
                if len(pages) > MAX_PDF_PAGES:
                    raise PdfToolError(
                        f"El resultado supera el límite de {MAX_PDF_PAGES} páginas."
                    )
    except PdfToolError:
        raise
    except ValueError as error:
        raise PdfToolError("Usa rangos como 1-3,5; evita rangos vacíos o invertidos.") from error

    return [page - 1 for page in pages]


def split_pdf(data: bytes, page_ranges: str) -> bytes:
    reader = _reader(data)
    selected_pages = parse_page_ranges(page_ranges, len(reader.pages))
    writer = PdfWriter()
    try:
        for page_number in selected_pages:
            writer.add_page(reader.pages[page_number])
        output = BytesIO()
        writer.write(output)
        return output.getvalue()
    except (PyPdfError, OSError, ValueError, KeyError, IndexError, TypeError) as error:
        raise PdfToolError("No se pudo crear el PDF con las páginas seleccionadas.") from error
    finally:
        writer.close()


def pdf_to_docx(data: bytes) -> bytes:
    reader = _reader(data)
    document = Document()
    extracted_any_text = False
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except (PyPdfError, OSError, ValueError, KeyError, IndexError, TypeError) as error:
            raise PdfToolError("No se pudo extraer texto de una página del PDF.") from error
        if text.strip():
            extracted_any_text = True
            if page_number > 1:
                document.add_page_break()
            document.add_paragraph(text.strip())
    if not extracted_any_text:
        raise PdfToolError(
            "No se encontró texto extraíble. El PDF puede ser escaneado; "
            "esta versión no incluye OCR y no generó un DOCX vacío."
        )
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def docx_to_pdf(data: bytes) -> bytes:
    validate_bytes(data, kind="docx")
    converter = shutil.which("libreoffice") or shutil.which("soffice")
    if not converter:
        raise ConversionUnavailableError(
            "Word a PDF requiere LibreOffice instalado en el servidor. "
            "Instala libreoffice-writer y vuelve a ejecutar la conversión."
        )

    with tempfile.TemporaryDirectory(prefix="pdf-toolbox-") as directory:
        input_path = Path(directory) / "documento.docx"
        input_path.write_bytes(data)
        try:
            result = subprocess.run(
                [
                    converter,
                    "--headless",
                    f"-env:UserInstallation={(Path(directory) / 'lo-profile').as_uri()}",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    directory,
                    str(input_path),
                ],
                check=False,
                capture_output=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired as error:
            raise PdfToolError("La conversión tardó demasiado y fue cancelada.") from error
        except OSError as error:
            raise PdfToolError("No se pudo iniciar LibreOffice para convertir el documento.") from error
        pdf_path = Path(directory) / "documento.pdf"
        if result.returncode != 0 or not pdf_path.is_file():
            raise PdfToolError(
                "LibreOffice no pudo convertir el documento. Verifica que el DOCX no esté dañado."
            )
        pdf_data = pdf_path.read_bytes()
        return validate_bytes(pdf_data, kind="pdf")
