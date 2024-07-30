from . import db,bcrypt
import base64
from datetime import datetime
class Usuario(db.Model):
    __tablename__ = 'usuario'
    idUsuario = db.Column(db.Integer, primary_key=True)
    dni = db.Column(db.String(20), nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    apell = db.Column(db.String(50), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    usuario = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    fecha_nac = db.Column(db.Date)
    rol = db.Column(db.String(50), nullable=False)
    face_encoding = db.Column(db.LargeBinary, nullable=False)



    #def set_password(self, password):
     #   self.password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    #def check_password(self, password):
     #   return bcrypt.check_password_hash(self.password, password)

    def as_dict(self):
        result = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if self.fecha_nac:
            result['fecha_nac'] = self.fecha_nac.strftime('%d %b %Y')  # Formatear fecha
        if self.face_encoding:
            result['face_encoding'] = base64.b64encode(self.face_encoding).decode('utf-8')  # Convertir a base64
        return result
    
    def to_dict(self, fields=None):
        if fields:
            return {field: getattr(self, field) for field in fields}
        return self.as_dict()





