
import math
import copy
import time
import random
import matplotlib.pyplot as plt
import io
import base64

# Registramos el reloj justo antes de empezar
tiempo_inicio = time.perf_counter()

# ==============================================================================
# DEMANDA Y PARAMETROS PARA SIMULACIONES
# ==============================================================================
print()
print('FASE 1: INGRESO DE DEMANDA Y PARAMETROS PARA SIMULACIONES')
# Parametros fijos de entrada
numAgendas = 36
numLibretas = 30
# Se calcula este valor en funcion de lo estipulado en el Reglamento, el cual
# estipula una proporción máxima de libretas respecto a las agendas
# Se utiliza division entera (//) para no exceder el tope
maxLibretas = (numAgendas * 10) // 12
# MONTE CARLO
# Define cuantos escenarios u horarios aleatorios distintos se generarán
# en la Fase 7 para competir contra los enfoques deterministas
CANTIDAD_RANDOMS = 7_100  # Ojo aca no exagerar demasiado, salvo en servidor
# Define la cantidad de "multiversos" o iteraciones de estres a las que se
# sometera el peor escenario en la Fase 8 (puede ser uno de los deterministas)
# Se multiplica por 100 para asegurar una muestra estadistica robusta
CANTIDAD_SIMULACIONES = 8_000  # Lo mismo por aca xD
print(f'Agendas a manufacturar: {numAgendas}')
print(f'Libretas a manufacturar: {numLibretas} (Máximo permitido: {maxLibretas})')
print(f'Cantidad de escenarios aleatrorios: {CANTIDAD_RANDOMS}')
print(f'Cantidad de simulaciones para estresar el peor escenario posible: {CANTIDAD_SIMULACIONES}')

if numLibretas > maxLibretas:
    print(f"Las libretas superan el máximo permitido por el Reglamento({maxLibretas}).")

print()
print('FASE 1 COMPLETADA')

# ==============================================================================
# COMISION
# ==============================================================================
# Cálculo de la cantidad de estudiantes requerida
# Se requiere 1 estudiante por cada 12 agendas, o 1 por cada 10 libretas
# Se utiliza math.ceil para redondear siempre hacia arriba (ej. 1.1 requiere 2 estudiantes)
# El max(1, ...) asegura que siempre haya al menos 1 persona trabajando
print()
print('FASE 2: COMISION')
estudiantesRequeridos = max(1, math.ceil(numAgendas / 12), math.ceil(numLibretas / 10))
print()
print(f'Cantidad de estudiantes requeridos para la comision: {estudiantesRequeridos}')
print()
print('FASE 2 COMPLETADA')

# ==============================================================================
# INVENTARIO
# ==============================================================================
# Diccionario de recursos disponibles en la sala de estudios o taller
# Estas cantidades actúan como "restricciones de capacidad" en el modelo
# El algoritmo de revisara este stock en cada bloque horario para
# evitar sobreasignaciones y modelar los cuellos de botella de manera realista
# TRABAJO FUTURO: El modelo asume una disponibilidad estatica inicial
# En futuras iteraciones, este diccionario podría parametrizarse mediante una
# interfaz para que el usuario  actualice el stock dinamicamente si hay
# maquinas en mantenimiento o se podria añadir un contador de tiempo funcionando
# par cada una de modo de tener un estimado de cuanto tiempo de vida util le
# queda a cada maquinaria, esto para pedir financiamiento a Decanato por ejemplo
print()
print('FASE 3: INVENTARIO')
# Aca asuminos que habrán multiples maquinarias para cada tarea. Corregir despues
recursos1 = {
    # TAREAS MANUALES (Inciso B)
    # Agrupamos Cutter, Mat de corte y Regla metalica como una unica "estacion de corte"
    "Corte_Carton": 1,
    "Tijera": 1,
    "Espatula": 1,
    # TAREAS DE CORTE MAYOR E IMPRESIÓN (Incisos C y D)
    "Guillotina": 1,
    "Impresora": 1,
    # TAREAS DE PERFORACIÓN Y ANILLADO (Incisos E y F)
    "Cinch": 1,
    "Mini_Cinch": 1,
    # TAREAS DE TERMINACIONES Y ACABADOS
    "Alicate_Corte": 1,
    "Ojetilladora": 1,
    "Alicate_Presion": 1
}

recursos = {
    # TAREAS MANUALES (Inciso B)
    # Agrupamos Cutter, Mat de corte y Regla metalica como una unica "estacion de corte"
    "Corte_Carton": 4,
    "Tijera": 6,
    "Espatula": 3,
    # TAREAS DE CORTE MAYOR E IMPRESIÓN (Incisos C y D)
    "Guillotina": 2,
    "Impresora": 3,
    # TAREAS DE PERFORACIÓN Y ANILLADO (Incisos E y F)
    "Cinch": 2,
    "Mini_Cinch": 3,
    # TAREAS DE TERMINACIONES Y ACABADOS
    "Alicate_Corte": 4,
    "Ojetilladora": 2,
    "Alicate_Presion": 5
}

print()
print('INVENTARIO CARGADO CORRECATAMENTE')
print()
print('FASE 3 COMPLETADA')

# ==============================================================================
# DISPONIBILIDADES
# ==============================================================================
print()
print('FASE 4: DISPONIBILIDADES')
diasSemana = ['    Lunes', '   Martes', 'Miercoles', '   Jueves', '  Viernes']
bloquesHorarios = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00',
                   '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00',
                   '17:00-18:00']

# Un estudiante no es rentable o util para el proyecto si no puede aportar
# al menos una cantidad mínima de horas a la semana. Si cambiamos este valor
# podria ocurrir que fallen todos los escenarios posibles
minHorasSemanales = 5
# Diccionario que almacena una matriz binaria de 5x9 para cada estudiante
# Filas = Días de la semana (Lunes a Viernes)
# Columnas = Bloques horarios (09:00 a 18:00)
# Valores: 1 = Disponible, 0 = No disponible
matrices_estudiantes = {
    "GEMITA": [ # Disponibilidad total
        [1, 1, 1, 1, 1, 1, 1, 1, 1], # Lunes
        [1, 1, 1, 1, 1, 1, 1, 1, 1], # Martes
        [1, 1, 1, 1, 1, 1, 1, 1, 1], # Miercoles
        [1, 1, 1, 1, 1, 1, 1, 1, 1], # Jueves
        [1, 1, 1, 1, 1, 1, 1, 1, 1]  # Viernes
    ],
    "OMAR": [ # Solo mañanas de 09:00 a 13:00 hrs
        [1, 1, 1, 1, 0, 0, 0, 0, 0], # Lunes
        [1, 1, 1, 1, 0, 0, 0, 0, 0], # Martes
        [1, 1, 1, 1, 0, 0, 0, 0, 0], # Miercoles
        [1, 1, 1, 1, 0, 0, 0, 0, 0], # Jueves
        [1, 1, 1, 1, 0, 0, 0, 0, 0]  # Viernes
    ],
    "GINO": [ # Solo un bloque continuo al mediodía de 3 hrs - 15 hrs
        [0, 0, 1, 1, 1, 0, 0, 0, 0], # Lunes
        [0, 0, 1, 1, 1, 0, 0, 0, 0], # Martes
        [0, 0, 1, 1, 1, 0, 0, 0, 0], # Miercoles
        [0, 0, 1, 1, 1, 0, 0, 0, 0], # Jueves
        [0, 0, 1, 1, 1, 0, 0, 0, 0]  # Viernes
    ],
    "ALBERTO": [ # Random
        [0, 1, 0, 0, 0, 0, 0, 0, 0], # Lunes
        [1, 0, 0, 1, 0, 1, 0, 0, 0], # Martes
        [0, 0, 1, 0, 0, 0, 0, 0, 0], # Miercoles
        [0, 1, 1, 0, 0, 0, 0, 0, 1], # Jueves
        [1, 0, 0, 1, 0, 0, 0, 0, 0]  # Viernes
    ],
    "LIBERTAD": [ # Solo los Miercoles disponible
        [0, 0, 0, 0, 0, 0, 0, 0, 0], # Lunes
        [0, 0, 0, 0, 0, 0, 0, 0, 0], # Martes
        [1, 1, 1, 1, 1, 1, 1, 1, 1], # Miercoles
        [0, 0, 0, 0, 0, 0, 0, 0, 0], # Jueves
        [0, 0, 0, 0, 0, 0, 0, 0, 0]  # Viernes
    ],
    "EUGENIO": [ # Solo tardes de 14:00 a 18:00 - 20 hrs
        [0, 0, 0, 0, 0, 1, 1, 1, 1], # Lunes
        [0, 0, 0, 0, 0, 1, 1, 1, 1], # Martes
        [0, 0, 0, 0, 0, 1, 1, 1, 1], # Miercoles
        [0, 0, 0, 0, 0, 1, 1, 1, 1], # Jueves
        [0, 0, 0, 0, 0, 1, 1, 1, 1]  # Viernes
    ],
    "ESCALONA": [ # Un bloque fijo diario de 13:00 a 14:00 hrs
        [0, 0, 0, 0, 1, 0, 0, 0, 0], # Lunes
        [0, 0, 0, 0, 1, 0, 0, 0, 0], # Martes
        [0, 0, 0, 0, 1, 0, 0, 0, 0], # Miercoles
        [0, 0, 0, 0, 1, 0, 0, 0, 0], # Jueves
        [0, 0, 0, 0, 1, 0, 0, 0, 0]  # Viernes
    ],
    "TRONCOSO": [ # Intercalado
        [1, 0, 1, 0, 1, 0, 1, 0, 1], # Lunes
        [0, 1, 0, 1, 0, 1, 0, 1, 0], # Martes
        [1, 0, 1, 0, 1, 0, 1, 0, 1], # Miercoles
        [0, 1, 0, 1, 0, 1, 0, 1, 0], # Jueves
        [1, 0, 1, 0, 1, 0, 1, 0, 1]  # Viernes
    ],
    "AYALA": [ # Solo tiene libre a primera hora y la ultima hora
        [1, 0, 0, 0, 0, 0, 0, 0, 1], # Lunes
        [1, 0, 0, 0, 0, 0, 0, 0, 1], # Martes
        [1, 0, 0, 0, 0, 0, 0, 0, 1], # Miercoles
        [1, 0, 0, 0, 0, 0, 0, 0, 1], # Jueves
        [1, 0, 0, 0, 0, 0, 0, 0, 1]  # Viernes
    ],
    "AGUAYO": [ # Libre Lunes, Miércoles y Viernes completo
        [1, 1, 1, 1, 1, 1, 1, 1, 1], # Lunes
        [0, 0, 0, 0, 0, 0, 0, 0, 0], # Martes
        [1, 1, 1, 1, 1, 1, 1, 1, 1], # Miercoles
        [0, 0, 0, 0, 0, 0, 0, 0, 0], # Jueves
        [1, 1, 1, 1, 1, 1, 1, 1, 1]  # Viernes
    ],
    "MONTECINO": [ # Sin un patron especifico
        [1, 1, 0, 1, 1, 0, 1, 1, 0], # Lunes
        [0, 1, 1, 0, 1, 1, 0, 1, 1], # Martes
        [1, 0, 1, 1, 0, 1, 1, 0, 1], # Miercoles
        [1, 1, 0, 1, 1, 0, 1, 1, 0], # Jueves
        [0, 1, 1, 0, 0, 0, 1, 1, 1]  # Viernes
    ],
        
}

nombresEstudiantes = []
horasDisponiblesEstudiantes = []
disponibilidad = []
# Mapeamos la matriz a una estructura de Diccionario plana con llaves
# de tupla: (dia, bloque) -> estado. Esto permite búsquedas en tiempo O(1) durante
# la simulación del motor, haciéndolo mucho más eficiente
# Solo tomamos de la "bolsa de trabajo" a los  estudiantes que realmente
# se necesitan calculados en la Fase 2. Fijarse que los primeros estduiantes
# sean los que van a particupar realmente o ir borrando a los que no se requieren
for i, (nombre, matriz) in enumerate(matrices_estudiantes.items()):
    # Si ya contratamos a los necesarios, ignoramos el resto del diccionario
    if i >= estudiantesRequeridos:
        break

    nombresEstudiantes.append(nombre)
    disp_estudiante = {}
    horas_acumuladas = 0
    # Iteramos sobre la matriz para aplanar los datos
    for d_idx, dia in enumerate(diasSemana):
        for b_idx, bloque in enumerate(bloquesHorarios):
            estado = matriz[d_idx][b_idx]
            disp_estudiante[(dia, bloque)] = estado
            # Sumamos las horas productivas totales
            horas_acumuladas += estado

    disponibilidad.append(disp_estudiante)
    horasDisponiblesEstudiantes.append(horas_acumuladas)

    print(f'Disponibilidad confirmada: {horas_acumuladas} horas registradas para {nombre}.')
    # Vemos si algun estudiante no tiene la disponibilidad minima necesaria
    if horas_acumuladas < minHorasSemanales:
        print(f'¡OJITO! {nombre} no cumple con el mínimo de {minHorasSemanales} horas semanales')

print()
print('FASE 4 COMPLETADA')

# ==============================================================================
# DISPONIBILIDADES A 8 SEMANAS
# ==============================================================================
print()
print('FASE 4.5: DISPONIBILIDADES A 8 SEMANAS')
# Segun el reglamento, el proyecto tiene un plazo estricto de 8 semanas
NUM_SEMANAS = 8
# CONSTRUCCIÓN DEL TIMELINE:
# Estas funciones toman la matriz de disponibilidad de 1 semana (creada en Fase 4)
# y la replican o clonan a lo largo de las 8 semanas del proyecto
# Esto nos permite tener una línea de tiempo continua y predecible

def generarDisponibilidadGlobal8Semanas(nombresEstudiantes, disponibilidad, diasSemana, bloquesHorarios, numSemanas=8):
    """Crea un diccionario donde la clave es el instante de tiempo (semana, dia, bloque)
       y el valor es la lista de todos los estudiantes trabajando en ese instante"""
    disponibilidadGlobal = {}
    for semana in range(1, numSemanas + 1):
        for dia in diasSemana:
            for bloque in bloquesHorarios:
                estudiantesDisponibles = []
                for i, nombre in enumerate(nombresEstudiantes):
                    if disponibilidad[i][(dia, bloque)] == 1:
                        estudiantesDisponibles.append(nombre)
                disponibilidadGlobal[(semana, dia, bloque)] = estudiantesDisponibles
    return disponibilidadGlobal

def generarDisponibilidadIndividual8Semanas(nombresEstudiantes, disponibilidad, diasSemana, bloquesHorarios, numSemanas=8):
    """Crea un diccionario anidado: Estudiante -> (semana, dia, bloque) -> 1 o 0
       El algoritmo de Monte Carlo consulta este diccionario en tiempo O(1) para
       saber si un estudiante específico fue a trabajar en un bloque determinado"""
    disponibilidadIndividual = {}
    for i, nombre in enumerate(nombresEstudiantes):
        disponibilidadIndividual[nombre] = {}
        for semana in range(1, numSemanas + 1):
            for dia in diasSemana:
                for bloque in bloquesHorarios:
                    disponibilidadIndividual[nombre][(semana, dia, bloque)] = disponibilidad[i][(dia, bloque)]
    return disponibilidadIndividual

# Generamos las estructuras de datos
disponibilidadGlobal8Semanas = generarDisponibilidadGlobal8Semanas(nombresEstudiantes, disponibilidad, diasSemana, bloquesHorarios, NUM_SEMANAS)
disponibilidadIndividual8Semanas = generarDisponibilidadIndividual8Semanas(nombresEstudiantes, disponibilidad, diasSemana, bloquesHorarios, NUM_SEMANAS)
# Se comentan las salidas por consola porque iterar e imprimir más de 360 bloques
# horarios satura la terminal y ralentiza la ejecución general.
'''
print()
print('DISPONIBILIDAD GLOBAL DEL PROYECTO')
for clave, estudiantes in disponibilidadGlobal8Semanas.items():
    semana, dia, bloque = clave
    print(f'Semana {semana} | {dia} | {bloque} -> {estudiantes}')

print('DISPONIBILIDAD INDIVIDUAL POR ESTUDIANTE')
for estudiante, agenda in disponibilidadIndividual8Semanas.items():
    print()
    print(f'ESTUDIANTE: {estudiante}')
    for clave, disponible in agenda.items():
        semana, dia, bloque = clave
        print(f'Semana {semana} | {dia} | {bloque} -> {disponible}')
'''

print()
print('FASE 4.5 COMPLETADA')

# ==============================================================================
# POOL DE LOTES Y TAREAS
# ==============================================================================
print()
print('fASE 5: POOL DE LOTES Y TAREAS')

# Estimacion obtenida midiendo los tiempos promedios del año pasado
# TRABAJO FUTURO: Seria super bueno poder ir actualizando estos valores
# para asi tener versiones realistas de los schedulings
tiempos_unitarios = {
    'B1': {'Agenda': 200, 'Libreta': 120},
    'B2': {'Agenda': 64,  'Libreta': 40},
    'B3': {'Agenda': 56,  'Libreta': 32},
    'B4': {'Agenda': 100, 'Libreta': 60},
    'C1': {'Agenda': 255, 'Libreta': 0},
    'C2': {'Agenda': 0,   'Libreta': 315},
    'D1': {'Agenda': 300, 'Libreta': 0},
    'D2': {'Agenda': 300, 'Libreta': 0},
    'D3': {'Agenda': 5400,'Libreta': 0},
    'D4': {'Agenda': 160, 'Libreta': 0},
    'E1': {'Agenda': 1215,'Libreta': 0}, #
    'E2': {'Agenda': 0,   'Libreta': 235},
    'F1': {'Agenda': 20,  'Libreta': 10},
    'F2': {'Agenda': 50,  'Libreta': 0},
    'F3': {'Agenda': 0,   'Libreta': 25},
    'F4': {'Agenda': 135, 'Libreta': 0}
}

# Grafo de dependencias lógicas (DAG - Directed Acyclic Graph)
# Define la secuencia obligatoria de manufactura. Ej: No se puede
# perforar e imprimir (D1/D2) si el papel no está cortado previamente (C1)
dependencias = {
    'B1': [],
    'B2': [],
    'B3': [],
    'B4': ['B1', 'B2', 'B3'],
    'C1': [],
    'C2': [],
    'D1': ['C1'],
    'D2': ['C1'],
    'D3': ['D1'],
    'D4': ['D2'],
    'E1': ['B4', 'D3', 'D4'],
    'E2': ['B4', 'C2'],
    'F1': [],
    'F2': ['E1', 'F1'],
    'F3': ['E2', 'F1'],
    'F4': ['F2']
}

