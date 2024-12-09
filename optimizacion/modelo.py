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

# Tipos de productos
M.TP = RangeSet(1, p.num_productos)

# Conversiones de índices de los nodos
def indiceEstacion(e):
    return e + p.num_clientes + p.num_almacenes

def indiceAlmacen(a):
    return a + p.num_clientes

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
M.S = Var(M.V, M.N, within=NonNegativeIntegers)

# Funciones auxiliares

# Número de vehículos usados
def N():
    return sum(sum(sum(M.X[a,i,v] for i in M.C) for a in M.A) for v in M.V) + sum(sum(sum(M.H[a,e,v] for e in M.E) for a in M.A) for v in M.V) 

# Cantidad de veces que se recarga un vehículo
def C_veces_recarga(v):
    return sum(sum(M.X[a,i,v] for i in M.C) for a in M.A) + sum(sum(M.U[e,i,v] for i in M.C) for e in M.E) + sum(sum(M.M[e,f,v] for f in M.E) for e in M.E) + sum(sum(M.L[e,a,v] + M.H[a,e,v] for e in M.E) for a in M.A) 

def calcularCargaVehiculo(tp, v):
    return (
        sum(M.X[a, i, v] * p.DEMANDAS[tp - 1][i - 1] for i in M.C for a in M.A) +
        sum(M.Z[i, j, v] * p.DEMANDAS[tp - 1][j - 1] for i in M.C for j in M.C) +
        sum(M.U[e, i, v] * p.DEMANDAS[tp - 1][i - 1] for e in M.E for i in M.C)
    )

# Distancia diaria recorrida por un vehículo
def d_distancia_diaria_v(v):
    xy = sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.X[a,i,v] * p.D_ai[t - 1,a - 1,i - 1] + M.Y[i,a,v] * p.D_ia[t - 1,i - 1,a - 1]) for t in M.T) for i in M.C) for a in M.A)
    zz = sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * M.Z[i,j,v] * p.D_ij[t - 1,i - 1,j - 1] for t in M.T) for j in M.C) for i in M.C)
    wu = sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.W[i,e,v] * p.D_ie[t - 1,i - 1,e - 1] + M.U[e,i,v] * p.D_ei[t - 1,e - 1,i - 1]) for t in M.T) for e in M.E) for i in M.C)
    mm = sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * M.M[e,f,v] * p.D_ef[t - 1,e - 1,f - 1] for t in M.T) for f in M.E) for e in M.E)
    lh = sum(sum(sum(p.TIPOS_VEHICULO[v-1, t-1] * (M.L[e,a,v] * p.D_ea[t - 1,e - 1,a - 1] + M.H[a,e,v] * p.D_ae[t - 1,a - 1,e - 1]) for t in M.T) for e in M.E) for a in M.A)
    return xy + zz + wu + mm + lh

# Borrar un componente
def borrar_componente(M, nombre_comp):
    lista_borrar = [vr for vr in vars(M)
                if nombre_comp == vr
                or vr.startswith(nombre_comp + '_index')
                or vr.startswith(nombre_comp + '_domain')]

    for cc in lista_borrar:
        M.del_component(cc)

# Obtener los costos desglosados
def obtener_costos(M):
    M.COSTO_CARGA_DIARIO = c_carga_diario
    M.COSTO_DISTANCIA_DIARIO = c_distancia_diario
    M.COSTO_TIEMPO_DIARIO = c_tiempo_diario
    M.COSTO_RECARGA_DIARIO = c_recarga_diario_t
    M.COSTO_ENERGIA_DIARIO = c_energia_diario
    M.COSTO_TIEMPO_ENERGIA_DIARIO = c_tiempo_energia_diario
    M.COSTO_MANTENIMIENTO_DIARIO = c_mantenimiento_diario

# Variables dependientes

