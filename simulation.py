import clases as cl
import arrive as ll
import numpy as np
from random import random, seed, shuffle

dia_inicial = 15

class Simulation:
    def __init__(self, dias, llegadas, meses, modo=None, plan=1, step=10):
        self.tiempo_maximo = dias*24*60
        self.llegadas = llegadas.pop(0)
        self.tiempo_actual = 0
        self.eventos = list()
        self.solicitudes = list()
        self.dia_actual = dia_inicial
        self.dias = 0 # dias que quedan de simulacion
        self.meses = meses
        self.plan = plan
        self.step = step

        #Estadisticas importantes
        self.podas_realizadas = 0
        self.tiempo_viaje = 0
        self.tiempo_restante = 0
        self.dias_atencion = []
        self.perdidas = 0
        self.descartadas = 0

        #Se crea el grafo
        self.grafo = cl.Grafo()

        # Simulation attributes
        self.metodos = {'nueva_solicitud': self.nueva_solicitud,
                        'planificar_podas': self.planificar_podas if not modo else self.planificar_base,
                        'fin_de_semana': self.fin_de_semana }

        #instanciar

    @property
    def _podas_pendientes(self):
        pendientes = len(self.solicitudes)
        return pendientes

    @property
    def _pendientes_tiempo(self):
        tiempo = 0
        for x in self.solicitudes:
            tiempo += x.tiempo_poda
        return tiempo/60


    def eventos_iniciales(self):
        self.eventos.append(cl.Evento('nueva_solicitud', self.llegadas.pop(0)))

        t = (8*60) + (24*dia_inicial*60)
        ft = 30*self.meses - dia_inicial
        if ft > 0:
            for _ in range(ft):
                if _%5 != 0 and _%6 != 0:
                # self.dias += 1
                    self.eventos.append(cl.Evento('planificar_podas', t))
                else:
                    self.eventos.append(cl.Evento('fin_de_semana', t))
                t += 24*60
    
    def fin_de_semana(self, *args):
        self.dia_actual += 1
    
    def nueva_solicitud(self, *args):
        # Se crean los evento de solicitudes y se agregan a la lista
        solicitud = cl.Solicitude(args[0].tiempo, self)

        #Se define la llegada de la siguiente solicitud (en llegadas array)
        tiempo_proximo_solicitud = self.llegadas.pop(0)
        self.eventos.append(cl.Evento('nueva_solicitud', tiempo_proximo_solicitud))

        # Si no es urgencia, 50% se descarta
        rand = random()
        if rand <= 0.9:
            self.solicitudes.append(solicitud)
            self.grafo.agregar_nodo(solicitud)
        else:
            self.descartadas += 1
    
    def eliminar_perdidas(self):
        
        perdidas = []
        for sol in self.solicitudes:
            if sol._plazo_maximo <= 0:
                self.perdidas += 1
                perdidas.append(sol.id)

        self.solicitudes = [sol for sol in self.solicitudes if sol._plazo_maximo > 0]

        eliminar = [node for node in self.grafo.nodos if node.id in perdidas]
        for node in eliminar:
            self.grafo.eliminar_nodo(node)
    
    def planificar_base(self, *args):
        
        # self.eliminar_perdidas()
        
        shuffle(self.solicitudes)

        def aux(x):
            try:
                return 1/x.prioridad
            except Exception:
                return 0

        for i in range(3):
            try:
                # print("Planificacion cuadrilla {}".format(i))
                ordenada = sorted(self.solicitudes, key=lambda x: (x.urgencia, aux(x)))
                sols = []
                nodos = []

                inicial = ordenada.pop(0)
                self.dias_atencion.append(inicial.plazo_inicial - inicial._plazo_maximo + 1)
                nodo_inicial =  self.grafo.encontrar_nodo(inicial.id)

                sols.append((inicial))
                nodos.append(nodo_inicial)

                tiempo = nodo_inicial.muni.tiempo + nodo_inicial.tiempo_poda

                for sol in ordenada:
                    proximo_nodo = self.grafo.encontrar_nodo(sol.id)
                    conection = self.grafo.encontrar_coneccion(proximo_nodo, nodos[-1])
                    posible = conection.tiempo + proximo_nodo.tiempo_poda + proximo_nodo.muni.tiempo
                    if tiempo + posible <= 8*60:
                        sols.append(sol)
                        self.dias_atencion.append(sol.plazo_inicial - sol._plazo_maximo + 1)
                        nodos.append(proximo_nodo)
                        tiempo += conection.tiempo + proximo_nodo.tiempo_poda
                
                self.podas_realizadas += len(sols)
                self.solicitudes = [sol for sol in self.solicitudes if sol not in sols]

                ids = [sol.id for sol in sols]
                tiempo_viaje = self.grafo.determinar_tiempo_viaje(ids)
                ids = [sol.id for sol in sols]
                tiempo_poda = self.grafo.determinar_tiempo_poda(ids)
                tiempo_t = 60*8 - tiempo_poda - tiempo_viaje

                
                self.tiempo_viaje += tiempo_viaje
                self.tiempo_restante += tiempo_t

                for node in nodos:
                    self.grafo.eliminar_nodo(node)
            except IndexError as e:
                    # print("no hay mas solicitudes")
                    pass
        
        self.dia_actual += 1

    def planificar_podas(self, *args):
        """
        ACA se debe de alguna manera establecer una lista con las urgenciaes de las podas para el dia siguiente
        Se hace una vez al dia. Esto en base a las decisiones que nosotros creamos importantes
        """
        # print("dia: ", self.dia_actual)

        # self.eliminar_perdidas()
        shuffle(self.solicitudes)

        for i in range(3):
            try:
                # print("Planificacion cuadrilla {}".format(i))
                ordenada = sorted(self.solicitudes, key=lambda x: x.prioridad, reverse=True)
                solicitud = ordenada.pop(0)
                
                if plan == 1:
                    recorridos = self.grafo.planificar(solicitud.id)
                else:
                    recorridos = self.grafo.planificar2(solicitud.id, step=self.step)
                # print([node.id for node in recorridos])
                self.podas_realizadas += len(recorridos)

                sols = [sol.id for sol in recorridos]

                for sol in self.solicitudes:
                    if sol.id in sols:
                        self.dias_atencion.append(sol.plazo_inicial - sol._plazo_maximo + 1)
                
                self.solicitudes = [sol for sol in self.solicitudes if sol.id not in sols]

                ids = [sol.id for sol in recorridos]
                tiempo_viaje = self.grafo.determinar_tiempo_viaje(ids)
                ids = [sol.id for sol in recorridos]
                tiempo_poda = self.grafo.determinar_tiempo_poda(ids)
                tiempo_t = 60*8 - tiempo_poda - tiempo_viaje


                self.tiempo_viaje += tiempo_viaje
                self.tiempo_restante += tiempo_t

                for node in recorridos:
                    self.grafo.eliminar_nodo(node)

                
            except IndexError as e:
                # print("no hay mas solicitudes")
                pass

        # ordenada = sorted(self.solicitudes, key=lambda x: x.prioridad, reverse=True)
        # print("dia: ", self.dia_actual)
        # for x in range(5):
        #     print("SOLICITUD {}: CON PRIORIDAD {} - URGENCIA: {}".format(ordenada[x].id, ordenada[x].prioridad, ordenada[x].urgencia))
        self.dia_actual += 1

    def run(self):
        self.eventos_iniciales()
        while self.tiempo_actual <= self.tiempo_maximo and self.eventos:
            self.eventos.sort(key=lambda evento: evento.tiempo)
            evento = self.eventos.pop(0)
            if evento.tiempo <= self.tiempo_maximo:
                self.tiempo_actual = evento.tiempo
                self.metodos[evento.nombre](evento)

