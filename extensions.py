"""
extensions.py
Instancias compartidas de extensiones Flask para evitar importaciones circulares.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

