import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyomo.environ import *
from pyomo.opt import SolverFactory
import sys

sys.path.append('optimizacion/')
from cargadorDeParametros import CargadorDeParametros

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

