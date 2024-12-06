import numpy as np
import pandas as pd
from pyomo.environ import *
from haversine import haversine, Unit
import requests

class CargadorDeParametros:
    def __init__(self):
        # Carga de datos
        self.clientes, self.almacenes, self.vehiculos, self.estaciones, self.capacidades_almacenes = self.cargarCasoDePrueba()

        self.num_clientes = len(self.clientes)
        self.num_almacenes = len(self.almacenes)
        self.num_vehiculos = len(self.vehiculos)
        self.num_estaciones = len(self.estaciones)

        # Distancias
        self.D_ai = np.zeros((3, self.num_almacenes, self.num_clientes))
        self.D_ia = np.zeros((3, self.num_clientes, self.num_almacenes))
        self.D_ij = np.zeros((3, self.num_clientes, self.num_clientes))
        self.D_ei = np.zeros((3, self.num_estaciones, self.num_clientes))
        self.D_ie = np.zeros((3, self.num_clientes, self.num_estaciones))
        self.D_ae = np.zeros((3, self.num_almacenes, self.num_estaciones))
        self.D_ea = np.zeros((3, self.num_estaciones, self.num_almacenes))
        self.D_ef = np.zeros((3, self.num_estaciones, self.num_estaciones))

        # Tiempos
        self.T_ai = np.zeros((3, self.num_almacenes, self.num_clientes))
        self.T_ia = np.zeros((3, self.num_clientes, self.num_almacenes))
        self.T_ij = np.zeros((3, self.num_clientes, self.num_clientes))
        self.T_ei = np.zeros((3, self.num_estaciones, self.num_clientes))
        self.T_ie = np.zeros((3, self.num_clientes, self.num_estaciones))
        self.T_ae = np.zeros((3, self.num_almacenes, self.num_estaciones))
        self.T_ea = np.zeros((3, self.num_estaciones, self.num_almacenes))
        self.T_ef = np.zeros((3, self.num_estaciones, self.num_estaciones))

        # Parámetros de los clientes
        self.DEMANDAS = self.clientes["Product"].to_numpy()
        self.LONGITUDES_CLIENTES = self.clientes["Longitude"].to_numpy()
        self.LATITUDES_CLIENTES = self.clientes["Latitude"].to_numpy()

        # Parámetros de los almacenes
        self.CAPACIDADES_PRODUCTOS_ALMACENES = self.capacidades_almacenes["Product"].to_numpy()
        self.LONGITUDES_ALMACENES = self.almacenes["Longitude"].to_numpy()
        self.LATITUDES_ALMACENES =  self.almacenes["Latitude"].to_numpy()

        # Parámetros de las estaciones de recarga
        self.LONGITUDES_ESTACIONES = self.estaciones["Longitude"].to_numpy()
        self.LATITUDES_ESTACIONES = self.estaciones["Latitude"].to_numpy()

        # Parámetros de los vehículos
        self.TIPOS_VEHICULO = self.obtenerMatrizTipoVehiculo()
        self.CAPACIDADES_PRODUCTOS_VEHICULO = self.vehiculos["Capacity"].to_numpy()
        self.RANGOS = self.vehiculos["Range"].to_numpy() * 10000000
        self.TIEMPOS_RECARGA_COMPLETA = [1, 20, 0]
        self.VELOCIDADES_PROMEDIO = [None, 40, None]
        self.EFICIENCIAS_ENERGETICAS = [10, 1/0.15, 1/0.15]
        self.TIEMPO_CARGA_MINUTO = 1/5

        # Carga de distancias y tiempos 
        self.obtenerMatricesDeTiempoYDistancia()
        
        # Parámetros de los costos vehiculares
        self.TARIFAS_FLETE = [5000, 500, 4000]
        self.TARIFAS_TIEMPO = [500, 500, 500]
        self.COSTOS_MANTENIMIENTO_DIARIO = [30000, 3000, 21000]
        self.COSTOS_RECARGA_UNIDAD_ENERGIA = [16000, 220.73, 0]
        self.COSTO_CARGA_MINUTO = 500
        

    def calcularDistanciaHarvesiana(self, matriz, conjuntoDatos1, conjuntoDatos2):
        for i in range(len(conjuntoDatos1)):
            for j in range(len(conjuntoDatos2)):
                punto1 = (conjuntoDatos1['Latitude'][i], conjuntoDatos1['Longitude'][i])
                punto2 = (conjuntoDatos2['Latitude'][j], conjuntoDatos2['Longitude'][j])
                matriz[i][j] = haversine(punto1, punto2, unit=Unit.KILOMETERS)

    def calcularDistanciaYTiempoRuta(self, matrizDistancia, matrizTiempo, conjuntoDatos1, conjuntoDatos2):
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
                for t in [0,2]:
                    matrizDistancia[t][i][j] = datos['distances'][i][j] / 1000
                    matrizTiempo[t][i][j] = datos['durations'][i][j] / 60 


    def calcularMatrizDistanciaYTiempo(self, matrizDistancia, matrizTiempo, conjuntoDatos1, conjuntoDatos2):
        self.calcularDistanciaYTiempoRuta(matrizDistancia, matrizTiempo, conjuntoDatos1, conjuntoDatos2)
        self.calcularDistanciaHarvesiana(matrizDistancia[1], conjuntoDatos1, conjuntoDatos2)
        matrizTiempo[1] = matrizDistancia[1] / (self.VELOCIDADES_PROMEDIO[1] / 60)

    def obtenerMatricesDeTiempoYDistancia(self):
        self.calcularMatrizDistanciaYTiempo(self.D_ai, self.T_ai,  self.almacenes, self.clientes)
        self.calcularMatrizDistanciaYTiempo(self.D_ia, self.T_ia,  self.clientes, self.almacenes)
        self.calcularMatrizDistanciaYTiempo(self.D_ij, self.T_ij,  self.clientes, self.clientes)
        self.calcularMatrizDistanciaYTiempo(self.D_ei, self.T_ei, self.estaciones, self.clientes)
        self.calcularMatrizDistanciaYTiempo(self.D_ie, self.T_ie,  self.clientes, self.estaciones)
        self.calcularMatrizDistanciaYTiempo(self.D_ae, self.T_ae, self.almacenes, self.estaciones)
        self.calcularMatrizDistanciaYTiempo(self.D_ea, self.T_ea, self.estaciones, self.almacenes)
        self.calcularMatrizDistanciaYTiempo(self.D_ef, self.T_ef, self.estaciones, self.estaciones)

    def obtenerMatrizTipoVehiculo(self):
        tipos_vehiculo = np.zeros((self.num_vehiculos, 3))
        for i in range(self.num_vehiculos):
            tipo_vehiculo = self.vehiculos["VehicleType"][i]
            if tipo_vehiculo == "Gas Car":
                tipos_vehiculo[i][0] = 1
            elif tipo_vehiculo == "drone":
                tipos_vehiculo[i][1] = 1
            elif tipo_vehiculo == "EV":
                tipos_vehiculo[i][2] = 1
        return tipos_vehiculo

    def cargarCaso(self, rutaBase):
        clientes = pd.read_csv(f"{rutaBase}Clients.csv")
        almacenes = pd.read_csv(f"{rutaBase}Depots.csv")
        vehiculos = pd.read_csv(f"{rutaBase}Vehicles.csv")
        estaciones = pd.read_csv(f"{rutaBase}RechargeNodes.csv")
        capacidades_almacenes = pd.read_csv(f"{rutaBase}DepotCapacities.csv")
        return clientes, almacenes, vehiculos, estaciones, capacidades_almacenes

    def cargarCasoDePrueba(self):
        print("1. Caso base")
        print("2. Caso 5 clientes por vehiculo")
        print("3. Caso grandes distancias poca demanda")
        print("4. almacenes con capacidad")
        caso = int(input("Digite el número del caso de prueba: "))

        rutaPorDefecto = "optimizacion/Proyecto Seneca Libre/"
        rutas = [
            "case_1_base/",
            "case_2_cost/",
            "case_3_supply_limits/",
            "case_4_multi_product/"
            "case_5_recharge_nodes/",
        ]
        return self.cargarCaso(rutaPorDefecto + rutas[caso - 1])


