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

# Cargue de parámetros
p = CargadorDeParametros()

# Creación del modelo	
M = ConcreteModel()

# Definicición de conjuntos

# Nodos
M.N = RangeSet(1, p.num_clientes + p.num_almacenes + p.num_estaciones)

# Clientes
M.C = RangeSet(1, p.num_clientes)

# Almacenes
M.A = RangeSet(1, p.num_almacenes)

# Estaciones
M.E = RangeSet(1, p.num_estaciones)

# Vehículos
M.V = RangeSet(1, p.num_vehiculos)

# Tipos de vehículos
M.T = RangeSet(1, 3)

# Conversiones de índices de los nodos
def indiceEstacion(e):
    return e + p.num_clientes + p.num_almacenes

def indiceAlmacen(a):
    return a + p.num_clientes

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

# Funciones auxiliares

# Número de vehículos usados
def N():
    return sum(sum(sum(M.X[a,i,v] for i in M.C) for a in M.A) for v in M.V) + sum(sum(sum(M.H[a,e,v] for e in M.E) for a in M.A) for v in M.V) 

# Variables dependientes

def t_kg_v_diario():
    x = sum(sum(sum(M.X[a,i,v] * p.DEMANDAS[i - 1] * p.TIEMPO_CARGA_MINUTO for i in M.C) for a in M.A) for v in M.V)
    z = sum(sum(sum(M.Z[i,j,v] * p.DEMANDAS[j - 1] * p.TIEMPO_CARGA_MINUTO for i in M.C) for j in M.C) for v in M.V)
    u = sum(sum(sum(M.U[e,i,v] * p.DEMANDAS[i - 1] * p.TIEMPO_CARGA_MINUTO for i in M.C) for e in M.E) for v in M.V)
    return x + z + u

def d_viaje_diario_t():
    xy = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.X[a,i,v] * p.D_ai[t - 1,a - 1,i - 1] + M.Y[i,a,v] * p.D_ia[t - 1,i - 1,a - 1]) for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    zz = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.Z[i,j,v] * p.D_ij[t - 1,i - 1,j - 1]) for t in M.T) for j in M.C) for i in M.C) for v in M.V)
    wu = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.W[i,e,v] * p.D_ie[t - 1,i - 1,e - 1] + M.U[e,i,v] * p.D_ei[t - 1,e - 1,i - 1]) for t in M.T) for e in M.E) for i in M.C) for v in M.V)
    mm = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.M[e,f,v] * p.D_ef[t - 1,e - 1,f - 1]) for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.L[e,a,v] * p.D_ea[t - 1,e - 1,a - 1] + M.H[a,e,v] * p.D_ae[t - 1,a - 1,e - 1]) for t in M.T) for e in M.E) for a in M.A) for v in M.V)
    return xy + zz + wu + mm + lh

def q_energia_diaria_t():
    x = sum(sum(sum(sum(M.X[a,i,v] * p.TIPOS_VEHICULO[v-1, t-1] * (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    u = sum(sum(sum(sum(M.U[e,i,v] * p.TIPOS_VEHICULO[v-1, t-1] * (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for e in M.E) for i in M.C) for v in M.V)
    m = sum(sum(sum(sum(M.M[e,f,v] * p.TIPOS_VEHICULO[v-1, t-1] * (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum((M.L[e,a,v] + M.H[a,e,v]) * p.TIPOS_VEHICULO[v-1, t-1] * (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for e in M.E) for a in M.A) for v in M.V)
    return x + u + m + lh

def t_recarga_diario_t():
    x = sum(sum(sum(sum(M.X[a,i,v] * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t] for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    u = sum(sum(sum(sum(M.U[e,i,v] * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t] for t in M.T) for i in M.C) for e in M.E) for v in M.V)
    m = sum(sum(sum(sum(M.M[e,f,v] * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t] for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum((M.L[e,a,v] + M.H[a,e,v]) * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t] for t in M.T) for a in M.A) for e in M.E) for v in M.V)
    return x + u + m + lh

# Función objetivo

def c_carga_diario():
    x = sum(sum(sum(M.X[a,i,v] * p.DEMANDAS[i - 1] * p.TIEMPO_CARGA_MINUTO * p.COSTO_CARGA_MINUTO for i in M.C) for a in M.A) for v in M.V)
    z = sum(sum(sum(M.Z[i,j,v] * p.DEMANDAS[j - 1] * p.TIEMPO_CARGA_MINUTO * p.COSTO_CARGA_MINUTO for j in M.C) for i in M.C) for v in M.V)
    u = sum(sum(sum(M.U[e,i,v] * p.DEMANDAS[i - 1] * p.TIEMPO_CARGA_MINUTO * p.COSTO_CARGA_MINUTO for i in M.C) for e in M.E) for v in M.V)
    return x + z + u

def c_distancia_diario():
    xy = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_FLETE[t - 1] * (M.X[a,i,v] * p.D_ai[t - 1,a - 1,i - 1] + M.Y[i,a,v] * p.D_ia[t - 1,i - 1,a - 1]) for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    zz = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_FLETE[t - 1] * (M.Z[i,j,v] * p.D_ij[t - 1,i - 1,j - 1]) for t in M.T) for j in M.C) for i in M.C) for v in M.V)
    wu = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_FLETE[t - 1] * (M.W[i,e,v] * p.D_ie[t - 1,i - 1,e - 1] + M.U[e,i,v] * p.D_ei[t - 1,e - 1,i - 1]) for t in M.T) for e in M.E) for i in M.C) for v in M.V)
    mm = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_FLETE[t - 1] * (M.M[e,f,v] * p.D_ef[t - 1,e - 1,f - 1]) for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_FLETE[t - 1] * (M.L[e,a,v] * p.D_ea[t - 1,e - 1,a - 1] + M.H[a,e,v] * p.D_ae[t - 1,a - 1,e - 1]) for t in M.T) for e in M.E) for a in M.A) for v in M.V)
    return xy + zz + wu + mm + lh

