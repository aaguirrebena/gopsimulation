import numpy as np
from random import random, randint, uniform
from functools import reduce
from math import exp, ceil, cos, sin, sqrt, atan2, radians

class Solicitude:
    num =1

    def __init__(self, tiempo_inicio, simulacion):
        self.tiempo_inicial = tiempo_inicio
        self.urgencia = self.definir_urgencia()
        self.plazo_inicial = 20
        self.simulacion = simulacion

        self.tiempo_poda = self.definir_tempo_poda()

        self.id = Solicitude.num
        Solicitude.num += 1

        self.lat = uniform(-33.509873, -33.469988)
        self.lon = uniform(-70.623459, -70.585459)

    @property
    def _dia_llegada(self):
        dia_llegada = ceil(self.tiempo_inicial/(24*60))
        return dia_llegada

    @property
    def _plazo_maximo(self):
        plazo_maximo = self.plazo_inicial - (self.simulacion.dia_actual - self._dia_llegada)
        if plazo_maximo < 0:
            plazo_maximo = 0
        elif plazo_maximo == 10:
            self._urgencia = 2
        elif plazo_maximo == 2:
            self._urgencia = 1

        return plazo_maximo

    @property
    def _urgencia(self):
        return self.urgencia

    @_urgencia.setter
    def _urgencia(self, x):
        if x < 1:
            self.urgencia = 1
        else:
            self.urgencia = x

    @property
    def prioridad(self):
        try:
            prioridad = (1/self.urgencia) + (1/self._plazo_maximo)
        except:
            prioridad = 0
        return prioridad

    def definir_urgencia(self):
        p = random()
        if p < 0.15:
            prior = 1
            self.plazo_inicial = 2
        elif 0.15 <= p < 0.5:
            prior = 2
        else:
            prior = 3
        return prior
    
    def definir_tempo_poda(self):
        p = random()
        if self.urgencia == 1 and p <= 0.5:
            return 7*60
        elif self.urgencia == 1:
            return 4*60
        else:
            return (2 + randint(0, 5))*60

class Evento:
    def __init__(self, nombre, tiempo):
        self.nombre = nombre
        self.tiempo = tiempo