def t_kg_v_diario():
    x = sum(sum(sum(M.X[a,i,v] * sum(p.DEMANDAS[tp - 1,i - 1] for tp in M.TP) * p.TIEMPO_CARGA_MINUTO for i in M.C) for a in M.A) for v in M.V)
    z = sum(sum(sum(M.Z[i,j,v] * sum(p.DEMANDAS[tp - 1,j - 1] for tp in M.TP) * p.TIEMPO_CARGA_MINUTO for i in M.C) for j in M.C) for v in M.V)
    u = sum(sum(sum(M.U[e,i,v] * sum(p.DEMANDAS[tp - 1,i - 1] for tp in M.TP) * p.TIEMPO_CARGA_MINUTO for i in M.C) for e in M.E) for v in M.V)
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
    x = sum(sum(sum(sum(M.X[a,i,v] * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t - 1] for t in M.T) for i in M.C) for a in M.A) for v in M.V)
    u = sum(sum(sum(sum(M.U[e,i,v] * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t - 1] for t in M.T) for i in M.C) for e in M.E) for v in M.V)
    m = sum(sum(sum(sum(M.M[e,f,v] * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t - 1] for t in M.T) for f in M.E) for e in M.E) for v in M.V)
    lh = sum(sum(sum(sum((M.L[e,a,v] + M.H[a,e,v]) * p.TIPOS_VEHICULO[v-1, t-1] * p.TIEMPOS_RECARGA_COMPLETA[t - 1] for t in M.T) for a in M.A) for e in M.E) for v in M.V)
    return x + u + m + lh

# Función objetivo

def c_carga_diario():
    x = sum(sum(sum(M.X[a,i,v] * sum(p.DEMANDAS[tp - 1,i - 1] for tp in M.TP) * p.TIEMPO_CARGA_MINUTO * p.COSTO_CARGA_MINUTO for i in M.C) for a in M.A) for v in M.V)
    z = sum(sum(sum(M.Z[i,j,v] * sum(p.DEMANDAS[tp - 1,j - 1] for tp in M.TP) * p.TIEMPO_CARGA_MINUTO * p.COSTO_CARGA_MINUTO for j in M.C) for i in M.C) for v in M.V)
    u = sum(sum(sum(M.U[e,i,v] * sum(p.DEMANDAS[tp - 1,i - 1] for tp in M.TP) * p.TIEMPO_CARGA_MINUTO * p.COSTO_CARGA_MINUTO for i in M.C) for e in M.E) for v in M.V)
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
    lh = sum(sum(sum(sum((M.L[e,a,v] + M.H[a,e,v]) * p.TIPOS_VEHICULO[v - 1,t - 1] * p.COSTOS_RECARGA_UNIDAD_ENERGIA[t - 1] * (p.RANGOS[v - 1] / p.EFICIENCIAS_ENERGETICAS[t - 1]) for t in M.T) for a in M.A) for e in M.E) for v in M.V)
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

def costo_nulo(model):
    return 0

# Restricciones

# 2.7.1 Restricciones propias de clientes, almacenes y vehículos 

M.abastecimientoEntrada = ConstraintList()
M.abastecimientoSalida = ConstraintList()
for i in M.C:
    # Abastecimiento único al cliente (entrada)
    M.abastecimientoEntrada.add(sum(sum(M.X[a,i,v] for a in M.A) for v in M.V) + sum(sum(M.Z[j,i,v] for j in M.C) for v in M.V) + sum(sum(M.U[e,i,v] for e in M.E) for v in M.V) == 1)
    # Abastecimiento único al cliente (salida)
    M.abastecimientoSalida.add(sum(sum(M.Y[i,a,v] for a in M.A) for v in M.V) + sum(sum(M.Z[i,j,v] for j in M.C) for v in M.V) + sum(sum(M.W[i,e,v] for e in M.E) for v in M.V) == 1)

# Capacidad de los almacenes
M.capacidadAlmacen = ConstraintList()
for a in M.A:
    for tp in M.TP:
        M.capacidadAlmacen.add(
            sum(
                (sum(M.X[a, i, v] for i in M.C) + sum(M.H[a, e, v] for e in M.E)) *
                calcularCargaVehiculo(tp, v)
                for v in M.V
            ) <= p.CAPACIDADES_PRODUCTOS_ALMACENES[tp - 1][a - 1]
        )

