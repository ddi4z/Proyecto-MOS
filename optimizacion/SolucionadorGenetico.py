import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys
import random

sys.path.append('optimizacion/')
from cargadorDeParametros import CargadorDeParametros
from VisualizadorGenetico import VisualizadorGenetico


class SolucionadorGenetico:
    """
    Clase que permite resolver el problema de VRP usando un algoritmo genético 
    para un solo vehículo y un solo almacén.
    """
    def __init__(self):
        self.p = CargadorDeParametros()

    def generate_population(self, size):
        """
        Genera una población inicial de un tamaño dado.

        Parámetros:
        size: int, tamaño de la población.

        Retorna:
        list, población generada.
        """
        return [
            random.sample(range(1, self.p.num_clientes + 1), self.p.num_clientes)
            for _ in range(size)
        ]

    def reward(self, individual):
        """
        Calcula la recompensa asociada a un individuo, basada en la distancia total recorrida.

        Parámetros:
        individual: list, individuo a evaluar.

        Retorna:
        float, recompensa asociada al individuo.
        """
        total_distance = 0
        for i in range(len(individual) - 1):
            total_distance += self.p.D_ij[0][individual[i] - 1][individual[i + 1] - 1]

        total_distance += self.p.D_ai[0][0][individual[0] - 1]
        total_distance += self.p.D_ia[0][individual[-1] - 1][0]

        return -total_distance

    def crossover(self, parent1, parent2):
        """
        Cruza dos individuos para generar dos hijos nuevos utilizando AEX.

        Parámetros:
        parent1, parent2: list, padres.

        Retorna:
        tuple, dos hijos generados.
        """
        def generate_child(start_node, nextP1, nextP2):
            child = []
            visited = set()
            current = start_node

            while len(child) < len(parent1):
                child.append(current)
                visited.add(current)

                if len(child) % 2 == 1:
                    current = nextP1.get(current)
                else:
                    current = nextP2.get(current)

                if current in visited or current is None:
                    for node in range(1, len(parent1) + 1):
                        if node not in visited:
                            current = node
                            break

            return child

        nextParent1 = {parent1[i]: parent1[i + 1] for i in range(len(parent1) - 1)}
        nextParent2 = {parent2[i]: parent2[i + 1] for i in range(len(parent2) - 1)}

        child1 = generate_child(parent1[0], nextParent1, nextParent2)
        child2 = generate_child(parent2[0], nextParent1, nextParent2)

        return child1, child2

    def mutate(self, individual, mutation_rate):
        """
        Muta un individuo intercambiando dos genes aleatorios con una probabilidad dada.

        Parámetros:
        individual: list, individuo a mutar.
        mutation_rate: float, probabilidad de mutación.
        """
        if random.random() < mutation_rate:
            i, j = random.sample(range(len(individual)), 2)
            individual[i], individual[j] = individual[j], individual[i]

    def select(self, population, fitnesses):
        """
        Selecciona dos individuos de la población usando selección aleatoria.

        Parámetros:
        population: list, población actual.
        fitnesses: list, recompensas de la población.

        Retorna:
        list, dos individuos seleccionados.
        """
        fitnessPositivo = [f - min(fitnesses) + 10 for f in fitnesses]
        selected = random.choices(population, weights=fitnessPositivo, k=2)
        return selected

    def evolve(self, population):
        """
        Evoluciona la población durante un número de generaciones dado.

        Parámetros:
        population: list, población inicial.

        Retorna:
        tuple, mejor individuo y su recompensa.
        """
        generations = 1000
        best_individual = None
        best_fitness = -float('inf')

        for generation in range(generations):
            print(f"Generación {generation}")
            fitnesses = [self.reward(ind) for ind in population]

            new_population = []
            for _ in range(len(population) // 2):
                parent1, parent2 = self.select(population, fitnesses)
                if random.random() < 0.8:
                    child1, child2 = self.crossover(parent1, parent2)
                else:
                    child1, child2 = parent1, parent2

                self.mutate(child1, 0.01)
                self.mutate(child2, 0.01)
                new_population.extend([child1, child2])

            population = sorted(new_population, key=self.reward, reverse=True)[:len(population)]

            if self.reward(population[0]) > best_fitness:
                best_individual = population[0]
                best_fitness = self.reward(best_individual)
            print("Mejor individuo encontrado:", population[0])
            print("Recompensa:", self.reward(population[0]))

        print("Mejor individuo encontrado:", best_individual)
        return best_individual, best_fitness


if __name__ == "__main__":
    s = SolucionadorGenetico()
    print("Generando población...")
    population = s.generate_population(100)
    print("Evolucionando...")
    best_individual, best_reward = s.evolve(population)
    print("Mejor solución:", best_individual)
    print("Recompensa:", best_reward)
    v = VisualizadorGenetico(s.p, best_individual)
    
