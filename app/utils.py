from datetime import datetime
from flask import current_app

def allowed_file(filename):
    allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def formatar_data(data):
    """Formata datetime ou date para string 'DD/MM/YYYY'"""
    if not data:
        return ''
    if isinstance(data, datetime):
        return data.strftime('%d/%m/%Y')
    # Se for date, também funciona
    return data.strftime('%d/%m/%Y')

def formatar_hora(hora):
    """Formata datetime ou time para string 'HH:MM'"""
    if not hora:
        return ''
    if isinstance(hora, datetime):
        return hora.strftime('%H:%M')
    return hora.strftime('%H:%M')

def formatar_data_hora(dt):
    """Formata datetime para 'DD/MM/YYYY HH:MM'"""
    if not dt:
        return ''
    return dt.strftime('%d/%m/%Y %H:%M')