M.capacidadVehiculo = ConstraintList()
# Una restricción incluye a la otra
M.rangoVehiculo = ConstraintList()
M.rangoVehiculoRecargas = ConstraintList()
for v in M.V:
    # Capacidad de los vehículos
    M.capacidadVehiculo.add(sum(sum(sum(p.DEMANDAS[tp - 1,i - 1] for tp in M.TP) * M.X[a,i,v] for i in M.C) for a in M.A) + sum(sum(sum(p.DEMANDAS[tp - 1,j - 1] for tp in M.TP) * M.Z[i,j,v] for i in M.C) for j in M.C) + sum(sum(sum(p.DEMANDAS[tp - 1,i - 1] for tp in M.TP) * M.U[e,i,v] for i in M.C) for e in M.E)  
                            <= sum(p.TIPOS_VEHICULO[v - 1, t - 1] * p.CAPACIDADES_PRODUCTOS_VEHICULO[v - 1] for t in M.T))
    
    # Una restricción incluye a la otra
    # Rango del vehículo sin tener en cuenta las recargas intermedias
    M.rangoVehiculo.add(d_distancia_diaria_v(v) <= p.RANGOS[v - 1])

    # Rango del vehículo con recargas intermedias
    # M.rangoVehiculoRecargas.add(d_distancia_diaria_v(v) <= p.RANGOS[v - 1] * C_veces_recarga(v))

# 2.7.2 Restricciones del grafo 

# Prohibición de subtoures
M.subtoures = ConstraintList()
# for v in M.V:
#     # Z_ijv
#     for i in M.C:
#         for j in M.C:
#             if i != j:
#                 M.subtoures.add(M.S[v,i] - M.S[v,j] + M.Z[i,j,v] * N() <= N() - 1)
                
#     for e in M.E:
#         # W_iev y U_eiv
#         for i in M.C:
#             M.subtoures.add(M.S[v,i] - M.S[v,indiceEstacion(e)] + M.W[i,e,v] * N() <= N() - 1)
#             M.subtoures.add(M.S[v,indiceEstacion(e)] - M.S[v,i] + M.U[e,i,v] * N() <= N() - 1)

#         # M_efv
#         for f in M.E:
#             if e != f:
#                 M.subtoures.add(M.S[v,indiceEstacion(e)] - M.S[v,indiceEstacion(f)] + M.M[e,f,v] * N() <= N() - 1)
                
                
# 2.7.3 Restricciones de los vehículos y los almacenes

M.salidaUnicaAlmacen = ConstraintList()
M.entradaUnicaAlmacen = ConstraintList()
M.salidaYVuelta = ConstraintList()
for v in M.V:
    # Salida única del almacén (nodo de origen)
    M.salidaUnicaAlmacen.add(sum(sum(M.X[a,i,v] for i in M.C) for a in M.A) + sum(sum(M.H[a,e,v] for e in M.E) for a in M.A) <= 1)
    # Entrada única al almacén (nodo de destino)
    M.entradaUnicaAlmacen.add(sum(sum(M.Y[i,a,v] for i in M.C) for a in M.A) + sum(sum(M.L[e,a,v] for e in M.E) for a in M.A) <= 1)
    # Salida y vuelta a un almacén de un vehículo
    M.salidaYVuelta.add(sum(sum(M.X[a,i,v] for i in M.C) for a in M.A) + sum(sum(M.H[a,e,v] for e in M.E) for a in M.A) - 
                        sum(sum(M.Y[i,a,v] for i in M.C) for a in M.A) - sum(sum(M.L[e,a,v] for e in M.E) for a in M.A) == 0)

# 2.7.4. Restricciones de los vehículos y los clientes

M.entradaUnicaCliente = ConstraintList()
M.salidaUnicaCliente = ConstraintList()
M.entradaYSalidaCliente = ConstraintList()
for i in M.C:
    for v in M.V:
        # Entrada única al cliente
        M.entradaUnicaCliente.add(sum(M.X[a,i,v] for a in M.A) + sum(M.Z[j,i,v] for j in M.C) + sum(M.U[e,i,v] for e in M.E) <= 1)
        # Salida única del cliente
        M.salidaUnicaCliente.add(sum(M.Y[i,a,v] for a in M.A) + sum(M.Z[i,j,v] for j in M.C) + sum(M.W[i,e,v] for e in M.E) <= 1)
        # Entrada y salida del cliente
        M.entradaYSalidaCliente.add(sum(M.X[a,i,v] for a in M.A) + sum(M.Z[j,i,v] for j in M.C) + sum(M.U[e,i,v] for e in M.E) - 
                                    sum(M.Y[i,a,v] for a in M.A) - sum(M.Z[i,j,v] for j in M.C) - sum(M.W[i,e,v] for e in M.E) == 0)

