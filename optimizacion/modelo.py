import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyomo.environ import *
from pyomo.opt import SolverFactory
import sys

sys.path.append('optimizacion/')
from cargadorDeParametros import CargadorDeParametros
from visualizador import Visualizador

p = CargadorDeParametros()

# Definicición de conjuntos
M = ConcreteModel()

# Nodos
M.N = RangeSet(1, len(p.clientes) + len(p.almacenes) + len(p.estaciones))

# Clientes
M.C = RangeSet(1, len(p.clientes))

# Almacenes
M.A = RangeSet(len(p.clientes) + 1, len(p.clientes) + len(p.almacenes))

# Estaciones
M.E = RangeSet(len(p.clientes) + len(p.almacenes) + 1, len(p.clientes) + len(p.almacenes) + len(p.estaciones))

# Vehículos
M.V = RangeSet(1, len(p.vehiculos))

# Tipos de vehículos
# 1:Gas Car | 2:Drone | 3:Solar EV
M.T = RangeSet(1, 3)

# Definición de parámetros
# Parámetros de los clientes
DEMANDAS = []
LONGITUDES_CLIENTES = []
LATITUDES_CLIENTES = []

# Parámetros de los almacenes
CAPACIDADES_PRODUCTOS_ALMACENES = []
LONGITUDES_ALMACENES = []
LATITUDES_ALMACENES = []

# Parámetros de las estaciones de recarga
LONGITUDES_ESTACIONES = []
LATITUDES_ESTACIONES = []

# Parámetros de los vehículos
TIPOS_VEHICULO = []
CAPACIDADES_PRODUCTOS_VEHICULO = []
RANGOS = []
TIEMPOS_RECARGA_COMPLETA = []
VELOCIDADES_PROMEDIO = []
EFICIENCIAS_ENERGETICAS = []
TIEMPOS_CARGA_MINUTO = []

# Parámetros de los costos vehiculares
TARIFAS_FLETE = []
TARIFAS_TIEMPO = []
COSTOS_MANTENIMIENTO_DIARIO = []
COSTOS_RECARGA_UNIDAD_ENERGIA = []
COSTOS_CARGA_MINUTO = []

# Variables de decisión
M.X = Var(M.A, M.C, M.V, within=Binary)
M.Y = Var(M.C, M.C, M.V, within=Binary)
M.Z = Var(M.C, M.A, M.V, within=Binary)

M.W = Var(M.C, M.E, M.V, within=Binary)
M.U = Var(M.E, M.C, M.V, within=Binary)
M.M = Var(M.A, M.E, M.V, within=Binary)
M.L = Var(M.E, M.A, M.V, within=Binary)
M.H = Var(M.E, M.E, M.V, within=Binary)

M.K = Var(M.V,M.T, within=Binary)
M.S = Var(M.V, M.N, within=Binary)

v = Visualizador(p.clientes, p.almacenes, p.estaciones)