# ALGORITMO DE AGRUPACION (BATCHING)
agendas_restantes = numAgendas
libretas_restantes = numLibretas
lotes_base = []
numero_lote = 1
# Segmentamos la demanda total en lotes de producción estandar
# Limite tecnico: Maximo 12 agendas y 10 libretas por lote de trabajo
# Segun lo establece el Reglamento Interno
while agendas_restantes > 0 or libretas_restantes > 0:
    lote_agendas = min(12, agendas_restantes)
    lote_libretas = min(10, libretas_restantes)

    if lote_agendas == 0 and lote_libretas == 0:
        break

    tipo_lote = 'Completo' if lote_agendas == 12 and lote_libretas == 10 else 'Incompleto'

    lotes_base.append({
        'id': numero_lote,
        'agendas': lote_agendas,
        'libretas': lote_libretas,
        'tipo': tipo_lote
    })

    agendas_restantes -= lote_agendas
    libretas_restantes -= lote_libretas
    numero_lote += 1


# CONSTRUIMOS EL POOL DE TAREAS A SIMULAR
pool_tareas = []
todas_las_tareas = list(tiempos_unitarios.keys())

for lote in lotes_base:
    lote_id = lote['id']
    q_a = lote['agendas']
    q_l = lote['libretas']
    tipo_lote = lote['tipo']
    # PRE-PROCESAMIENTO: Identificamos que tareas son válidas para este lote
    # Esto evita que el algoritmo exija tareas de libretas si el lote solo tiene agendas
    # tareas_validas_lote = set()
    tareas_validas_lote = set()
    for t in todas_las_tareas:
        if (tiempos_unitarios[t]['Agenda'] * q_a + tiempos_unitarios[t]['Libreta'] * q_l) > 0:
            tareas_validas_lote.add(t)

    def registrar_tarea(codigo_tarea):
        # Cálculamos el tiempo real requerido por la tarea segun volumen del lote
        # Esto es super util porque asi podemos asignar mas de 5 lotes de tareas
        # si son pequeños siempre y cuando no nos excedamos de las 5 horas extracurriculares
        # maximas que se le podran asignar a cada estudiante
        t_agenda = tiempos_unitarios[codigo_tarea]['Agenda'] * q_a
        t_libreta = tiempos_unitarios[codigo_tarea]['Libreta'] * q_l
        tiempo_total = t_agenda + t_libreta

        if tiempo_total <= 0:
            return

        if t_agenda > 0 and t_libreta > 0:
            producto = '  Ambos' # Este espacio fue para que se vea ordenado en la salida por pantalla
        elif t_agenda > 0:
            producto = ' Agenda'
        else:
            producto = 'Libreta'

        # Filtrado de predecesoras: Solo exige tareas que existan en el lote actual
        # No podemos darle la mitad de un lote a un estudiante y la mitad a otro
        preds_validas = [f"L{lote_id}_{p}" for p in dependencias[codigo_tarea] if p in tareas_validas_lote]
        # Inyectamos la tarea estandarizada al Pool global (listado de diccionarios)
        pool_tareas.append({
            'id_tarea': f'L{lote_id}_{codigo_tarea}',
            'codigo': codigo_tarea,
            'lote': lote_id,
            'producto': producto,
            'cantidad_agendas': q_a,
            'cantidad_libretas': q_l,
            'tipo_lote': tipo_lote,
            'tiempo_total_seg': tiempo_total,
            'predecesoras': preds_validas,
            'estado': 'pendiente' # Flag inicial para el motor de Scheduling
        })

    for tarea in tareas_validas_lote:
        registrar_tarea(tarea)

# VERIFICACIÓN VISUAL COMENTADA PARA OPTIMIZAR LA CONSOLA
'''
print()
print('LOTES GENERADOS')
for lote in lotes_base:
    print(f"Lote {lote['id']} | Agendas={lote['agendas']} | Libretas={lote['libretas']} | Tipo={lote['tipo']}")

print()
print('TAREAS GENERADAS')
for tarea in pool_tareas:
    preds_str = ", ".join(tarea['predecesoras']) if tarea['predecesoras'] else "Ninguna"
    print(
        f"{tarea['id_tarea']} | "
        f"{tarea['producto']} | "
        f"A:{tarea['cantidad_agendas']}, L:{tarea['cantidad_libretas']} | "
        f"{tarea['tiempo_total_seg']} seg | "
        f"Predecesoras: [{preds_str}]"
    )
'''
print()
print(f'ÉXITO: Se generaron {len(pool_tareas)} tareas')
print(f'LOTES GENERADOS: {len(lotes_base)}')
print()
print('FASE 5 COMPLETADA')

# ==============================================================================
# PAQUETES DE RETRIBUCION SEGUN REGLAMENTO
# ==============================================================================
print()
print('FASE 5.5:PAQUETES DE RETRIBUCION SEGUN REGLAMENTO')

# El inciso 7 del Reglamento Interno establece recompensas base de 1 hora
# extracurricular por cada paquete de tareas completado, asumiendo un "lote completo"
# (12 agendas y 10 libretas). Aca tenemos que pensar que la moneda de pago del proyecto
# seran las horas extracurriculares para los estudiantes
paquetes_retribucion = {
    'B': {'descripcion': 'Fabricación de tapas', 'hora_extracurricular': 1, 'tareas': ['B1','B2','B3','B4']},
    'C': {'descripcion': 'Corte de hojas', 'hora_extracurricular': 1, 'tareas': ['C1','C2']},
    'D': {'descripcion': 'Impresión', 'hora_extracurricular': 1, 'tareas': ['D1','D2','D3','D4']},
    'E': {'descripcion': 'Compaginado y perforado', 'hora_extracurricular': 1, 'tareas': ['E1','E2']},
    'F': {'descripcion': 'Cierre y terminaciones', 'hora_extracurricular': 1, 'tareas': ['F1','F2','F3','F4']}
}
# CALCULO DEL TIEMPO TEORICO (LOTE PERFECTO)
# Calculamos cuanto tiempo en segundos tomaraa hacer cada paquete si el lote
# estuviera al tope máximo permitido (12 agendas y 10 libretas)
tiempo_paquete_completo = {}
for paquete, datos in paquetes_retribucion.items():
    tiempo_completo = sum(
        12 * tiempos_unitarios[t]['Agenda'] + 10 * tiempos_unitarios[t]['Libreta']
        for t in datos['tareas']
    )
    tiempo_paquete_completo[paquete] = tiempo_completo

# CÁLCULO DE RETRIBUCIÓN PROPORCIONAL POR LOTE REAL
# Como el algoritmo divide la demanda en lotes que pueden ser "incompletos",
# la retribución debe ser exactamente proporcional al esfuerzo real realizado
paquetes_lotes = []
for lote in lotes_base:
    lote_id = lote['id']
    agendas = lote['agendas']
    libretas = lote['libretas']

    for paquete, datos in paquetes_retribucion.items():
        # Tiempo que realmente toma este sub-paquete en este lote especifico
        tiempo_real = sum(
            agendas * tiempos_unitarios[t]['Agenda'] + libretas * tiempos_unitarios[t]['Libreta']
            for t in datos['tareas']
        )

        if tiempo_real > 0:
            # Fraccionamiento de la hora extracurricular
            # JUSTIFICACION: Otorgar fracciones de hora permite al modelo
            # de optimizacion asignar múltiples tareas dispersas a un mismo estudiante
            # sin que este alcance prematuramente el límite duro de 5 horas semanales
            proporcion = tiempo_real / tiempo_paquete_completo[paquete]
            horas_equivalentes = round(proporcion * datos['hora_extracurricular'], 4)

            paquetes_lotes.append({
                'lote': lote_id,
                'paquete': paquete,
                'descripcion': datos['descripcion'],
                'tiempo_real_seg': tiempo_real,
                'tiempo_lote_completo_seg': tiempo_paquete_completo[paquete],
                'proporcion': proporcion, # No estoy segura que tan factible es dar una fraccion de hora extracurricular, pero esto
                # sirve para poder darle mas de solo 5 actividades a un mismo estudiante
                # por ejemplo si una actividad otorga 0.5 horas extracurriculares y lo sumamos a otras 4 que den 1 hora cada uno,
                # podemos agregar otra actividad mas que como maximo otorgue 0.5 horas y seguimos estando bajo la restriccion que lo maximo
                # que se le puede asignar a un mismo estudiante son 5 horas en total
                # Quizas esto no suena muy justo, pero el objetivo del codigo era minimizar el makespan, no distribuir de manera pareja el trabajo entre los estudiantes
                'horas_extracurriculares': horas_equivalentes
            })

# VERIFICACIÓN VISUAL COMENTADA PARA OPTIMIZAR LA CONSOLA
"""
print()
print('RESUMEN DE PAQUETES DE RETRIBUCION DE HORAS EXTRACURRICULARES')
for p in paquetes_lotes:
    print(
        f"Lote {p['lote']} | "
        f"Paquete {p['paquete']} | "
        f"{p['descripcion']} | "
        f"{p['horas_extracurriculares']:.3f} horas extracurriculares "
        f"({100*p['proporcion']:.1f}% del lote completo)"
    )
"""
print()
print('FASE 5.5 COMPLETADA')

# ==============================================================================
# COTA SUPERIOR Y DISTRIBUCIÓN EXACTA POR LOTE
# ==============================================================================
print()
print('FASE 6: COTA SUPERIOR Y DISTRIBUCION EXACTA POR LOTE')
# NOTA: Esta función no alimenta directamente al motor de simulación de las
# Fases 7 y 8. Su propósito es estrictamente analítico, pero no fue eliminada
# Calcula el "peor escenario teoico" (Upper Bound) resolviendo todas las permutaciones
# válidas. Esto sirve como métrica de control o "línea base" para
# demostrar matemáticamente en el informe cuánto tiempo ahorran los algoritmos de optimización

def calcular_cota_superior_exacta(tiempos_unitarios, lotes_base):
    # Tenemos las 16 acciones contempladas en nuestro modelo
    acciones = ['B1', 'B2', 'B3', 'B4', 'C1', 'C2', 'D1', 'D2', 'D3', 'D4', 'E1', 'E2', 'F1', 'F2', 'F3', 'F4']
    # Redefinicion local de dependencias
    dependencias = {
        'B4': {'B1', 'B2', 'B3'},
        'E2': {'C2', 'B4'},
        'D1': {'C1'}, 'D2': {'C1'},
        'D3': {'D1'}, 'D4': {'D2'},
        'E1': {'B4', 'D3', 'D4'},
        'F2': {'F1', 'E1'},
        'F4': {'F2'},
        'F3': {'E2', 'F1'}
    }
    # Construimos la lista de adyacencia y grados de entrada para grafo dirigido
    adj = {nodo: [] for nodo in acciones}
    grados_entrada = {nodo: 0 for nodo in acciones}
    for hijo, padres in dependencias.items():
        for p in padres:
            adj[p].append(hijo)
            grados_entrada[hijo] += 1

    cota_superior_global = 0
    reporte_lotes = []

    # ARCHIVO DE TEXTO COMENTADO:
    #nombre_archivo = "distribucion_makespans_todos_los_lotes.txt"
    #print(f"Generando el archivo '{nombre_archivo}'")

    #with open(nombre_archivo, "w", encoding="utf-8") as f:
        #f.write("DISTRIBUCIÓN DE MAKESPANS POR LOTE (ORDENADOS DEL PEOR AL MEJOR)\n\n")

    # Mover a la derecha todo el for si se descomenta lo anterior
    for lote in lotes_base:
        lote_id = lote['id']
        q_a = lote['agendas']
        q_l = lote['libretas']
        tipo_lote = lote['tipo']

        tiempo_por_tarea = {}
        for tarea in acciones:
            t_agenda = tiempos_unitarios[tarea]['Agenda'] * q_a
            t_libreta = tiempos_unitarios[tarea]['Libreta'] * q_l
            tiempo_por_tarea[tarea] = t_agenda + t_libreta

        registro_makespans = []
        # Sub-motor de simulación teorica
        # Calcula el tiempo asumiendo 1 solo recurso
        # trabajando en serie, sin paralelizar actividades
        # Esto se obtuvo simulando un lote hecho por un estudiante
        # y concatenando todo a continuacion
        def simular_secuencia(secuencia):
            bloque_actual_seg = 3600
            tiempo_total_simulado = 0

            for tarea in secuencia:
                tiempo_restante_tarea = tiempo_por_tarea[tarea]
                es_inicio_tarea = True

                while tiempo_restante_tarea > 0:
                    if tarea in ['D1', 'D2'] and es_inicio_tarea:
                        if bloque_actual_seg < 900:
                            tiempo_total_simulado += bloque_actual_seg
                            bloque_actual_seg = 3600

                    if tarea in ['D3', 'D4']:
                        if bloque_actual_seg < 600:
                            tiempo_total_simulado += bloque_actual_seg
                            bloque_actual_seg = 3600

                    es_inicio_tarea = False

                    tiempo_a_procesar = min(tiempo_restante_tarea, bloque_actual_seg)
                    tiempo_restante_tarea -= tiempo_a_procesar
                    bloque_actual_seg -= tiempo_a_procesar
                    tiempo_total_simulado += tiempo_a_procesar

                    if bloque_actual_seg == 0:
                        bloque_actual_seg = 3600

            return tiempo_total_simulado

        # Algoritmo de busqueda en profundidad (DFS) para encontrar todas las
        # ordenaciones válidas en el grafo de dependencias del proyecto
        def buscar_todos_makespans(grados_actuales, ruta_actual):
            pos = len(ruta_actual)

            if pos == len(acciones):
                makespan = simular_secuencia(ruta_actual)
                registro_makespans.append((makespan, list(ruta_actual)))
                return

            disponibles = [n for n in acciones if grados_actuales[n] == 0 and n not in ruta_actual]

            for nodo in disponibles:

                # REGLAS ESTRICTAS DE PODA (Pruning)
                # Fuerzan la logica secuencial para reducir el arbol de combinaciones
                # En caso contrario esto es inmanejable y explota computacionalmente
                if pos == 0 and nodo != 'C1': continue
                if pos == 1 and nodo != 'C2': continue
                if pos == 2 and nodo not in ['D1', 'D2']: continue

                if pos == 15 and nodo != 'F4': continue
                if pos != 15 and nodo == 'F4': continue

                # Secuencias inmediatas a la etapa de impresion
                if 'D1' in ruta_actual and 'D3' not in ruta_actual and nodo != 'D3': continue
                if 'D2' in ruta_actual and 'D4' not in ruta_actual and nodo != 'D4': continue

                ruta_actual.append(nodo)
                for vecino in adj[nodo]: grados_actuales[vecino] -= 1

                buscar_todos_makespans(grados_actuales, ruta_actual) # Llamada recursiva
                # Backtracking: Deshacemos el estado para explorar la siguiente rama
                for vecino in adj[nodo]: grados_actuales[vecino] += 1
                ruta_actual.pop()

        buscar_todos_makespans(grados_entrada.copy(), [])
        # Ordenamos los resultados para extraer las metricas que necesitamos
        registro_makespans.sort(key=lambda x: x[0], reverse=True)
        peor_makespan_segundos = registro_makespans[0][0]
        mejor_makespan_segundos = registro_makespans[-1][0]
        promedio_makespan = sum(m[0] for m in registro_makespans) / len(registro_makespans)
        # Acumulamos el peor caso de este lote a la cota superior global del proyecto
        cota_superior_global += peor_makespan_segundos

        reporte_lotes.append({
            'lote_id': lote_id,
            'tipo': tipo_lote,
            'agendas': q_a,
            'libretas': q_l,
            'peor': peor_makespan_segundos,
            'mejor': mejor_makespan_segundos,
            'promedio': promedio_makespan
        })

            # Esto esta a la altura correcta, no es necesario moverlo
            #f.write(f"Total de combinaciones evaluadas: {len(registro_makespans)}\n")
            #f.write(f"LOTE {lote_id} | {q_a} Agendas, {q_l} Libretas ({tipo_lote})\n")
            #f.write(f"Estadísticas: El peor = {peor_makespan_segundos}s | El mejor = {mejor_makespan_segundos}s | El promedio = {promedio_makespan:.0f}s\n")
            #f.write("-" * 60 + "\n")
            #for i, (mkspn, seq) in enumerate(registro_makespans, 1):
                #f.write(f"{i}. Makespan: {mkspn} seg | Secuencia: {' -> '.join(seq)}\n")
            #f.write("\n\n")

    # VERIFICACIÓN VISUAL COMENTADA PARA OPTIMIZAR LA CONSOLA
    '''
    print()
    print("RESUMEN POR LOTE")
    for r in reporte_lotes:
        print(
            f"  > Lote {r['lote_id']} ({r['tipo']}): "
            f"Peor = {r['peor']} seg ({r['peor']/3600:.2f} hrs) | "
            f"Mejor = {r['mejor']} seg ({r['mejor']/3600:.2f} hrs)"
        )

    print()
    print("COTA SUPERIOR GLOBAL ESTABLECIDA")
    print(f"Cantidad total de lotes evaluados: {len(lotes_base)}")
    print(f"LÍMITE MÁXIMO DEL PROYECTO (sumando los peores): {cota_superior_global} seg ({cota_superior_global/3600:.2f} hrs)") # No tenia sentido mostrar esto en segundos
    '''
    return cota_superior_global, reporte_lotes