M.visitaClientesIntermediosSalida = ConstraintList()
M.visitaClientesIntermediosEntrada = ConstraintList()
for v in M.V:
    for ii in M.C:
        for jj in M.C:
            if ii != jj:
                # Visita de clientes intermedios (salida del almacén)
                M.visitaClientesIntermediosSalida.add(M.Z[ii,jj,v] <= 
                                                      sum(sum(M.X[a,i,v] for i in M.C) for a in M.A) + sum(sum(M.H[a,e,v] for e in M.E) for a in M.A))
                # Visita de clientes intermedios (entrada al almacén)
                M.visitaClientesIntermediosEntrada.add(M.Z[ii,jj,v] <= 
                                                      sum(sum(M.Y[i,a,v] for i in M.C) for a in M.A) + sum(sum(M.L[e,a,v] for e in M.E) for a in M.A))

# 2.7.5. Restricciones de los vehículos y las estaciones de carga

M.entradaUnicaEstacion = ConstraintList()
M.salidaUnicaEstacion = ConstraintList()
M.entradaYSalidaEstacion = ConstraintList()
for e in M.E:
    for v in M.V:
        # Entrada única a la estación
        M.entradaUnicaEstacion.add(sum(M.H[a,e,v] for a in M.A) + sum(M.W[i,e,v] for i in M.C) + sum(M.M[f,e,v] for f in M.E) <= 1)
        # Salida única de la estación
        M.salidaUnicaEstacion.add(sum(M.L[e,a,v] for a in M.A) + sum(M.U[e,i,v] for i in M.C) + sum(M.M[e,f,v] for f in M.E) <= 1)
        # Entrada y salida de la estación de recarga
        M.entradaYSalidaEstacion.add(sum(M.H[a,e,v] for a in M.A) + sum(M.W[i,e,v] for i in M.C) + sum(M.M[f,e,v] for f in M.E) -
                                     sum(M.L[e,a,v] for a in M.A) - sum(M.U[e,i,v] for i in M.C) - sum(M.M[e,f,v] for f in M.E) == 0)
        
M.visitaEstacionesIntermediasSalida = ConstraintList()
M.visitaEstacionesIntermediasEntrada = ConstraintList()
for v in M.V:
    for ee in M.E:
        for ff in M.E:
            if ee != ff:
                # Visita de estaciones intermedias (salida del almacén)
                M.visitaEstacionesIntermediasSalida.add(M.M[ee,ff,v] <= 
                                                      sum(sum(M.X[a,i,v] for i in M.C) for a in M.A) + sum(sum(M.H[a,e,v] for e in M.E) for a in M.A))
                # Visita de estaciones intermedias (entrada al almacén)
                M.visitaEstacionesIntermediasEntrada.add(M.M[ee,ff,v] <= 
                                                      sum(sum(M.Y[i,a,v] for i in M.C) for a in M.A) + sum(sum(M.L[e,a,v] for e in M.E) for a in M.A))

# Solución del modelo con SCIP
solver_name = "scip"

# Solución del modelo factible
# solver_factible = SolverFactory(solver_name)
# solver_factible.options['numerics/feastol'] = 1e-9
# solver_factible.options['limits/time'] = 570
# solver_factible.options['limits/absgap'] = 10

# M.FO = Objective(rule=costo_nulo, sense=minimize)
# resultado_factible = solver_factible.solve(M, tee=True)

# Solución del modelo
solver = SolverFactory("couenne", executable="optimizacion/couenne.exe")

M.FO = Objective(rule=costo_total, sense=minimize)
resultado = solver.solve(M, tee=True)

# Visualización de la solución
obtener_costos(M)
v = Visualizador(p, M)
