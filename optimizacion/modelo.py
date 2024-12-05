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



# Variables de decisión

# Almacén - Cliente
M.X = Var(M.A, M.C, M.V, within=Binary)
M.Y = Var(M.C, M.A, M.V, within=Binary)

# Cliente - Cliente
M.Z = Var(M.C, M.C, M.V, within=Binary)

# Cliente - Estación
M.W = Var(M.C, M.E, M.V, within=Binary)
M.U = Var(M.E, M.C, M.V, within=Binary)

# Estación - Estación
M.M = Var(M.E, M.E, M.V, within=Binary)

# Estación - Almacén
M.L = Var(M.E, M.A, M.V, within=Binary)
M.H = Var(M.A, M.E, M.V, within=Binary)

# Subtoures
M.S = Var(M.V, M.N, within=Binary)

# Variables dependientes

def t_kg_v_diario():
    x = sum(sum(sum(M.X[a,i,v] * p.DEMANDAS[i] * p.TIEMPO_CARGA_MINUTO for i in M.C) for a in M.A) for v in M.V)
    z = sum(sum(sum(M.Z[i,j,v] * p.DEMANDAS[j] * p.TIEMPO_CARGA_MINUTO for i in M.C) for j in M.C) for v in M.V)
    u = sum(sum(sum(M.U[e,i,v] * p.DEMANDAS[i] * p.TIEMPO_CARGA_MINUTO for i in M.C) for e in M.E) for v in M.V)
    return x + z + u

def d_viaje_diario_t():
    xy = sum(sum(sum(sum(p.TIPOS_VEHICULO[v,t] * (M.X[a,i,v] * p.D_ai + M.Y[i,a,v] * p.D_ia) for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    zz = sum(sum(sum(sum(p.TIPOS_VEHICULO[v,t] * (M.Z[i,j,v] * p.D_ij + M.Z[j,i,v] * p.D_ij) for t in M.T) for j in M.C) for i in M.C) for v in M.V)
    wu = sum(sum(sum(sum(p.TIPOS_VEHICULO[v,t] * (M.W[i,e,v] * p.D_ie + M.U[e,i,v] * p.D_ei) for t in M.T) for e in M.E) for i in M.C) for v in M.V)
    mm = sum(sum(sum(sum(p.TIPOS_VEHICULO[v,t] * (M.M[e,f,v] * p.D_ef + M.M[f,e,v] * p.D_fe) for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum(p.TIPOS_VEHICULO[v,t] * (M.L[e,a,v] * p.D_ea + M.H[a,e,v] * p.D_ae) for t in M.T) for e in M.E) for a in M.A) for v in M.V)
    return xy + zz + wu + mm + lh

def q_energia_diaria_t():
    x = sum(sum(sum(sum(M.X[a,i,v]*p.TIPOS_VEHICULO[v,t]* (p.RANGOS[v] / p.EFICIENCIAS_ENERGETICAS[t]) for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    u = sum(sum(sum(sum(M.U[e,i,v]*p.TIPOS_VEHICULO[v,t]* (p.RANGOS[v] / p.EFICIENCIAS_ENERGETICAS[t]) for t in M.T) for e in M.E) for i in M.C) for v in M.V)
    m = sum(sum(sum(sum(M.M[e,f,v]*p.TIPOS_VEHICULO[v,t]* (p.RANGOS[v] / p.EFICIENCIAS_ENERGETICAS[t]) for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum(M.L[e,a,v]*p.TIPOS_VEHICULO[v,t]* (p.RANGOS[v] / p.EFICIENCIAS_ENERGETICAS[t]) for t in M.T) for e in M.E) for a in M.A) for v in M.V)
    return x + u + m + lh

def t_recarga_diario_t():
    x = sum(sum(sum(sum(M.X[a,i,v] * p.TIPOS_VEHICULO[v,t] * p.TIEMPOS_RECARGA_COMPLETA[t] for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    u = sum(sum(sum(sum(M.U[e,i,v] * p.TIPOS_VEHICULO[v,t] * p.TIEMPOS_RECARGA_COMPLETA[t] for t in M.T) for i in M.C) for e in M.E) for v in M.V)
    m = sum(sum(sum(sum(M.M[e,f,v] * p.TIPOS_VEHICULO[v,t] * p.TIEMPOS_RECARGA_COMPLETA[t] for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum(M.L[e,a,v] * p.TIPOS_VEHICULO[v,t] * p.TIEMPOS_RECARGA_COMPLETA[t] for t in M.T) for a in M.A) for e in M.E) for v in M.V)
    return x + u + m + lh

# Función objetivo

def c_carga_diario():
    x = 
    z = 
    u = 
    return

def c_distancia_diario():
    return

def c_tiempo_diario():
    return

def c_energia_unidad_t():
    return

def c_recarga_diario_t():
    return

def c_mantenimiento_diario():
    return

M.FO = Objective(expr = c_carga_diario() + c_distancia_diario() + c_tiempo_diario() + c_recarga_diario_t() + c_mantenimiento_diario(), sense=minimize)
v = Visualizador(p.clientes, p.almacenes, p.estaciones)