cota_superior, reporte_metricas_lotes = calcular_cota_superior_exacta(tiempos_unitarios, lotes_base)
print()
print('FASE 6 COMPLETADA')
"""
# ==============================================================================
# 8 HEURÍSTICAS VS SIMULACIONES DE MONTE CARLO
# ==============================================================================
# HALLAZGO CLAVE:
# A baja escala de producción, las dependencias estrictas y los tiempos de
# impresión dominan el makespan teórico, volviendo irrelevante la heurística
# de asignación (todos los enfoques deterministas tienden al mismo resultado)
# Sin embargo, la simulación estocástica demuestra que el verdadero riesgo
# del proyecto no está en el orden de las tareas, sino en la tasa de fallas humanas
print()
print('FASE 7: 8 HEURÍSTICAS VS SIMULACIONES DE MONTE CARLO')

inicio_ejecucion = time.time()

# Preparamos el calendario continuo aplanando el diccionario para convertirlo
# en una lista lineal de tuplas (semana, dia, bloque) para iterar cronologicamente
linea_de_tiempo = []
for sem in range(1, NUM_SEMANAS + 1):
    for dia in diasSemana:
        for bloque in bloquesHorarios:
            linea_de_tiempo.append((sem, dia, bloque))


# Reglas heurísticas de despacho (dispatching rules) usadas en IO
# jeje las dos primeras se usan en gastronomia internacional
# fue cool poder aplicar algo de mi carrera anterior en este contexto
estrategias_deterministas = [
    'FIFO', # First In, First Out (Primero en llegar, primero en salir)
    'LIFO', # Last In, First Out (Último en llegar, primero en salir)
    'Lote_Mas_Incompleto', # Equivalente a MWKR (Most Work Remaining)
    'Lote_Mas_Completo', # Equivalente a LWKR (Least Work Remaining)
    'Tarea_Mas_Larga_Primero', # LPT (Longest Processing Time)
    'Tarea_Mas_Corta_Primero', # SPT (Shortest Processing Time)
    'Lote_Con_Mas_Tareas_Pendientes', # MOPNR (Most Operations Remaining)
    'Lote_Con_Menos_Tareas_Pendientes' # LOPNR (Least Operations Remaining)
]
estrategias_aleatorias = [f'RANDOM_{i}' for i in range(1, CANTIDAD_RANDOMS + 1)]
estrategias = estrategias_deterministas + estrategias_aleatorias

resultados_torneo = []

# Mapeo estricto de requerimientos fisicos. Respondemos ¿que maquina necesita cada tarea?
maquina_req = {
    'B1': 'Corte_Carton', 'B2': 'Corte_Carton', 'B3': 'Corte_Carton', 'B4': 'Corte_Carton',
    'C1': 'Guillotina', 'C2': 'Guillotina',
    'D1': 'Impresora', 'D2': 'Impresora', 'D3': 'Impresora', 'D4': 'Impresora',
    'E1': 'Cinch', 'E2': 'Cinch',
    'F1': 'Tijera', 'F2': 'Alicate_Corte', 'F3': 'Alicate_Presion', 'F4': 'Ojetilladora'
}

def obtener_paquete(codigo_tarea):
    # Busca a que paquete de retribucion (B, C, D, E o F) pertenece una tarea especifica
    for paquete, datos in paquetes_retribucion.items():
        if codigo_tarea in datos['tareas']:
            return paquete
    return None

print(f"Ejecutando {len(estrategias)} escenarios (heuristicas vs aleatorios)")

# Para bajar un poco la amsiedad mostramos cada un 10% de avance para hacerse una idea de como va el script
total_escenarios = len(estrategias)
paso_progreso = max(1, total_escenarios // 10)
# BUCLE PRINCIPAL DEL MOTOR DE SCHEDULING (ALGO ASI COMO UN TORNEO DE ESTRATEGIAS)
for i, estrategia in enumerate(estrategias):

    # MOSTRAMOS EL AVANCE POR PANTALLA
    if (i + 1) % paso_progreso == 0:
        porcentaje_avance = int((i + 1) / total_escenarios * 100)
        print(f"Analizando: {porcentaje_avance:3d}% completado ({i+1}/{total_escenarios} escenarios)")

    # CONGELAMOS LA SEMILLA
    # Si la estrategia es aleatoria (ej. "RANDOM_1993"), extraemos su número (1993)
    # y lo usamos para fijar la semilla de random.seed(), entonces es aleatorio,
    # pero a la vez reproducible para propositos de trazabilidad
    if estrategia.startswith('RANDOM'):
        semilla_actual = int(estrategia.split('_')[1])
        random.seed(semilla_actual)

    # Clonamos el universo de tareas base para no contaminar la siguiente iteración
    tareas = copy.deepcopy(pool_tareas)
    for t in tareas:
        # CORRECCION: COSTO FIJO DE CONFIGURAR LA IMPRESORA CADA VEZ QUE SE VA A PONER A IMPRIMIR
        # Si la tarea es configurar impresora (D1 o D2), el tiempo no depende
        # de la cantidad de agendas, es un valor fijo de 300 segundos por lote
        # Mas aun, esto debera cumplirse independientemente de la cantidad de veces
        # que el mismo estudiante comience a imprimir, es algo asi como un peaje
        # que se cobra justo antes de imprimir, mientras queden hojas por imprimir
        if t['codigo'] in ['D1', 'D2']:
            t['tiempo_total_seg'] = tiempos_unitarios[t['codigo']]['Agenda']

        # Reseteo de variables de estado para la simulacion
        t['tiempo_restante'] = t['tiempo_total_seg']
        t['terminada'] = False
        t['pausada'] = False
        t['tiempo_libre_restante'] = 0

    # SINCRONIZAMOS DE LA META DE MAXIMO 5 HORAS EXTRACURRICULARES
    # Recalculamos el tiempo total esperado para cada paquete basandonos en las tareas ya corregidas
    for p_lote in paquetes_lotes:
        tiempo_corregido = sum(t['tiempo_total_seg'] for t in tareas if t['lote'] == p_lote['lote'] and obtener_paquete(t['codigo']) == p_lote['paquete'])
        p_lote['tiempo_real_seg'] = tiempo_corregido

    estado_estudiantes = {nombre: {
        'tarea_principal': None,
        'maquina': None,
        'ultima_maquina': None
    } for nombre in nombresEstudiantes}

    propietarios_paquetes = {}
    tiempo_total_proyecto = 0
    tareas_pendientes = len(tareas)
    registro_timeline = []
    tiempo_trabajado_real = {e: 0 for e in nombresEstudiantes}
    tiempo_limpieza = {e: 0 for e in nombresEstudiantes}
    registro_retribucion = {e: {} for e in nombresEstudiantes}
    # RESTRICCION INVIOLABLE: MAXIMO DE 5 HORAS EXTRACURRICULARES PARA CADA ESTUDIANTE
    horas_ganadas_tracker = {e: 0.0 for e in nombresEstudiantes}
    # AVANCE CRONOLOGICO:
    # Recorremos bloque por bloque de la línea de tiempo buscando trabajo por hacer
    for instante in linea_de_tiempo:
        if tareas_pendientes == 0:
            break # Proyecto terminado, detenemos el tiempo

        sem, dia, bloque = instante
        # Consulta O(1) a la matriz de disponibilidad (Fase 4.5)
        estudiantes_del_bloque = sorted([e for e in nombresEstudiantes if disponibilidadIndividual8Semanas[e][instante] == 1])
        tiempo_consumido_bloque = {e: 0 for e in estudiantes_del_bloque}
        tiempo_maquinas = {f"{m} {i+1}": 0 for m, cant in recursos.items() for i in range(cant)}
        bloque_efectivamente_trabajado = False

        while True:
            # Filtramos estrictamente a quienes no han superado las 5.0 horas, LA SEGUNDA RESTRICCION ES LA QUE DEBE APLICARSE
            activos = [e for e in estudiantes_del_bloque if tiempo_consumido_bloque[e] < 3600 and horas_ganadas_tracker[e] < 5.0]

            if not activos or tareas_pendientes == 0:
                break

            # Prioridad de asignacion: Al que ha trabajado menos en este bloque horario
            estudiante = min(activos, key=lambda x: tiempo_consumido_bloque[x])
            t_actual = tiempo_consumido_bloque[estudiante]
            tiempo_disponible_estudiante = 3600 - t_actual

            tarea_a_trabajar = None
            # a) LOGICA DE REANUDACIÓN DE TAREAS PAUSADAS
            if estado_estudiantes[estudiante]['tarea_principal'] is not None:
                tarea_a_trabajar = estado_estudiantes[estudiante]['tarea_principal']

                if tarea_a_trabajar['pausada'] and tarea_a_trabajar['codigo'] in ['D3', 'D4']:

                    # LOGICA DE CONTINUIDAD PARA EL CASO DE LAS IMPRESIONES
                    # Si un estudiante esta durante mas de un bloque consecutivo
                    # no deería reconfigurar la impresora a cada rato, sino solo una vez
                    # y que sirva por todo el bloque continuo en el que estara trabajando
                    ultimo_dia = estado_estudiantes[estudiante].get('dia_ultimo_bloque')
                    ultimo_fin = estado_estudiantes[estudiante].get('fin_ultimo_bloque')
                    bloque_inicio = bloque.split('-')[0] # Extrae "10:00" de "10:00-11:00" para que sea el tiempo de inicio
                    es_continuo = (dia == ultimo_dia and bloque_inicio == ultimo_fin)

                    if es_continuo:
                        # Le quitamos la pausa y sigue trabajando
                        tarea_a_trabajar['pausada'] = False
                    else:
                        # Hay un quiebre de tiempo. Toca cobrar el castigo
                        # Definimos dinamicamente cual fue la tarea de configuración previa
                        codigo_config = 'D1' if tarea_a_trabajar['codigo'] == 'D3' else 'D2'
                        # Extraemos el valor exacto desde el diccionario
                        tiempo_castigo = tiempos_unitarios[codigo_config]['Agenda']

                        if tiempo_disponible_estudiante >= tiempo_castigo:
                            tiempo_disponible_estudiante -= tiempo_castigo
                            tarea_a_trabajar['pausada'] = False
                            maq_str = estado_estudiantes[estudiante]['maquina']
                            registro_timeline.append(f"Sem {sem} | {dia} | {bloque} | {estudiante} -> ¡REPETIR! {tiempo_castigo} segundos reconfigurando {maq_str} para {tarea_a_trabajar['id_tarea']}")
                            bloque_efectivamente_trabajado = True
                            tiempo_consumido_bloque[estudiante] += tiempo_castigo
                            if maq_str in tiempo_maquinas:
                                tiempo_maquinas[maq_str] = max(tiempo_maquinas[maq_str], tiempo_consumido_bloque[estudiante])
                        else:
                            # Si no le alcanza el tiempo ni para configurar, limpia y espera
                            espera = tiempo_disponible_estudiante
                            tiempo_limpieza[estudiante] += espera
                            tiempo_consumido_bloque[estudiante] = 3600
                            continue
            # b) LOGICA DE ASIGNACION DE TAREAS NUEVAS
            else:
                completadas = [t['id_tarea'] for t in tareas if t['terminada']]
                # Validamos restricciones de precedencia (DAG)
                disponibles_bruto = [t for t in tareas if not t['terminada'] and t['tiempo_restante'] == t['tiempo_total_seg'] and all(p in completadas for p in t['predecesoras'])]

                # CORRECCION 3 HECHA POR IA EN CONVERSACIÓN 2:
                # -----------------------------------------------
                disponibles = []
                # 1. Calculamos la deuda de tiempo: ¿Cuántas horas ya tiene comprometidas este estudiante?
                horas_comprometidas = sum(
                    p['horas_extracurriculares'] for p in paquetes_lotes 
                    if propietarios_paquetes.get((p['lote'], p['paquete'])) == estudiante
                )

                for t in disponibles_bruto:
                    paq_id = obtener_paquete(t['codigo'])
                    propietario_actual = propietarios_paquetes.get((t['lote'], paq_id))

                    puede_tomar_tarea = False

                    if propietario_actual == estudiante:
                        # Ya es el dueño legal, TIENE que poder continuar
                        puede_tomar_tarea = True
                    elif propietario_actual is None:
                        # Es un paquete sin dueño. ¿Le alcanza el límite de 5 horas para comprometerse?
                        horas_del_nuevo_paquete = next((p['horas_extracurriculares'] for p in paquetes_lotes if p['lote'] == t['lote'] and p['paquete'] == paq_id), 0)
                        
                        # Usamos 5.001 para curarnos en salud con los decimales flotantes de Python
                        if horas_comprometidas + horas_del_nuevo_paquete <= 5.001:
                            puede_tomar_tarea = True

                    if puede_tomar_tarea:
                        req = maquina_req.get(t['codigo'])
                        if req:
                            maq_libres_ahora = [m for m, t_maq in tiempo_maquinas.items() if m.startswith(req) and t_maq <= t_actual]
                            if maq_libres_ahora: disponibles.append(t)
                        else: disponibles.append(t)
                # -----------------------------------------------

                if not disponibles:
                    # Tiempos muertos u ocio forzado (lo consideramos como tiempo que dedica a la limpieza del puesto)
                    espera = min(60, 3600 - t_actual)
                    tiempo_consumido_bloque[estudiante] += espera
                    tiempo_limpieza[estudiante] += espera
                    continue

                # Agrupamos por tipo de tarea para forzar secuencialidad logica
                c1_disp = [t for t in disponibles if t['codigo'] == 'C1']
                c2_disp = [t for t in disponibles if t['codigo'] == 'C2']
                impresion_activa_disp = [t for t in disponibles if t['codigo'] in ['D3', 'D4']]
                config_impresora_disp = [t for t in disponibles if t['codigo'] in ['D1', 'D2']]
                manual_disp = [t for t in disponibles if t['codigo'] in ['B1','B2','B3','B4','E1','E2','F1','F2','F3']]
                f4_disp = [t for t in disponibles if t['codigo'] == 'F4']
                # Aplicamos en cascada las prioridades absolutas del proyecto
                # Estas restricciones son super estrictas y probablemente sean
                # las que hacen que si hay pocos lotes, los tiempos no varien demasiado
                if c1_disp:
                    tarea_a_trabajar = sorted(c1_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]
                elif c2_disp:
                    tarea_a_trabajar = sorted(c2_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]
                elif impresion_activa_disp:
                    tarea_a_trabajar = sorted(impresion_activa_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]
                elif config_impresora_disp and tiempo_disponible_estudiante >= 900:
                    tarea_a_trabajar = sorted(config_impresora_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]
                # APLICACION DE HEURISTICAS DE DESPACHO PARA LAS TAREAS MANUALES
                elif manual_disp:
                    # Iteramos a lo largo de todos los enfoques que definimos previamente.
                    # Notese que las reglas acá son sencillas, por tanto COMO TRABAJO FUTURO
                    # se podrian incluir otros que fueran de interes analizar
                    # Recordemos que siquiera con un lote tenemos 16! ordenamientos
                    # entonces siempre habra 'pocos' escenarios randoms que se evaluen
                    if estrategia == 'FIFO':
                        # Ordena por el numero de lote de menor a mayor (Primero en entrar, primero en salir)
                        tarea_a_trabajar = sorted(manual_disp, key=lambda x: (x['lote'], -x['tiempo_total_seg']))[0]

                    elif estrategia == 'LIFO':
                        # Ordena por el numero de lote de mayor a menor (Ultimo en entrar, primero en salir)
                        tarea_a_trabajar = sorted(manual_disp, key=lambda x: (-x['lote'], -x['tiempo_total_seg']))[0]

                    elif estrategia == 'Lote_Mas_Incompleto':
                        # Ordena por la suma total de segundos que le faltan al lote (de mayor a menor)
                        tarea_a_trabajar = sorted(manual_disp, key=lambda x: (-sum(t['tiempo_restante'] for t in tareas if t['lote'] == x['lote']), x['lote']))[0]

                    elif estrategia == 'Lote_Mas_Completo':
                        # Ordena por la menor cantidad de segundos que le faltan al lote (de menor a mayor)
                        tarea_a_trabajar = sorted(manual_disp, key=lambda x: (sum(t['tiempo_restante'] for t in tareas if t['lote'] == x['lote']), x['lote']))[0]

                    elif estrategia == 'Tarea_Mas_Larga_Primero':
                        # Busca ir terminando las tareas mas extensas en primer lugar
                        tarea_a_trabajar = sorted(manual_disp, key=lambda x: (-x['tiempo_total_seg'], x['lote']))[0]

                    elif estrategia == 'Tarea_Mas_Corta_Primero':
                        # Busca ir terminando las tareas mas cortas en primer lugar
                        tarea_a_trabajar = sorted(manual_disp, key=lambda x: (x['tiempo_total_seg'], x['lote']))[0]

                    elif estrategia == 'Lote_Con_Mas_Tareas_Pendientes':
                        # Ordena por la cantidad de operaciones (tareas) no terminadas que le quedan al lote
                        tarea_a_trabajar = sorted(manual_disp, key=lambda x: (-sum(1 for t in tareas if t['lote'] == x['lote'] and not t['terminada']), x['lote']))[0]

                    elif estrategia == 'Lote_Con_Menos_Tareas_Pendientes':
                        # Ordena por la menor cantidad de operaciones no terminadas que le quedan al lote
                        tarea_a_trabajar = sorted(manual_disp, key=lambda x: (sum(1 for t in tareas if t['lote'] == x['lote'] and not t['terminada']), x['lote']))[0]

                    elif estrategia.startswith('RANDOM'):
                        tarea_a_trabajar = random.choice(manual_disp)
                elif f4_disp:
                    tarea_a_trabajar = sorted(f4_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]

                # CORRECCION 1 HECHA POR IA EN CONVERSACIÓN 2:
                # --- ¡AQUÍ VA EL PARCHE! ---
                if not tarea_a_trabajar:
                    # El estudiante tiene tareas disponibles (ej. D1/D2), pero no le alcanza el 
                    # tiempo mínimo exigido (900s). Forzamos a que el tiempo sobrante se vaya 
                    # a limpieza/ocio para salir del bucle.
                    espera = min(60, 3600 - t_actual)
                    tiempo_consumido_bloque[estudiante] += espera
                    tiempo_limpieza[estudiante] += espera
                    continue
                # -----------------------------
                # ASIGNACIÓN DE TAREAS, PROPIEDAD Y MAQUINAS
                if tarea_a_trabajar:
                    # Hacemos el registro de la actividad actual en el estado del estudiante
                    estado_estudiantes[estudiante]['tarea_principal'] = tarea_a_trabajar
                    tarea_a_trabajar['pausada'] = False

                    # Logica de propiedad (Ownership) para retribucion extracurricular
                    # Vinculamos al estudiante con este sub-paquete específico del lote
                    # Esto asegura que el estudiante que toma un paquete, se vuelve
                    # dueño de este, evitando que el trabajo (y el pago) se traslape
                    paq_asignado = obtener_paquete(tarea_a_trabajar['codigo'])
                    if paq_asignado:
                        propietarios_paquetes[(tarea_a_trabajar['lote'], paq_asignado)] = estudiante

                    # Hacemos la asignación de maquinaria y optimizacion de movimientos
                    req = maquina_req.get(tarea_a_trabajar['codigo'])
                    if req:
                        # Filtramos las máquinas del tipo requerido que estan desocupadas en este segundo
                        maq_libres_ahora = sorted([m for m, t_maq in tiempo_maquinas.items() if m.startswith(req) and t_maq <= t_actual])
                        maq_previa = estado_estudiantes[estudiante].get('ultima_maquina')
                        # Heuristica de eficiencia espacial: Si la maquina que el estudiante
                        # uso la ultima vez sigue libre, se le reasigna. Esto simula que la persona
                        # se queda en su mismo puesto de trabajo en lugar de rotar innecesariamente
                        # En caso contrario tendriamos que en cada bloque podriamos estar haciendo
                        # que el estudiante cambie de maquinaria usada
                        if maq_previa in maq_libres_ahora:
                            maq_asignada = maq_previa
                        else:
                            maq_asignada = maq_libres_ahora[0] # Toma la primera maquina disponible de la lista

                        estado_estudiantes[estudiante]['maquina'] = maq_asignada
                        estado_estudiantes[estudiante]['ultima_maquina'] = maq_asignada
                    else:
                        # Si la tarea no requiere maquinaria, va al pool de trabajo manual
                        estado_estudiantes[estudiante]['maquina'] = "Mesa de Trabajo (Manual)"
                        estado_estudiantes[estudiante]['ultima_maquina'] = None

                    # Regla especial de tiempos muertos (autonomiaa en impresion)
                    # Las tareas D3 y D4 corresponden a la impresora. Por observación empirica,
                    # se establece que el 40% del tiempo de impresion la impresora trabaja sola,
                    # dejando al estudiante con "tiempo libre restante" dentro de ese mismo bloque
                    # el cual obviamente puede aprovechar realizando otra tarea, pero dejamos
                    # bliqueada a esa impresora para no ser reasignada en el tiempo que corresponde
                    if tarea_a_trabajar['codigo'] in ['D3', 'D4']:
                        tarea_a_trabajar['tiempo_libre_restante'] = tarea_a_trabajar['tiempo_total_seg'] * 0.4

            # REGISTRO DE TIEMPOS, DESCUENTOS Y RETRIBUCION DE LAS HORAS EXTRACURRICULARES
            if tarea_a_trabajar:
                # Realizamos el calculo de capacidad de procesamiento
                # El tiempo a dedicar es el mínimo entre lo que le queda libre al estudiante
                # en este bloque horario (max 3600s) y lo que le falta a la tarea para terminar
                tiempo_a_dedicar = min(tiempo_disponible_estudiante, tarea_a_trabajar['tiempo_restante'])

                if tiempo_a_dedicar > 0:
                    bloque_efectivamente_trabajado = True
                    tiempo_trabajado_real[estudiante] += tiempo_a_dedicar
                    # Contabilizamos el "pago" de las horas extracurriculares
                    # Buscamos a que paquete pertenece la tarea para abonar el tiempo a la
                    # "billetera" del estudiante correspondiente
                    paq = obtener_paquete(tarea_a_trabajar['codigo'])
                    if paq:
                        clave_ret = (tarea_a_trabajar['lote'], paq)
                        registro_retribucion[estudiante][clave_ret] = registro_retribucion[estudiante].get(clave_ret, 0) + tiempo_a_dedicar
                        # ACTUALIZACIÓN EN TIEMPO REAL (limite estricto de 5 horas)
                        # Calculamos dinamicamente qué porcentaje de la tarea completo en este instante
                        # y le sumamos la fracción equivalente de horas extracurriculares a su tracker
                        # Vital para que el ciclo 'while' se detenga si alcanza las 5.0 horas
                        for p_lote in paquetes_lotes:
                            if p_lote['lote'] == tarea_a_trabajar['lote'] and p_lote['paquete'] == paq:
                                if p_lote['tiempo_real_seg'] > 0:
                                    horas_sumadas = (tiempo_a_dedicar / p_lote['tiempo_real_seg']) * p_lote['horas_extracurriculares']
                                    horas_ganadas_tracker[estudiante] += horas_sumadas
                                break

                # Bitacora del sistema (timeline)
                # Evaluamos de forma anticipada si este avance terminara la tarea o no,
                # esto para que el registro en texto quede escrito correctamente
                estado_accion = "FINALIZADA" if (tarea_a_trabajar['tiempo_restante'] - tiempo_a_dedicar) <= 0 else "EN PROGRESO"
                maq_str = estado_estudiantes[estudiante]['maquina']
                registro_timeline.append(f"Sem {sem} | {dia} | {bloque} | {estudiante} -> {tiempo_a_dedicar}s en {tarea_a_trabajar['id_tarea']} (en {maq_str}) Se encuentra {estado_accion}")
                # Actualizamos los estados de simulacion
                tarea_a_trabajar['tiempo_restante'] -= tiempo_a_dedicar
                tiempo_consumido_bloque[estudiante] += tiempo_a_dedicar
                # Actualizamos la ocupacion de la maquina para evitar superposiciones
                if maq_str in tiempo_maquinas:
                    tiempo_maquinas[maq_str] = max(tiempo_maquinas[maq_str], tiempo_consumido_bloque[estudiante])
                # Descuento del tiempo de autonomía de la máquina (ej: impresora trabajando sola)
                if tarea_a_trabajar['tiempo_libre_restante'] > 0:
                    tarea_a_trabajar['tiempo_libre_restante'] -= tiempo_a_dedicar
                # Logica de finalizacion o suspensiom (preemption)
                if tarea_a_trabajar['tiempo_restante'] <= 0:
                    # CASO A: La tarea se completó exitosamente
                    tarea_a_trabajar['terminada'] = True
                    tareas_pendientes -= 1
                    estado_estudiantes[estudiante]['tarea_principal'] = None
                    estado_estudiantes[estudiante]['maquina'] = None
                else:
                    # CASO B: El estudiante agoto su bloque de 1 hora (3600s) pero la tarea sigue activa
                    # Se debe pausar la tarea y guardar el instante exacto en que la dejo
                    if tiempo_consumido_bloque[estudiante] >= 3600:
                        tarea_a_trabajar['pausada'] = True
                        # GUARDAMOS LA HORA EXACTA EN QUE SE FUE A PAUSA
                        # Esto alimenta la logica de continuidad posterior. Si el estudiante vuelve
                        # en el bloque inmediatamente siguiente, no se le cobra el tiempo de configuración
                        # de la impresora porque al cobrarlo la primera vez, 'sirve' para
                        # todos los bloques consecutivos en los que estara haciendo la misma tarea
                        estado_estudiantes[estudiante]['dia_ultimo_bloque'] = dia
                        estado_estudiantes[estudiante]['fin_ultimo_bloque'] = bloque.split('-')[1] # Ej: extrae "11:00" para que sea el tiempo final


        if bloque_efectivamente_trabajado:
            tiempo_total_proyecto += 3600 # ESTE VALOR ES CONSTANTE ASUMIENDO QUE SON BLOQUES DE 1 HORA CADA UNO

    exito = tareas_pendientes == 0
    resultados_torneo.append({
        'estrategia': estrategia,
        'exito': exito,
        'makespan': tiempo_total_proyecto if exito else float('inf'),
        'pendientes': tareas_pendientes,
        'timeline': copy.deepcopy(registro_timeline),
        'stats_tiempo_real': copy.deepcopy(tiempo_trabajado_real),
        'stats_limpieza': copy.deepcopy(tiempo_limpieza),
        'stats_retribucion': copy.deepcopy(registro_retribucion)
    })

fin_ejecucion = time.time()

# RESULTADOS
print()
print("RESULTADOS")
print()

resultados_det = [r for r in resultados_torneo if r['exito'] and not r['estrategia'].startswith('RANDOM')]
resultados_rand = [r for r in resultados_torneo if r['exito'] and r['estrategia'].startswith('RANDOM')]

# Imprimir las deterministas
print()
print("DESEMPEÑO DE REGLAS HEURISTICAS")
for r in resultados_det:
    print(f"  > Estrategia {r['estrategia'].ljust(7)}: {r['makespan']} seg ({r['makespan']/3600:.2f} hrs de ocupación)")

# Análisis del Monte Carlo
if resultados_rand:
    resultados_rand.sort(key=lambda x: x['makespan'])
    mejor_rand = resultados_rand[0]
    peor_rand = resultados_rand[-1]
    total_corridas = len(resultados_rand)
    promedio_rand = sum(r['makespan'] for r in resultados_rand) / total_corridas

    print()
    print(f"RESUMEN DE LAS {total_corridas} SIMULACIONES ALEATORIAS ")
    print(f"Mejor ({mejor_rand['estrategia']}): {mejor_rand['makespan']} seg ({mejor_rand['makespan']/3600:.2f} hrs)")
    print(f"Peor({peor_rand['estrategia']}): {peor_rand['makespan']} seg ({peor_rand['makespan']/3600:.2f} hrs)")
    print(f"Promedio: {promedio_rand:.0f} seg ({promedio_rand/3600:.2f} hrs)")

print()
#print(f"DETALLE DE ESTRATEGIAS (Se omiten los {total_corridas - 1} escenarios aleatorios descartados)")
print()

# Filtramos para mostrar los detalles (todas las deterministas + el mejor y el peor random)
estrategias_a_mostrar = resultados_det.copy()
if resultados_rand:
    estrategias_a_mostrar.append(mejor_rand)
    # Solo lo agregamos si es distinto al mejor (por si acaso evaluamos pocos randoms)
    if peor_rand['estrategia'] != mejor_rand['estrategia']:
        estrategias_a_mostrar.append(peor_rand)

# RESUMEN DONDE MOSTRAMOS TODAS LAS ESTRATEGIAS POSIBLES
for r in estrategias_a_mostrar:
    print()
    print()
    print(f"ESTRATEGIA: {r['estrategia']} | Makespan: {r['makespan']} seg ({r['makespan']/3600:.2f} hrs)")
    print()
    # Por cada una mostramos el itinerario completo
    print("LINEA DE TIEMPO")
    bloque_anterior = None
    for linea in r['timeline']:
        # Extraemos la semana, el dia y la hora para saber en qué bloque estamos
        partes = linea.split(" | ")
        if len(partes) >= 3:
            bloque_actual = f"{partes[0]} | {partes[1]} | {partes[2]}"
            # Si el bloque cambio respecto al de la línea anterior, insertamos un espacio en blanco para que se pueda leer de forma mas comoda por pantalla
            if bloque_anterior is not None and bloque_actual != bloque_anterior:
                print("")

        bloque_anterior = bloque_actual

        print(linea)

    # Para este enfoque mostramos el resumen de los estudiantes que trabajaron
    print()
    print("RESUMEN DE ESTUDIANTES Y RETRIBUCION DE LAS HORAS EXTRACURRICULARES")
    for estudiante in nombresEstudiantes:
        t_real_seg = r['stats_tiempo_real'][estudiante]
        t_limpieza_seg = r['stats_limpieza'][estudiante]
        horas_extra_totales = 0.0
        print()
        print(f"Estudiante: {estudiante.upper()}")
        print(f"Tiempo real trabajando: {t_real_seg} seg ({t_real_seg/3600:.2f} hrs)")
        print(f"Tiempo en orden/limpieza/ocio: {t_limpieza_seg} seg ({t_limpieza_seg/3600:.2f} hrs)")

        for (lote_id, paquete_id), seg_trabajados in r['stats_retribucion'][estudiante].items():
            for p_lote in paquetes_lotes:
                if p_lote['lote'] == lote_id and p_lote['paquete'] == paquete_id:
                    if p_lote['tiempo_real_seg'] > 0:
                        proporcion_trabajada = seg_trabajados / p_lote['tiempo_real_seg']
                        horas_ganadas = proporcion_trabajada * p_lote['horas_extracurriculares']
                        horas_extra_totales += horas_ganadas
                        print(f"Lote {lote_id} | Pqt {paquete_id}: Aporto {seg_trabajados}s ({proporcion_trabajada*100:.1f}%) y le corresponden {horas_ganadas:.3f} hrs. extracurriculares")

        print(f"Total a asignar: {horas_extra_totales:.3f} hrs extracurriculares")

    # Version individual, para ver la línea de tiempo de cada estudiante
    # Si hay un unico estudiante, no es necesario mostrarlo porque es el mismo
    # que para el proyecto completo
    if len(nombresEstudiantes) > 1:
        print("")
        print("ORDENAMIENTOS DE TRABAJO INDIVIDUALES")
        for estudiante in nombresEstudiantes:
            print()
            print(f"ESTUDIANTE: {estudiante.upper()}")

            semanas_dict = {}
            for linea in r['timeline']:
                if " -> " not in linea:
                    continue

                # Desarmamos la línea de texto para extraer sus componentes
                partes = linea.split(" | ")
                if len(partes) >= 4:
                    sem_str = partes[0].strip()
                    dia_str = partes[1].strip()
                    bloque_str = partes[2].strip()
                    est_str, accion_str = partes[3].split(" -> ", 1)
                    est_str = est_str.strip()

                    # Si la línea le pertenece al estudiante que estamos evaluando, la guardamos
                    if est_str == estudiante:
                        if sem_str not in semanas_dict:
                            semanas_dict[sem_str] = {}
                        if dia_str not in semanas_dict[sem_str]:
                            semanas_dict[sem_str][dia_str] = []
                        semanas_dict[sem_str][dia_str].append(f"[{bloque_str}] -> {accion_str}")

            if not semanas_dict: # Caso muy rebusacado donde un estudiante tiene poca disponibilidad y es muy al final de la semana
                # entonces todas las tareas ya fueron asignadas y uno se queda sin hacer nada, quizas no lo veamos en la practica jiji
                print("Sin tareas asignadas en esta estrategia")
            else:
                # Imprimimos de forma agrupada y bonita
                for sem in sorted(semanas_dict.keys()):
                    print()
                    print(f"{sem.upper()}")
                    for dia, acciones in semanas_dict[sem].items():
                        print(f"{dia}:")

                        bloque_anterior = None
                        for accion in acciones:
                            # Extraemos el bloque de la cadena (ej: "[09:00-10:00") para compararlo
                            bloque_actual = accion.split("]")[0]

                            # Si hay un bloque anterior y es distinto al actual, imprimimos una línea en blanco
                            if bloque_anterior is not None and bloque_actual != bloque_anterior:
                                print("")

                            bloque_anterior = bloque_actual
                            print(f"{accion}")

# TIEMPO DE EJECUCION
tiempo_total = fin_ejecucion - inicio_ejecucion
horas, resto = divmod(tiempo_total, 3600)
minutos, segundos = divmod(resto, 60)
print()
print(f"Tiempo total de procesamiento ({len(estrategias_deterministas)} + {CANTIDAD_RANDOMS} escenarios): {tiempo_total:.4f} segundos ({int(horas):02d}:{int(minutos):02d}:{segundos:05.2f})")
print()
print('FASE 7 COMPLETADA')

# ==============================================================================
# SIMULACIONES DE ERRORES (REGLA: EL QUE ROMPE, LO ARREGLA)
# ==============================================================================

print()
print('FASE 8: SIMULACIONES DE ERRORES (REGLA: EL QUE ROMPE, LO ARREGLA)')

inicio_fase8 = time.time()

try:
    peor_escenario = max(resultados_torneo, key=lambda x: x['makespan'])
    estrategia_objetivo = peor_escenario['estrategia']
    makespan_base = peor_escenario['makespan']
except NameError:
    print("[ERROR] Ejecuta la fase anterior")
    estrategia_objetivo = 'FIFO'
    makespan_base = 0

print()
print(f"Estrategia seleccionada para someter a estres: {estrategia_objetivo}")
print(f"Makespan original (sin errores): {makespan_base/3600:.2f} hrs")

# Probabilidad de aruinar alguna de las acciones
# Aca solo vamos a considerar que el error es humano
# No estamos considerando que se rehagan todas las fases previas
# Por ejemplo si se arruina B4, se deberia rehacer B1, B2 y B3, pero por el amor de dios
# ya llevo mas de 1000 lineas de codigo, que eso lo haga otra persona si retoma este codigo
probabilidad_ruina = {
    'B1': 0.15, 'B2': 0.25, 'B3': 0.20, 'B4': 0.15,
    'C1': 0.45, 'C2': 0.40,
    'D1': 0.50, 'D2': 0.55, 'D3': 0.55, 'D4': 0.50, # Cuello de botella estresado
    'E1': 0.35, 'E2': 0.30,
    'F1': 0.25, 'F2': 0.15, 'F3': 0.15, 'F4': 0.20
}

resultados_estocasticos = []

print(f"Iniciando {CANTIDAD_SIMULACIONES} simulaciones de universos paralelos con fallas")
print()

def simular_con_ruina(semilla):
    random.seed(semilla)

    tareas = copy.deepcopy(pool_tareas) ##  estoooooo

    for t in tareas:
        if t['codigo'] in ['D1', 'D2']:
            t['tiempo_total_seg'] = tiempos_unitarios[t['codigo']]['Agenda']
        t['tiempo_restante'] = t['tiempo_total_seg']
        t['terminada'] = False
        t['pausada'] = False
        t['tiempo_libre_restante'] = 0
        t['es_retrabajo'] = False # Para desviar el tiempo a la billetera de errores

    for p_lote in paquetes_lotes:
        tiempo_corregido = sum(t['tiempo_total_seg'] for t in tareas if t['lote'] == p_lote['lote'] and obtener_paquete(t['codigo']) == p_lote['paquete'])
        p_lote['tiempo_real_seg'] = tiempo_corregido

    estado_estudiantes = {nombre: {'tarea_principal': None, 'maquina': None, 'ultima_maquina': None} for nombre in nombresEstudiantes}
    propietarios_paquetes = {}

    tiempo_total_proyecto = 0
    tareas_pendientes = len(tareas)
    registro_timeline = []
    tiempo_trabajado_real = {e: 0 for e in nombresEstudiantes}
    tiempo_limpieza = {e: 0 for e in nombresEstudiantes}
    registro_retribucion = {e: {} for e in nombresEstudiantes}

    # DOS BILLETERAS, UNA PARA EL TIEMPO GENERAL QUE SON MAXIMO 5 HORAS Y OTRA PARA EL TIEMPO ADICIONAL REHACIENDO LAS TAREAS
    horas_ganadas_tracker = {e: 0.0 for e in nombresEstudiantes}
    horas_error_tracker = {e: 0.0 for e in nombresEstudiantes}

    for instante in linea_de_tiempo:
        if tareas_pendientes == 0:
            break

        sem, dia, bloque = instante
        estudiantes_del_bloque = sorted([e for e in nombresEstudiantes if disponibilidadIndividual8Semanas[e][instante] == 1])
        tiempo_consumido_bloque = {e: 0 for e in estudiantes_del_bloque}
        tiempo_maquinas = {f"{m} {i+1}": 0 for m, cant in recursos.items() for i in range(cant)}
        bloque_efectivamente_trabajado = False

        while True:
            # ESTRICTO: Solo trabajan si su billetera base tiene menos de 5.0 horas, en caso contrario debera ir a la otra billetera
            activos = [e for e in estudiantes_del_bloque if tiempo_consumido_bloque[e] < 3600 and horas_ganadas_tracker[e] < 5.0]
            if not activos or tareas_pendientes == 0:
                break

            estudiante = min(activos, key=lambda x: tiempo_consumido_bloque[x])
            t_actual = tiempo_consumido_bloque[estudiante]
            tiempo_disponible_estudiante = 3600 - t_actual

            tarea_a_trabajar = None

            # REANUDAR
            if estado_estudiantes[estudiante]['tarea_principal'] is not None:
                tarea_a_trabajar = estado_estudiantes[estudiante]['tarea_principal']
                if tarea_a_trabajar['pausada']:
                    if tarea_a_trabajar['codigo'] in ['D3', 'D4']:
                        # CONTINUIDAD
                        ultimo_dia = estado_estudiantes[estudiante].get('dia_ultimo_bloque')
                        ultimo_fin = estado_estudiantes[estudiante].get('fin_ultimo_bloque')
                        bloque_inicio = bloque.split('-')[0]

                        es_continuo = (dia == ultimo_dia and bloque_inicio == ultimo_fin)

                        if es_continuo:
                            # Continuidad perfecta, no hay castigo
                            tarea_a_trabajar['pausada'] = False
                        else:
                            # Hubo interrupcion, se cobra el castigo
                            codigo_config = 'D1' if tarea_a_trabajar['codigo'] == 'D3' else 'D2'
                            tiempo_castigo = tiempos_unitarios[codigo_config]['Agenda']

                            if tiempo_disponible_estudiante >= tiempo_castigo:
                                tiempo_disponible_estudiante -= tiempo_castigo
                                tarea_a_trabajar['pausada'] = False
                                maq_str = estado_estudiantes[estudiante]['maquina']
                                registro_timeline.append(f"Sem {sem} | {dia} | {bloque} | {estudiante} -> ¡REPETIR! {tiempo_castigo} segundos reconfigurando {maq_str} para {tarea_a_trabajar['id_tarea']}")
                                bloque_efectivamente_trabajado = True
                                tiempo_consumido_bloque[estudiante] += tiempo_castigo
                                if maq_str in tiempo_maquinas:
                                    tiempo_maquinas[maq_str] = max(tiempo_maquinas[maq_str], tiempo_consumido_bloque[estudiante])
                            else:
                                tiempo_limpieza[estudiante] += tiempo_disponible_estudiante
                                tiempo_consumido_bloque[estudiante] = 3600
                                continue
                    else:
                        tarea_a_trabajar['pausada'] = False
            else:
                completadas = [t['id_tarea'] for t in tareas if t['terminada']]
                disponibles_bruto = [t for t in tareas if not t['terminada'] and t['tiempo_restante'] == t['tiempo_total_seg'] and all(p in completadas for p in t['predecesoras'])]
                # CORRECCION 3 HECHA POR IA EN CONVERSACIÓN 2:
                # -----------------------------------------------
                disponibles = []
                # 1. Calculamos la deuda de tiempo: ¿Cuántas horas ya tiene comprometidas este estudiante?
                horas_comprometidas = sum(
                    p['horas_extracurriculares'] for p in paquetes_lotes 
                    if propietarios_paquetes.get((p['lote'], p['paquete'])) == estudiante
                )

                for t in disponibles_bruto:
                    paq_id = obtener_paquete(t['codigo'])
                    propietario_actual = propietarios_paquetes.get((t['lote'], paq_id))

                    puede_tomar_tarea = False

                    if propietario_actual == estudiante:
                        # Ya es el dueño legal, TIENE que poder continuar
                        puede_tomar_tarea = True
                    elif propietario_actual is None:
                        # Es un paquete sin dueño. ¿Le alcanza el límite de 5 horas para comprometerse?
                        horas_del_nuevo_paquete = next((p['horas_extracurriculares'] for p in paquetes_lotes if p['lote'] == t['lote'] and p['paquete'] == paq_id), 0)
                        
                        # Usamos 5.001 para curarnos en salud con los decimales flotantes de Python
                        if horas_comprometidas + horas_del_nuevo_paquete <= 5.001:
                            puede_tomar_tarea = True

                    if puede_tomar_tarea:
                        req = maquina_req.get(t['codigo'])
                        if req:
                            maq_libres_ahora = [m for m, t_maq in tiempo_maquinas.items() if m.startswith(req) and t_maq <= t_actual]
                            if maq_libres_ahora: disponibles.append(t)
                        else: disponibles.append(t)
                # -----------------------------------------------

                if not disponibles:
                    espera = min(60, 3600 - t_actual)
                    tiempo_consumido_bloque[estudiante] += espera
                    tiempo_limpieza[estudiante] += espera
                    continue

                c1_disp = [t for t in disponibles if t['codigo'] == 'C1']
                c2_disp = [t for t in disponibles if t['codigo'] == 'C2']
                imp_activa_disp = [t for t in disponibles if t['codigo'] in ['D3', 'D4']]
                conf_imp_disp = [t for t in disponibles if t['codigo'] in ['D1', 'D2']]
                manual_disp = [t for t in disponibles if t['codigo'] in ['B1','B2','B3','B4','E1','E2','F1','F2','F3']]
                f4_disp = [t for t in disponibles if t['codigo'] == 'F4']

                # Respetamos SIEMPRE la peor estrategia que fue identificada
                estrategia = estrategia_objetivo

                if c1_disp: tarea_a_trabajar = sorted(c1_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]
                elif c2_disp: tarea_a_trabajar = sorted(c2_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]
                elif imp_activa_disp: tarea_a_trabajar = sorted(imp_activa_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]
                elif conf_imp_disp and tiempo_disponible_estudiante >= 900: tarea_a_trabajar = sorted(conf_imp_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]
                elif manual_disp:
                    if estrategia == 'FIFO': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (x['lote'], -x['tiempo_total_seg']))[0]
                    elif estrategia == 'LIFO': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (-x['lote'], -x['tiempo_total_seg']))[0]
                    elif estrategia == 'Lote_Mas_Incompleto': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (-sum(t['tiempo_restante'] for t in tareas if t['lote'] == x['lote']), x['lote']))[0]
                    elif estrategia == 'Lote_Mas_Completo': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (sum(t['tiempo_restante'] for t in tareas if t['lote'] == x['lote']), x['lote']))[0]
                    elif estrategia == 'Tarea_Mas_Larga_Primero': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (-x['tiempo_total_seg'], x['lote']))[0]
                    elif estrategia == 'Tarea_Mas_Corta_Primero': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (x['tiempo_total_seg'], x['lote']))[0]
                    elif estrategia == 'Lote_Con_Mas_Tareas_Pendientes': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (-sum(1 for t in tareas if t['lote'] == x['lote'] and not t['terminada']), x['lote']))[0]
                    elif estrategia == 'Lote_Con_Menos_Tareas_Pendientes': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (sum(1 for t in tareas if t['lote'] == x['lote'] and not t['terminada']), x['lote']))[0]
                elif f4_disp: tarea_a_trabajar = sorted(f4_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]

                # CORRECCION 1 HECHA POR IA EN CONVERSACIÓN 2:
                # --- ¡AQUÍ VA EL PARCHE PARA EL MONTE CARLO! ---
                if not tarea_a_trabajar:
                    espera = min(60, 3600 - t_actual)
                    tiempo_consumido_bloque[estudiante] += espera
                    tiempo_limpieza[estudiante] += espera
                    continue
                # -----------------------------------------------

                if tarea_a_trabajar:
                    estado_estudiantes[estudiante]['tarea_principal'] = tarea_a_trabajar
                    tarea_a_trabajar['pausada'] = False
                    paq_asignado = obtener_paquete(tarea_a_trabajar['codigo'])
                    if paq_asignado: propietarios_paquetes[(tarea_a_trabajar['lote'], paq_asignado)] = estudiante
                    req = maquina_req.get(tarea_a_trabajar['codigo'])
                    if req:
                        maq_libres_ahora = sorted([m for m, t_maq in tiempo_maquinas.items() if m.startswith(req) and t_maq <= t_actual])
                        maq_previa = estado_estudiantes[estudiante].get('ultima_maquina')
                        maq_asignada = maq_previa if maq_previa in maq_libres_ahora else maq_libres_ahora[0]
                        estado_estudiantes[estudiante]['maquina'] = maq_asignada
                        estado_estudiantes[estudiante]['ultima_maquina'] = maq_asignada
                    else:
                        estado_estudiantes[estudiante]['maquina'] = "Mesa de Trabajo"
                        estado_estudiantes[estudiante]['ultima_maquina'] = None

                    if tarea_a_trabajar['codigo'] in ['D3', 'D4']:
                        tarea_a_trabajar['tiempo_libre_restante'] = tarea_a_trabajar['tiempo_total_seg'] * 0.4

            # REGISTRO DE TIEMPOS PARA SCHEDULINGS
            if tarea_a_trabajar:
                tiempo_a_dedicar = min(tiempo_disponible_estudiante, tarea_a_trabajar['tiempo_restante'])

                if tiempo_a_dedicar > 0:
                    bloque_efectivamente_trabajado = True
                    tiempo_trabajado_real[estudiante] += tiempo_a_dedicar

                    paq = obtener_paquete(tarea_a_trabajar['codigo'])
                    if paq:
                        clave_ret = (tarea_a_trabajar['lote'], paq)
                        registro_retribucion[estudiante][clave_ret] = registro_retribucion[estudiante].get(clave_ret, 0) + tiempo_a_dedicar

                        # ACTUALIZAMOS LAS BILLETERAS EN TIEMPO REAL
                        for p_lote in paquetes_lotes:
                            if p_lote['lote'] == tarea_a_trabajar['lote'] and p_lote['paquete'] == paq:
                                if p_lote['tiempo_real_seg'] > 0:
                                    horas_sumadas = (tiempo_a_dedicar / p_lote['tiempo_real_seg']) * p_lote['horas_extracurriculares']
                                    if tarea_a_trabajar.get('es_retrabajo', False):
                                        horas_error_tracker[estudiante] += horas_sumadas
                                    else:
                                        horas_ganadas_tracker[estudiante] += horas_sumadas
                                break

                estado_accion = "FINALIZADA" if (tarea_a_trabajar['tiempo_restante'] - tiempo_a_dedicar) <= 0 else "EN PROGRESO"
                maq_str = estado_estudiantes[estudiante]['maquina']
                registro_timeline.append(f"Sem {sem} | {dia} | {bloque} | {estudiante} -> {tiempo_a_dedicar}s en {tarea_a_trabajar['id_tarea']} (en {maq_str}) Se encuentra {estado_accion}")

                tarea_a_trabajar['tiempo_restante'] -= tiempo_a_dedicar
                tiempo_consumido_bloque[estudiante] += tiempo_a_dedicar

                if maq_str in tiempo_maquinas:
                    tiempo_maquinas[maq_str] = max(tiempo_maquinas[maq_str], tiempo_consumido_bloque[estudiante])

                if tarea_a_trabajar['tiempo_libre_restante'] > 0:
                    tarea_a_trabajar['tiempo_libre_restante'] -= tiempo_a_dedicar

                # ESTOCASTICA
                if tarea_a_trabajar['tiempo_restante'] <= 0:
                    prob_fallo = probabilidad_ruina.get(tarea_a_trabajar['codigo'], 0.0)

                    if random.random() < prob_fallo:
                        # DESASTRE: Se arruino la tarea.
                        tarea_a_trabajar['tiempo_restante'] = tarea_a_trabajar['tiempo_total_seg']
                        if tarea_a_trabajar['codigo'] in ['D3', 'D4']:
                            tarea_a_trabajar['tiempo_libre_restante'] = tarea_a_trabajar['tiempo_total_seg'] * 0.4
                        tarea_a_trabajar['terminada'] = False
                        tarea_a_trabajar['pausada'] = True # OBLIGA AL MISMO ESTUDIANTE A REHACERLA
                        tarea_a_trabajar['es_retrabajo'] = True # EL TIEMPO AHORA SE VA A LA BILLETERA DE ERRORES, NO AL PRINCIPAL
                        registro_timeline.append(f"Sem {sem} | {dia} | {bloque} | {estudiante} -> ¡ARRUINADA! La accion {tarea_a_trabajar['id_tarea']} no fue hecha correctamente. PRIORIDAD: rehacer la tarea")
                    else:
                        # EXITO
                        tarea_a_trabajar['terminada'] = True
                        tareas_pendientes -= 1
                        estado_estudiantes[estudiante]['tarea_principal'] = None
                        estado_estudiantes[estudiante]['maquina'] = None
                else:
                    if tiempo_consumido_bloque[estudiante] >= 3600:
                        tarea_a_trabajar['pausada'] = True
                    # GUARDAMOS LA HORA EXACTA EN QUE SE FUE A PAUSA
                        estado_estudiantes[estudiante]['dia_ultimo_bloque'] = dia
                        estado_estudiantes[estudiante]['fin_ultimo_bloque'] = bloque.split('-')[1]

        if bloque_efectivamente_trabajado:
            tiempo_total_proyecto += 3600

    exito = (tareas_pendientes == 0)
    return {
        'exito': exito,
        'makespan': tiempo_total_proyecto if exito else float('inf'),
        'pendientes': tareas_pendientes,
        'timeline_completo': copy.deepcopy(registro_timeline),
        'stats_tiempo_real': copy.deepcopy(tiempo_trabajado_real),
        'stats_limpieza': copy.deepcopy(tiempo_limpieza),
        'stats_retribucion': copy.deepcopy(registro_retribucion),
        'stats_horas_base': copy.deepcopy(horas_ganadas_tracker),
        'stats_horas_error': copy.deepcopy(horas_error_tracker)
    }

# MONTE CARLO
exitos_totales = 0
makespans_exitosos = []
peor_timeline_completo = []
peor_makespan_registrado = 0
peor_stats_tiempo_real = {}
peor_stats_limpieza = {}
peor_stats_retribucion = {}
peor_stats_horas_base = {}
peor_stats_horas_error = {}

# ALGO ASI COMO UN HISTOGRAMA
distribucion_fallas = {}

# PROGRESO ( 10 EN 10%)
paso_progreso = max(1, CANTIDAD_SIMULACIONES // 10)

for i in range(CANTIDAD_SIMULACIONES):
    resultado = simular_con_ruina(semilla=1000 + i)

    # CORRECCION 2 HECHA POR IA EN CONVERSACIÓN 2:
    # -----------------------------------------------
    # Añadimos un ID para identificar el universo al imprimir
    resultado['universo_id'] = i + 1 
    
    # ¡AQUÍ GUARDAMOS CADA SIMULACIÓN EN TU LISTA!
    resultados_estocasticos.append(resultado)
    # -----------------------------------------------
    # LA CORRECCIÓN SIGUIENTE DEL MISMO MENSAJE NO FUE IMPLEMENTADA 

    # AVANCE
    if (i + 1) % paso_progreso == 0:
        porcentaje_avance = int((i + 1) / CANTIDAD_SIMULACIONES * 100)
        print(f"Analizando multiverso: {porcentaje_avance:3d}% completado ({i+1}/{CANTIDAD_SIMULACIONES} escenarios)")

    # Contamos las fallas exclusivamente en ESTE universo en particular y lo guardamos
    fallas_en_este_universo = sum(1 for linea in resultado['timeline_completo'] if '¡ARRUINADA!' in linea)
    distribucion_fallas[fallas_en_este_universo] = distribucion_fallas.get(fallas_en_este_universo, 0) + 1

    if resultado['exito']:
        exitos_totales += 1
        makespans_exitosos.append(resultado['makespan'])

        # Guardamos el timeline COMPLETO y las estadísticas del universo que mas horas tardo
        # Esto para ponernos efectivamente en el peor de los casos posibles
        if resultado['makespan'] > peor_makespan_registrado:
            peor_makespan_registrado = resultado['makespan']
            peor_timeline_completo = resultado['timeline_completo']
            peor_stats_tiempo_real = resultado['stats_tiempo_real']
            peor_stats_limpieza = resultado['stats_limpieza']
            peor_stats_retribucion = resultado['stats_retribucion']
            peor_stats_horas_base = resultado['stats_horas_base']
            peor_stats_horas_error = resultado['stats_horas_error']
    else:
        # MUY REBUSCADO: Si no hay exitos, guardamos los datos del colapso para el reporte
        # Aca obviamente se van a ir multiplicando las probabilidades
        if exitos_totales == 0:
            peor_timeline_completo = resultado['timeline_completo']
            peor_stats_tiempo_real = resultado['stats_tiempo_real']
            peor_stats_limpieza = resultado['stats_limpieza']
            peor_stats_retribucion = resultado['stats_retribucion']
            peor_stats_horas_base = resultado['stats_horas_base']
            peor_stats_horas_error = resultado['stats_horas_error']

# RESUMEN
fin_fase8 = time.time()
tiempo_fase8 = fin_fase8 - inicio_fase8

print()
print("RESUMEN (MONTE CARLO)")
print()
print(f"Estrategia evaluada: {estrategia_objetivo} (el peor caso determinista)")
print(f"Universos simulados: {CANTIDAD_SIMULACIONES}")
print()

prob_exito = (exitos_totales / CANTIDAD_SIMULACIONES) * 100

if exitos_totales > 0:
    promedio_mk = sum(makespans_exitosos) / len(makespans_exitosos)

    print(f"NIVEL DE CONFIABILIDAD : {prob_exito:.2f}% (Lograron terminar en ≤ 8 semanas)")
    print(f"PROBABILIDAD DE FRACASO: {100 - prob_exito:.2f}% (El proyecto se atraso)")
    print()
    print(f"Makespan promedio c/error: {promedio_mk/3600:.2f} hrs versus {makespan_base/3600:.2f} hrs teoricas")
    print(f"Peor makespan exitoso: {peor_makespan_registrado/3600:.2f} hrs.")
else:
    print(f"NIVEL DE CONFIABILIDAD : 0.00% (¡El proyecto colapso en todas las simulaciones!)")

print()
print(" ANALISIS DEL PEOR ESCENARIO (EL UNIVERSO MAS LENTO)")
bloque_anterior = None
for linea in peor_timeline_completo:
    partes = linea.split(" | ")
    if len(partes) >= 3 and " -> " in linea:
        bloque_actual = f"{partes[0]} | {partes[1]} | {partes[2]}"

        # Si el bloque cambio, metemos el salto de linea para que un mismo bloque horario quede aisaldo del resto, queda mas facil de entender
        if bloque_anterior is not None and bloque_actual != bloque_anterior:
            print("")

        bloque_anterior = bloque_actual

    print(f"{linea}")

print()
print("ORDENAMIENTOS DE TRABAJO INDIVIDUALES (EN EL PEOR ESCENARIO DONDE SI FUE FACTIBLE EL PROYECTO DENTRO DEL TIEMPO SEÑALADO)")
for estudiante in nombresEstudiantes:
    print()
    print(f"ESTUDIANTE: {estudiante.upper()}")

    semanas_dict = {}
    for linea in peor_timeline_completo:
        if " -> " not in linea:
            continue

        partes = linea.split(" | ")
        if len(partes) >= 4:
            sem_str = partes[0].strip()
            dia_str = partes[1].strip()
            bloque_str = partes[2].strip()
            est_str, accion_str = partes[3].split(" -> ", 1)
            est_str = est_str.strip()

            if est_str == estudiante:
                if sem_str not in semanas_dict:
                    semanas_dict[sem_str] = {}
                if dia_str not in semanas_dict[sem_str]:
                    semanas_dict[sem_str][dia_str] = []
                semanas_dict[sem_str][dia_str].append(f"[{bloque_str}] -> {accion_str}")

    if not semanas_dict: # ESTO ES UN CASO MUY IMPROBABLE. LO AÑADIREMOS PARA QUE NO SE CAIGA EL CODIGO
        print("UWU: Sin tareas asignadas en este escenario crítico")
    else:
        for sem in sorted(semanas_dict.keys()):
            print()
            print(f"{sem.upper()}")
            for dia, acciones in semanas_dict[sem].items():
                print(f"{dia}:")
                for accion in acciones:
                    print(f"{accion}")

print()
print("RESUMEN DE ESTUDIANTES Y RETRIBUCIÓN EXTRACURRICULAR (EN EL PEOR ESCENARIO)")
for estudiante in nombresEstudiantes:
    t_real_seg = peor_stats_tiempo_real[estudiante]
    t_limpieza_seg = peor_stats_limpieza[estudiante]
    horas_extra_totales = 0.0
    print()
    print(f"Estudiante: {estudiante.upper()}")
    print(f"Tiempo real produciendo: {t_real_seg} seg ({t_real_seg/3600:.2f} hrs)")
    print(f"Tiempo en orden/limpieza: {t_limpieza_seg} seg ({t_limpieza_seg/3600:.2f} hrs)")

    for (lote_id, paquete_id), seg_trabajados in peor_stats_retribucion[estudiante].items():
        for p_lote in paquetes_lotes:
            if p_lote['lote'] == lote_id and p_lote['paquete'] == paquete_id:
                if p_lote['tiempo_real_seg'] > 0:
                    proporcion_trabajada = seg_trabajados / p_lote['tiempo_real_seg']
                    horas_ganadas = proporcion_trabajada * p_lote['horas_extracurriculares']
                    horas_extra_totales += horas_ganadas
                    print(f"      - Lote {lote_id} | Pqt {paquete_id}: Aportó {seg_trabajados}s ({proporcion_trabajada*100:.1f}%) -> Ganó {horas_ganadas:.3f} hrs extra")

    total_base = peor_stats_horas_base[estudiante]
    total_error = peor_stats_horas_error[estudiante]
    total_absoluto = total_base + total_error
    print(f"Total a asignar: {total_absoluto:.3f} hrs ({total_base:.3f} hrs regulares + {total_error:.3f} hrs corrigiendo errores)")
    # Aca hay algo un poco raro y es que como el estudiante rehace las tareas, suman despues mas del 100%
    # Y suman mas de 1 hora extracurricular, pero con el desglose se entiende, es porque se esta volviendo a hacer el mismo trabajo


print()
print("DISTRIBUCIÓN ESTADÍSTICA DE FALLAS (HISTOGRAMA DE RIESGO)")
print()

if distribucion_fallas:
    max_fallas = max(distribucion_fallas.keys())
    total_fallas_acumuladas = sum(k * v for k, v in distribucion_fallas.items())
    promedio_fallas = total_fallas_acumuladas / CANTIDAD_SIMULACIONES if CANTIDAD_SIMULACIONES > 0 else 0

    print(f"Promedio global: {promedio_fallas:.1f} fallas por cada proyecto simulado.\n")

    for cantidad in range(max_fallas + 1):
        frecuencia = distribucion_fallas.get(cantidad, 0)
        if frecuencia > 0:
            porcentaje = (frecuencia / CANTIDAD_SIMULACIONES) * 100

            # Generamos una barra visual (1 bloque █ por cada 1.5% de frecuencia)
            bloques_visuales = "█" * int(porcentaje / 1.5)
            # Si el porcentaje es mayor a 0 pero muy bajito, ponemos una línea fina
            if bloques_visuales == "" and frecuencia > 0:
                bloques_visuales = "▏"

            print(f"{cantidad:2d} fallas | {str(frecuencia).rjust(4)} universos | {porcentaje:5.1f}% | {bloques_visuales}")
else:
    print("No se registraron fallas en ninguna simulación.")

# EJECUCION
horas, resto = divmod(tiempo_fase8, 3600)
minutos, segundos = divmod(resto, 60)
print()
print(f"Tiempo Monte Carlo: {tiempo_fase8:.2f} segundos ({int(horas):02d}:{int(minutos):02d}:{segundos:05.2f})")
print()
print('FASE 8 COMPLETADA')
print()
print('THE END')
"""