def global_statistics(n, dias, meses, modo=None, plan=1, step=10):
    tiempo_maximo = 24 * 60 * dias
    estadisticas = list()
    for i in range(n):
        seed(i)
        llegadas = ll.generar_llegadas(dias, repetitions, i)
        s = Simulation(dias, llegadas, meses, modo, plan, step)
        s.run()
        estadisticas.append(
            {'podas_realizadas': s.podas_realizadas,
            "podas_pendientes": s._podas_pendientes,
            "dias_atencion": np.mean(s.dias_atencion),
            "solicitudes_perdidas": s.perdidas,
            "solicitudes_descartadas": s.descartadas,
            "tiempo_viaje": s.tiempo_viaje,
            "tiempo_pendientes": s._pendientes_tiempo,
            "tiempo_restante": s.tiempo_restante
            })
        # print("Simulacion numero: {}".format(i))
        # for x in range(len(s.solicitudes)):
        #     print("dia_actual: {} - id solicitud: {} - urgencia: {} - dia_llegada: {} - plazo_restante: {}".format(s.dia_actual, s.solicitudes[x].id, s.solicitudes[x].urgencia, s.solicitudes[x]._dia_llegada, s.solicitudes[x]._plazo_maximo))
        # s.grafo.print_conecciones(s.grafo.nodos[0])

    return estadisticas, tiempo_maximo

