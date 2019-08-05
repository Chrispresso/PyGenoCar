from typing import List
from .individual import Individual
    

class Population(object):
    def __init__(self, individuals: List[Individual]):
        self.individuals = individuals

    @property
    def num_individuals(self):
        return len(self.individuals)

    @num_individuals.setter
    def num_individuals(self, val):
        raise Exception('Cannot set the number of individuals. You must change Population.individuals instead')

    @property
    def num_genes(self):
        return self.individuals[0].chromosome.shape[1]

    @num_genes.setter
    def num_genes(self, val):
        raise Exception('Cannot set the number of genes. You must change Population.individuals instead')

    @property
    def average_fitness(self):
        return sum(individual.fitness for individual in self.individuals) / float(self.num_individuals)

    @average_fitness.setter
    def average_fitness(self, val):
        raise Exception('Cannot set average fitness. This is a read-only property.')

    @property
    def fittest_individual(self) -> Individual:
        return max(self.individuals, key = lambda individual: individual.fitness, reverse=True)

    @fittest_individual.setter
    def fittest_individual(self, val) -> None:
        raise Exception('Cannot set fittest individual. This is a read-only property')
    