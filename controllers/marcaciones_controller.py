from flask import Blueprint, request,jsonify,send_file
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from models import db
from models.horario import Horario
from models.usuario_horarios import UsuarioHorarios
import cv2
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity,create_access_token
from models.usuario import Usuario
from models.marcaciones import Marcacion
from werkzeug.security import check_password_hash,generate_password_hash
import face_recognition
import base64
import numpy as np
from io import BytesIO
from PIL import Image
from datetime import datetime,timedelta
import pytz
from pytz import timezone
from sqlalchemy import and_


marcaciones_bp=Blueprint('marcaciones_bp', __name__)

peru_tz = pytz.timezone('America/Lima')


@marcaciones_bp.route('/marcar_entrada', methods=['POST'])
def marcar_entrada():
    data = request.json
    id_usuario = data.get('idUsuario')

    if not id_usuario:
        return jsonify({'success': False, 'message': 'Faltan datos'}), 400

    hora_actual_peru = datetime.now(peru_tz)
    dia_semana_actual = hora_actual_peru.strftime('%A')  # Obtener el día de la semana actual en inglés

    # Mapeo de días de la semana en inglés a español
    dia_semana_en_espanol = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miercoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sabado',
        'Sunday': 'Domingo'
    }

    dia_semana_actual_es = dia_semana_en_espanol[dia_semana_actual]  # Convertir el día de la semana actual a español
    print(f"Hoy es: {dia_semana_actual_es}")  # Debug: imprimir el día actual en español

    # Obtener todos los horarios asignados al usuario
    usuario_horarios = UsuarioHorarios.query.filter_by(id_usuario=id_usuario).all()

    if not usuario_horarios:
        return jsonify({'success': False, 'message': 'No se encontró un horario para este usuario'}), 400

    horario_correcto = False
    advertencia = None
    impuntual = False
    min_tardes = 0  # Inicializar los minutos de tardanza en 0

    for usuario_horario in usuario_horarios:
        horario = Horario.query.get(usuario_horario.id_horario)
        print(f"Evaluando horario: {horario.dia_semana}")  # Debug: imprimir el día asignado del horario

        if dia_semana_actual_es == horario.dia_semana:
            horario_correcto = True
            hora_inicio = horario.hora_inicio
            hora_fin = horario.hora_fin

            if hora_inicio <= hora_actual_peru.time() <= hora_fin:
                # Verificar impuntualidad
                margen_impuntualidad = timedelta(minutes=15)
                hora_limite_impuntualidad = (datetime.combine(datetime.today(), hora_inicio) + margen_impuntualidad).time()

                impuntual = hora_actual_peru.time() > hora_limite_impuntualidad
                if impuntual:
                    # Calcular los minutos de tardanza
                    hora_limite_impuntualidad_datetime = peru_tz.localize(datetime.combine(datetime.today(), hora_limite_impuntualidad))
                    tardanza = hora_actual_peru - hora_limite_impuntualidad_datetime
                    min_tardes = int(tardanza.total_seconds() // 60)  # Convertir a minutos

                break
            else:
                advertencia = 'Advertencia: Está marcando entrada fuera de su rango de horas asignadas.'
        else:
            advertencia = 'Advertencia: Está marcando entrada fuera de su día de horario asignado.'

    if not horario_correcto:
        return jsonify({'success': False, 'message': 'No tiene horario asignado para el día de hoy'}), 400

    nueva_entrada = Marcacion(
        idUsuario=id_usuario,
        hora_inicio=hora_actual_peru,
        est_falta=1,  # Establecer est_falta en 1
        min_tarde=min_tardes  # Asignar los minutos de tardanza
    )

    db.session.add(nueva_entrada)
    db.session.commit()

    response_message = 'Hora de entrada registrada con éxito'
    if advertencia:
        response_message += f'. {advertencia}'

    return jsonify({'success': True, 'message': response_message, 'impuntual': impuntual}), 200
@marcaciones_bp.route('/marcar_salida', methods=['POST'])
def marcar_salida():
    data = request.json
    id_usuario = data.get('idUsuario')

    if not id_usuario:
        return jsonify({'success': False, 'message': 'Faltan datos'}), 400

    marcacion = Marcacion.query.filter_by(idUsuario=id_usuario).order_by(Marcacion.id_marcaciones.desc()).first()

    if not marcacion or marcacion.hora_fin is not None:
        return jsonify({'success': True, 'message': 'No se encontró una entrada sin salida para este usuario'}), 200

    hora_actual_peru = datetime.now(peru_tz)
    dia_semana_actual = hora_actual_peru.strftime('%A')

    dia_semana_en_espanol = {
        'Monday': 'Lunes',
        'Tuesday': 'Martes',
        'Wednesday': 'Miércoles',
        'Thursday': 'Jueves',
        'Friday': 'Viernes',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }

    dia_semana_actual_es = dia_semana_en_espanol[dia_semana_actual]

    usuario_horarios = UsuarioHorarios.query.filter_by(id_usuario=id_usuario).all()

    if not usuario_horarios:
        return jsonify({'success': False, 'message': 'No se encontró un horario para este usuario'}), 400

    horario_correcto = False
    salida_temprana = False
    advertencia = None

    for usuario_horario in usuario_horarios:
        horario = Horario.query.get(usuario_horario.id_horario)

        if dia_semana_actual_es == horario.dia_semana:
            horario_correcto = True
            hora_inicio = horario.hora_inicio
            hora_fin = horario.hora_fin

            # Permitir registrar salida si es antes del inicio del horario de trabajo
            if hora_actual_peru.time() < hora_inicio:
                break

            # Permitir registrar salida solo en los últimos 15 minutos del horario de trabajo
            hora_fin_con_margen = (datetime.combine(datetime.today(), hora_fin) - timedelta(minutes=15)).time()
            if hora_actual_peru.time() < hora_fin_con_margen:
                return jsonify({'success': False, 'message': 'No se puede registrar la salida más de 15 minutos antes de la hora de finalización'}), 200

            salida_temprana = hora_actual_peru.time() < hora_fin
            break

    if not horario_correcto:
        return jsonify({'success': False, 'message': 'No tiene horario asignado para el día de hoy'}), 400

    if marcacion.hora_inicio:
        hora_inicio_peru = peru_tz.localize(marcacion.hora_inicio)
        delta = hora_actual_peru - hora_inicio_peru
        segundos_trabajados = delta.total_seconds()

        if marcacion.ini_break and marcacion.end_break:
            break_start = datetime.combine(datetime.today(), marcacion.ini_break)
            break_end = datetime.combine(datetime.today(), marcacion.end_break)
            break_duration = (break_end - break_start).total_seconds()
            segundos_trabajados -= break_duration

        horas_trabajadas = round(segundos_trabajados / 3600, 2)

    marcacion.hora_fin = hora_actual_peru
    marcacion.horas_trabajadas = horas_trabajadas
    db.session.commit()

    response_message = 'Hora de salida registrada con éxito'
    if advertencia:
        response_message += f'. {advertencia}'

    return jsonify({
        'success': True,
        'message': response_message,
        'salida_temprana': salida_temprana
    }), 200
@marcaciones_bp.route('/start_break', methods=['POST'])
def start_break():
    data = request.get_json()
    user_id = data.get('idUsuario')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required.'})

    current_time = datetime.now(peru_tz).time()

    # Assuming you want to update the last marcacion for the user
    marcacion = Marcacion.query.filter_by(idUsuario=user_id).order_by(Marcacion.id_marcaciones.desc()).first()
    if marcacion:
        marcacion.ini_break = current_time
        db.session.commit()
        return jsonify({'success': True, 'message': 'Break started successfully.'})
    else:
        return jsonify({'success': False, 'message': 'No marcacion found for the user.'})

@marcaciones_bp.route('/stop_break', methods=['POST'])
def stop_break():
    data = request.get_json()
    user_id = data.get('idUsuario')
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required.'})

    current_time = datetime.now(peru_tz).time()

    # Assuming you want to update the last marcacion for the user
    marcacion = Marcacion.query.filter_by(idUsuario=user_id).order_by(Marcacion.id_marcaciones.desc()).first()
    if marcacion:
        marcacion.end_break = current_time
        db.session.commit()
        return jsonify({'success': True, 'message': 'Break ended successfully.'})
    else:
        return jsonify({'success': False, 'message': 'No marcacion found for the user.'})
    
@marcaciones_bp.route('/asistencia', methods=['POST'])
def generar_asistencia():
    data = request.json

    if 'idUsuario' not in data:
        return jsonify({'error': 'idUsuario is required'}), 400

    id_usuario = data['idUsuario']

    try:
        fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%dT%H:%M:%S')
        fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%dT%H:%M:%S')
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # Asegurarse de que la fecha_fin incluye hasta el final del día
    fecha_inicio = fecha_inicio.replace(hour=00, minute=00, second=00, microsecond=0)
    fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59, microsecond=999999)

    print(f"Filtrando marcaciones desde {fecha_inicio} hasta {fecha_fin} para el usuario {id_usuario}")

    marcaciones = Marcacion.query.filter( and_(
            Marcacion.hora_inicio >= fecha_inicio,
            Marcacion.hora_inicio <= fecha_fin,
            Marcacion.idUsuario == id_usuario
        )
    ).all()

    if not marcaciones:
        print("No se encontraron marcaciones para el rango de fechas especificado.")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Título del documento
    styles = getSampleStyleSheet()
    titulo = f"Reporte de Asistencia del {fecha_inicio.date()} al {fecha_fin.date()}"
    elements.append(Paragraph(titulo, styles['Title']))

    # Encabezado de la tabla
    data = [['Nombre', 'Apellido', 'DNI', 'Hora Inicio', 'Hora Fin']]

    for marcacion in marcaciones:
        usuario = Usuario.query.get(marcacion.idUsuario)
        fila = [
            usuario.nombre,
            usuario.apell,
            usuario.dni,
            marcacion.hora_inicio.strftime('%Y-%m-%d %H:%M:%S'),
            marcacion.hora_fin.strftime('%Y-%m-%d %H:%M:%S') if marcacion.hora_fin else 'N/A'
        ]
        data.append(fila)

    # Crear la tabla
    table = Table(data, colWidths=[doc.width/5.0]*5)
    
    # Estilo de la tabla
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
    doc.build(elements)
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="reporte_asistencia.pdf", mimetype='application/pdf')