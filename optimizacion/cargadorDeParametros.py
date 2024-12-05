import numpy as np
import pandas as pd
from pyomo.environ import *
from haversine import haversine, Unit
import requests

class CargadorDeParametros:
    def __init__(self):
        # Cuadro 1: Parámetros de Costos y Eficiencia para Vehículo
        # Gas Car | Drone | Solar EV
        self.tarifaFlete = [5000, 500, 4000]
        self.tarifaTiempo = [500, 500, 500]
        self.costoMantenimiento = [30000, 3000, 21000]
        self.costoRecarga = [16000, 220.73, 0]
        self.tiempoRecarga = [0.1,2,0]
        self.eficienteCombustible = [10,0,0]
        self.eficienciaEnergetica = [0,0.15,0.15]
        self.clientes, self.almacenes, self.vehiculos, self.estaciones = self.cargarCasoDePrueba()

        # Distancias
        self.D_tai = np.zeros((3, len(self.almacenes), len(self.clientes)))
        self.D_tia = np.zeros((3, len(self.clientes), len(self.almacenes)))
        self.D_tij = np.zeros((3, len(self.clientes), len(self.clientes)))
        self.D_tei = np.zeros((3, len(self.estaciones), len(self.clientes)))
        self.D_tie = np.zeros((3, len(self.clientes), len(self.estaciones)))
        self.D_tae = np.zeros((3, len(self.almacenes), len(self.estaciones)))
        self.D_tea = np.zeros((3, len(self.estaciones), len(self.almacenes)))
        self.D_tef = np.zeros((3, len(self.estaciones), len(self.estaciones)))

        # Tiempos
        self.T_tai = np.zeros((3, len(self.almacenes), len(self.clientes)))
        self.T_tia = np.zeros((3, len(self.clientes), len(self.almacenes)))
        self.T_tij = np.zeros((3, len(self.clientes), len(self.clientes)))
        self.T_tei = np.zeros((3, len(self.estaciones), len(self.clientes)))
        self.T_tie = np.zeros((3, len(self.clientes), len(self.estaciones)))
        self.T_tae = np.zeros((3, len(self.almacenes), len(self.estaciones)))
        self.T_tea = np.zeros((3, len(self.estaciones), len(self.almacenes)))
        self.T_tef = np.zeros((3, len(self.estaciones), len(self.estaciones)))
        self.obtenerMatricesDeTiempoYDistancia()



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
                    matrizDistancia[t][i][j] = datos['distances'][i][j]
                    matrizTiempo[t][i][j] = datos['durations'][i][j]


    def calcularMatrizDistanciaYTiempo(self, matrizDistancia, matrizTiempo, conjuntoDatos1, conjuntoDatos2):
        self.calcularDistanciaYTiempoRuta(matrizDistancia, matrizTiempo, conjuntoDatos1, conjuntoDatos2)
        self.calcularDistanciaHarvesiana(matrizDistancia[1], conjuntoDatos1, conjuntoDatos2)
        matrizTiempo[1] = matrizDistancia[1] / 40

    def obtenerMatricesDeTiempoYDistancia(self):
        self.calcularMatrizDistanciaYTiempo(self.D_tai, self.T_tai,  self.almacenes, self.clientes)
        self.calcularMatrizDistanciaYTiempo(self.D_tia, self.T_tia,  self.clientes, self.almacenes)
        self.calcularMatrizDistanciaYTiempo(self.D_tij, self.T_tij,  self.clientes, self.clientes)
        self.calcularMatrizDistanciaYTiempo(self.D_tei, self.T_tei, self.estaciones, self.clientes)
        self.calcularMatrizDistanciaYTiempo(self.D_tie, self.T_tie,  self.clientes, self.estaciones)
        self.calcularMatrizDistanciaYTiempo(self.D_tae, self.T_tae, self.almacenes, self.estaciones)
        self.calcularMatrizDistanciaYTiempo(self.D_tea, self.T_tea, self.estaciones, self.almacenes)
        self.calcularMatrizDistanciaYTiempo(self.D_tef, self.T_tef, self.estaciones, self.estaciones)

    def cargarCaso(self, rutaBase):
        clientes = pd.read_csv(f"{rutaBase}Clients.csv")
        almacenes = pd.read_csv(f"{rutaBase}Depots.csv")
        vehiculos = pd.read_csv(f"{rutaBase}Vehicles.csv")
        estaciones = pd.read_csv(f"{rutaBase}RechargeNodes.csv")
        return clientes, almacenes, vehiculos, estaciones

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


