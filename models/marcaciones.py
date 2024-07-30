from . import db
from datetime import datetime

class Marcacion(db.Model):
    __tablename__ = 'marcaciones'
    id_marcaciones = db.Column(db.Integer, primary_key=True)
    idUsuario = db.Column(db.Integer, db.ForeignKey('usuario.idUsuario'), nullable=False)
    hora_inicio = db.Column(db.DateTime, nullable=False)
    hora_fin = db.Column(db.DateTime, nullable=True)
    ini_break = db.Column(db.Time, nullable=True)
    end_break = db.Column(db.Time, nullable=True)
    horas_trabajadas = db.Column(db.Numeric(10, 2), nullable=True)
    min_tarde = db.Column(db.Integer, nullable=True)
    est_falta = db.Column(db.Integer, nullable=True)

    usuario = db.relationship('Usuario', backref=db.backref('marcaciones', lazy=True))
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}