# CORRECCION 4 HECHA POR IA EN CONVERSACIÓN 2:
# Se comentan las triples comillas dobles para que el código sea ejecutable, ya que la función simulador() estaba comentada y no se podía ejecutar.
# Se ponen triples comillas dobles en el bloque anterior para comentar ese bloque y que en cambio
# esta nueva versión unificada si se pueda ejecutar correctamente.
# La conversación completa puede ser vista en:
# https://share.gemini.google/ZlhDvUf7O2IN
#"""
# Esta función unifica la logica de la Fase 7  que es determinista o ideal y la
# Fase 8 que es estocastica o con Errores) Si se le pasa un mapa de riesgos vacío,
# asume 0% de probabilidad de falla en todas las tareas que seria la fase 7
# y en caso contrario replica la logica de la fase 8
# No alcance a revisar linea por linea que sea exactamente lo mismo,
# pero en la version anterior la Fase 7 esta con comentarios
# ==============================================================================
def simulador(estrategia, semilla=None, mapa_de_riesgos=None):
    if mapa_de_riesgos is None:
        mapa_de_riesgos = {}

    if semilla is not None:
        random.seed(semilla)

    tareas = copy.deepcopy(pool_tareas)

    for t in tareas:
        if t['codigo'] in ['D1', 'D2']:
            t['tiempo_total_seg'] = tiempos_unitarios[t['codigo']]['Agenda']

        t['tiempo_restante'] = t['tiempo_total_seg']
        t['terminada'] = False
        t['pausada'] = False
        t['tiempo_libre_restante'] = 0
        t['es_retrabajo'] = False

    for p_lote in paquetes_lotes:
        tiempo_corregido = sum(t['tiempo_total_seg'] for t in tareas if t['lote'] == p_lote['lote'] and obtener_paquete(t['codigo']) == p_lote['paquete'])
        p_lote['tiempo_real_seg'] = tiempo_corregido

    estado_estudiantes = {nombre: {'tarea_principal': None, 'maquina': None, 'ultima_maquina': None} for nombre in nombresEstudiantes}
    propietarios_paquetes = {}

    tiempo_total_proyecto = 0
    tareas_pendientes = len(tareas)
    registro_timeline = []
    tiempo_trabajado_real = {e: 0 for e in nombresEstudiantes}
    tiempo_limpieza = {e: 0 for e in nombresEstudiantes}
    registro_retribucion = {e: {} for e in nombresEstudiantes}

    horas_ganadas_tracker = {e: 0.0 for e in nombresEstudiantes}
    horas_error_tracker = {e: 0.0 for e in nombresEstudiantes}

    for instante in linea_de_tiempo:
        if tareas_pendientes == 0:
            break

        sem, dia, bloque = instante
        estudiantes_del_bloque = sorted([e for e in nombresEstudiantes if disponibilidadIndividual8Semanas[e][instante] == 1])
        tiempo_consumido_bloque = {e: 0 for e in estudiantes_del_bloque}
        tiempo_maquinas = {f"{m} {i+1}": 0 for m, cant in recursos.items() for i in range(cant)}
        bloque_efectivamente_trabajado = False

        while True:
            activos = [e for e in estudiantes_del_bloque if tiempo_consumido_bloque[e] < 3600 and horas_ganadas_tracker[e] < 5.0]
            if not activos or tareas_pendientes == 0:
                break

            estudiante = min(activos, key=lambda x: tiempo_consumido_bloque[x])
            t_actual = tiempo_consumido_bloque[estudiante]
            tiempo_disponible_estudiante = 3600 - t_actual
            tarea_a_trabajar = None

            if estado_estudiantes[estudiante]['tarea_principal'] is not None:
                tarea_a_trabajar = estado_estudiantes[estudiante]['tarea_principal']
                if tarea_a_trabajar['pausada']:
                    if tarea_a_trabajar['codigo'] in ['D3', 'D4']:
                        ultimo_dia = estado_estudiantes[estudiante].get('dia_ultimo_bloque')
                        ultimo_fin = estado_estudiantes[estudiante].get('fin_ultimo_bloque')
                        bloque_inicio = bloque.split('-')[0]
                        es_continuo = (dia == ultimo_dia and bloque_inicio == ultimo_fin)

                        if es_continuo:
                            tarea_a_trabajar['pausada'] = False
                        else:
                            codigo_config = 'D1' if tarea_a_trabajar['codigo'] == 'D3' else 'D2'
                            tiempo_castigo = tiempos_unitarios[codigo_config]['Agenda']

                            if tiempo_disponible_estudiante >= tiempo_castigo:
                                tiempo_disponible_estudiante -= tiempo_castigo
                                tarea_a_trabajar['pausada'] = False
                                maq_str = estado_estudiantes[estudiante]['maquina']
                                registro_timeline.append(f"Sem {sem} | {dia} | {bloque} | {estudiante} -> ¡REPETIR! {tiempo_castigo} segundos reconfigurando {maq_str} para {tarea_a_trabajar['id_tarea']}")
                                bloque_efectivamente_trabajado = True
                                tiempo_consumido_bloque[estudiante] += tiempo_castigo
                                if maq_str in tiempo_maquinas:
                                    tiempo_maquinas[maq_str] = max(tiempo_maquinas[maq_str], tiempo_consumido_bloque[estudiante])
                            else:
                                tiempo_limpieza[estudiante] += tiempo_disponible_estudiante
                                tiempo_consumido_bloque[estudiante] = 3600
                                continue
                    else:
                        tarea_a_trabajar['pausada'] = False
            else:
                completadas = [t['id_tarea'] for t in tareas if t['terminada']]
                disponibles_bruto = [t for t in tareas if not t['terminada'] and all(p in completadas for p in t['predecesoras'])]
                disponibles = []

                horas_comprometidas = sum(
                    p['horas_extracurriculares'] for p in paquetes_lotes
                    if propietarios_paquetes.get((p['lote'], p['paquete'])) == estudiante
                )

                for t in disponibles_bruto:
                    paq_id = obtener_paquete(t['codigo'])
                    propietario_actual = propietarios_paquetes.get((t['lote'], paq_id))

                    puede_tomar_tarea = False

                    if propietario_actual == estudiante:
                        puede_tomar_tarea = True
                    elif propietario_actual is None:
                        horas_del_nuevo_paquete = next((p['horas_extracurriculares'] for p in paquetes_lotes if p['lote'] == t['lote'] and p['paquete'] == paq_id), 0)
                        if horas_comprometidas + horas_del_nuevo_paquete <= 5.001:
                            puede_tomar_tarea = True

                    if puede_tomar_tarea:
                        req = maquina_req.get(t['codigo'])
                        if req:
                            maq_libres_ahora = [m for m, t_maq in tiempo_maquinas.items() if m.startswith(req) and t_maq <= t_actual]
                            if maq_libres_ahora: disponibles.append(t)
                        else: disponibles.append(t)

                if not disponibles:
                    espera = min(60, 3600 - t_actual)
                    tiempo_consumido_bloque[estudiante] += espera
                    tiempo_limpieza[estudiante] += espera
                    continue

                c1_disp = [t for t in disponibles if t['codigo'] == 'C1']
                c2_disp = [t for t in disponibles if t['codigo'] == 'C2']
                imp_activa_disp = [t for t in disponibles if t['codigo'] in ['D3', 'D4']]
                conf_imp_disp = [t for t in disponibles if t['codigo'] in ['D1', 'D2']]
                manual_disp = [t for t in disponibles if t['codigo'] in ['B1','B2','B3','B4','E1','E2','F1','F2','F3']]
                f4_disp = [t for t in disponibles if t['codigo'] == 'F4']

                if c1_disp: tarea_a_trabajar = sorted(c1_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]
                elif c2_disp: tarea_a_trabajar = sorted(c2_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]
                elif imp_activa_disp: tarea_a_trabajar = sorted(imp_activa_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]
                elif conf_imp_disp and tiempo_disponible_estudiante >= 900: tarea_a_trabajar = sorted(conf_imp_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]
                elif manual_disp:
                    if estrategia == 'FIFO': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (x['lote'], -x['tiempo_total_seg']))[0]
                    elif estrategia == 'LIFO': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (-x['lote'], -x['tiempo_total_seg']))[0]
                    elif estrategia == 'Lote_Mas_Incompleto': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (-sum(t['tiempo_restante'] for t in tareas if t['lote'] == x['lote']), x['lote']))[0]
                    elif estrategia == 'Lote_Mas_Completo': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (sum(t['tiempo_restante'] for t in tareas if t['lote'] == x['lote']), x['lote']))[0]
                    elif estrategia == 'Tarea_Mas_Larga_Primero': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (-x['tiempo_total_seg'], x['lote']))[0]
                    elif estrategia == 'Tarea_Mas_Corta_Primero': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (x['tiempo_total_seg'], x['lote']))[0]
                    elif estrategia == 'Lote_Con_Mas_Tareas_Pendientes': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (-sum(1 for t in tareas if t['lote'] == x['lote'] and not t['terminada']), x['lote']))[0]
                    elif estrategia == 'Lote_Con_Menos_Tareas_Pendientes': tarea_a_trabajar = sorted(manual_disp, key=lambda x: (sum(1 for t in tareas if t['lote'] == x['lote'] and not t['terminada']), x['lote']))[0]
                    elif estrategia.startswith('RANDOM'): tarea_a_trabajar = random.choice(manual_disp)
                elif f4_disp: tarea_a_trabajar = sorted(f4_disp, key=lambda x: (-(x['cantidad_agendas']+x['cantidad_libretas']), x['lote']))[0]

                if not tarea_a_trabajar:
                    espera = min(60, 3600 - t_actual)
                    tiempo_consumido_bloque[estudiante] += espera
                    tiempo_limpieza[estudiante] += espera
                    continue

                if tarea_a_trabajar:
                    estado_estudiantes[estudiante]['tarea_principal'] = tarea_a_trabajar
                    tarea_a_trabajar['pausada'] = False
                    paq_asignado = obtener_paquete(tarea_a_trabajar['codigo'])
                    if paq_asignado: propietarios_paquetes[(tarea_a_trabajar['lote'], paq_asignado)] = estudiante
                    req = maquina_req.get(tarea_a_trabajar['codigo'])
                    if req:
                        maq_libres_ahora = sorted([m for m, t_maq in tiempo_maquinas.items() if m.startswith(req) and t_maq <= t_actual])
                        maq_previa = estado_estudiantes[estudiante].get('ultima_maquina')
                        maq_asignada = maq_previa if maq_previa in maq_libres_ahora else maq_libres_ahora[0]
                        estado_estudiantes[estudiante]['maquina'] = maq_asignada
                        estado_estudiantes[estudiante]['ultima_maquina'] = maq_asignada
                    else:
                        estado_estudiantes[estudiante]['maquina'] = "Mesa de Trabajo (Manual)"
                        estado_estudiantes[estudiante]['ultima_maquina'] = None

                    if tarea_a_trabajar['codigo'] in ['D3', 'D4']:
                        tarea_a_trabajar['tiempo_libre_restante'] = tarea_a_trabajar['tiempo_total_seg'] * 0.4

            if tarea_a_trabajar:
                tiempo_a_dedicar = min(tiempo_disponible_estudiante, tarea_a_trabajar['tiempo_restante'])

                if tiempo_a_dedicar > 0:
                    bloque_efectivamente_trabajado = True
                    tiempo_trabajado_real[estudiante] += tiempo_a_dedicar

                    paq = obtener_paquete(tarea_a_trabajar['codigo'])
                    if paq:
                        clave_ret = (tarea_a_trabajar['lote'], paq)
                        registro_retribucion[estudiante][clave_ret] = registro_retribucion[estudiante].get(clave_ret, 0) + tiempo_a_dedicar

                        for p_lote in paquetes_lotes:
                            if p_lote['lote'] == tarea_a_trabajar['lote'] and p_lote['paquete'] == paq:
                                if p_lote['tiempo_real_seg'] > 0:
                                    horas_sumadas = (tiempo_a_dedicar / p_lote['tiempo_real_seg']) * p_lote['horas_extracurriculares']
                                    if tarea_a_trabajar.get('es_retrabajo', False):
                                        horas_error_tracker[estudiante] += horas_sumadas
                                    else:
                                        horas_ganadas_tracker[estudiante] += horas_sumadas
                                break

                estado_accion = "FINALIZADA" if (tarea_a_trabajar['tiempo_restante'] - tiempo_a_dedicar) <= 0 else "EN PROGRESO"
                maq_str = estado_estudiantes[estudiante]['maquina']
                registro_timeline.append(f"Sem {sem} | {dia} | {bloque} | {estudiante} -> {tiempo_a_dedicar}s en {tarea_a_trabajar['id_tarea']} (en {maq_str}) Se encuentra {estado_accion}")

                tarea_a_trabajar['tiempo_restante'] -= tiempo_a_dedicar
                tiempo_consumido_bloque[estudiante] += tiempo_a_dedicar

                if maq_str in tiempo_maquinas:
                    tiempo_maquinas[maq_str] = max(tiempo_maquinas[maq_str], tiempo_consumido_bloque[estudiante])

                if tarea_a_trabajar['tiempo_libre_restante'] > 0:
                    tarea_a_trabajar['tiempo_libre_restante'] -= tiempo_a_dedicar

                if tarea_a_trabajar['tiempo_restante'] <= 0:
                    # LÓGICA ESTOCÁSTICA DE FALLAS
                    prob_fallo = mapa_de_riesgos.get(tarea_a_trabajar['codigo'], 0.0)

                    if random.random() < prob_fallo:
                        tarea_a_trabajar['tiempo_restante'] = tarea_a_trabajar['tiempo_total_seg']
                        if tarea_a_trabajar['codigo'] in ['D3', 'D4']:
                            tarea_a_trabajar['tiempo_libre_restante'] = tarea_a_trabajar['tiempo_total_seg'] * 0.4
                        tarea_a_trabajar['terminada'] = False
                        tarea_a_trabajar['pausada'] = True
                        tarea_a_trabajar['es_retrabajo'] = True
                        registro_timeline.append(f"Sem {sem} | {dia} | {bloque} | {estudiante} -> ¡ARRUINADA! La accion {tarea_a_trabajar['id_tarea']} no fue hecha correctamente. PRIORIDAD: rehacer la tarea")
                    else:
                        tarea_a_trabajar['terminada'] = True
                        tareas_pendientes -= 1
                        estado_estudiantes[estudiante]['tarea_principal'] = None
                        estado_estudiantes[estudiante]['maquina'] = None
                else:
                    if tiempo_consumido_bloque[estudiante] >= 3600:
                        tarea_a_trabajar['pausada'] = True
                        estado_estudiantes[estudiante]['dia_ultimo_bloque'] = dia
                        estado_estudiantes[estudiante]['fin_ultimo_bloque'] = bloque.split('-')[1]

        if bloque_efectivamente_trabajado:
            tiempo_total_proyecto += 3600

    exito = (tareas_pendientes == 0)
    return {
        'estrategia': estrategia,
        'exito': exito,
        'makespan': tiempo_total_proyecto if exito else float('inf'),
        'pendientes': tareas_pendientes,
        'timeline': copy.deepcopy(registro_timeline),
        'stats_tiempo_real': copy.deepcopy(tiempo_trabajado_real),
        'stats_limpieza': copy.deepcopy(tiempo_limpieza),
        'stats_retribucion': copy.deepcopy(registro_retribucion),
        'stats_horas_base': copy.deepcopy(horas_ganadas_tracker),
        'stats_horas_error': copy.deepcopy(horas_error_tracker)
    }


