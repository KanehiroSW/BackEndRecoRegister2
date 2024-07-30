from models import db
from models.horario import Horario
from datetime import time

def initialize_horarios():
    dias = [
        ('Lunes', time(9, 0), time(17, 0)),
        ('Martes', time(9, 0), time(17, 0)),
        ('Miercoles', time(9, 0), time(17, 0)),
        ('Jueves', time(9, 0), time(17, 0)),
        ('Viernes', time(9, 0), time(17, 0)),
        ('Sabado', time(9, 0), time(14, 0))
    ]
    
    for dia_semana, hora_inicio, hora_fin in dias:
        horario = Horario.query.filter_by(dia_semana=dia_semana).first()
        if not horario:
            nuevo_horario = Horario(
                dia_semana=dia_semana,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin
            )
            db.session.add(nuevo_horario)
    db.session.commit()

