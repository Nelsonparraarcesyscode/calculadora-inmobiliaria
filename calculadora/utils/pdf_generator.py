import io
import logging
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

logger = logging.getLogger(__name__)


def fmt_clp(value):
    return f"${value:,.0f}".replace(",", ".")


def fmt_uf(value):
    return f"{value:,.2f} UF"


def hex_to_color(hex_str):
    return HexColor(hex_str)


def generar_pdf(submission, pdf_config):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=20*mm, bottomMargin=25*mm)

    primary = hex_to_color(pdf_config.color_primario)
    secondary = hex_to_color(pdf_config.color_secundario)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        textColor=primary, fontSize=18, spaceAfter=6*mm
    ))
    styles.add(ParagraphStyle(
        'SectionHeader', parent=styles['Heading2'],
        textColor=primary, fontSize=13, spaceBefore=6*mm, spaceAfter=3*mm
    ))
    styles.add(ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=8, textColor=HexColor('#666666'), alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'ResultPositive', parent=styles['Heading2'],
        textColor=HexColor('#16a34a'), fontSize=14, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'ResultNegative', parent=styles['Heading2'],
        textColor=HexColor('#dc2626'), fontSize=14, alignment=TA_CENTER
    ))

    elements = []

    if pdf_config.logo and pdf_config.logo.name:
        try:
            img = Image(pdf_config.logo.path, width=50*mm, height=20*mm)
            img.hAlign = 'CENTER'
            elements.append(img)
            elements.append(Spacer(1, 3*mm))
        except Exception as e:
            logger.warning("No se pudo cargar el logo del PDF: %s", e)

    elements.append(Paragraph(pdf_config.header_text, styles['CustomTitle']))
    elements.append(Spacer(1, 4*mm))

    elements.append(Paragraph("Datos del Solicitante", styles['SectionHeader']))
    datos_personales = [
        ['Nombre', submission.nombre_completo],
        ['Email', submission.email],
    ]
    if submission.telefono:
        datos_personales.append(['Teléfono', submission.telefono])

    tabla_personal = Table(datos_personales, colWidths=[50*mm, 120*mm])
    tabla_personal.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), secondary),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#ffffff')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(tabla_personal)

    elements.append(Paragraph("Detalle del Crédito", styles['SectionHeader']))
    datos_credito = [
        ['Valor Propiedad', fmt_uf(submission.valor_propiedad)],
        ['Pie', fmt_uf(submission.pie)],
        ['Monto Crédito', fmt_uf(submission.monto_credito)],
        ['Plazo', f"{submission.plazo_anios} años ({submission.plazo_anios * 12} cuotas)"],
        ['Tasa de Interés', f"{submission.tasa_interes}% anual ({submission.tasa_interes_nombre})"],
        ['Valor UF utilizado', fmt_clp(submission.valor_uf)],
        ['Renta Bruta Mensual', fmt_clp(submission.renta_bruta_clp)],
    ]
    if pdf_config.mostrar_deudas:
        datos_credito.append(['Deudas Vigentes', fmt_clp(submission.deudas_vigentes_clp)])

    tabla_credito = Table(datos_credito, colWidths=[50*mm, 120*mm])
    tabla_credito.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), secondary),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#ffffff')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(tabla_credito)

    elements.append(Paragraph("Resultado de la Evaluación", styles['SectionHeader']))
    resultado_style = 'ResultPositive' if submission.califica else 'ResultNegative'
    resultado_text = "CALIFICA" if submission.califica else "NO CALIFICA"
    elements.append(Paragraph(resultado_text, styles[resultado_style]))
    elements.append(Spacer(1, 3*mm))

    datos_resultado = [
        ['Cuota Mensual', f"{fmt_uf(submission.cuota_mensual)}  ({fmt_clp(submission.cuota_mensual_clp)})"],
        ['Relación Cuota/Ingreso', f"{submission.relacion_cuota_ingreso:.2f}% (máximo 25%)"],
        ['Renta Mínima Requerida', fmt_clp(submission.renta_minima_requerida_clp)],
        ['Costo Total del Crédito', fmt_uf(submission.costo_total_credito)],
    ]
    tabla_resultado = Table(datos_resultado, colWidths=[50*mm, 120*mm])
    tabla_resultado.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), primary),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#ffffff')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(tabla_resultado)

    if pdf_config.mostrar_tabla_amortizacion:
        elements.append(Paragraph("Tabla de Amortización (primeros 12 meses)", styles['SectionHeader']))
        r = submission.tasa_interes / 100 / 12
        saldo = submission.monto_credito
        cuota = submission.cuota_mensual
        amort_data = [['Mes', 'Cuota (UF)', 'Interés (UF)', 'Amortización (UF)', 'Saldo (UF)']]
        meses = min(12, submission.plazo_anios * 12)
        for mes in range(1, meses + 1):
            interes = saldo * r
            amortizacion = cuota - interes
            saldo -= amortizacion
            amort_data.append([
                str(mes),
                f"{cuota:,.4f}",
                f"{interes:,.4f}",
                f"{amortizacion:,.4f}",
                f"{max(saldo, 0):,.4f}",
            ])
        tabla_amort = Table(amort_data, colWidths=[15*mm, 30*mm, 30*mm, 35*mm, 35*mm])
        tabla_amort.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(tabla_amort)

    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(pdf_config.footer_text, styles['Footer']))

    doc.build(elements)
    buffer.seek(0)
    return buffer