# 8 HEURÍSTICAS VS SIMULACIONES DE MONTE CARLO (FASE 7)

print()
print('FASE 7: 8 HEURÍSTICAS VS SIMULACIONES DE MONTE CARLO')

inicio_ejecucion = time.time()

linea_de_tiempo = []
for sem in range(1, NUM_SEMANAS + 1):
    for dia in diasSemana:
        for bloque in bloquesHorarios:
            linea_de_tiempo.append((sem, dia, bloque))

estrategias_deterministas = [
    'FIFO', 'LIFO', 'Lote_Mas_Incompleto', 'Lote_Mas_Completo',
    'Tarea_Mas_Larga_Primero', 'Tarea_Mas_Corta_Primero',
    'Lote_Con_Mas_Tareas_Pendientes', 'Lote_Con_Menos_Tareas_Pendientes'
]
estrategias_aleatorias = [f'RANDOM_{i}' for i in range(1993, CANTIDAD_RANDOMS + 1993)]
estrategias = estrategias_deterministas + estrategias_aleatorias

maquina_req = {
    'B1': 'Corte_Carton', 'B2': 'Corte_Carton', 'B3': 'Corte_Carton', 'B4': 'Corte_Carton',
    'C1': 'Guillotina', 'C2': 'Guillotina',
    'D1': 'Impresora', 'D2': 'Impresora', 'D3': 'Impresora', 'D4': 'Impresora',
    'E1': 'Cinch', 'E2': 'Cinch',
    'F1': 'Tijera', 'F2': 'Alicate_Corte', 'F3': 'Alicate_Presion', 'F4': 'Ojetilladora'
}

