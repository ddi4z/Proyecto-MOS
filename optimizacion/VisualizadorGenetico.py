import io
import math
import folium
import numpy as np
from pyomo.environ import value as pyomo_value
import csv

class VisualizadorGenetico:
    def __init__(self, p, individuo):
        self.p = p
        self.individuo = individuo
        self.path_archivo_resultados_txt = self.p.rutaCarpeta + "resultados.txt"
        self.path_archivo_resultados_csv = self.p.rutaCarpeta + "resultados.csv"
        self.path_archivo_resultados_html = self.p.rutaCarpeta + "solucion.html"
        self.path_archivo_solucion = self.p.rutaCarpeta + "solucion.txt"
        self.visualizar()
        self.guardar_resultados_txt()
        self.guardar_resultados_csv()
        
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

    def hacer_linea(self, mapa, tipo_i, tipo_j, coordenadas_i, coordenadas_j, i, j, v):
        color_linea = self.escoger_color(v)
        mensaje_hover = f"Vehículo {v} - {tipo_i} {i} hacia {tipo_j} {j}"

        x1, y1 = coordenadas_i[i - 1][1], coordenadas_i[i - 1][2]
        x2, y2 = coordenadas_j[j - 1][1], coordenadas_j[j - 1][2]
        folium.PolyLine(locations=[(x1, y1), (x2, y2)], color=color_linea, tooltip=mensaje_hover, weight=4).add_to(mapa)

        # Calcular el ángulo de rotación de la flecha
        dx = x2 - x1
        dy = y2 - y1
        angle = math.degrees(math.atan2(dy, dx))

        # Tamaño del triángulo ajustado
        size = 0.0005

        # Calcular las coordenadas del triángulo (flecha)
        point1 = (x2, y2)  # Punta de la flecha
        point2 = (x2 + size * math.cos(math.radians(angle + 150)), 
                y2 + size * math.sin(math.radians(angle + 150)))
        point3 = (x2 + size * math.cos(math.radians(angle - 150)), 
                y2 + size * math.sin(math.radians(angle - 150)))

        # Dibujar la flecha
        folium.Polygon(
            locations=[point1, point2, point3, point1],
            color=color_linea,
            tooltip=mensaje_hover,
            fill=True,
            fill_color=color_linea,
            fill_opacity=1
        ).add_to(mapa)
        


    def visualizar(self):
        coordenadas_estaciones = [(i + 1, self.p.estaciones['Latitude'][i], self.p.estaciones['Longitude'][i]) for i in range(self.p.num_estaciones)]
        coordenadas_almacenes = [(i + 1, self.p.almacenes['Latitude'][i], self.p.almacenes['Longitude'][i]) for i in range(self.p.num_almacenes)]
        coordenadas_clientes = [(i + 1, self.p.clientes['Latitude'][i], self.p.clientes['Longitude'][i]) for i in range(self.p.num_clientes)]

        numeroLineas = 0
        centro = (self.p.almacenes['Latitude'][0], self.p.almacenes['Longitude'][0])
        mapa = folium.Map(location=centro, zoom_start=13)

        # Agregar puntos al mapa
        for i, lat, lon in coordenadas_estaciones:
            folium.Marker(location=(lat, lon), popup=f"Estación {i}", icon=folium.Icon(color='blue')).add_to(mapa)

        for i, lat, lon in coordenadas_almacenes:
            folium.Marker(location=(lat, lon), popup=f"Almacén {i}", icon=folium.Icon(color='green')).add_to(mapa)

        for i, lat, lon in coordenadas_clientes:
            folium.Marker(location=(lat, lon), popup=f"Cliente {i}", icon=folium.Icon(color='red')).add_to(mapa)

        self.agregar_convenciones(mapa)
        for i in range(len(self.individuo) - 1):
            numeroLineas += 1
            self.hacer_linea(mapa, "cliente", "cliente", coordenadas_clientes, coordenadas_clientes, self.individuo[i], self.individuo[i + 1], 1)
        
        numeroLineas += 2
        self.hacer_linea(mapa, "almacen", "cliente", coordenadas_almacenes, coordenadas_clientes, 1, self.individuo[0], 1)
        self.hacer_linea(mapa, "cliente", "almacen", coordenadas_clientes, coordenadas_almacenes, self.individuo[-1], 1, 1)
        
        print(f"Se han agregado {numeroLineas} líneas al mapa")
        mapa.save(self.path_archivo_resultados_html)
        
        
    def agregar_convenciones(self, mapa):
        convenciones_html = """
        <div style="
            position: fixed; 
            bottom: 50px; left: 50px; width: 200px;
            background-color: rgba(255, 255, 255, 0.8); 
            border: 2px solid grey; 
            z-index:9999; 
            font-size:14px; 
            box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
            padding: 10px;">
            <b>Convenciones</b><br>
            <i style="color:orange;">&#9679;</i> Gas Car<br>
            <i style="color:blue;">&#9679;</i> Drone<br>
            <i style="color:green;">&#9679;</i> Electric Car<br>
        </div>
        """
        mapa.get_root().html.add_child(folium.Element(convenciones_html))


    def guardar_resultados_txt(self):
        with open(self.path_archivo_resultados_txt, "w", encoding="utf-8") as archivo:
            archivo.write("RECOMPENSA\n")
            distancia = 0
            for i in range(len(self.individuo) - 1):
                distancia += self.p.D_ij[0][self.individuo[i] - 1][self.individuo[i + 1] - 1]
            distancia += self.p.D_ai[0][0][self.individuo[0] - 1]
            distancia += self.p.D_ia[0][self.individuo[-1] - 1][0]
            archivo.write(f"Distancia total recorrida: {distancia}\n")
            archivo.write(f"Almacén 1 -> Cliente {self.individuo[0]}\n")
            for i in range(len(self.individuo) - 1):
                archivo.write(f"Cliente {self.individuo[i]} -> Cliente {self.individuo[i + 1]}\n")
            archivo.write(f"Cliente {self.individuo[-1]} -> Almacén 1\n")
            archivo.write("\n")



    def guardar_resultados_csv(self):
        with open(self.path_archivo_resultados_csv, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)

            # Escribir encabezado
            escritor.writerow(["idVehiculo", "tipoInicio", "numeroInicio", "tipoFin", "numeroFin"])
            escritor.writerow([1, "almacen", 1, "cliente", self.individuo[0]])
            for i in range(len(self.individuo) - 1):
                escritor.writerow([1, "cliente", self.individuo[i], "cliente", self.individuo[i + 1]])
            escritor.writerow([1, "cliente", self.individuo[-1], "almacen", 1])
            

