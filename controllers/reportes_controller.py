from flask import Blueprint, request,jsonify,send_file

from models import db

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from datetime import datetime,timedelta
from io import BytesIO

reportes_bp=Blueprint('reportes_bp', __name__)

def serialize(obj):
    if isinstance(obj, timedelta):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)._name_} is not JSON serializable")

def validar_formatear_fechas(data):
    try:
        ini_date = datetime.strptime(data['ini_date'], '%Y-%m-%d')
        fin_date = datetime.strptime(data['fin_date'], '%Y-%m-%d')
        return ini_date, fin_date, None
    except ValueError as e:
        return None, None, str(e)

def ejecutar_sp_general(sp,ini_date, fin_date):
    conn = db.engine.raw_connection()
    try:
        cursor = conn.cursor()
        cursor.callproc(sp, [ini_date, fin_date])
        marcas = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        results = [dict(zip(col_names, row)) for row in marcas]
    finally:
        cursor.close()
        conn.close()
    return results

def ejecutar_sp_user(sp,ini_date, fin_date,iduser):
    conn = db.engine.raw_connection()
    try:
        cursor = conn.cursor()
        cursor.callproc(sp, [ini_date, fin_date,iduser])
        marcas = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        results = [dict(zip(col_names, row)) for row in marcas]
    finally:
        cursor.close()
        conn.close()
    return results

def sp_falta_user(ini_date, fin_date,mes,iduser):
    conn = db.engine.raw_connection()
    try:
        cursor = conn.cursor()
        cursor.callproc('ObtenerAusencias', [ini_date, fin_date,mes,iduser])
        marcas = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        results = [dict(zip(col_names, row)) for row in marcas]
    finally:
        cursor.close()
        conn.close()
    return results

def crear_pdf(titulo,cabeceras,ancho,serializable_results, agregar_sum=False):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Paragraph(titulo, styles['Title']))

    data = [cabeceras]
    sumatoria = 0
    for result in serializable_results:
        fila = []
        for key, value in result.items():
            fila.append(value)
            if key == 'Min. Tarde' and isinstance(value, (int, float)):
                sumatoria += value
        data.append(fila)

    table = Table(data, colWidths=[doc.width/ancho]*8)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)
    elements.append(table)

    if agregar_sum:
        elements.append(Spacer(1, 12))
        bold_style = ParagraphStyle(name='Bold', parent=styles['Normal'], fontName='Helvetica-Bold')
        elements.append(Paragraph(f"Sumatoria de minutos tarde: {sumatoria}", bold_style))

    doc.build(elements)

    buffer.seek(0)
    return buffer

@reportes_bp.route('/marcas_general', methods=['POST'])
def get_marcas_general():
    #Obtener datos
    data = request.json
    ini_date, fin_date, error = validar_formatear_fechas(data)
    if error:
        return jsonify({'error': error}), 400

    print(f"Filtrando marcaciones desde {ini_date} hasta {fin_date}")

    results = ejecutar_sp_general('marcaciones_generales',ini_date,fin_date)
    if not results:
        print("No se encontraron marcaciones para el rango de fechas especificado.")

    #Formato para brindar resultados en formato JSON
    serializable_results = []
    for result in results:
        serializable_result = {}
        for key, value in result.items():
            if isinstance(value, timedelta):
                serializable_result[key] = str(value)
            else:
                serializable_result[key] = value
        serializable_results.append(serializable_result)

    titulo = f"Reporte general de marcaciones del {ini_date.date()} hasta {fin_date.date()}"
    cabeceras = ['Nombre', 'Apellido', 'DNI', 'Fecha', 'Entrada', 'Inicio Break', 'Fin Break', 'Salida']

    buffer = crear_pdf(titulo,cabeceras,7.0,serializable_results)
    return send_file(buffer, as_attachment=True, download_name="reporte_marcas_general.pdf", mimetype='application/pdf')