class Grafo:
    def __init__(self):
        self.nodos = []
        self.municipalidad = Nodo(0, 0, 0, -33.4854454, -70.5967252, 0)

    @staticmethod
    def calcular_distancia(nodo1, nodo2):
        # Aqui se hace la llamada a la api
        r = 6373.0

        lat1 = radians(nodo1.lat)
        lon1 = radians(nodo1.lon)
        lat2 = radians(nodo2.lat)
        lon2 = radians(nodo2.lon)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        c = 2*atan2(sqrt(a), sqrt(1 - a))

        distance = r*c

        return distance/5 * 60 + 20
    
    @staticmethod
    def key_sort(coneccion):
        return coneccion.tiempo + coneccion.conections[1].tiempo_poda,  coneccion.conections[1].tiempo_inicial

    def agregar_nodo(self, solicitud):
        nuevo_nodo = Nodo(solicitud.tiempo_inicial, solicitud.id, solicitud.urgencia, solicitud.lat, solicitud.lon, solicitud.tiempo_poda)
        for nodo in self.nodos:
            self.agregar_coneccion(nuevo_nodo, nodo)
        self.nodos.append(nuevo_nodo)

        muni = Coneccion(nuevo_nodo, self.municipalidad, self.calcular_distancia(nuevo_nodo, self.municipalidad))
        nuevo_nodo.muni = muni
        self.municipalidad.conecciones.append(muni)

    def agregar_coneccion(self, nodo1, nodo2):
        coneccion = Coneccion(nodo1, nodo2, self.calcular_distancia(nodo1, nodo2))
        coneccion2 = Coneccion(nodo2, nodo1, self.calcular_distancia(nodo1, nodo2))
        nodo1.conecciones.append(coneccion)
        nodo2.conecciones.append(coneccion2)
        nodo1.conecciones.sort(key=self.key_sort)
        nodo2.conecciones.sort(key=self.key_sort)

    def print_conecciones(self, nodo):
        for coneccion in nodo.conecciones:
            nodo2 = coneccion.conections[1]
            print("Nodo {}: se conecta a {} con poda de {}".format(nodo.id, nodo2.id, nodo2.tiempo_poda))

    def eliminar_nodo(self, nodo):
        nodo_id = [node for node in range(len(self.nodos)) if self.nodos[node].id == nodo.id][0]
        nodo = self.nodos.pop(nodo_id)
        for coneccion in nodo.conecciones:
            if nodo.id != coneccion.conections[0].id:
                nodo2 = coneccion.conections[0]
            else:
                nodo2 = coneccion.conections[1]
            self.eliminar_coneccion(nodo, nodo2)
    
    def eliminar_coneccion(self, node1, node2):
        node1.conecciones = [i for i in node1.conecciones if i.conections[1] != node2]
        node2.conecciones = [i for i in node2.conecciones if i.conections[1] != node1]
            
    
    def planificar(self, id, start=None, muni=True, tiempo=0, visitados=[]):
        start_node = self.encontrar_nodo(id)
        visitados.append(start_node)
        if muni:
            tiempo += start_node.muni.tiempo
        elif start is not None:
            tiempo += self.encontrar_coneccion(start_node, start).tiempo
        tiempo += start_node.tiempo_poda
        
        for conect in start_node.conecciones:
            nodo2 = conect.conections[1]
            
            if nodo2 not in visitados:
                posible = conect.tiempo + nodo2.tiempo_poda + nodo2.muni.tiempo
                # print(posible)
                if tiempo + posible <= 8*60:
                    return [start_node] + self.planificar(nodo2.id, start_node, False, tiempo + conect.tiempo, visitados)
        return [start_node]
    
    def planificar2(self, id, start=None, muni=True, tiempo=0, visitados=[], step=10):
            start_node = self.encontrar_nodo(id)
            visitados.append(start_node)
            if muni:
                tiempo += start_node.muni.tiempo
            elif start is not None:
                tiempo += self.encontrar_coneccion(start_node, start).tiempo
            tiempo += start_node.tiempo_poda

            i = 0
            while i < len(start_node.conecciones):
                if i + step < len(start_node.conecciones):
                    conections = start_node.conecciones[i: i+step]
                else:
                    conections = start_node.conecciones[i::]
                
                conections = sorted(conections, key = lambda x: (x.conections[1].tiempo_inicial, self.key_sort))
            
                for conect in conections:
                    nodo2 = conect.conections[1]
                    
                    if nodo2 not in visitados:
                        posible = conect.tiempo + nodo2.tiempo_poda + nodo2.muni.tiempo
                        # print(posible)
                        if tiempo + posible <= 8*60:
                            return [start_node] + self.planificar(nodo2.id, start_node, False, tiempo + conect.tiempo, visitados)
                i += step
            return [start_node]
        
    def encontrar_nodo(self, nodo1):
        for nodo in self.nodos:
            if nodo.id == nodo1:
                return nodo
    
    def encontrar_coneccion(self, nodo1, nodo2):
        for conect in nodo1.conecciones:
            if nodo1 in conect.conections and nodo2 in conect.conections:
                return conect

class Nodo:
    def __init__(self, tiempo_inicial, num, urgencia, lat, lon, tiempo_poda):
        self.id = num
        self.tiempo_inicial = tiempo_inicial
        self.urgencia = urgencia
        self.lat = lat
        self.lon = lon
        self.conecciones = []
        self.tiempo_poda = tiempo_poda
        self.muni = None

class Coneccion:
    def __init__(self, nodo1, nodo2, tiempo):
        self.conections = (nodo1, nodo2)
        self.tiempo = tiempo