def c_tiempo_diario():
    xy = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_TIEMPO[t - 1] * (M.X[a,i,v] * p.T_ai[t - 1,a - 1,i - 1] + M.Y[i,a,v] * p.T_ia[t - 1,i - 1,a - 1]) for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    zz = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_TIEMPO[t - 1] * (M.Z[i,j,v] * p.T_ij[t - 1,i - 1,j - 1]) for t in M.T) for j in M.C) for i in M.C) for v in M.V)
    wu = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_TIEMPO[t - 1] * (M.W[i,e,v] * p.T_ie[t - 1,i - 1,e - 1] + M.U[e,i,v] * p.T_ei[t - 1,e - 1,i - 1]) for t in M.T) for e in M.E) for i in M.C) for v in M.V)
    mm = sum(sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.TARIFAS_TIEMPO[t - 1] * (M.M[e,f,v] * p.T_ef[t - 1,e - 1,f - 1]) for t in M.T) for f in M.E) for e in M.E) for v in M.V)
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
    return sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * p.COSTOS_MANTENIMIENTO_DIARIO[t - 1] for t in M.T) for v in M.V)

def costo_total(model):
    return c_carga_diario() + c_distancia_diario() + c_tiempo_diario() + c_recarga_diario_t() + c_mantenimiento_diario()

M.FO = Objective(rule=costo_total, sense=minimize)

# Restricciones

# 2.7.1 Restricciones propias de clientes, almacenes y vehículos 

M.abastecimiento = ConstraintList()
for i in M.C:
    # Abastecimiento único al cliente (entrada)
    M.abastecimiento.add(sum(sum(M.X[a,i,v] for a in M.A) for v in M.V) + sum(sum(M.Z[j,i,v] for j in M.C) for v in M.V) + sum(sum(M.U[e,i,v] for e in M.E) for v in M.V) == 1)
    # Abastecimiento único al cliente (salida): 
    M.abastecimiento.add(sum(sum(M.Y[i,a,v] for a in M.A) for v in M.V) + sum(sum(M.Z[i,j,v] for j in M.C) for v in M.V) + sum(sum(M.W[i,e,v] for e in M.E) for v in M.V) == 1)

# Capacidad de los almacenes
M.capacidadAlmacen = ConstraintList()
for a in M.A:
    M.capacidadAlmacen.add(sum(sum(p.DEMANDAS[i - 1] * M.X[a,i,v] for i in M.C) for v in M.V) <= p.CAPACIDADES_PRODUCTOS_ALMACENES[a - 1])

# Capacidad de los vehículos
M.capacidadVehiculo = ConstraintList()
for v in M.V:
    M.capacidadVehiculo.add(sum(sum(p.DEMANDAS[i - 1] * M.X[a,i,v] for i in M.C) for a in M.A) + sum(sum(p.DEMANDAS[j - 1] * M.Z[i,j,v] for i in M.C) for j in M.C) + sum(sum(p.DEMANDAS[i - 1] * M.U[e,i,v] for i in M.C) for e in M.E) 
                            <= sum(p.TIPOS_VEHICULO[v - 1, t - 1] * p.CAPACIDADES_PRODUCTOS_VEHICULO[v - 1] for t in M.T))