@reportes_bp.route('/marcas_user', methods=['POST'])
def get_marcas_user():
    data = request.json
    ini_date, fin_date, error = validar_formatear_fechas(data)
    if error:
        return jsonify({'error': error}), 400

    print(f"Filtrando marcaciones desde {ini_date} hasta {fin_date}")

    results = ejecutar_sp_user('marcaciones_por_usuario',ini_date,fin_date,data['idUser'])
    if not results:
        print("No se encontraron marcaciones para el rango de fechas especificado.")

    #Formato para brindar resultados en formato JSON
    serializable_results = []
    for result in results:
        serializable_result = {}
        for key, value in result.items():
            if isinstance(value, timedelta):
                serializable_result[key] = str(value)
            else:
                serializable_result[key] = value
        serializable_results.append(serializable_result)

    titulo = f"Reporte de marcaciones del {ini_date.date()} hasta {fin_date.date()}"
    cabeceras = ['Nombre', 'Apellido', 'DNI', 'Fecha', 'Entrada', 'Inicio Break', 'Fin Break', 'Salida']

    buffer = crear_pdf(titulo,cabeceras,7.0,serializable_results)
    return send_file(buffer, as_attachment=True, download_name="reporte_marcas_user.pdf", mimetype='application/pdf')

@reportes_bp.route('/minutos_tarde_fecha', methods=['POST'])
def get_min_tarde_fecha():
    data = request.json
    ini_date, fin_date, error = validar_formatear_fechas(data)
    if error:
        return jsonify({'error': error}), 400

    print(f"Filtrando marcaciones desde {ini_date} hasta {fin_date}")

    results = ejecutar_sp_general('min_tarde_fecha',ini_date,fin_date)
    if not results:
        print("No se encontraron marcaciones para el rango de fechas especificado.")

    #Formato para brindar resultados en formato JSON
    serializable_results = []
    for result in results:
        serializable_result = {}
        for key, value in result.items():
            if isinstance(value, timedelta):
                serializable_result[key] = str(value)
            else:
                serializable_result[key] = value
        serializable_results.append(serializable_result)

    titulo = f"Reporte general de minutos de tardanza del {ini_date.date()} hasta {fin_date.date()}"
    cabeceras = ['Nombre', 'Apellido', 'DNI', 'fecha', 'Min. Tarde']

    buffer = crear_pdf(titulo,cabeceras,5.0,serializable_results)
    return send_file(buffer, as_attachment=True, download_name="reporte_min_tarde_fecha.pdf", mimetype='application/pdf')

@reportes_bp.route('/minutos_tarde_user', methods=['POST'])
def get_min_tarde_user():
    data = request.json
    ini_date, fin_date, error = validar_formatear_fechas(data)
    if error:
        return jsonify({'error': error}), 400

    print(f"Filtrando marcaciones desde {ini_date} hasta {fin_date}")

    results = ejecutar_sp_user('min_tarde_user',ini_date,fin_date,data['idUser'])
    if not results:
        print("No se encontraron marcaciones para el rango de fechas especificado.")

    #Formato para brindar resultados en formato JSON
    serializable_results = []
    for result in results:
        serializable_result = {}
        for key, value in result.items():
            if isinstance(value, timedelta):
                serializable_result[key] = str(value)
            else:
                serializable_result[key] = value
        serializable_results.append(serializable_result)

    titulo = f"Reporte de minutos de tardanza del {ini_date.date()} hasta {fin_date.date()}"
    cabeceras = ['Nombre', 'Apellido', 'DNI', 'fecha', 'Min. Tarde']

    buffer = crear_pdf(titulo,cabeceras,5.0,serializable_results,True)
    return send_file(buffer, as_attachment=True, download_name="reporte_min_tarde_user.pdf", mimetype='application/pdf')

@reportes_bp.route('/falta_user', methods=['POST'])
def get_falta_user():
    data = request.json
    ini_date, fin_date, error = validar_formatear_fechas(data)
    if error:
        return jsonify({'error': error}), 400

    print(f"Filtrando faltas desde {ini_date} hasta {fin_date}")

    results = sp_falta_user(ini_date,fin_date,data['mes'],data['idUser'])
    if not results:
        print("No se encontraron marcaciones para el rango de fechas especificado.")

    #Formato para brindar resultados en formato JSON
    serializable_results = []
    for result in results:
        serializable_result = {}
        for key, value in result.items():
            if isinstance(value, timedelta):
                serializable_result[key] = str(value)
            else:
                serializable_result[key] = value
        serializable_results.append(serializable_result)

    titulo = f"Reporte de faltas del {ini_date.date()} hasta {fin_date.date()}"
    cabeceras = ['Nombre completo', 'Fechas faltadas', 'Nro. Días faltados']

    buffer = crear_pdf(titulo,cabeceras,2.4,serializable_results)
    return send_file(buffer, as_attachment=True, download_name="reporte_falta_user.pdf", mimetype='application/pdf')