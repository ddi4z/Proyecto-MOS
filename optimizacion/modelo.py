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


def t_kg_v_diario():
    x = sum(sum(sum(M.X[a,i,v] * DEMANDAS[i] for i in M.C) for a in M.A) for v in M.V)
    z = sum(sum(sum(M.Z[i,j,v] * DEMANDAS[j] for i in M.C) for j in M.C) for v in M.V)
    u = sum(sum(sum(M.U[e,i,v] * DEMANDAS[i] for i in M.C) for e in M.E) for v in M.V)
    return x + z + u

def d_viaje_diario_t():
    xy = sum(sum(sum(sum())))
    zz = sum(sum(sum(sum())))
    wu = sum(sum(sum(sum())))
    mm = sum(sum(sum(sum())))
    lh = sum(sum(sum(sum())))
    

v = Visualizador(p.clientes, p.almacenes, p.estaciones)

