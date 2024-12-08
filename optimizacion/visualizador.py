import io
import math
import folium
import numpy as np
from pyomo.environ import value as pyomo_value
import csv

class Visualizador:
    def __init__(self, p, M):
        self.p = p
        self.M = M
        self.path_archivo_resultados_txt = self.p.rutaCarpeta + "resultados.txt"
        self.path_archivo_resultados_csv = self.p.rutaCarpeta + "resultados.csv"
        self.path_archivo_resultados_html = self.p.rutaCarpeta + "solucion.html"
        self.path_archivo_solucion = self.p.rutaCarpeta + "solucion.txt"
        self.visualizar()
        self.guardar_resultados_txt()
        self.guardar_resultados_csv()
        self.guardar_solucion()

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

    def visualizar(self):
        coordenadas_estaciones = [(i + 1, self.p.estaciones['Latitude'][i], self.p.estaciones['Longitude'][i]) for i in range(self.p.num_estaciones)]
        coordenadas_almacenes = [(i + 1, self.p.almacenes['Latitude'][i], self.p.almacenes['Longitude'][i]) for i in range(self.p.num_almacenes)]
        coordenadas_clientes = [(i + 1, self.p.clientes['Latitude'][i], self.p.clientes['Longitude'][i]) for i in range(self.p.num_clientes)]

        numeroLineas = 0
        centro = [4.6097, -74.0817]
        mapa = folium.Map(location=centro, zoom_start=13)

        # Agregar puntos al mapa
        for i, lat, lon in coordenadas_estaciones:
            folium.Marker(location=(lat, lon), tooltip=f"Estación {i}", icon=folium.Icon(color='blue')).add_to(mapa)

        for i, lat, lon in coordenadas_almacenes:
            folium.Marker(location=(lat, lon), tooltip=f"Almacén {i}", icon=folium.Icon(color='green')).add_to(mapa)

        for i, lat, lon in coordenadas_clientes:
            folium.Marker(location=(lat, lon), tooltip=f"Cliente {i}", icon=folium.Icon(color='red')).add_to(mapa)

        # Agregar convenciones al mapa
        self.agregar_convenciones(mapa)

        # Agregar rutas al mapa
        # X_aiv y Y_iav
        for a in self.M.A:
            for i in self.M.C:
                for v in self.M.V:
                    if self.M.X[a,i,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, "Almacén", "Cliente", coordenadas_almacenes, coordenadas_clientes, a, i, v)
                    if self.M.Y[i,a,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, "Cliente", "Almacén", coordenadas_clientes, coordenadas_almacenes, i, a, v)
                                
        # Z_ij
        for i in self.M.C:
            for j in self.M.C:
                for v in self.M.V:
                    if i != j and self.M.Z[i,j,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, "Cliente", "Cliente", coordenadas_clientes, coordenadas_clientes, i, j, v)

                        
        # W_ie y U_ei
        for i in self.M.C:
            for e in self.M.E:
                for v in self.M.V:
                    if self.M.W[i,e,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, "Cliente", "Estación", coordenadas_clientes, coordenadas_estaciones, i, e, v)
                    if self.M.U[e,i,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, "Estación", "Cliente", coordenadas_estaciones, coordenadas_clientes, e, i, v)

        # M_ef
        for e in self.M.E:
            for f in self.M.E:
                for v in self.M.V:
                    if e != f and self.M.M[e,f,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, "Estación", "Estación", coordenadas_estaciones, coordenadas_estaciones, e, f, v)

        # L_ea y H_ae
        for e in self.M.E:
            for a in self.M.A:
                for v in self.M.V:
                    if self.M.L[e,a,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, "Estación", "Almacén", coordenadas_estaciones, coordenadas_almacenes, e, a, v)
                    if self.M.H[a,e,v].value == 1:
                        numeroLineas += 1
                        self.hacer_linea(mapa, "Almacén", "Estación", coordenadas_almacenes, coordenadas_estaciones, a, e, v)
        
        print(f"Se han agregado {numeroLineas} líneas al mapa")
        mapa.save(self.path_archivo_resultados_html)

    def guardar_resultados_txt(self):
        with open(self.path_archivo_resultados_txt, "w", encoding="utf-8") as archivo:
            # Desglose de costos
            archivo.write("DESGLOSE DE COSTOS\n")
            archivo.write(f"Costo total: {pyomo_value(self.M.FO())} COP\n")
            archivo.write(f"Costo de carga diario: {pyomo_value(self.M.COSTO_CARGA_DIARIO())} COP\n")
            archivo.write(f"Costo de distancia diario: {pyomo_value(self.M.COSTO_DISTANCIA_DIARIO())} COP\n")
            archivo.write(f"Costo de tiempo diario: {pyomo_value(self.M.COSTO_TIEMPO_DIARIO())} COP\n")
            archivo.write(f"Costo de recarga diario: {pyomo_value(self.M.COSTO_RECARGA_DIARIO())} COP\n")
            archivo.write(f"- Costo de energía diario: {pyomo_value(self.M.COSTO_ENERGIA_DIARIO())} COP\n")
            archivo.write(f"- Costo de tiempo de recarga diario: {pyomo_value(self.M.COSTO_TIEMPO_ENERGIA_DIARIO())} COP\n")
            archivo.write(f"Costo de mantenimiento diario: {pyomo_value(self.M.COSTO_MANTENIMIENTO_DIARIO())} COP\n")

            # Rutas tomadas por los vehículos
            archivo.write("\nRUTAS TOMADAS POR LOS VEHÍCULOS")
            for v in self.M.V:
                capacidadAlmacen = np.zeros(self.p.num_productos)
                productosTransportados = np.zeros(self.p.num_productos)
                archivo.write(f"\nVEHÍCULO {v}:\n")
                # Salida del almacen (X_aiv y H_aev)
                for a in self.M.A:
                    for i in self.M.C:
                        if self.M.X[a,i,v]() == 1:
                            capacidadAlmacen = self.p.CAPACIDADES_PRODUCTOS_ALMACENES[:,a - 1]
                            productosTransportados += self.p.DEMANDAS[:,i - 1]
                            archivo.write(f"Almacén {a} -> Cliente {i}\n")
                    for e in self.M.E:
                        if self.M.H[a,e,v]() == 1:
                            archivo.write(f"Almacén {a} -> Estación {e}\n")

                # Recorrido entre clientes (Z_ijv)
                for i in self.M.C:
                    for j in self.M.C:
                        if i != j and self.M.Z[i,j,v]() == 1:
                            productosTransportados += self.p.DEMANDAS[:,j - 1]
                            archivo.write(f"Cliente {i} -> Cliente {j}\n")

                # Recorrido entre clientes y estaciones (W_iev y U_eiv)
                for i in self.M.C:
                    for e in self.M.E:
                        if self.M.W[i,e,v]() == 1:
                            archivo.write(f"Cliente {i} -> Estación {e}\n")
                        if self.M.U[e,i,v]() == 1:
                            productosTransportados += self.p.DEMANDAS[:,i - 1]
                            archivo.write(f"Estación {e} -> Cliente {i}\n")

                # Recorrido entre estaciones (M_efv)
                for e in self.M.E:
                    for f in self.M.E:
                        if e != f and self.M.M[e,f,v]() == 1:
                            archivo.write(f"Estación {e} -> Estación {f}\n")

                # Entrada al almacen (Y_iav y L_eav)
                for a in self.M.A:
                    for i in self.M.C:
                        if self.M.Y[i,a,v]() == 1:
                            archivo.write(f"Cliente {i} -> Almacén {a}\n")
                    for e in self.M.E:
                        if self.M.L[e,a,v]() == 1:
                            archivo.write(f"Estación {e} -> Almacén {a}\n")
                
                archivo.write(f"Productos transportados: {productosTransportados}\n")
                archivo.write(f"Capacidad del almacén: {capacidadAlmacen}\n")
                archivo.write("\n")



    def guardar_resultados_csv(self):
        with open(self.path_archivo_resultados_csv, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)

            # Escribir encabezado
            escritor.writerow(["idVehiculo", "tipoInicio", "numeroInicio", "tipoFin", "numeroFin"])

            for v in self.M.V:  # Iterar sobre los vehículos
                # Salida del almacén (X_aiv y H_aev)
                for a in self.M.A:
                    for i in self.M.C:
                        if self.M.X[a, i, v]() == 1:
                            escritor.writerow([v, "Almacén", a, "Cliente", i])
                    for e in self.M.E:
                        if self.M.H[a, e, v]() == 1:
                            escritor.writerow([v, "Almacén", a, "Estación", e])

                # Recorrido entre clientes (Z_ijv)
                for i in self.M.C:
                    for j in self.M.C:
                        if i != j and self.M.Z[i, j, v]() == 1:
                            escritor.writerow([v, "Cliente", i, "Cliente", j])

                # Recorrido entre clientes y estaciones (W_iev y U_eiv)
                for i in self.M.C:
                    for e in self.M.E:
                        if self.M.W[i, e, v]() == 1:
                            escritor.writerow([v, "Cliente", i, "Estación", e])
                        if self.M.U[e, i, v]() == 1:
                            escritor.writerow([v, "Estación", e, "Cliente", i])

                # Recorrido entre estaciones (M_efv)
                for e in self.M.E:
                    for f in self.M.E:
                        if e != f and self.M.M[e, f, v]() == 1:
                            escritor.writerow([v, "Estación", e, "Estación", f])

                # Entrada al almacén (Y_iav y L_eav)
                for a in self.M.A:
                    for i in self.M.C:
                        if self.M.Y[i, a, v]() == 1:
                            escritor.writerow([v, "Cliente", i, "Almacén", a])
                    for e in self.M.E:
                        if self.M.L[e, a, v]() == 1:
                            escritor.writerow([v, "Estación", e, "Almacén", a])

    def guardar_solucion(self):
        buffer = io.StringIO()
        self.M.display(ostream=buffer)
        contenido_display = buffer.getvalue()
        buffer.close()
        
        with open(self.path_archivo_solucion, "w", encoding="utf-8") as archivo:
            archivo.write(contenido_display)
