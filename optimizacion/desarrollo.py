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

def calcularDistanciaYTiempoRuta(matrizDistancia, matrizTiempo, conjuntoDatos1, conjuntoDatos2):
    coordenadasFilas = conjuntoDatos1[['Longitude', 'Latitude']].to_numpy()
    coordenadasColumnas = conjuntoDatos2[['Longitude', 'Latitude']].to_numpy()
    coordenasFilasString = ';'.join([f'{coordenada[0]},{coordenada[1]}' for coordenada in coordenadasFilas])
    coordenasColumnasString = ';'.join([f'{coordenada[0]},{coordenada[1]}' for coordenada in coordenadasColumnas])
    url = f'http://router.project-osrm.org/table/v1/driving/{coordenasFilasString};{coordenasColumnasString}'
    parametros = {
        'annotations': "distance,duration",
        'sources': ';'.join([str(i) for i in range(len(coordenadasFilas))]),
        'destinations': ';'.join([str(i) for i in range(len(coordenadasColumnas))])
    }

    respuesta = requests.get(url, params=parametros)
    datos = respuesta.json()
    for i in range(len(coordenadasFilas)):
        for j in range(len(coordenadasColumnas)):
            matrizDistancia[i][j] = datos['distances'][i][j]
            matrizTiempo[i][j] = datos['durations'][i][j]


def calcularMatrizDistanciaYTiempo(matrizDistancia, matrizTiempo, conjuntoDatos1, conjuntoDatos2):
    calcularDistanciaYTiempoRuta(matrizDistancia[0], matrizTiempo[0], conjuntoDatos1, conjuntoDatos2)
    calcularDistanciaHarvesiana(matrizDistancia[1], conjuntoDatos1, conjuntoDatos2)
    matrizTiempo[1] = matrizDistancia[1] / 40

def obtenerMatricesDeTiempoYDistancia(clientes, almacenes, estaciones):
    D_ai = np.zeros((2, len(almacenes), len(clientes)))
    D_ia = np.zeros((2, len(clientes), len(almacenes)))
    D_ij = np.zeros((2, len(clientes), len(clientes)))
    D_ei = np.zeros((2, len(estaciones), len(clientes)))
    D_ie = np.zeros((2, len(clientes), len(estaciones)))
    D_ae = np.zeros((2, len(almacenes), len(estaciones)))
    D_ea = np.zeros((2, len(estaciones), len(almacenes)))
    D_ef = np.zeros((2, len(estaciones), len(estaciones)))

    T_ai = np.zeros((2, len(almacenes), len(clientes)))
    T_ia = np.zeros((2, len(clientes), len(almacenes)))
    T_ij = np.zeros((2, len(clientes), len(clientes)))
    T_ei = np.zeros((2, len(estaciones), len(clientes)))
    T_ie = np.zeros((2, len(clientes), len(estaciones)))
    T_ae = np.zeros((2, len(almacenes), len(estaciones)))
    T_ea = np.zeros((2, len(estaciones), len(almacenes)))
    T_ef = np.zeros((2, len(estaciones), len(estaciones)))

    calcularMatrizDistanciaYTiempo(D_ai, T_ai,  almacenes, clientes)
    calcularMatrizDistanciaYTiempo(D_ia, T_ia,  clientes, almacenes)
    calcularMatrizDistanciaYTiempo(D_ij, T_ij,  clientes, clientes)
    calcularMatrizDistanciaYTiempo(D_ei, T_ei, estaciones, clientes)
    calcularMatrizDistanciaYTiempo(D_ie, T_ie,  clientes, estaciones)
    calcularMatrizDistanciaYTiempo(D_ae, T_ae, almacenes, estaciones)
    calcularMatrizDistanciaYTiempo(D_ea, T_ea, estaciones, almacenes)
    calcularMatrizDistanciaYTiempo(D_ef, T_ef, estaciones, estaciones)
    return D_ai, D_ia, D_ij, D_ei, D_ie, D_ae, D_ea, D_ef, T_ai, T_ia, T_ij, T_ei, T_ie, T_ae, T_ea, T_ef

def cargarCaso(rutaBase):
    clientes = pd.read_csv(f"{rutaBase}Clients.csv")
    almacenes = pd.read_csv(f"{rutaBase}Depots.csv")
    if rutaBase.count("case_1_base") > 0:
        vehiculos = pd.read_csv(f"{rutaBase}multi_vehicles.csv")
    else:
        vehiculos = pd.read_csv(f"{rutaBase}Vehicles.csv")
    estaciones = pd.read_csv(f"{rutaBase}RechargeNodes.csv")
    return clientes, almacenes, vehiculos, estaciones

def cargarCasoDePrueba():
    print("1. Caso base")
    print("2. Caso 5 clientes por vehiculo")
    print("3. Caso grandes distancias poca demanda")
    print("4. almacenes con capacidad")
    caso = int(input("Digite el número del caso de prueba: "))

    rutaPorDefecto = "optimizacion/Proyecto Seneca Libre/"
    rutas = [
        "case_1_base/",
        "case_2_5_clients_per_vehicle/",
        "case_3_big_distances_small_demands/",
        "case_4_capacitated_depots/"
    ]
    return cargarCaso(rutaPorDefecto + rutas[caso - 1])


clientes, almacenes, vehiculos, estaciones = cargarCasoDePrueba()
D_ai, D_ia, D_ij, D_ei, D_ie, D_ae, D_ea, D_ef, T_ai, T_ia, T_ij, T_ei, T_ie, T_ae, T_ea, T_ef = obtenerMatricesDeTiempoYDistancia(clientes, almacenes, estaciones)

# Cuadro 1: Parámetros de Costos y Eficiencia para Vehículo
# Gas Car | Drone | Solar EV
tarifaFlete = [5000, 500, 4000]
tarifaTiempo = [500, 500, 500]
costoMantenimiento = [30000, 3000, 21000]
costoRecarga = [16000, 220.73, 0]
tiempoRecarga = [0.1,2,0]
eficienteCombustible = [10,0,0]
eficienciaEnergetica = [0,0.15,0.15]





