import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyomo.environ import *
from pyomo.opt import SolverFactory
from pyomo.contrib.appsi.solvers import Highs
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
M.A = RangeSet(1, len(p.almacenes))

# Estaciones
M.E = RangeSet(1, len(p.estaciones))

# Vehículos
M.V = RangeSet(1, len(p.vehiculos))

# Tipos de vehículos
M.T = RangeSet(1, 3)

def indiceEstacion(e):
    return e + len(p.clientes) + len(p.almacenes)

def indiceAlmacen(a):
    return a + len(p.clientes)

def indice(c):
    return c - 1



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
    x = sum(sum(sum(M.X[a,i,v] * p.DEMANDAS[i - 1] * p.TIEMPO_CARGA_MINUTO for i in M.C) for a in M.A) for v in M.V)
    z = sum(sum(sum(M.Z[i,j,v] * p.DEMANDAS[j - 1] * p.TIEMPO_CARGA_MINUTO for i in M.C) for j in M.C) for v in M.V)
    u = sum(sum(sum(M.U[e,i,v] * p.DEMANDAS[i - 1] * p.TIEMPO_CARGA_MINUTO for i in M.C) for e in M.E) for v in M.V)
    return x + z + u

def d_viaje_diario_t():
    xy = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.X[a,i,v] * p.D_ai[t - 1,a - 1,i - 1] + M.Y[i,a,v] * p.D_ia[t - 1,i - 1,a - 1]) for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    zz = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.Z[i,j,v] * p.D_ij[t - 1,i - 1,j - 1] + M.Z[j,i,v] * p.D_ij[t - 1,j - 1,i - 1]) for t in M.T) for j in M.C) for i in M.C) for v in M.V)
    wu = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.W[i,e,v] * p.D_ie[t - 1,i - 1,e - 1] + M.U[e,i,v] * p.D_ei[t - 1,e - 1,i - 1]) for t in M.T) for e in M.E) for i in M.C) for v in M.V)
    mm = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.M[e,f,v] * p.D_ef[t - 1,e - 1,f - 1] + M.M[f,e,v] * p.D_fe[t - 1,f - 1,e - 1]) for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.L[e,a,v] * p.D_ea[t - 1,e - 1,a - 1] + M.H[a,e,v] * p.D_ae[t - 1,a - 1,e - 1]) for t in M.T) for e in M.E) for a in M.A) for v in M.V)
    return xy + zz + wu + mm + lh

def q_energia_diaria_t():
    x = sum(sum(sum(sum(M.X[a,i,v]*p.TIPOS_VEHICULO[v-1, t-1]* (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    u = sum(sum(sum(sum(M.U[e,i,v]*p.TIPOS_VEHICULO[v-1, t-1]* (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for e in M.E) for i in M.C) for v in M.V)
    m = sum(sum(sum(sum(M.M[e,f,v]*p.TIPOS_VEHICULO[v-1, t-1]* (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum(M.L[e,a,v]*p.TIPOS_VEHICULO[v-1, t-1]* (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for e in M.E) for a in M.A) for v in M.V)
    return x + u + m + lh

def t_recarga_diario_t():
    x = sum(sum(sum(sum(M.X[a,i,v] * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t] for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    u = sum(sum(sum(sum(M.U[e,i,v] * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t] for t in M.T) for i in M.C) for e in M.E) for v in M.V)
    m = sum(sum(sum(sum(M.M[e,f,v] * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t] for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum(M.L[e,a,v] * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t] for t in M.T) for a in M.A) for e in M.E) for v in M.V)
    return x + u + m + lh

# Función objetivo

def c_carga_diario():
    x = sum(sum(sum(M.X[a,i,v] * p.DEMANDAS[i - 1] * p.TIEMPO_CARGA_MINUTO * p.COSTO_CARGA_MINUTO for i in M.C) for a in M.A) for v in M.V)
    z = sum(sum(sum(M.Z[i,j,v] * p.DEMANDAS[j - 1] * p.TIEMPO_CARGA_MINUTO * p.COSTO_CARGA_MINUTO for j in M.C) for i in M.C) for v in M.V)
    u = sum(sum(sum(M.U[e,i,v] * p.DEMANDAS[i - 1] * p.TIEMPO_CARGA_MINUTO * p.COSTO_CARGA_MINUTO for i in M.C) for e in M.E) for v in M.V)
    return x + z + u

def c_distancia_diario():
    xy = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_FLETE[t - 1] * (M.X[a,i,v] * p.D_ai[t - 1,a - 1,i - 1] + M.Y[i,a,v] * p.D_ia[t - 1,i - 1,a - 1]) for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    zz = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_FLETE[t - 1] * (M.Z[i,j,v] * p.D_ij[t - 1,i - 1,j - 1] + M.Z[j,i,v] * p.D_ij[t - 1,j - 1,i - 1]) for t in M.T) for j in M.C) for i in M.C) for v in M.V)
    wu = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_FLETE[t - 1] * (M.W[i,e,v] * p.D_ie[t - 1,i - 1,e - 1] + M.U[e,i,v] * p.D_ei[t - 1,e - 1,i - 1]) for t in M.T) for e in M.E) for i in M.C) for v in M.V)
    mm = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_FLETE[t - 1] * (M.M[e,f,v] * p.D_ef[t - 1,e - 1,f - 1] + M.M[f,e,v] * p.D_fe[t - 1,f - 1,e - 1]) for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_FLETE[t - 1] * (M.L[e,a,v] * p.D_ea[t - 1,e - 1,a - 1] + M.H[a,e,v] * p.D_ae[t - 1,a - 1,e - 1]) for t in M.T) for e in M.E) for a in M.A) for v in M.V)
    return xy + zz + wu + mm + lh