def printear(n, estadisticas, tiempo_maximo):
    """
    n: numero de repeticiones
    estadisticas: diccionario generado en cada simulacion con datos que nos interesen
    tiempo_maximo: puede llegar a servir para calcular medias
    """
    for n_sim in range(n):
        #  Por si queremos ver cosas de cada simulacion
        pass
   
    print("\nPensar en datos relevantes")
    print("Estadisticas Promedio:")
    print("Simulacion de {} dias".format(dias))
    #EJEMPLO que calcularia el promedio arboles podados de todas las simulaciones
    print("   Promedio solicitudes realizadas:                  {0:<10.6}".format(np.mean([est['podas_realizadas'] for est in estadisticas])))
    print("   Promedio solicitudes pendientes:                  {0:<10.6}".format(np.mean([est['podas_pendientes'] for est in estadisticas])))
    print("   Promedio solicitudes perdidas:                  {0:<10.6}".format(np.mean([est['solicitudes_perdidas'] for est in estadisticas])))
    print("   Promedio dias de atencion:                  {0:<10.6}".format(np.mean([est['dias_atencion'] for est in estadisticas])))
    print("   Promedio de solicitudes descartadas:                  {0:<10.6}".format(np.mean([est['solicitudes_descartadas'] for est in estadisticas])))
    print("   Promedio de tiempo de viaje:                  {0:<10.6}".format(np.mean([est['tiempo_viaje'] for est in estadisticas])))
    print("   Promedio de tiempo de restante:                  {0:<10.6}".format(np.mean([est['tiempo_restante'] for est in estadisticas])))
    print("   Promedio de tiempo de pendientes:                  {0:<10.6}".format(np.mean([est['tiempo_pendientes'] for est in estadisticas])))

if __name__ == '__main__':
    meses = 12
    dias = 30*meses
    repetitions = 5
    
    print("\nCaso HEURISTICA 1")
    modo = 'base'
    estadisticas, tiempo = global_statistics(repetitions, dias, meses, modo)
    printear(repetitions, estadisticas, tiempo)

    print("\nCaso HEURISTICA 2")
    modo = None
    plan = 1
    estadisticas, tiempo = global_statistics(repetitions, dias, meses, modo)
    printear(repetitions, estadisticas, tiempo)

    step = 5
    print("\nCaso HEURISTICA 3 con STEP={}".format(step))
    modo = None
    plan = 2
    estadisticas, tiempo = global_statistics(repetitions, dias, meses, modo, plan, step)
    printear(repetitions, estadisticas, tiempo)
