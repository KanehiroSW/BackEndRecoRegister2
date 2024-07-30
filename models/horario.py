from . import db
from datetime import datetime


class Horario(db.Model):
    __tablename__ = 'horarios'
    id_horario = db.Column(db.Integer, primary_key=True)
    dia_semana = db.Column(db.String(10), nullable=True)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)

    def as_dict(self):
        result = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if self.hora_inicio:
            result['hora_inicio'] = self.hora_inicio.strftime('%H:%M:%S')
        if self.hora_fin:
            result['hora_fin'] = self.hora_fin.strftime('%H:%M:%S')
        return result