from abc import abstractmethod
from typing import Optional, Union
import numpy as np

class Individual(object):
    def __init__(self):
        pass

    @abstractmethod
    def calculate_fitness(self):
        raise Exception('calculate_fitness function must be defined')

    @property
    @abstractmethod
    def fitness(self):
        raise Exception('fitness property must be defined')

    @fitness.setter
    @abstractmethod
    def fitness(self, val):
        raise Exception('fitness property cannot be set. Use calculate_fitness instead')


    @abstractmethod
    def encode_chromosome(self):
        raise Exception('encode_chromosome function must be defined')

    @abstractmethod
    def decode_chromosome(self):
        raise Exception('decode_chromosome function must be defined')

    @property
    @abstractmethod
    def chromosome(self):
        raise Exception('chromosome property must be defined')

    @chromosome.setter
    def chromosome(self, val):
        raise Exception('chromosome property cannot be set.')

    def __sub__(self, other: Union['Individual', np.ndarray]) -> np.ndarray:
        p1_chromosome = self.chromosome
        p2_chromosome = None
        if isinstance(other, Individual):
            p2_chromosome = other.chromosome
        elif isinstance(other, np.ndarray):
            p2_chromosome = other
        
        child_chromosome = p1_chromosome - p2_chromosome

        return child_chromosome

    def __add__(self, other: Union['Individual', np.ndarray]) -> np.ndarray:
        p1_chromosome = self.chromosome
        p2_chromosome = None
        if isinstance(other, Individual):
            p2_chromosome = other.chromosome
        elif isinstance(other, np.ndarray):
            p2_chromosome = other
        
        child_chromosome = p1_chromosome + p2_chromosome

        return child_chromosome