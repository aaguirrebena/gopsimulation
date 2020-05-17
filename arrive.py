from random import expovariate, uniform

solicitudes = 40 # Solicitudes por semana
tiempo_semana = 60*24*7 # minutos*horas*dias (tiempo para la ocurrencia)
lamb = solicitudes/tiempo_semana # lambda, ocurrencias en un tiempo

def generar_llegadas(dias, rep):
    llegadas = []
    for _ in range(rep):
        tiempo_maximo = 24*60*dias
        tiempo = 0
        tiempos_llegadas = []
        while tiempo < tiempo_maximo:
            tiempo_proximo_persona = tiempo + expovariate(lamb)
            tiempo = tiempo_proximo_persona
            tiempos_llegadas.append(tiempo)
        llegadas.append(tiempos_llegadas)
    return llegadas