def obtener_paquete(codigo_tarea):
    for paquete, datos in paquetes_retribucion.items():
        if codigo_tarea in datos['tareas']:
            return paquete
    return None

resultados_torneo = []
total_escenarios = len(estrategias)
paso_progreso = max(1, total_escenarios // 10)

print(f"Ejecutando {total_escenarios} escenarios (heuristicas vs aleatorios)")

for i, estrategia in enumerate(estrategias):
    if (i + 1) % paso_progreso == 0:
        porcentaje_avance = int((i + 1) / total_escenarios * 100)
        print(f"Analizando: {porcentaje_avance:3d}% completado ({i+1}/{total_escenarios} escenarios)")

    semilla_actual = int(estrategia.split('_')[1]) if estrategia.startswith('RANDOM') else None

    # LLAMADA A LA FUNCIÓN CENTRAL PARA LA FASE 7 (SIN RIESGOS)
    resultado = simulador(estrategia, semilla=semilla_actual, mapa_de_riesgos={})
    resultados_torneo.append(resultado)

fin_ejecucion = time.time()

# RESULTADOS FASE 7

print()
print("RESULTADOS")
print()

resultados_det = [r for r in resultados_torneo if r['exito'] and not r['estrategia'].startswith('RANDOM')]
resultados_rand = [r for r in resultados_torneo if r['exito'] and r['estrategia'].startswith('RANDOM')]

print("DESEMPEÑO DE REGLAS HEURISTICAS")
for r in resultados_det:
    print(f"  > Estrategia {r['estrategia'].ljust(7)}: {r['makespan']} seg ({r['makespan']/3600:.2f} hrs de ocupación)")

if resultados_rand:
    resultados_rand.sort(key=lambda x: x['makespan'])
    mejor_rand = resultados_rand[0]
    peor_rand = resultados_rand[-1]
    total_corridas = len(resultados_rand)
    promedio_rand = sum(r['makespan'] for r in resultados_rand) / total_corridas

    print()
    print(f"RESUMEN DE LAS {total_corridas} SIMULACIONES ALEATORIAS ")
    print(f"Mejor ({mejor_rand['estrategia']}): {mejor_rand['makespan']} seg ({mejor_rand['makespan']/3600:.2f} hrs)")
    print(f"Peor({peor_rand['estrategia']}): {peor_rand['makespan']} seg ({peor_rand['makespan']/3600:.2f} hrs)")
    print(f"Promedio: {promedio_rand:.0f} seg ({promedio_rand/3600:.2f} hrs)")

print()
print(f"DETALLE DE ESTRATEGIAS (Se omiten los {total_corridas - 1 if resultados_rand else 0} escenarios aleatorios descartados)")
print()

estrategias_a_mostrar = resultados_det.copy()
if resultados_rand:
    estrategias_a_mostrar.append(mejor_rand)
    if peor_rand['estrategia'] != mejor_rand['estrategia']:
        estrategias_a_mostrar.append(peor_rand)

for r in estrategias_a_mostrar:
    print()
    print()
    print(f"ESTRATEGIA: {r['estrategia']} | Makespan: {r['makespan']} seg ({r['makespan']/3600:.2f} hrs)")
    print()
    print("LINEA DE TIEMPO")
    bloque_anterior = None
    for linea in r['timeline']:
        partes = linea.split(" | ")
        if len(partes) >= 3:
            bloque_actual = f"{partes[0]} | {partes[1]} | {partes[2]}"
            if bloque_anterior is not None and bloque_actual != bloque_anterior:
                print("")
            bloque_anterior = bloque_actual
        print(linea)

    print()
    print("RESUMEN DE ESTUDIANTES Y RETRIBUCION DE LAS HORAS EXTRACURRICULARES")
    for estudiante in nombresEstudiantes:
        t_real_seg = r['stats_tiempo_real'][estudiante]
        t_limpieza_seg = r['stats_limpieza'][estudiante]
        horas_extra_totales = 0.0
        print()
        print(f"Estudiante: {estudiante.upper()}")
        print(f"Tiempo real trabajando: {t_real_seg} seg ({t_real_seg/3600:.2f} hrs)")
        print(f"Tiempo en orden/limpieza/ocio: {t_limpieza_seg} seg ({t_limpieza_seg/3600:.2f} hrs)")

        for (lote_id, paquete_id), seg_trabajados in r['stats_retribucion'][estudiante].items():
            for p_lote in paquetes_lotes:
                if p_lote['lote'] == lote_id and p_lote['paquete'] == paquete_id:
                    if p_lote['tiempo_real_seg'] > 0:
                        proporcion_trabajada = seg_trabajados / p_lote['tiempo_real_seg']
                        horas_ganadas = proporcion_trabajada * p_lote['horas_extracurriculares']
                        horas_extra_totales += horas_ganadas
                        print(f"Lote {lote_id} | Pqt {paquete_id}: Aporto {seg_trabajados}s ({proporcion_trabajada*100:.1f}%) y le corresponden {horas_ganadas:.3f} hrs. extracurriculares")

        print(f"Total a asignar: {horas_extra_totales:.3f} hrs extracurriculares")

    if len(nombresEstudiantes) > 1:
        print("")
        print("ORDENAMIENTOS DE TRABAJO INDIVIDUALES")
        for estudiante in nombresEstudiantes:
            print()
            print(f"ESTUDIANTE: {estudiante.upper()}")

            semanas_dict = {}
            for linea in r['timeline']:
                if " -> " not in linea:
                    continue

                partes = linea.split(" | ")
                if len(partes) >= 4:
                    sem_str = partes[0].strip()
                    dia_str = partes[1].strip()
                    bloque_str = partes[2].strip()
                    est_str, accion_str = partes[3].split(" -> ", 1)
                    est_str = est_str.strip()

                    if est_str == estudiante:
                        if sem_str not in semanas_dict:
                            semanas_dict[sem_str] = {}
                        if dia_str not in semanas_dict[sem_str]:
                            semanas_dict[sem_str][dia_str] = []
                        semanas_dict[sem_str][dia_str].append(f"[{bloque_str}] -> {accion_str}")

            if not semanas_dict:
                print("Sin tareas asignadas en esta estrategia")
            else:
                for sem in sorted(semanas_dict.keys()):
                    print()
                    print(f"{sem.upper()}")
                    for dia, acciones in semanas_dict[sem].items():
                        print(f"{dia}:")
                        bloque_anterior = None
                        for accion in acciones:
                            bloque_actual = accion.split("]")[0]
                            if bloque_anterior is not None and bloque_actual != bloque_anterior:
                                print("")
                            bloque_anterior = bloque_actual
                            print(f"{accion}")

tiempo_total = fin_ejecucion - inicio_ejecucion
horas, resto = divmod(tiempo_total, 3600)
minutos, segundos = divmod(resto, 60)
print()
print(f"Tiempo total de procesamiento Fase 7: {tiempo_total:.4f} segundos ({int(horas):02d}:{int(minutos):02d}:{segundos:05.2f})")
print()
print('FASE 7 COMPLETADA')

# SIMULACIONES DE ERRORES (REGLA: EL QUE ROMPE, LO ARREGLA) (FASE 8)

print()
print('FASE 8: SIMULACIONES DE ERRORES (REGLA: EL QUE ROMPE, LO ARREGLA)')

inicio_fase8 = time.time()

try:
    peor_escenario = max(resultados_torneo, key=lambda x: x['makespan'])
    estrategia_objetivo = peor_escenario['estrategia']
    makespan_base = peor_escenario['makespan']
except (NameError, ValueError):
    print("[ERROR] No se identificó un escenario válido en la Fase 7")
    estrategia_objetivo = 'FIFO'
    makespan_base = 0

print()
print(f"Estrategia seleccionada para someter a estres: {estrategia_objetivo}")
print(f"Makespan original (sin errores): {makespan_base/3600:.2f} hrs")

probabilidad_ruina = {
    'B1': 0.15, 'B2': 0.25, 'B3': 0.20, 'B4': 0.15,
    'C1': 0.45, 'C2': 0.40,
    'D1': 0.50, 'D2': 0.55, 'D3': 0.55, 'D4': 0.50,
    'E1': 0.35, 'E2': 0.30,
    'F1': 0.25, 'F2': 0.15, 'F3': 0.15, 'F4': 0.20
}

exitos_totales = 0
makespans_exitosos = []
peor_timeline_completo = []
peor_makespan_registrado = 0
peor_stats_tiempo_real = {}
peor_stats_limpieza = {}
peor_stats_retribucion = {}
peor_stats_horas_base = {}
peor_stats_horas_error = {}

distribucion_fallas = {}
paso_progreso = max(1, CANTIDAD_SIMULACIONES // 10)

print(f"Iniciando {CANTIDAD_SIMULACIONES} simulaciones de universos paralelos con fallas")
print()

for i in range(CANTIDAD_SIMULACIONES):
    if (i + 1) % paso_progreso == 0:
        porcentaje_avance = int((i + 1) / CANTIDAD_SIMULACIONES * 100)
        print(f"Analizando multiverso: {porcentaje_avance:3d}% completado ({i+1}/{CANTIDAD_SIMULACIONES} escenarios)")

    # LLAMADA A LA FUNCION CENTRAL PARA LA FASE 8 (CON RIESGOS)
    resultado = simulador(estrategia_objetivo, semilla=1000+i, mapa_de_riesgos=probabilidad_ruina)

    fallas_en_este_universo = sum(1 for linea in resultado['timeline'] if '¡ARRUINADA!' in linea)
    distribucion_fallas[fallas_en_este_universo] = distribucion_fallas.get(fallas_en_este_universo, 0) + 1

    if resultado['exito']:
        exitos_totales += 1
        makespans_exitosos.append(resultado['makespan'])

        if resultado['makespan'] > peor_makespan_registrado:
            peor_makespan_registrado = resultado['makespan']
            peor_timeline_completo = resultado['timeline']
            peor_stats_tiempo_real = resultado['stats_tiempo_real']
            peor_stats_limpieza = resultado['stats_limpieza']
            peor_stats_retribucion = resultado['stats_retribucion']
            peor_stats_horas_base = resultado['stats_horas_base']
            peor_stats_horas_error = resultado['stats_horas_error']
    else:
        if exitos_totales == 0:
            peor_timeline_completo = resultado['timeline']
            peor_stats_tiempo_real = resultado['stats_tiempo_real']
            peor_stats_limpieza = resultado['stats_limpieza']
            peor_stats_retribucion = resultado['stats_retribucion']
            peor_stats_horas_base = resultado['stats_horas_base']
            peor_stats_horas_error = resultado['stats_horas_error']

fin_fase8 = time.time()
tiempo_fase8 = fin_fase8 - inicio_fase8

# RESULTADOS FASE 8

print()
print("RESUMEN (MONTE CARLO)")
print()
print(f"Estrategia evaluada: {estrategia_objetivo} (el peor caso determinista)")
print(f"Universos simulados: {CANTIDAD_SIMULACIONES}")
print()

prob_exito = (exitos_totales / CANTIDAD_SIMULACIONES) * 100 if CANTIDAD_SIMULACIONES > 0 else 0

if exitos_totales > 0:
    promedio_mk = sum(makespans_exitosos) / len(makespans_exitosos)
    print(f"NIVEL DE CONFIABILIDAD : {prob_exito:.2f}% (Lograron terminar en ≤ 8 semanas)")
    print(f"PROBABILIDAD DE FRACASO: {100 - prob_exito:.2f}% (El proyecto se atraso)")
    print()
    print(f"Makespan promedio c/error: {promedio_mk/3600:.2f} hrs versus {makespan_base/3600:.2f} hrs teoricas")
    print(f"Peor makespan exitoso: {peor_makespan_registrado/3600:.2f} hrs.")
else:
    print(f"NIVEL DE CONFIABILIDAD    : 0.00% (¡El proyecto colapso en todas las simulaciones!)")

print()
print(" ANALISIS DEL PEOR ESCENARIO (EL UNIVERSO MAS LENTO)")
bloque_anterior = None
for linea in peor_timeline_completo:
    partes = linea.split(" | ")
    if len(partes) >= 3 and " -> " in linea:
        bloque_actual = f"{partes[0]} | {partes[1]} | {partes[2]}"
        if bloque_anterior is not None and bloque_actual != bloque_anterior:
            print("")
        bloque_anterior = bloque_actual
    print(f"{linea}")


print()
print("RESUMEN DE ESTUDIANTES Y RETRIBUCIÓN EXTRACURRICULAR (EN EL PEOR ESCENARIO)")
for estudiante in nombresEstudiantes:
    t_real_seg = peor_stats_tiempo_real.get(estudiante, 0)
    t_limpieza_seg = peor_stats_limpieza.get(estudiante, 0)
    horas_extra_totales = 0.0
    print()
    print(f"Estudiante: {estudiante.upper()}")
    print(f"Tiempo real produciendo: {t_real_seg} seg ({t_real_seg/3600:.2f} hrs)")
    print(f"Tiempo en orden/limpieza: {t_limpieza_seg} seg ({t_limpieza_seg/3600:.2f} hrs)")

    for (lote_id, paquete_id), seg_trabajados in peor_stats_retribucion.get(estudiante, {}).items():
        for p_lote in paquetes_lotes:
            if p_lote['lote'] == lote_id and p_lote['paquete'] == paquete_id:
                if p_lote['tiempo_real_seg'] > 0:
                    proporcion_trabajada = seg_trabajados / p_lote['tiempo_real_seg']
                    horas_ganadas = proporcion_trabajada * p_lote['horas_extracurriculares']
                    horas_extra_totales += horas_ganadas
                    print(f"      - Lote {lote_id} | Pqt {paquete_id}: Aportó {seg_trabajados}s ({proporcion_trabajada*100:.1f}%) -> Ganó {horas_ganadas:.3f} hrs extra")

    total_base = peor_stats_horas_base.get(estudiante, 0.0)
    total_error = peor_stats_horas_error.get(estudiante, 0.0)
    total_absoluto = total_base + total_error
    print(f"Total a asignar: {total_absoluto:.3f} hrs ({total_base:.3f} hrs regulares + {total_error:.3f} hrs corrigiendo errores)")

 

print()
print("ORDENAMIENTOS DE TRABAJO INDIVIDUALES (EN EL PEOR ESCENARIO DONDE SI FUE FACTIBLE EL PROYECTO DENTRO DEL TIEMPO SEÑALADO)")
for estudiante in nombresEstudiantes:
    print()
    print(f"ESTUDIANTE: {estudiante.upper()}")

    semanas_dict = {}
    for linea in peor_timeline_completo:
        if " -> " not in linea:
            continue

        partes = linea.split(" | ")
        if len(partes) >= 4:
            sem_str = partes[0].strip()
            dia_str = partes[1].strip()
            bloque_str = partes[2].strip()
            est_str, accion_str = partes[3].split(" -> ", 1)
            est_str = est_str.strip()

            if est_str == estudiante:
                if sem_str not in semanas_dict:
                    semanas_dict[sem_str] = {}
                if dia_str not in semanas_dict[sem_str]:
                    semanas_dict[sem_str][dia_str] = []
                semanas_dict[sem_str][dia_str].append(f"[{bloque_str}] -> {accion_str}")

    if not semanas_dict:
        print("UWU: Sin tareas asignadas en este escenario crítico")
    else:
        for sem in sorted(semanas_dict.keys()):
            print()
            print(f"{sem.upper()}")
            for dia, acciones in semanas_dict[sem].items():
                print(f"{dia}:")
                for accion in acciones:
                    print(f"{accion}")
                    

print()
print("DISTRIBUCIÓN ESTADÍSTICA DE FALLAS (HISTOGRAMA DE RIESGO)")
print()

# CORRECCION HECHA POR IA EN CONVERSACIÓN 1:
# -----------------------------------------------
grafico_base64 = ""
if distribucion_fallas:
    max_fallas = max(distribucion_fallas.keys())
    total_fallas_acumuladas = sum(k * v for k, v in distribucion_fallas.items())
    promedio_fallas = total_fallas_acumuladas / CANTIDAD_SIMULACIONES if CANTIDAD_SIMULACIONES > 0 else 0

    print(f"Promedio global: {promedio_fallas:.1f} fallas por cada proyecto simulado.\n")

    for cantidad in range(max_fallas + 1):
        frecuencia = distribucion_fallas.get(cantidad, 0)
        if frecuencia > 0:
            porcentaje = (frecuencia / CANTIDAD_SIMULACIONES) * 100
            bloques_visuales = "█" * int(porcentaje / 1.5)
            if bloques_visuales == "" and frecuencia > 0:
                bloques_visuales = "▏"
            print(f"{cantidad:2d} fallas | {str(frecuencia).rjust(4)} universos | {porcentaje:5.1f}% | {bloques_visuales}")

    # ... (TU CÓDIGO ACTUAL SE MANTIENE INTACTO HASTA AQUÍ) ...

    # --- NUEVO: Generación de la imagen para el HTML ---
    # Preparamos los ejes X e Y asegurando que cubran desde 0 hasta max_fallas
    x_vals = list(range(max_fallas + 1))
    y_vals = [distribucion_fallas.get(i, 0) for i in x_vals]
    
    # Antes era (8, 2.5). Puedes subirlo para darle más resolución nativa:
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.bar(x_vals, y_vals, color="#DB7093") # Usamos tu --rosa-principal
    ax.set_title(f"Distribución Estadística de Riesgo (Promedio global: {promedio_fallas:.1f})")
    ax.set_xlabel("Cantidad de Fallas")
    ax.set_ylabel("Universos")
    
    # Ajustamos márgenes para que no ocupe espacio innecesario
    plt.tight_layout() 
    
    # Guardamos en memoria como Base64 (fondo transparente para que haga match con tu CSS)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    buf.seek(0)
    grafico_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig) # Liberamos memoria
    # -----------------------------------------------
else:
    print("No se registraron fallas en ninguna simulación.")

horas, resto = divmod(tiempo_fase8, 3600)
minutos, segundos = divmod(resto, 60)
print()
print(f"Tiempo Monte Carlo: {tiempo_fase8:.2f} segundos ({int(horas):02d}:{int(minutos):02d}:{segundos:05.2f})")
print()
print('FASE 8 COMPLETADA')
print()
print('THE END')
#"""

# DESDE AQUÍ HACIA ABAJO ESTE BLOQUE DE CÓDIGO FUE HECHO CON AYUDA DE IA
# CORRESPONDE A LA CONVERSACIÓN 1 Y PUEDE VERSE COMPLETA EN:
# adjuntar el link
# EN LA CONVERSACION 2, NO SE INLCUYO ESTE FRAGEMENTO DE CÓDIGO
# SINO SOLO SE LE INDICARON LOS NOMBRES DE LAS VARIABLES Y FUNCIONES, Y SE LE PIDIÓ QUE GENERARA EL CÓDIGO NUEVO

import json
from datetime import datetime
from zoneinfo import ZoneInfo


def generar_reporte_html():
    mapa_paquetes = {(p['lote'], p['paquete']): p for p in paquetes_lotes}

    # --- Pre-procesamiento Fase 7 ---
    datos_fase7 = []
    for esc in estrategias_a_mostrar:
        tabla = []
        for est in nombresEstudiantes:
            t_real = esc['stats_tiempo_real'].get(est, 0)
            t_limp = esc['stats_limpieza'].get(est, 0)
            str_treal = f"{t_real} seg ({t_real/3600.0:.2f} hrs)"
            str_tlimp = f"{t_limp} seg ({t_limp/3600.0:.2f} hrs)"

            retrib = esc['stats_retribucion'].get(est, {})
            suma_horas = 0.0
            html_ret = '<ul style="margin:0; padding-left: 20px;">'
            for (lote_id, pqt_id), seg_aport in retrib.items():
                pqt = mapa_paquetes.get((lote_id, pqt_id), {'tiempo_real_seg': 1, 'horas_extracurriculares': 0})
                t_real_pqt = pqt['tiempo_real_seg']
                h_ext = pqt['horas_extracurriculares']
                prop = seg_aport / t_real_pqt if t_real_pqt > 0 else 0
                h_ganadas = prop * h_ext
                suma_horas += h_ganadas
                html_ret += f"<li>Lote {lote_id} | Pqt {pqt_id}: Aportó {seg_aport}s ({prop*100:.1f}%) -> Ganó {h_ganadas:.3f} hrs extra.</li>"
            html_ret += f"</ul><br><b>Total a asignar: {suma_horas:.3f} hrs</b>"

            tabla.append({
                "estudiante": est, "t_real": str_treal, "t_limp": str_tlimp, "retribucion": html_ret
            })
        
        datos_fase7.append({
            "estrategia": esc['estrategia'],
            "makespan": esc['makespan'],
            "timeline": esc['timeline'],
            "tabla": tabla
        })

    # --- Pre-procesamiento Fase 8 (Base) ---
    tabla_base_estres = []
    for est in nombresEstudiantes:
        t_real = peor_escenario['stats_tiempo_real'].get(est, 0)
        t_limp = peor_escenario['stats_limpieza'].get(est, 0)
        str_treal = f"{t_real} seg ({t_real/3600.0:.2f} hrs)"
        str_tlimp = f"{t_limp} seg ({t_limp/3600.0:.2f} hrs)"

        retrib = peor_escenario['stats_retribucion'].get(est, {})
        suma_horas = 0.0
        html_ret = '<ul style="margin:0; padding-left: 20px;">'
        for (lote_id, pqt_id), seg_aport in retrib.items():
            pqt = mapa_paquetes.get((lote_id, pqt_id), {'tiempo_real_seg': 1, 'horas_extracurriculares': 0})
            t_real_pqt = pqt['tiempo_real_seg']
            h_ext = pqt['horas_extracurriculares']
            prop = seg_aport / t_real_pqt if t_real_pqt > 0 else 0
            h_ganadas = prop * h_ext
            suma_horas += h_ganadas
            html_ret += f"<li>Lote {lote_id} | Pqt {pqt_id}: Aportó {seg_aport}s ({prop*100:.1f}%) -> Ganó {h_ganadas:.3f} hrs extra.</li>"
        html_ret += f"</ul><br><b>Total a asignar: {suma_horas:.3f} hrs</b>"

        tabla_base_estres.append({
            "estudiante": est, "t_real": str_treal, "t_limp": str_tlimp, "retribucion": html_ret
        })

    # --- Pre-procesamiento Fase 8 (Caótico/Stress) ---
    tabla_fase8 = []
    for est in nombresEstudiantes:
        t_real = peor_stats_tiempo_real.get(est, 0)
        t_limp = peor_stats_limpieza.get(est, 0)
        str_treal = f"{t_real} seg ({t_real/3600.0:.2f} hrs)"
        str_tlimp = f"{t_limp} seg ({t_limp/3600.0:.2f} hrs)"

        retrib = peor_stats_retribucion.get(est, {})
        html_ret = '<ul style="margin:0; padding-left: 20px;">'
        for (lote_id, pqt_id), seg_aport in retrib.items():
            pqt = mapa_paquetes.get((lote_id, pqt_id), {'tiempo_real_seg': 1, 'horas_extracurriculares': 0})
            t_real_pqt = pqt['tiempo_real_seg']
            h_ext = pqt['horas_extracurriculares']
            prop = seg_aport / t_real_pqt if t_real_pqt > 0 else 0
            h_ganadas = prop * h_ext
            html_ret += f"<li>Lote {lote_id} | Pqt {pqt_id}: Aportó {seg_aport}s ({prop*100:.1f}%) -> Ganó {h_ganadas:.3f} hrs extra.</li>"
        
        h_b = peor_stats_horas_base.get(est, 0.0)
        h_e = peor_stats_horas_error.get(est, 0.0)
        t_h = h_b + h_e
        html_ret += f"</ul><br>Horas Base: {h_b:.3f} hrs<br>Horas Error: {h_e:.3f} hrs<br><b>Total a asignar: {t_h:.3f} hrs</b>"

        tabla_fase8.append({
            "estudiante": est, "t_real": str_treal, "t_limp": str_tlimp, "retribucion": html_ret
        })

    datos_fase8 = {
        "estrategia_base": peor_escenario['estrategia'],
        "makespan_teorico": peor_escenario['makespan'],
        "timeline_base": peor_escenario['timeline'],
        "tabla_base": tabla_base_estres,
        "makespan_estresado": peor_makespan_registrado,
        "timeline_caotico": peor_timeline_completo,
        "tabla_caotica": tabla_fase8
    }

    # --- Renderizado HTML ---
    nombres_str = ", ".join(nombresEstudiantes)
    tot_esc = len(estrategias_a_mostrar)
    tot_det = len(estrategias_deterministas)
    tot_al = len(estrategias_aleatorias)
    
    # Reemplaza tu definición de header_str por esta:
    header_str = f"Agendas: {numAgendas} | Libretas: {numLibretas} | Estudiantes Requeridos: {estudiantesRequeridos} ({nombres_str})<br><br>Escenarios Fase 7: {tot_esc} Escenarios ({tot_det} Empíricos + {tot_al} Simulados) | Universos Fase 8: {CANTIDAD_SIMULACIONES}"
    
    #if grafico_base64:
        #header_str += f'<br><br><img src="data:image/png;base64,{grafico_base64}" class="histograma-header">'

    payload_fase7 = json.dumps(datos_fase7)
    payload_fase8 = json.dumps(datos_fase8)
    lista_estudiantes = json.dumps(nombresEstudiantes)

    opciones_html = ""
    for idx, esc in enumerate(datos_fase7):
        opciones_html += f'<option value="{idx}">{esc["estrategia"]} (Makespan: {esc["makespan"]} seg)</option>'
    
    opciones_html += f'<option value="STRESS" style="font-weight:bold; color:var(--rosa-oscuro);">🔥 Análisis de Estrés: {peor_escenario["estrategia"]} (Makespan estresado: {peor_makespan_registrado} seg)</option>'

    html_grafico = ""
    if grafico_base64:
        html_grafico = f'''
        <div style="flex-grow: 1; display: flex; justify-content: flex-end;">
            <img src="data:image/png;base64,{grafico_base64}" class="histograma-filtros">
        </div>
        '''

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Reporte de Simulación</title>
    <style>
        :root {{
            --rosa-principal: #DB7093;
            --rosa-claro: #FFB6C1;
            --rosa-oscuro: #B03060;
            --rosa-fondo: #FFF0F5;
        }}
        body {{
            background-color: var(--rosa-fondo);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0; padding: 20px;
            color: #333;
        }}
        .header {{
            background: white; border: 2px solid var(--rosa-principal);
            padding: 15px; border-radius: 8px; margin-bottom: 20px;
            text-align: center; font-size: 16px; font-weight: bold;
        }}
        .filtros {{
            display: flex; gap: 20px; margin-bottom: 20px;
            background: white; padding: 15px; border-radius: 8px;
            border: 1px solid var(--rosa-principal);
            align-items: center; /* NUEVO: alinea verticalmente las listas con la imagen */
        }}
        
        .histograma-filtros {{
            max-width: 850px; /* ¡Sube este valor! Prueba con 500px o 600px */
            height: auto; 
            display: block;
        }}
        select {{
            /* padding: Arriba | Derecha (los 100px extra) | Abajo | Izquierda */
            padding: 8px 100px 8px 10px; 
            border: 1px solid var(--rosa-principal);
            border-radius: 4px; outline: none; font-size: 14px;
        }}
        #select-escenario, #select-estudiante {{ 
            width: auto; 
            min-width: 300px; 
            max-width: 100%;
        }}
        
        .vista {{ display: none; }}
        
        .split-view {{
            display: flex; gap: 20px; width: 100%;
        }}
        .panel {{
            flex: 1; background: white; padding: 15px; border-radius: 8px;
            border: 1px solid var(--rosa-principal); overflow: hidden;
        }}
        
        h2, h3 {{ color: var(--rosa-oscuro); margin-top: 0; }}
        
        .timeline {{
            background-color: #1e1e1e; color: var(--rosa-claro);
            padding: 10px; height: 300px; overflow-y: auto;
            font-family: monospace; border-radius: 4px;
            margin-bottom: 15px; white-space: pre-wrap; font-size: 13px;
        }}
        
        table {{
            width: 100%; border-collapse: collapse; margin-top: 10px;
            table-layout: fixed;
        }}
        th, td {{
            border: 1px solid #ccc; padding: 8px; text-align: left; vertical-align: top;
            word-wrap: break-word;
        }}
        th {{ background-color: var(--rosa-principal); color: white; font-weight: bold;}}
        
        /* AGREGA ESTAS 4 LÍNEAS AQUÍ: */
        th:nth-child(1) {{ width: 20%; }}
        th:nth-child(2) {{ width: 15%; }} /* Era 20%, le quitamos 5% */
        th:nth-child(3) {{ width: 15%; }} /* Era 20%, le quitamos 5% */
        th:nth-child(4) {{ width: 50%; }} /* Era 40%, le sumamos 10% */

        .histograma-header {{
            width: 100%; 
            max-width: 700px; /* Ancho máximo para que no se estire demasiado en pantallas grandes */
            height: auto; 
            margin-top: 15px;
            display: block;
            margin-left: auto;
            margin-right: auto;
        }}
    </style>
