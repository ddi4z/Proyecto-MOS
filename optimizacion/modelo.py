import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pyomo.environ import *
from pyomo.opt import SolverFactory



# Definicición de conjuntos

# Nodos
N = RangeSet(1, len(clientes) + len(almacenes) + len(estaciones))

# Clientes
C = RangeSet(1, len(clientes))

# Almacenes
A = RangeSet(len(clientes) + 1, len(clientes) + len(almacenes))

# Estaciones
E = RangeSet(len(clientes) + len(almacenes) + 1, len(clientes) + len(almacenes) + len(estaciones))

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

