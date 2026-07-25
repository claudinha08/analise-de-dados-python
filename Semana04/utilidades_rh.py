import re

def calcular_horas_trabalhadas(entrada, saida):
    return (saida - entrada).seconds / 3600

def calcular_atraso(hora_entrada, minuto_entrada, hora_prevista=8, minuto_previsto=0):
    minutos_reais = hora_entrada * 60 + minuto_entrada
    minutos_previstos = hora_prevista * 60 + minuto_previsto
    return minutos_reais - minutos_previstos

def classificar_pontualidade(atraso_minutos, tolerancia=10):
    if atraso_minutos <= tolerancia:
        return "Pontual"
    return "Atrasado"

def validar_email(email):
    padrao = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    return bool(re.match(padrao, email))
