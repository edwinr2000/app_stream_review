from io import BytesIO
import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Ruta absoluta robusta para encontrar el logo sin importar dónde se ejecute la app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.normpath(os.path.join(BASE_DIR, "../assets/logo.png"))


def generar_pdf_pedido(pedido_id, info_pedido, df_detalle, cliente_info):
  """Genera el PDF de la factura/comprobante de un pedido y retorna los bytes"""
  buffer = BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=36,
      leftMargin=36,
      topMargin=36,
      bottomMargin=36,
  )
  story = []
  styles = getSampleStyleSheet()

  # Estilos personalizados
  title_style = ParagraphStyle(
      'InvoiceTitle',
      parent=styles['Heading1'],
      fontSize=18,
      textColor=colors.HexColor('#1f2937'),
      spaceAfter=6,
  )
  normal_style = ParagraphStyle(
      'InvoiceNormal',
      parent=styles['Normal'],
      fontSize=10,
      textColor=colors.HexColor('#4b5563'),
  )
  bold_style = ParagraphStyle(
      'InvoiceBold', parent=normal_style, fontName='Helvetica-Bold'
  )

  # --- CARGAR LOGO EN EL ENCABEZADO ---
  if os.path.exists(LOGO_PATH):
    try:
      logo = Image(LOGO_PATH, width=100, height=40)
      story.append(logo)
      story.append(Spacer(1, 10))
    except Exception as e:
      print(f"Error al procesar la imagen del logo: {e}")
  else:
    print(f"⚠️ No se encontró el logo en la ruta calculada: {LOGO_PATH}")

  # Encabezado
  story.append(
      Paragraph(
          f"<b>COMPROBANTE DE PEDIDO # {pedido_id}</b>", title_style
      )
  )
  story.append(
      Paragraph(
          f"<b>Fecha de Emisión:</b>"
          f" {info_pedido.get('fecha_pedido', 'N/A')}",
          normal_style,
      )
  )
  story.append(Spacer(1, 15))

  # Datos del Cliente y Empresa
  cliente_data = [
      [
          Paragraph("<b>Cliente:</b>", bold_style),
          Paragraph(
              f"{cliente_info.get('nombre_empresa', 'N/A')} - Contacto:"
              f" {cliente_info.get('contacto_nombre', 'N/A')}",
              normal_style,
          ),
      ],
      [
          Paragraph("<b>Dirección:</b>", bold_style),
          Paragraph(
              f"{cliente_info.get('direccion', 'N/A')},"
              f" {cliente_info.get('ciudad', 'N/A')}",
              normal_style,
          ),
      ],
      [
          Paragraph("<b>Correo:</b>", bold_style),
          Paragraph(cliente_info.get('email', 'N/A'), normal_style),
      ],
  ]
  t_cliente = Table(cliente_data, colWidths=[80, 450])
  t_cliente.setStyle(
      TableStyle([
          ('VALIGN', (0, 0), (-1, -1), 'TOP'),
          ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
      ])
  )
  story.append(t_cliente)
  story.append(Spacer(1, 20))

  # Tabla de Productos / Detalle
  table_data = [[
      Paragraph("<b>Producto</b>", bold_style),
      Paragraph("<b>Cantidad</b>", bold_style),
      Paragraph("<b>Precio Unitario</b>", bold_style),
      Paragraph("<b>Subtotal</b>", bold_style),
  ]]

  for _, row in df_detalle.iterrows():
    table_data.append([
        Paragraph(str(row.get('producto_nombre', 'Producto')), normal_style),
        Paragraph(str(row.get('cantidad', 0)), normal_style),
        Paragraph(f"${row.get('precio_unitario', 0):,.2f}", normal_style),
        Paragraph(f"${row.get('subtotal_linea', 0):,.2f}", normal_style),
    ])

  t_detalle = Table(table_data, colWidths=[230, 70, 110, 120])
  t_detalle.setStyle(
      TableStyle([
          (
              'BACKGROUND',
              (0, 0),
              (-1, 0),
              colors.HexColor('#f3f4f6'),
          ),
          ('FONTSIZE', (0, 0), (-1, -1), 9),
          ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
          ('TOPPADDING', (0, 0), (-1, -1), 6),
          ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
          (
              'GRID',
              (0, 0),
              (-1, -1),
              0.5,
              colors.HexColor('#e5e7eb'),
          ),
      ])
  )
  story.append(t_detalle)
  story.append(Spacer(1, 15))

  # Totales
  subtotal = info_pedido.get('subtotal', 0)
  impuestos = info_pedido.get('impuestos', 0)
  total = info_pedido.get('total', 0)

  totales_data = [
      ['', Paragraph('Subtotal:', normal_style), Paragraph(f'${subtotal:,.2f}', normal_style)],
      ['', Paragraph('Impuestos (IVA):', normal_style), Paragraph(f'${impuestos:,.2f}', normal_style)],
      ['', Paragraph('Total a Pagar:', bold_style), Paragraph(f'<b>${total:,.2f}</b>', bold_style)],
  ]
  t_totales = Table(totales_data, colWidths=[270, 110, 120])
  t_totales.setStyle(
      TableStyle([
          ('FONTSIZE', (0, 0), (-1, -1), 10),
          ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
          ('TOPPADDING', (0, 0), (-1, -1), 4),
          ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
          ('LINEABOVE', (1, -1), (-1, -1), 1, colors.HexColor('#111827')),
      ])
  )
  story.append(t_totales)

  # Construir documento
  doc.build(story)
  buffer.seek(0)
  return buffer.getvalue()