import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyomo.environ import *
from pyomo.opt import SolverFactory
from haversine import haversine, Unit
import os
import requests


def calcularDistanciaHarvesiana(matriz, conjuntoDatos1, conjuntoDatos2):
    for i in range(len(conjuntoDatos1)):
        for j in range(len(conjuntoDatos2)):
            punto1 = (conjuntoDatos1['Latitude'][i], conjuntoDatos1['Longitude'][i])
            punto2 = (conjuntoDatos2['Latitude'][j], conjuntoDatos2['Longitude'][j])
            matriz[i][j] = haversine(punto1, punto2, unit=Unit.KILOMETERS)
            

def calcularDistanciaRuta(matriz, conjuntoDatos1, conjuntoDatos2):
    for i in range(len(conjuntoDatos1)):
        for j in range(len(conjuntoDatos2)):
            punto1 = (conjuntoDatos1['Latitude'][i], conjuntoDatos1['Longitude'][i])
            punto2 = (conjuntoDatos2['Latitude'][j], conjuntoDatos2['Longitude'][j])
            endpoint = f'http://router.project-osrm.org/route/v1/driving/{punto1[1]},{punto1[0]};{punto2[1]},{punto2[0]}?overview=false'
            respuesta = requests.get(endpoint)
            distancia = respuesta.json()['routes'][0]['distance']
            matriz[i][j] = distancia 
    
    
def calcularMatrizDistancia(matriz, conjuntoDatos1, conjuntoDatos2):
    calcularDistanciaRuta(matriz[0], conjuntoDatos1, conjuntoDatos2)
    calcularDistanciaHarvesiana(matriz[1], conjuntoDatos1, conjuntoDatos2)

def obtenerMatricesDeDistancia(clientes, depositos, estaciones, ruta):
    if os.path.exists(ruta + 'D_ai.npy'):
        D_ai = np.load(ruta + 'D_ai.npy')
        D_ij = np.load(ruta + 'D_ij.npy')
        D_ei = np.load(ruta + 'D_ei.npy')
        D_ae = np.load(ruta + 'D_ae.npy')
        D_ef = np.load(ruta + 'D_ef.npy')
        return D_ai, D_ij, D_ei, D_ae, D_ef
                       
    D_ai = np.zeros((2, len(depositos), len(clientes)))
    D_ij = np.zeros((2, len(clientes), len(clientes)))
    D_ei = np.zeros((2, len(estaciones), len(clientes)))
    D_ae = np.zeros((2, len(depositos), len(estaciones)))
    D_ef = np.zeros((2, len(estaciones), len(estaciones)))
    
    calcularMatrizDistancia(D_ai, depositos, clientes)
    np.save(ruta + 'D_ai.npy', D_ai)
    calcularMatrizDistancia(D_ij, clientes, clientes)
    np.save(ruta + 'D_ij.npy', D_ij)
    calcularMatrizDistancia(D_ei, estaciones, clientes)
    np.save(ruta + 'D_ei.npy', D_ei)
    calcularMatrizDistancia(D_ae, depositos, estaciones)
    np.save(ruta + 'D_ae.npy', D_ae)
    calcularMatrizDistancia(D_ef, estaciones, estaciones)
    np.save(ruta + 'D_ef.npy', D_ef)
    
    return D_ai, D_ij, D_ei, D_ae, D_ef
    
def cargarCaso(rutaBase):
    clientes = pd.read_csv(f"{rutaBase}Clients.csv")
    depositos = pd.read_csv(f"{rutaBase}Depots.csv")
    if rutaBase == "Proyecto Seneca Libre/case_1_base/":
        vehiculos = pd.read_csv(f"{rutaBase}multi_vehicles.csv")
    else:
        vehiculos = pd.read_csv(f"{rutaBase}Vehicles.csv")
    estaciones = pd.read_csv(f"{rutaBase}RechargeNodes.csv")
    D_ai, D_ij, D_ei, D_ae, D_ef = obtenerMatricesDeDistancia(clientes, depositos, estaciones, rutaBase)
    return clientes, depositos, vehiculos, estaciones, D_ai, D_ij, D_ei, D_ae, D_ef
    
def cargarCasoDePrueba():
    print("1. Caso base")
    print("2. Caso 5 clientes por vehiculo")
    print("3. Caso grandes distancias poca demanda")
    print("4. Depositos con capacidad")
    caso = int(input("Digite el número del caso de prueba: "))
    
    rutas = [
        "Proyecto Seneca Libre/case_1_base/",
        "Proyecto Seneca Libre/case_2_5_clients_per_vehicle/",
        "Proyecto Seneca Libre/case_3_big_distances_small_demands/",
        "Proyecto Seneca Libre/case_4_capacitated_depots/"
    ]

    return cargarCaso(rutas[caso - 1])


clientes, depositos, vehiculos, estaciones, D_ai, D_ij, D_ei, D_ae, D_ef = cargarCasoDePrueba()


# Cuadro 1: Parámetros de Costos y Eficiencia para Vehículo
# Gas Car | Drone | Solar EV
tarifaFlete = [5000, 500, 4000]
tarifaTiempo = [500, 500, 500]
costoMantenimiento = [30000, 3000, 21000]
costoRecarga = [16000, 220.73, 0]
tiempoRecarga = [0.1,2,0]
velocidadPromedio = [0,40,0]
eficienteCombustible = [10,0,0]
eficienciaEnergetica = [0,0.15,0.15]


# Definicición de conjuntos

# Nodos
N = RangeSet(1, len(clientes) + len(depositos) + len(estaciones))

# Clientes
C = RangeSet(1, len(clientes))

# Almacenes
A = RangeSet(len(clientes) + 1, len(clientes) + len(depositos))

# Estaciones
E = RangeSet(len(clientes) + len(depositos) + 1, len(clientes) + len(depositos) + len(estaciones))

# Vehículos
V = RangeSet(1, len(vehiculos))

# Tipos de vehículos
# 1:Gas Car | 2:Drone | 3:Solar EV
T = RangeSet(1, 3)

# Definición de parámetros


# Variables de decisión
X = Var(A, C, V, within=Binary)
Y = Var(C, C, V, within=Binary)
Z = Var(C, A, V, within=Binary)

W = Var(C, E, V, within=Binary)
U = Var(E, C, V, within=Binary)
M = Var(A, E, V, within=Binary)
L = Var(E, A, V, within=Binary)
H = Var(E, E, V, within=Binary)

K = Var(V,T, within=Binary)
S = Var(V, N, within=Binary)