# Rango del vehículo sin tener en cuenta las recargas intermedias
M.rangoVehiculo = ConstraintList()
for v in M.V:
    M.rangoVehiculo.add(d_viaje_diario_t() <= p.RANGOS[v - 1])

# Rango del vehículo con recargas intermedias



# 2.7.2 Restricciones del grafo 

# Prohibición de subtoures

M.subtoures = ConstraintList()
for v in M.V:
    for i in M.C:
        for j in M.C:
            if i != j:
                M.subtoures.add(M.S[v,i] - M.S[v,j] + M.Z[i,j,v] * N() <= N() - 1)
                
    for e in M.E:
        for i in M.C:
            M.subtoures.add(M.S[v,i] - M.S[v,indiceEstacion(e)] + M.W[i,e,v] * N() <= N() - 1)
            M.subtoures.add(M.S[v,indiceEstacion(e)] - M.S[v,i] + M.U[e,i,v] * N() <= N() - 1)
    
        for f in M.E:
            if e != f:
                M.subtoures.add(M.S[v,indiceEstacion(e)] - M.S[v,indiceEstacion(f)] + M.M[e,f,v] * N() <= N() - 1)

# 2.7.3 Restricciones de los vehículos y los almacenes

# Salida única del almacén (nodo de origen)
M.salidaUnicaAlmacen = ConstraintList()
for v in M.V:
    M.salidaUnicaAlmacen.add(sum(sum(M.X[a,i,v] for i in M.C) for a in M.A) + sum(sum(M.H[a,e,v] for e in M.E) for a in M.A) <= 1)

# Entrada única al almacén (nodo de destino)
M.entradaUnicaAlmacen = ConstraintList()
for v in M.V:
    M.entradaUnicaAlmacen.add(sum(sum(M.Y[i,a,v] for i in M.C) for a in M.A) + sum(sum(M.L[e,a,v] for e in M.E) for a in M.A) <= 1)

# Salida y vuelta a un almacén de un vehículo
M.salidaYVuelta = ConstraintList()
for v in M.V:
    M.salidaYVuelta.add(sum(sum(M.X[a,i,v] for i in M.C) for a in M.A) + sum(sum(M.H[a,e,v] for e in M.E) for a in M.A) - sum(sum(M.Y[i,a,v] for i in M.C) for a in M.A) + sum(sum(M.L[e,a,v] for e in M.E) for a in M.A) == 0)

# 2.7.4 Restricciones de los vehículos y los clientes

# Entrada única al cliente
M.entradaUnicaCliente = ConstraintList()
for i in M.C:
    for v in M.V:
        M.entradaUnicaCliente.add(sum(M.X[a,i,v] for a in M.A) + sum(M.Z[j,i,v] for j in M.C) + sum(M.U[e,i,v] for e in M.E) <= 1)

# Salida única del cliente
M.salidaUnicaCliente = ConstraintList()
for i in M.C:
    for v in M.V:
        M.salidaUnicaCliente.add(sum(M.Y[i,a,v] for a in M.A) + sum(M.Z[i,j,v] for j in M.C) + sum(M.W[i,e,v] for e in M.E) <= 1)

# Entrada y salida del cliente
M.entradaYSalidaCliente = ConstraintList()
for i in M.C:
    for v in M.V:
        M.entradaYSalidaCliente.add(sum(M.X[a,i,v] for a in M.A) + sum(M.Z[j,i,v] for j in M.C) + sum(M.U[e,i,v] for e in M.E) - sum(M.Y[i,a,v] for a in M.A) - sum(M.Z[i,j,v] for j in M.C) - sum(M.W[i,e,v] for e in M.E) == 0)

# 2.7.5. Restricciones de los vehículos y las estaciones de carga

# Entrada única a la estación



# Salida única de la estación



# Entrada y salida de la estación de recarga



# Solución del modelo con SCIP

solver_name = "scip"
solver = SolverFactory(solver_name)
solver.options['limits/time'] = 570
solver.options['heuristics'] = 'aggressive'
solver.options['limits/absgap'] = 10 
result = solver.solve(M, tee=True)


# Visualización de la solución

M.display()
v = Visualizador(p, M)
