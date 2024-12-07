
# README del Proyecto de Optimización

Este repositorio contiene los archivos y herramientas necesarias para la implementación, análisis y resolución del modelo matemático planteado, así como las soluciones a los casos propuestos. A continuación, se describe la estructura del repositorio y la funcionalidad de cada componente.

---

## Estructura del Repositorio

### Carpeta `docs`

Esta carpeta incluye toda la documentación relacionada con el modelo matemático planteado, así como las soluciones obtenidas para los casos presentados. Los documentos en esta carpeta explican el enfoque, las formulaciones matemáticas y los resultados obtenidos.

---

### Carpeta `optimizacion`

#### Contenido:

1. **`cargadorDeParametros.py`**  
   - Este script contiene las funcionalidades necesarias para la carga y cálculo de todos los parámetros asociados a los casos definidos por el usuario.  
   - Su propósito es automatizar y facilitar el manejo de los datos necesarios para alimentar el modelo matemático.

2. **`visualizador.py`**  
   - Permite generar los archivos de visualización correspondientes a las soluciones obtenidas.  
   - Entre los formatos generados se encuentran:
     - Mapas interactivos (`.html`).
     - Tablas y resúmenes en texto y CSV.

3. **`modelo.py`**  
   - Este es el archivo principal de la aplicación. Contiene la lógica para:
     - Cargar los parámetros definidos en `cargadorDeParametros.py`.
     - Resolver el modelo matemático utilizando los datos cargados.
     - Generar y visualizar las respuestas obtenidas.

4. **`modelo_sin_subtoures.py`**  
   - Similar a `modelo.py`, pero con una modificación clave: incluye la restricción de Miller-Tucker-Zemlin (MTZ) para prohibir subtoures en las soluciones.  
   - Se utiliza para resolver variantes del problema en las que se requiere esta restricción adicional.

---

### Carpeta `optimizacion/Proyecto Seneca Libre`

#### Estructura y Contenido:

- Dentro de esta carpeta, hay subcarpetas específicas para cada caso presentado.  
  - Cada subcarpeta contiene los archivos fuente proporcionados por **SenecaLibre**, junto con los resultados y visualizaciones generados por el modelo.

#### Archivos en cada subcarpeta:

1. **`solucion.html`**  
   - Mapa interactivo que representa gráficamente la solución propuesta.  
   - Facilita la comprensión visual de las rutas obtenidas.

2. **`solucion.txt`**  
   - Presenta la solución en el formato de salida estándar de **Pyomo**, detallando las variables de decisión y valores obtenidos.

3. **`resultados.txt`**  
   - Un resumen en formato texto que incluye los datos más relevantes de la solución, como los costos, tiempos y rutas.

4. **`resultados.csv`**  
   - Tabla en formato CSV que detalla las rutas obtenidas, incluyendo la información sobre nodos y distancias recorridas.

---

## Uso del Proyecto

1. **Resolver el modelo:**  
   - Utilizar `modelo.py` para resolver el modelo sin restricciones de subtoures.  
   - Si se requiere la restricción MTZ, ejecutar `modelo_sin_subtoures.py`.


---

## Requisitos

- **Python 3.x**  
- Bibliotecas necesarias:
  - `Pyomo`
  - `Pandas`
  - `Folium` 

---


## Autoría

Este proyecto fue desarrollado como parte de un análisis y resolución de problemas de optimización planteados por **SenecaLibre**.
Desarrollado por Daniel Diaz y Sara Cárdenas

--- 

