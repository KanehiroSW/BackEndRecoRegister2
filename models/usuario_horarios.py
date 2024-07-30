from . import db
from datetime import datetime

class UsuarioHorarios(db.Model):
    __tablename__ = 'usuario_horarios'
    id_usuario_horario = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    id_horario = db.Column(db.Integer, db.ForeignKey('horarios.id_horario'), nullable=False)
    diaSemana = db.Column(db.String(10), nullable=True)

    usuario = db.relationship('Usuario', backref=db.backref('usuario_horarios', lazy=True))
    horario = db.relationship('Horario', backref=db.backref('usuario_horarios', lazy=True))

    def as_dict(self):
        result = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        return result