def c_tiempo_diario():
    xy = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_TIEMPO[t - 1] * (M.X[a,i,v] * p.T_ai[t - 1,a - 1,i - 1] + M.Y[i,a,v] * p.T_ia[t - 1,i - 1,a - 1]) for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    zz = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_TIEMPO[t - 1] * (M.Z[i,j,v] * p.T_ij[t - 1,i - 1,j - 1] + M.Z[j,i,v] * p.T_ij[t - 1,j - 1,i - 1]) for t in M.T) for j in M.C) for i in M.C) for v in M.V)
    wu = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_TIEMPO[t - 1] * (M.W[i,e,v] * p.T_ie[t - 1,i - 1,e - 1] + M.U[e,i,v] * p.T_ei[t - 1,e - 1,i - 1]) for t in M.T) for e in M.E) for i in M.C) for v in M.V)
    mm = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_TIEMPO[t - 1] * (M.M[e,f,v] * p.T_ef[t - 1,e - 1,f - 1] + M.M[f,e,v] * p.T_fe[t - 1,f - 1,e - 1]) for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_TIEMPO[t - 1] * (M.L[e,a,v] * p.T_ea[t - 1,e - 1,a - 1] + M.H[a,e,v] * p.T_ae[t - 1,a - 1,e - 1]) for t in M.T) for e in M.E) for a in M.A) for v in M.V)
    return xy + zz + wu + mm + lh

def c_energia_diario():
    x = sum(sum(sum(sum(M.X[a,i,v] * p.TIPOS_VEHICULO[v -1,t - 1] * p.COSTOS_RECARGA_UNIDAD_ENERGIA[t - 1] * (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    u = sum(sum(sum(sum(M.U[e,i,v] * p.TIPOS_VEHICULO[v - 1,t - 1] * p.COSTOS_RECARGA_UNIDAD_ENERGIA[t - 1] * (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for e in M.E) for i in M.C) for v in M.V)
    m = sum(sum(sum(sum(M.M[e,f,v] * p.TIPOS_VEHICULO[v - 1,t - 1] * p.COSTOS_RECARGA_UNIDAD_ENERGIA[t - 1] * (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum((M.L[e,a,v] + M.H[a,e,v]) * p.TIPOS_VEHICULO[v - 1,t - 1] * p.COSTOS_RECARGA_UNIDAD_ENERGIA[t] * (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for a in M.A) for e in M.E) for v in M.V)
    return x + u + m + lh

def c_tiempo_energia_diario():
    x = sum(sum(sum(sum(M.X[a,i,v] * p.TIPOS_VEHICULO[v - 1,t - 1] * p.TIEMPOS_RECARGA_COMPLETA[t - 1] for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    u = sum(sum(sum(sum(M.U[e,i,v] * p.TIPOS_VEHICULO[v - 1,t - 1] * p.TIEMPOS_RECARGA_COMPLETA[t - 1] for t in M.T) for i in M.C) for e in M.E) for v in M.V)
    m = sum(sum(sum(sum(M.M[e,f,v] * p.TIPOS_VEHICULO[v - 1,t - 1] * p.TIEMPOS_RECARGA_COMPLETA[t - 1] for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum((M.L[e,a,v] + M.H[a,e,v]) * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t - 1] for t in M.T) for a in M.A) for e in M.E) for v in M.V)
    return x + u + m + lh

def c_recarga_diario_t():
    return c_energia_diario() + c_tiempo_energia_diario()
 
def c_mantenimiento_diario():
    return sum(sum(p.TIPOS_VEHICULO[v-1, t-1]* p.COSTOS_MANTENIMIENTO_DIARIO[t - 1] for t in M.T) for v in M.V)

def costo_total(model):
    return c_carga_diario() + c_distancia_diario() + c_tiempo_diario() + c_recarga_diario_t() + c_mantenimiento_diario()

M.FO = Objective(rule=costo_total, sense=minimize)


solver = SolverFactory('scip')
result = solver.solve(M, tee=True)  

M.display()