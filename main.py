from kivy.app import App
from kivy.clock import Clock
from kivy.properties import (
    ListProperty,
    NumericProperty,
)
from kivy.vector import Vector
from kivy.uix.widget import Widget
import random


POOL_SIZE = 30
GENOME_SIZE = 400
MAX_ACCELERATION = .5
MAX_SPEED = 5


class Krokets(App):
    frame_count = NumericProperty()

    def build(self):
        self.target = self.root.ids.target
        self.obstacle = self.root.ids.obstacle
        Clock.schedule_interval(self.update, 0)
        self.reset()

    def reset(self):
        self.population = None

    def update(self, *args):
        if not self.population:
            self.population = Population()

        self.population.update()
        self.frame_count += 1

        if self.frame_count > GENOME_SIZE:
            self.frame_count = 0
            self.population.new_generation()


class Population:
    def __init__(self):
        self.rockets = []

        for _ in range(POOL_SIZE):
            rocket = Rocket(
                center_x=app.root.center_x,
                center_y=app.root.height * .25,
            )
            self.rockets.append(rocket)
            app.root.add_widget(rocket)

    def update(self):
        for rocket in self.rockets:
            rocket.update()

    def reset(self):
        for rocket in self.rockets:
            app.root.remove_widget(rocket)

        self.rockets = []

    def calculate_fitness(self):
        for rocket in self.rockets:
            rocket.calculate_fitness()

        fitnesses = [rocket.fitness for rocket in self.rockets]
        total_fitness = sum(fitnesses)

        for rocket in self.rockets:
            rocket.fitness /= total_fitness

        new_fitnesses = [rocket.fitness for rocket in self.rockets]
        print('\n'.join('%d: %f' % item for item in enumerate(new_fitnesses)))
        print('Min: %f (%d)' % (min(new_fitnesses), new_fitnesses.index(min(new_fitnesses))))
        print('Avg: %f' % (sum(new_fitnesses) / POOL_SIZE))
        print('Max: %f (%d)' % (max(new_fitnesses), new_fitnesses.index(max(new_fitnesses))))

    def new_generation(self):
        self.calculate_fitness()

        self.mating_pool = []

        for _ in range(POOL_SIZE):
            selected = 0
            selector = random.random()

            while selector > 0:
                selector -= self.rockets[selected].fitness
                selected += 1

            selected -= 1
            self.mating_pool.append(self.rockets[selected].dna)
            print('Picked %d (%f)' % (selected, self.rockets[selected].fitness))

        mutation_rate = .1 if not all(
            rocket.crashed for rocket in self.rockets
        ) else .5
        print('Mutation rate: %f' % mutation_rate)
        self.reset()
        self.natural_selection(mutation_rate)

    def natural_selection(self, mutation_rate):
        mother, father = (random.choice(self.mating_pool) for _ in 'mf')

        for _ in range(POOL_SIZE):
            rocket = Rocket(
                dna=mother.crossover(father),
                center_x=app.root.center_x,
                center_y=app.root.height * .25,
            )
            rocket.dna.mutate(mutation_rate)
            self.rockets.append(rocket)
            app.root.add_widget(rocket)


class Rocket(Widget):
    velocity = ListProperty([0, 0])
    acceleration = ListProperty([0, 0])

    def __init__(self, dna=None, **kwargs):
        super(Rocket, self).__init__(**kwargs)
        if not dna:
            self.dna = DNA()
        else:
            self.dna = dna

        self.completed = False
        self.crashed = False

    def apply_force(self, force):
        self.acceleration = force + self.acceleration

    def update(self):
        distance = Vector(self.center).distance(app.target.center)

        if distance < app.target.width / 2.:
            self.completed = True
            self.center = app.target.center

        if(
            (
                app.obstacle.x < self.center_x < app.obstacle.right and
                app.obstacle.y < self.center_y < app.obstacle.top
            ) or (
                self.center_x < 0 or self.center_x > app.root.width or
                self.center_y < 0 or self.center_y > app.root.height
            )
        ):
            self.crashed = True

        if self.completed or self.crashed:
            return

        if app.frame_count < GENOME_SIZE:
            self.apply_force(self.dna.genes[app.frame_count])

        self.velocity = Vector(self.velocity) + self.acceleration
        if Vector(self.velocity).length() > MAX_SPEED:
            self.velocity = Vector(self.velocity).normalize() * MAX_SPEED
        self.pos = Vector(self.velocity) + self.pos
        self.acceleration = [0, 0]

    def calculate_fitness(self):
        distance = Vector(self.center).distance(app.target.center)
        max_distance = app.root.width
        self.fitness = max(0, max_distance - distance)

        if self.completed:
            self.fitness *= 5

        if self.crashed:
            self.fitness *= .2


class DNA:
    def __init__(self, genome=None):
        if genome:
            self.genes = genome
        else:
            self.genes = []
            for _ in range(GENOME_SIZE):
                self.genes.append(
                    Vector((
                        random.random() * 2 * MAX_ACCELERATION
                        - MAX_ACCELERATION
                        for _ in 'xy'
                    ))
                )

    def __iter__(self):
        return iter(self.genes)

    def __eq__(self, other):
        try:
            genes = iter(other)
        except TypeError:
            return False

        return list(genes) == self.genes

    def crossover(self, dna):
        genome = []
        midpoint = random.randrange(0, GENOME_SIZE)

        for index, (mother, father) in enumerate(zip(self, dna)):
            if index < midpoint:
                genome.append(mother)
            else:
                genome.append(father)

        return DNA(genome)

    def mutate(self, rate):
        for index, gene in enumerate(self.genes[:]):
            if random.random() < rate:
                self.genes[index] = Vector((
                    gene.x + random.gauss(0, .2 * MAX_ACCELERATION),
                    gene.y + random.gauss(0, .2 * MAX_ACCELERATION),
                ))


app = Krokets()

if __name__ == '__main__':
    app.run()
