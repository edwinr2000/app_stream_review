from io import BytesIO
from urllib.parse import urlparse

import qrcode
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)


QR_ERROR_LEVELS = {
    "Bajo (7 %)": ERROR_CORRECT_L,
    "Medio (15 %)": ERROR_CORRECT_M,
    "Alto (25 %)": ERROR_CORRECT_Q,
    "Máximo (30 %)": ERROR_CORRECT_H,
}


def escape_wifi_field(value: str) -> str:
    for character in ("\\", ";", ",", ":", '"'):
        value = value.replace(character, "\\" + character)
    return value


def validate_text_payload(content: str) -> str:
    content = content.strip()
    if not content:
        raise ValueError("Escribe un texto o una URL.")
    if "://" in content:
        parsed = urlparse(content)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("La URL debe comenzar con http:// o https:// y tener un dominio.")
    if len(content.encode("utf-8")) > 2000:
        raise ValueError("El contenido supera el máximo de 2.000 bytes.")
    return content


def wifi_payload(ssid: str, password: str, security: str) -> str:
    ssid = ssid.strip()
    if not ssid:
        raise ValueError("Escribe el nombre de la red Wi-Fi.")
    if security not in {"WPA/WPA2", "WEP", "Sin contraseña"}:
        raise ValueError("Selecciona un tipo de seguridad válido.")
    if security != "Sin contraseña" and not password:
        raise ValueError("Escribe la contraseña de la red Wi-Fi.")
    security_code = {
        "WPA/WPA2": "WPA",
        "WEP": "WEP",
        "Sin contraseña": "nopass",
    }[security]
    payload = f"WIFI:T:{security_code};S:{escape_wifi_field(ssid)};"
    if security != "Sin contraseña":
        payload += f"P:{escape_wifi_field(password)};"
    payload += ";"
    if len(payload.encode("utf-8")) > 2000:
        raise ValueError("El contenido supera el máximo de 2.000 bytes.")
    return payload


def generate_qr_png(
    content: str,
    *,
    error_correction: int = ERROR_CORRECT_M,
    box_size: int = 8,
) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=error_correction,
        box_size=box_size,
        border=4,
    )
    qr.add_data(content)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
