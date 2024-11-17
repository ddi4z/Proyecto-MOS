import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyomo.environ import *
from pyomo.opt import SolverFactory

def cargarCaso1():
    clientes = pd.read_csv("Proyecto Seneca Libre/case_1_base/Clients.csv")
    clientes = clientes.drop('DepotID', axis=1)
    depositos = pd.read_csv("Proyecto Seneca Libre/case_1_base/Depots.csv")
    vehiculos = pd.read_csv("Proyecto Seneca Libre/case_1_base/multi_vehicles.csv")
    estaciones = pd.read_csv("Proyecto Seneca Libre/case_1_base/RechargeNodes.csv")
    return clientes, depositos, vehiculos, estaciones
    

def cargarCaso2():
    clientes = pd.read_csv("Proyecto Seneca Libre/case_2_5_clients_per_vehicle/Clients.csv")
    depositos = pd.read_csv("Proyecto Seneca Libre/case_2_5_clients_per_vehicle/Depots.csv")
    vehiculos = pd.read_csv("Proyecto Seneca Libre/case_2_5_clients_per_vehicle/Vehicles.csv")
    estaciones = pd.read_csv("Proyecto Seneca Libre/case_2_5_clients_per_vehicle/RechargeNodes.csv")
    return clientes, depositos, vehiculos, estaciones

def cargarCaso3():
    clientes = pd.read_csv("Proyecto Seneca Libre/case_3_big_distances_small_demands/Clients.csv")
    depositos = pd.read_csv("Proyecto Seneca Libre/case_3_big_distances_small_demands/Depots.csv")
    vehiculos = pd.read_csv("Proyecto Seneca Libre/case_3_big_distances_small_demands/Vehicles.csv")
    estaciones = pd.read_csv("Proyecto Seneca Libre/case_3_big_distances_small_demands/RechargeNodes.csv")
    return clientes, depositos, vehiculos, estaciones

def cargarCaso4():
    clientes = pd.read_csv("Proyecto Seneca Libre/case_4_capacitated_depots/Clients.csv")
    depositos = pd.read_csv("Proyecto Seneca Libre/case_4_capacitated_depots/Depots.csv")
    vehiculos = pd.read_csv("Proyecto Seneca Libre/case_4_capacitated_depots/Vehicles.csv")
    estaciones = pd.read_csv("Proyecto Seneca Libre/case_4_capacitated_depots/RechargeNodes.csv")
    return clientes, depositos, vehiculos, estaciones

def cargarCasoDePrueba():
    print("1. Caso base")
    print("2. Caso 5 clientes por vehiculo")
    print("3. Caso grandes distancias poca demanda")
    print("4. Depositos con capacidad")
    caso = input("Digite el número del caso de prueba: ")
    if caso == "1":
        return cargarCaso1()
    elif caso == "2":
        return cargarCaso2()
    elif caso == "3":
        return cargarCaso3()
    elif caso == "4":
        return cargarCaso4()


clientes, depositos, vehiculos, estaciones = cargarCasoDePrueba()

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

C_cargaDiario = C_cargaMinuto* T_kgxvDiario
C_distanciaDiario = C_km,t * D_viajeDiario
C_tiempoDiario = C_viajeHora,t * T_viajeDiario


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
