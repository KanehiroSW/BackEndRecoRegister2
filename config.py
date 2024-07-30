import os
from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/face'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'clave_secreta_aleatoria'
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(days=7)