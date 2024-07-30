from flask import Flask, render_template, Response, request, redirect, url_for, flash
import cv2 
from config import Config
from controllers.inicializar import initialize_horarios 
import face_recognition
import numpy as np
from models import db, bcrypt, usuario, horario, marcaciones
from controllers.usuario_controller import usuario_bp
from controllers.horario_controller import horario_bp
from controllers.marcaciones_controller import marcaciones_bp
from controllers.reportes_controller import reportes_bp
from models import db
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask import jsonify
from flask_cors import CORS
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
CORS(app)
jwt = JWTManager(app)

app.config.from_object(Config)
db.init_app(app)
bcrypt.init_app(app)
app.register_blueprint(usuario_bp)
app.register_blueprint(horario_bp)
app.register_blueprint(marcaciones_bp)
app.register_blueprint(reportes_bp)




@app.before_request
def create_tables():
    db.create_all()
    initialize_horarios()
    


if __name__ == "__main__":
    print("Iniciando la aplicación Flask")
    app.run(debug=True)

