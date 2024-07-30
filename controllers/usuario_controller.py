from flask import Blueprint, request,jsonify
from models import db
import cv2
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity,create_access_token,decode_token
from models.usuario import Usuario
from models.horario import Horario
from models.usuario_horarios import UsuarioHorarios
from werkzeug.security import check_password_hash,generate_password_hash
import face_recognition
import base64
import numpy as np
from io import BytesIO
from PIL import Image
from datetime import datetime, time
from sqlalchemy import or_


usuario_bp=Blueprint('usuario_bp', __name__)

@usuario_bp.route('/all_docentes', methods=['GET'])
def all_docentes():
    usuarios = Usuario.query.filter( or_(Usuario.rol == 'Docente', Usuario.rol == 'sub-administrador')).all()
    fields = ['idUsuario', 'nombre', 'apell']
    return jsonify([usuario.to_dict(fields) for usuario in usuarios])

@usuario_bp.route('/usuario', methods=['POST'])
def add_usuario():
    # Verificar que la solicitud es POST y contiene los datos necesarios
    if not request.is_json:
        return jsonify({"error": "La solicitud debe ser JSON"}), 400
    
    data = request.get_json()
    dni = data.get('dni')
    nombre = data.get('nombre')
    apell = data.get('apell')
    telefono = data.get('telefono')
    usuario = data.get('usuario')
    email = data.get('email')
    password = data.get('password')
    fecha_nac = data.get('fecha_nac')
    rol = data.get('rol')
    image_base64 = data.get('image')  # La imagen debe ser enviada como una cadena base64

    if not dni or not nombre or not apell or not telefono or not usuario or not email or not password or not rol or not image_base64:
        return jsonify({"error": "Faltan datos en la solicitud"}), 400

    # Decodificar la imagen base64
    try:
        image_data = np.frombuffer(base64.b64decode(image_base64), np.uint8)
        image_np = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    except Exception as e:
        return jsonify({"error": "Error al procesar la imagen"}), 400

    # Procesar la imagen con face_recognition
    face_encodings = face_recognition.face_encodings(image_np)
    if len(face_encodings) == 0:
        return jsonify({"error": "No se detectó ningún rostro en la imagen"}), 400

    face_encoding = face_encodings[0]

    # Guardar usuario en la base de datos
    hashed_password = generate_password_hash(password)
    nuevo_usuario = Usuario(
        dni=dni,
        nombre=nombre,
        apell=apell,
        telefono=telefono,
        usuario=usuario,
        email=email,
        password=hashed_password,  # Contraseña hasheada
        fecha_nac=fecha_nac,
        rol=rol,
        face_encoding=face_encoding.tobytes()  # Guardar la codificación del rostro
    )
    db.session.add(nuevo_usuario)
    db.session.commit()
    horarios = Horario.query.all()
    for horario in horarios:
        nuevo_usuario_horario = UsuarioHorarios(
            id_usuario=nuevo_usuario.idUsuario,
            id_horario=horario.id_horario,
            diaSemana=horario.dia_semana
        )
        db.session.add(nuevo_usuario_horario)
    db.session.commit()
    return jsonify({'message': 'Usuario añadido correctamente'}), 201


@usuario_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    usuario = data.get('usuario')
    password = data.get('password')
    
    # Buscar usuario por nombre de usuario
    user = Usuario.query.filter_by(usuario=usuario).first()
    
    if user and check_password_hash(user.password, password):
        # Generar token JWT
        access_token = create_access_token(identity=user.idUsuario)
        
        # Preparar los datos del usuario para devolver (sin la contraseña)
        user_data = user.as_dict()
        del user_data['password']
        
        # Devolver respuesta con el token JWT y los datos del usuario
        return jsonify({
            'message': 'Inicio de sesión exitoso',
            'usuario': user_data,
            'access_token': access_token,
            'rol':user.rol
        }), 200
    else:
        return jsonify({'message': 'Nombre de usuario o contraseña incorrectos'}), 401

@usuario_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    usuario = Usuario.query.get_or_404(current_user_id)
    user_data = usuario.as_dict()
    del user_data['password']  # No incluir la contraseña en la respuesta
    return jsonify(user_data)

@usuario_bp.route('/facial_login', methods=['POST'])
def facial_login():
    data = request.get_json()
    if not data or 'image' not in data:
        return jsonify({'success': False, 'message': 'Image is required.'})

    image_data = data['image']

    try:
        # Decodificar la imagen de base64
        image_bytes = base64.b64decode(image_data)
    except base64.binascii.Error as e:
        return jsonify({'success': False, 'message': 'Invalid image data.'})

    image = Image.open(BytesIO(image_bytes)).convert('RGB')

    # Convertir la imagen a formato compatible con face_recognition
    image_np = np.array(image)

    # Procesar la imagen con face_recognition
    face_encodings = face_recognition.face_encodings(image_np)
    if len(face_encodings) == 0:
        return jsonify({'success': False, 'message': 'Rostro no Detectado.'})

    face_encoding = face_encodings[0]

    # Buscar en la base de datos la cara que coincida
    users = Usuario.query.all()
    for user in users:
        user_face_encoding = np.frombuffer(user.face_encoding, dtype=np.float64)
        match = face_recognition.compare_faces([user_face_encoding], face_encoding, tolerance=0.54)
        if match[0]:
            token = create_access_token(identity=user.idUsuario)
            return jsonify({
                'success': True,
                'user_id': user.idUsuario,
                'rol': user.rol,
                'token': token,
                'user_data': {
                    'idUsuario': user.idUsuario
                }
            })
    
    return jsonify({'success': False, 'message': 'Usted es un IMPOSTOR.'})

