import folium

class Visualizador:
    def __init__(self, clientes, almacenes, estaciones):
        self.clientes = clientes
        self.almacenes = almacenes
        self.estaciones = estaciones
        self.visualizar()

    def visualizar(self):
        coordenadasEstaciones = [(self.estaciones['Latitude'][i], self.estaciones['Longitude'][i]) for i in range(len(self.estaciones))]
        almacenes = [(self.almacenes['Latitude'][i], self.almacenes['Longitude'][i]) for i in range(len(self.almacenes))]
        clientes = [(self.clientes['Latitude'][i], self.clientes['Longitude'][i]) for i in range(len(self.clientes))]

        centro = [4.6097, -74.0817]
        mapa = folium.Map(location=centro, zoom_start=13)

        # Agregar puntos al mapa
        for lat, lon in coordenadasEstaciones:
            folium.Marker(location=(lat, lon), popup="Estación", icon=folium.Icon(color='blue')).add_to(mapa)

        for lat, lon in almacenes:
            folium.Marker(location=(lat, lon), popup="Almacén", icon=folium.Icon(color='green')).add_to(mapa)

        for lat, lon in clientes:
            folium.Marker(location=(lat, lon), popup="Cliente", icon=folium.Icon(color='red')).add_to(mapa)

        mapa.save('solucion.html')
