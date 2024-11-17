class Vehiculo:
    def __init__(self, tipo, capacidad, rango):
        self.tipo = tipo
        self.capacidad = capacidad
        self.rango = rango
        self.tarifaFlete = [5000, 500, 4000][self.tipoAId(tipo)]
        self.tarifaTiempo = [500, 500, 500][self.tipoAId(tipo)]
        self.costoMantenimiento = [30000, 3000, 21000][self.tipoAId(tipo)]
        self.costoRecarga = [16000, 220.73, 0][self.tipoAId(tipo)]
        self.tiempoRecarga = [0.1,2,0][self.tipoAId(tipo)]
        self.velocidadPromedio = [0,40,0][self.tipoAId(tipo)]
        self.eficienteCombustible = [10,0,0][self.tipoAId(tipo)]
        self.eficienciaEnergetica = [0,0.15,0.15][self.tipoAId(tipo)]
        
    def tipoAId(self, tipo):
        if tipo == "Gas Car":
            return 0
        elif tipo == "drone":
            return 1
        elif tipo == "EV":
            return 2

