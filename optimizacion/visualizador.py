import folium
from pyomo.environ import *

class Visualizador:
    def __init__(self, p, M):
        self.p = p
        self.M = M
        self.visualizar()

    def hacer_linea(self, mapa, coordenadas_i, coordenadas_j, i, j, color_linea='blue'):
        x1, y1 = coordenadas_i[i-1][1], coordenadas_i[i-1][2]
        x2, y2 = coordenadas_j[j-1][1], coordenadas_j[j-1][2]
        
        folium.PolyLine(locations=[(x1, y1), (x2, y2)], color=color_linea,weight=4).add_to(mapa)
        
    def escoger_color(self, v):
        color_linea = 'blue'
        tipo_vehiculo = self.p.vehiculos["VehicleType"][v - 1]
        if tipo_vehiculo == "Gas Car":
            color_linea = 'orange'
        elif tipo_vehiculo == "drone":
            color_linea = 'blue'
        else:
            color_linea = 'green'
        return color_linea

    def visualizar(self):
        coordenadas_estaciones = [(i + 1, self.p.estaciones['Latitude'][i], self.p.estaciones['Longitude'][i]) for i in range(self.p.num_estaciones)]
        coordenadas_almacenes = [(i + 1, self.p.almacenes['Latitude'][i], self.p.almacenes['Longitude'][i]) for i in range(self.p.num_almacenes)]
        coordenadas_clientes = [(i + 1, self.p.clientes['Latitude'][i], self.p.clientes['Longitude'][i]) for i in range(self.p.num_clientes)]

        numeroLineas = 0
        centro = [4.6097, -74.0817]
        mapa = folium.Map(location=centro, zoom_start=13)

        # este sirve
        self.hacer_linea(mapa, coordenadas_clientes, coordenadas_clientes, 1, 2, "purple")

        # Agregar puntos al mapa
        for i, lat, lon in coordenadas_estaciones:
            folium.Marker(location=(lat, lon), popup=f"Estación {i}", icon=folium.Icon(color='blue')).add_to(mapa)

        for i, lat, lon in coordenadas_almacenes:
            folium.Marker(location=(lat, lon), popup=f"Almacén {i}", icon=folium.Icon(color='green')).add_to(mapa)

        for i, lat, lon in coordenadas_clientes:
            folium.Marker(location=(lat, lon), popup=f"Cliente {i}", icon=folium.Icon(color='red')).add_to(mapa)

        # Agregar rutas al mapa
        # X_aiv y Y_iav
        for a in self.M.A:
            for i in self.M.C:
                for v in self.M.V:
                    if self.M.X[a,i,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, coordenadas_almacenes, coordenadas_clientes, a, i, self.escoger_color(v))
                    if self.M.Y[i,a,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, coordenadas_clientes, coordenadas_almacenes, i, a, self.escoger_color(v))
                                
        # Z_ij
        for i in self.M.C:
            for j in self.M.C:
                for v in self.M.V:
                    if i != j and self.M.Z[i,j,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, coordenadas_clientes, coordenadas_clientes, i, j, self.escoger_color(v))

                        
        # W_ie y U_ei
        for i in self.M.C:
            for e in self.M.E:
                for v in self.M.V:
                    if self.M.W[i,e,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, coordenadas_clientes, coordenadas_estaciones, i, e, self.escoger_color(v))
                    if self.M.U[e,i,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, coordenadas_estaciones, coordenadas_clientes, e, i, self.escoger_color(v))

        # M_ef
        for e in self.M.E:
            for f in self.M.E:
                for v in self.M.V:
                    if e != f and self.M.M[e,f,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, coordenadas_estaciones, coordenadas_estaciones, e, f, self.escoger_color(v))

        # L_ea y H_ae
        for e in self.M.E:
            for a in self.M.A:
                for v in self.M.V:
                    if self.M.L[e,a,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, coordenadas_estaciones, coordenadas_almacenes, e, a, self.escoger_color(v))
                    if self.M.H[a,e,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, coordenadas_almacenes, coordenadas_estaciones, a, e, self.escoger_color(v))
        
        print(f"Se han agregado {numeroLineas} líneas al mapa")
        mapa.save('solucion.html')