</head>
<body>
    <div class="header">
        {header_str}
    </div>

    <div class="filtros">
        <div>
            <label><strong>Escenario Principal:</strong></label><br>
            <select id="select-escenario" onchange="actualizarVistas()">
                {opciones_html}
            </select>
        </div>
        <div>
            <label><strong>Filtro Estudiante:</strong></label><br>
            <select id="select-estudiante" onchange="aplicarFiltrosTimeline()">
                <option value="TODOS">Todos</option>
            </select>
        </div>

        {html_grafico}
    </div>

    <div id="div_fase7" class="vista panel">
        <h2 id="f7-title"></h2>
        <div class="timeline" id="f7-timeline"></div>
        <table>
            <thead>
                <tr>
                    <th>Estudiante</th>
                    <th>Tiempo Real</th>
                    <th>Limpieza</th>
                    <th>Desglose Retribución</th>
                </tr>
            </thead>
            <tbody id="f7-tbody"></tbody>
        </table>
    </div>

    <div id="div_fase8" class="vista split-view">
        <div class="panel">
            <h2>Plan Ideal (Base)</h2>
            <h3 id="f8-base-title"></h3>
            <div class="timeline" id="f8-timeline-base"></div>
            <table>
                <thead>
                    <tr>
                        <th>Estudiante</th>
                        <th>Tiempo Real</th>
                        <th>Limpieza</th>
                        <th>Desglose Retribución</th>
                    </tr>
                </thead>
                <tbody id="f8-tbody-base"></tbody>
            </table>
        </div>
        <div class="panel">
            <h2>Ejecución Caótica (STRESS)</h2>
            <h3 id="f8-stress-title"></h3>
            <div class="timeline" id="f8-timeline-caotico"></div>
            <table>
                <thead>
                    <tr>
                        <th>Estudiante</th>
                        <th>Tiempo Real</th>
                        <th>Limpieza</th>
                        <th>Desglose Retribución</th>
                    </tr>
                </thead>
                <tbody id="f8-tbody-caotico"></tbody>
            </table>
        </div>
    </div>

    <script>
        const datosFase7 = {payload_fase7};
        const datosFase8 = {payload_fase8};
        const estudiantes = {lista_estudiantes};

        function init() {{
            const selEst = document.getElementById('select-estudiante');
            estudiantes.forEach(est => {{
                let opt = document.createElement('option');
                opt.value = est;
                opt.text = est;
                selEst.appendChild(opt);
            }});
            actualizarVistas();
        }}

        function generarFilasTabla(datosTabla) {{
            return datosTabla.map(r => `
                <tr>
                    <td>${{r.estudiante}}</td>
                    <td>${{r.t_real}}</td>
                    <td>${{r.t_limp}}</td>
                    <td>${{r.retribucion}}</td>
                </tr>
            `).join('');
        }}

        function filtrarLineas(lineas, estudiante) {{
            if (estudiante === 'TODOS') return lineas.join('\\n');
            return lineas.filter(l => l.includes(estudiante)).join('\\n');
        }}

        function actualizarVistas() {{
            const val = document.getElementById('select-escenario').value;
            const divF7 = document.getElementById('div_fase7');
            const divF8 = document.getElementById('div_fase8');

            if (val === 'STRESS') {{
                divF7.style.display = 'none';
                divF8.style.display = 'flex';
                
                document.getElementById('f8-base-title').innerText = "Makespan Teórico: " + datosFase8.makespan_teorico + " seg";
                document.getElementById('f8-tbody-base').innerHTML = generarFilasTabla(datosFase8.tabla_base);
                
                document.getElementById('f8-stress-title').innerText = "Makespan Estresado: " + datosFase8.makespan_estresado + " seg";
                document.getElementById('f8-tbody-caotico').innerHTML = generarFilasTabla(datosFase8.tabla_caotica);
            }} else {{
                divF8.style.display = 'none';
                divF7.style.display = 'block';
                
                const esc = datosFase7[val];
                document.getElementById('f7-title').innerText = esc.estrategia + " (Makespan: " + esc.makespan + " seg)";
                document.getElementById('f7-tbody').innerHTML = generarFilasTabla(esc.tabla);
            }}
            aplicarFiltrosTimeline();
        }}

        function aplicarFiltrosTimeline() {{
            const val = document.getElementById('select-escenario').value;
            const estudiante = document.getElementById('select-estudiante').value;

            if (val === 'STRESS') {{
                document.getElementById('f8-timeline-base').innerText = filtrarLineas(datosFase8.timeline_base, estudiante);
                document.getElementById('f8-timeline-caotico').innerText = filtrarLineas(datosFase8.timeline_caotico, estudiante);
            }} else {{
                const esc = datosFase7[val];
                document.getElementById('f7-timeline').innerText = filtrarLineas(esc.timeline, estudiante);
            }}
        }}

        window.onload = init;
    </script>
</body>
</html>"""

    meses = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    # ... (la lista de meses se mantiene intacta)
    ahora = datetime.now(ZoneInfo("America/Santiago"))
    nombre_archivo = f"Reporte Makespan Dia {ahora.day:02d} de {meses[ahora.month]} de {ahora.strftime('%y')} a las {ahora.strftime('%H:%M:%S')}.html"
    # ... (el bloque with open se mantiene intacto)

    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write(html_content)

generar_reporte_html()

# Registramos el reloj justo al terminar
tiempo_fin = time.perf_counter()

# Calculamos la diferencia
tiempo_ejecucion = tiempo_fin - tiempo_inicio

# Convertimos los segundos a horas, minutos y segundos (formato hh:mm:ss)
horas, residuo = divmod(tiempo_ejecucion, 3600)
minutos, segundos = divmod(residuo, 60)

# Mostramos el resultado final formateado con ceros a la izquierda
print(f"El proceso tardó {int(horas):02d}:{int(minutos):02d}:{int(segundos):02d} en completarse.")