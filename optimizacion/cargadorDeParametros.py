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

        # Parámetros de las rutas entre almacenes, clientes y estaciones
        # Distancias
        self.D_ai = np.zeros((2, len(self.almacenes), len(self.clientes)))
        self.D_ia = np.zeros((2, len(self.clientes), len(self.almacenes)))
        self.D_ij = np.zeros((2, len(self.clientes), len(self.clientes)))
        self.D_ei = np.zeros((2, len(self.estaciones), len(self.clientes)))
        self.D_ie = np.zeros((2, len(self.clientes), len(self.estaciones)))
        self.D_ae = np.zeros((2, len(self.almacenes), len(self.estaciones)))
        self.D_ea = np.zeros((2, len(self.estaciones), len(self.almacenes)))
        self.D_ef = np.zeros((2, len(self.estaciones), len(self.estaciones)))

        # Tiempos
        self.T_ai = np.zeros((2, len(self.almacenes), len(self.clientes)))
        self.T_ia = np.zeros((2, len(self.clientes), len(self.almacenes)))
        self.T_ij = np.zeros((2, len(self.clientes), len(self.clientes)))
        self.T_ei = np.zeros((2, len(self.estaciones), len(self.clientes)))
        self.T_ie = np.zeros((2, len(self.clientes), len(self.estaciones)))
        self.T_ae = np.zeros((2, len(self.almacenes), len(self.estaciones)))
        self.T_ea = np.zeros((2, len(self.estaciones), len(self.almacenes)))
        self.T_ef = np.zeros((2, len(self.estaciones), len(self.estaciones)))
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
                matrizDistancia[i][j] = datos['distances'][i][j]
                matrizTiempo[i][j] = datos['durations'][i][j]


    def calcularMatrizDistanciaYTiempo(self, matrizDistancia, matrizTiempo, conjuntoDatos1, conjuntoDatos2):
        self.calcularDistanciaYTiempoRuta(matrizDistancia[0], matrizTiempo[0], conjuntoDatos1, conjuntoDatos2)
        self.calcularDistanciaHarvesiana(matrizDistancia[1], conjuntoDatos1, conjuntoDatos2)
        matrizTiempo[1] = matrizDistancia[1] / 40

    def obtenerMatricesDeTiempoYDistancia(self):
        self.calcularMatrizDistanciaYTiempo(self.D_ai, self.T_ai,  self.almacenes, self.clientes)
        self.calcularMatrizDistanciaYTiempo(self.D_ia, self.T_ia,  self.clientes, self.almacenes)
        self.calcularMatrizDistanciaYTiempo(self.D_ij, self.T_ij,  self.clientes, self.clientes)
        self.calcularMatrizDistanciaYTiempo(self.D_ei, self.T_ei, self.estaciones, self.clientes)
        self.calcularMatrizDistanciaYTiempo(self.D_ie, self.T_ie,  self.clientes, self.estaciones)
        self.calcularMatrizDistanciaYTiempo(self.D_ae, self.T_ae, self.almacenes, self.estaciones)
        self.calcularMatrizDistanciaYTiempo(self.D_ea, self.T_ea, self.estaciones, self.almacenes)
        self.calcularMatrizDistanciaYTiempo(self.D_ef, self.T_ef, self.estaciones, self.estaciones)

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


