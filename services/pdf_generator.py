from io import BytesIO
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOGO_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "../assets/logo.png")
)


# ============================================================
# UTILIDADES
# ============================================================

def formato_moneda(valor):
    """Formatea valores como moneda colombiana."""

    if valor is None:
        valor = 0

    try:
        valor = float(valor)
    except (ValueError, TypeError):
        valor = 0

    return f"$ {valor:,.0f}".replace(",", ".")


# ============================================================
# GENERADOR PDF
# ============================================================

def generar_pdf_pedido(
    pedido_id,
    info_pedido,
    df_detalle,
    cliente_info,
):
    """
    Genera un comprobante comercial de pedido
    y retorna el PDF en formato bytes.
    """

    # ============================================================
    # FECHA DE EMISIÓN
    # Zona horaria:
    # Bogotá 🇨🇴 / Lima 🇵🇪 / Quito 🇪🇨
    # ============================================================

    zona_horaria = ZoneInfo("America/Bogota")

    fecha_actual = datetime.now(zona_horaria)

    fecha = fecha_actual.strftime("%d/%m/%Y %I:%M %p")


    # ============================================================
    # DOCUMENTO PDF
    # ============================================================

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=35,
        bottomMargin=35,
    )

    story = []

    styles = getSampleStyleSheet()


    # ============================================================
    # PALETA DE COLORES
    # ============================================================

    COLOR_PRIMARIO = colors.HexColor("#0F172A")
    COLOR_SECUNDARIO = colors.HexColor("#4F46E5")

    COLOR_FONDO = colors.HexColor("#F8FAFC")
    COLOR_GRIS = colors.HexColor("#64748B")
    COLOR_BORDE = colors.HexColor("#E2E8F0")

    COLOR_TOTAL = colors.HexColor("#EEF2FF")


    # ============================================================
    # ESTILOS
    # ============================================================

    titulo_empresa = ParagraphStyle(
        "TituloEmpresa",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=COLOR_PRIMARIO,
    )

    titulo_documento = ParagraphStyle(
        "TituloDocumento",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        alignment=TA_CENTER,
        textColor=colors.white,
    )

    numero_documento = ParagraphStyle(
        "NumeroDocumento",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.white,
    )

    titulo_seccion = ParagraphStyle(
        "TituloSeccion",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=COLOR_SECUNDARIO,
        spaceAfter=5,
    )

    normal_style = ParagraphStyle(
        "NormalFactura",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=COLOR_PRIMARIO,
    )

    normal_gris = ParagraphStyle(
        "NormalGris",
        parent=normal_style,
        textColor=COLOR_GRIS,
    )

    bold_style = ParagraphStyle(
        "BoldFactura",
        parent=normal_style,
        fontName="Helvetica-Bold",
    )

    tabla_header = ParagraphStyle(
        "TablaHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=colors.white,
        alignment=TA_CENTER,
    )

    tabla_texto = ParagraphStyle(
        "TablaTexto",
        parent=normal_style,
        fontSize=8,
    )

    total_style = ParagraphStyle(
        "TotalStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        alignment=TA_RIGHT,
        textColor=COLOR_PRIMARIO,
    )


    # ============================================================
    # ESTADO DEL PEDIDO
    # ============================================================

    estado_id = info_pedido.get("estado_id")


    estados_map = {

        1: {
            "codigo": "PENDIENTE",
            "nombre": "PENDIENTE DE APROBACIÓN",
        },

        2: {
            "codigo": "APROBADO",
            "nombre": "APROBADO Y EN PROCESO",
        },

        3: {
            "codigo": "ENVIADO",
            "nombre": "ENVIADO / DESPACHADO",
        },

        4: {
            "codigo": "ENTREGADO",
            "nombre": "ENTREGADO CON ÉXITO",
        },

        5: {
            "codigo": "CANCELADO",
            "nombre": "CANCELADO",
        },

    }


    try:

        estado_id = int(estado_id)

    except (ValueError, TypeError):

        estado_id = 1


    estado_info = estados_map.get(
        estado_id,
        estados_map[1],
    )


    estado = estado_info["codigo"]

    estado_nombre = estado_info["nombre"]


    # ============================================================
    # CONFIGURACIÓN VISUAL DE LOS ESTADOS
    # ============================================================

    estados_config = {

        "PENDIENTE": {
            "color": colors.HexColor("#CA8A04"),
            "fondo": colors.HexColor("#FEF9C3"),
            "icono": "●",
        },

        "APROBADO": {
            "color": colors.HexColor("#2563EB"),
            "fondo": colors.HexColor("#DBEAFE"),
            "icono": "✓",
        },

        "ENVIADO": {
            "color": colors.HexColor("#7C3AED"),
            "fondo": colors.HexColor("#EDE9FE"),
            "icono": "➜",
        },

        "ENTREGADO": {
            "color": colors.HexColor("#16A34A"),
            "fondo": colors.HexColor("#DCFCE7"),
            "icono": "✓",
        },

        "CANCELADO": {
            "color": colors.HexColor("#DC2626"),
            "fondo": colors.HexColor("#FEE2E2"),
            "icono": "✕",
        },

    }


    config_estado = estados_config.get(
        estado,
        estados_config["PENDIENTE"],
    )


    # ============================================================
    # HEADER - EMPRESA
    # ============================================================

    if os.path.exists(LOGO_PATH):

        try:

            logo = Image(
                LOGO_PATH,
                width=75,
                height=75,
            )


            empresa_info = Table(
                [[

                    logo,

                    Paragraph(
                        """
                        <b>INVENTAPP</b><br/>
                        <font size="8" color="#64748B">
                        Sistema de Pedidos e Inventario<br/>
                        Bogotá, Colombia
                        </font>
                        """,
                        titulo_empresa,
                    ),

                ]],

                colWidths=[85, 215],
            )


            empresa_info.setStyle(
                TableStyle([

                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),

                ])
            )


        except Exception as e:

            print(f"Error cargando logo: {e}")


            empresa_info = Paragraph(
                """
                <b>INVENTAPP</b><br/>
                <font size="8">
                Sistema de Pedidos e Inventario
                </font>
                """,
                titulo_empresa,
            )


    else:

        print(f"Logo no encontrado: {LOGO_PATH}")


        empresa_info = Paragraph(
            """
            <b>INVENTAPP</b><br/>
            <font size="8">
            Sistema de Pedidos e Inventario
            </font>
            """,
            titulo_empresa,
        )


    # ============================================================
    # NÚMERO DEL PEDIDO
    # ============================================================

    try:

        numero_pedido = f"PED-{int(pedido_id):06d}"

    except (ValueError, TypeError):

        numero_pedido = f"PED-{pedido_id}"


    # ============================================================
    # CAJA DEL PEDIDO
    # ============================================================

    pedido_box = Table(
        [

            [
                Paragraph(
                    "COMPROBANTE DE PEDIDO",
                    titulo_documento,
                )
            ],

            [
                Paragraph(
                    numero_pedido,
                    numero_documento,
                )
            ],

        ],

        colWidths=[200],
    )


    pedido_box.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                COLOR_SECUNDARIO,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                12,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                12,
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),

        ])
    )


    # ============================================================
    # HEADER COMPLETO
    # ============================================================

    header = Table(
        [[

            empresa_info,
            pedido_box,

        ]],

        colWidths=[300, 200],
    )


    header.setStyle(
        TableStyle([

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),

        ])
    )


    story.append(header)

    story.append(
        Spacer(1, 20)
    )


    # ============================================================
    # ESTILO DEL BADGE
    # ============================================================

    badge_style = ParagraphStyle(
        "BadgeEstado",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        alignment=TA_CENTER,
        textColor=config_estado["color"],
    )


    # ============================================================
    # BADGE DEL ESTADO
    # ============================================================

    badge_estado = Table(
        [[

            Paragraph(
                f"{config_estado['icono']} {estado_nombre}",
                badge_style,
            )

        ]],

        colWidths=[160],
    )


    badge_estado.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                config_estado["fondo"],
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                config_estado["color"],
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),

        ])
    )


    # ============================================================
    # INFORMACIÓN DEL DOCUMENTO
    # ============================================================

    info_documento = Table(
        [[

            Paragraph(
                f"<b>Fecha de emisión:</b> {fecha}",
                normal_style,
            ),

            badge_estado,

        ]],

        colWidths=[340, 160],
    )


    info_documento.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                COLOR_FONDO,
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                COLOR_BORDE,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                12,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                12,
            ),

            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),

            (
                "ALIGN",
                (1, 0),
                (1, 0),
                "RIGHT",
            ),

        ])
    )


    story.append(
        info_documento
    )

    story.append(
        Spacer(1, 18)
    )


    # ============================================================
    # DATOS DEL CLIENTE
    # ============================================================

    cliente_nombre = cliente_info.get(
        "nombre_empresa",
        "Cliente no registrado",
    )

    contacto = cliente_info.get(
        "contacto_nombre",
        "N/A",
    )

    direccion = cliente_info.get(
        "direccion",
        "N/A",
    )

    ciudad = cliente_info.get(
        "ciudad",
        "",
    )

    email = cliente_info.get(
        "email",
        "N/A",
    )


    cliente_data = [

        [

            Paragraph(
                "DATOS DEL CLIENTE",
                titulo_seccion,
            )

        ],

        [

            Paragraph(
                f"<b>{cliente_nombre}</b>",
                bold_style,
            )

        ],

        [

            Paragraph(
                f"<b>Contacto:</b> {contacto}",
                normal_gris,
            )

        ],

        [

            Paragraph(
                f"<b>Dirección:</b> {direccion}, {ciudad}",
                normal_gris,
            )

        ],

        [

            Paragraph(
                f"<b>Correo:</b> {email}",
                normal_gris,
            )

        ],

    ]


    t_cliente = Table(
        cliente_data,
        colWidths=[500],
    )


    t_cliente.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                COLOR_FONDO,
            ),

            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                COLOR_BORDE,
            ),

            (
                "LINEBELOW",
                (0, 0),
                (-1, 0),
                0.5,
                COLOR_BORDE,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),

            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                12,
            ),

            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                12,
            ),

        ])
    )


    story.append(
        t_cliente
    )

    story.append(
        Spacer(1, 20)
    )


    # ============================================================
    # TABLA DE PRODUCTOS
    # ============================================================

    table_data = [

        [

            Paragraph(
                "PRODUCTO",
                tabla_header,
            ),

            Paragraph(
                "CANT.",
                tabla_header,
            ),

            Paragraph(
                "PRECIO UNIT.",
                tabla_header,
            ),

            Paragraph(
                "TOTAL",
                tabla_header,
            ),

        ]

    ]


    # ============================================================
    # DETALLE DE PRODUCTOS
    # ============================================================

    for _, row in df_detalle.iterrows():

        producto = str(
            row.get(
                "producto_nombre",
                "Producto",
            )
        )

        cantidad = row.get(
            "cantidad",
            0,
        )

        precio_unitario = row.get(
            "precio_unitario",
            0,
        )

        subtotal_linea = row.get(
            "subtotal_linea",
            0,
        )


        table_data.append(

            [

                Paragraph(
                    producto,
                    tabla_texto,
                ),

                Paragraph(
                    str(cantidad),
                    tabla_texto,
                ),

                Paragraph(
                    formato_moneda(
                        precio_unitario
                    ),
                    tabla_texto,
                ),

                Paragraph(
                    formato_moneda(
                        subtotal_linea
                    ),
                    tabla_texto,
                ),

            ]

        )


    # ============================================================
    # TABLA DETALLE
    # ============================================================

    t_detalle = Table(

        table_data,

        colWidths=[
            250,
            60,
            95,
            95,
        ],

        repeatRows=1,

    )


    t_detalle.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                COLOR_PRIMARIO,
            ),

            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                COLOR_BORDE,
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8,
            ),

            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "RIGHT",
            ),

            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    COLOR_FONDO,
                ],
            ),

        ])
    )


    story.append(
        t_detalle
    )

    story.append(
        Spacer(1, 18)
    )


    # ============================================================
    # TOTALES
    # ============================================================

    subtotal = info_pedido.get(
        "subtotal",
        0,
    )

    impuestos = info_pedido.get(
        "impuestos",
        0,
    )

    total = info_pedido.get(
        "total",
        0,
    )


    totales_data = [

        [

            Paragraph(
                "Subtotal",
                normal_gris,
            ),

            Paragraph(
                formato_moneda(subtotal),
                normal_style,
            ),

        ],

        [

            Paragraph(
                "IVA",
                normal_gris,
            ),

            Paragraph(
                formato_moneda(impuestos),
                normal_style,
            ),

        ],

        [

            Paragraph(
                "TOTAL",
                bold_style,
            ),

            Paragraph(
                formato_moneda(total),
                total_style,
            ),

        ],

    ]


    t_totales = Table(

        totales_data,

        colWidths=[
            150,
            150,
        ],

        hAlign="RIGHT",

    )


    t_totales.setStyle(
        TableStyle([

            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "RIGHT",
            ),

            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),

            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),

            (
                "BACKGROUND",
                (0, 2),
                (-1, 2),
                COLOR_TOTAL,
            ),

            (
                "LINEABOVE",
                (0, 2),
                (-1, 2),
                1.5,
                COLOR_SECUNDARIO,
            ),

        ])
    )


    story.append(
        t_totales
    )

    story.append(
        Spacer(1, 30)
    )


    # ============================================================
    # FOOTER
    # ============================================================

    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=8,
        leading=12,
        textColor=COLOR_GRIS,
    )


    footer = Paragraph(
        """
        <b>Gracias por su compra</b><br/>
        <font color="#64748B">
        Este documento es un comprobante generado por InventApp.<br/>
        Sistema de Pedidos e Inventario | by EdwinTorresR
        </font>
        """,
        footer_style,
    )


    story.append(
        footer
    )


    # ============================================================
    # CONSTRUIR PDF
    # ============================================================

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()