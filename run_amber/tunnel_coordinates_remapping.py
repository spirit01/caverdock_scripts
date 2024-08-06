#!/usr/bin/env python
"""
This code was developed with the assistance of the ChatGPT model from OpenAI.
The ChatGPT model was used for consultations and ideas during the creation of this project.
"""

import math
from argparse import ArgumentParser
import sys
import re
from pathlib import Path
import numpy as np
import re
import pandas as pd
import matplotlib.pyplot as plt



class POINT:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f"{self.x} {self.y} {self.z}"


class Model:
    def __init__(self, number, model_string):
        self.model_string = model_string.strip()
        self.drag_atoms = find_drag_atom(self.model_string)
        self.number = number
        self.drag_atom = None
        self.energy_lb = 0


class Circle:
    def __init__(self, center, normal, radius, disc, dist_from_SP):
        self.disc = disc
        self.center = np.array(center)
        self.normal = np.array(normal)
        self.radius = radius
        self.closest_point = None
        self.models = []
        self.distance = 100 #distance to the model
        self.dist_from_SP = dist_from_SP # distance from starting point in the tunnel (x array in graph)

    def has_model(self):
        #return isinstance(self.models, Model) if self.models else False
        if len(self.models) == 0:
            return False
        else:
            return True

    def __eq__(self, other):
        """Porovnávání podle hodnoty atributu disc."""
        if not isinstance(other, Circle):
            return NotImplemented
        return self.disc == other.disc

    def get_projected_point(self, X):
        if not isinstance(X, POINT):
            raise ValueError("Argument X must be of type POINT")

        X_np = np.array([X.x, X.y, X.z])
        t = -np.dot(self.normal, X_np) - self.radius / np.dot(self.normal, self.normal)
        Y_np = X_np + t * self.normal
        self.closest_point = POINT(Y_np[0], Y_np[1], Y_np[2])
        return Y_np[0], Y_np[1], Y_np[2]



class TUNNEL:
    def __init__(self, name, output):
        self.name = name
        self.output = output
        self.circles = []  # Seznam kruhových rovin
        self.model_array = []

    def count_distance(self, center, normal, last, dist):

        #last = []
        #center = [float(array[0]), float(array[1]), float(array[2])]
        #normal = [float(array[3]), float(array[4]), float(array[5])]
        if len(last) != 0:
            # compute distance between plate of current disc and center of previous disc
            d = - center[0] * normal[0] - center[1] * normal[1] - center[2] * normal[2]
            t = -(normal[0] * last[0] + normal[1] * last[1] + normal[2] * last[2] + d) / (
                    normal[0] * normal[0] + normal[1] * normal[1] + normal[2] * normal[2])
            dist += abs(t)
            last = center
        else:
            last = center

        return dist, last

    def load_tunnel_with_circles(self):
        with open(self.name) as file:
            previous_disc = []
            distance = 0
            for disc, line in enumerate(file):
                if line.strip() and not line.startswith("#"):
                    line = line.strip('\n')
                    array = line.split(' ')
                    array = list(map(float, array))
                    center = np.array(array[:3])
                    normal = np.array(array[3:6])
                    radius = array[-1]
                    #print(center, previous_disc)
                    distance, previous_disc = self.count_distance(center, normal, previous_disc, distance)
                    # Vytvoření kruhové roviny pro každý bod
                    circle = Circle(center, normal, radius, disc, distance)
                    self.circles.append(circle)

    # TODO: nejblizsi kruh ke kazdemu modelu, zajisti spojitost
    def get_closest_circle_to_models(self):
        for model in self.model_array:
            min_distance = 10
            model.drag_atom = find_drag_atom(model.model_string)
            model.energy_lb = find_lb(model.model_string)

            distances = []
            for circle in self.circles:
               # xyz = circle.get_projected_point(model.drag_atom)
                distance_to_center = np.linalg.norm(np.array([model.drag_atom.x,
                                                              model.drag_atom.y,
                                                              model.drag_atom.z]) - circle.center)
                candidate_distance = distance_to_center - circle.radius
                # print(circle.center, model.model_string, candidate_distance)
                distances.append((candidate_distance, model, circle))
            distance = min(distances)
            for circle in self.circles:
                if circle == distance[2]:
                    circle.models.append(distance[1])
                    #print(circle.disc)

    # TODO: pro neobsazene kruhy najde nejblizsi model, jinak se bude pouzivat nejlizsi kruh k model(opacny loop)
    def get_closest_model_to_circles(self):  # pocita pouze vzdalenost bodu od středu, nehleda bod přímo na kružnici
        for circle in self.circles:
            # todo: tady pridat podmonku testovani prazdnosti disku
            min_distance = 100
            if not circle.has_model():
                for model in self.model_array:
                    model.drag_atom = find_drag_atom(model.model_string)
                    model.energy_lb = find_lb(model.model_string)

                    distance_to_center = np.linalg.norm(np.array([model.drag_atom.x,
                                                                  model.drag_atom.y,
                                                                  model.drag_atom.z]) - circle.center)
                    distance = distance_to_center - circle.radius
                    if distance < min_distance:
                        min_distance = distance
                        circle.models = [model]
                       # print(circle.disc)

    def print_model_for_final_trajectory(self):
        with open(self.output, 'w') as file:
            for circle in self.circles:
                for model in circle.models:
                    model.model_string = replace_tunnel_value(model.model_string, circle.disc)
                    file.write(f'{model.model_string} \n')


    def print_graph(self):
        discs = []
        energy_lb = []
        distances = []

        for circle in self.circles:
            for model in circle.models:
                m = model.model_string.split()
                discs.append(circle.disc)
                energy_lb.append(model.energy_lb)
                distances.append(circle.dist_from_SP)
               # print(circle.disc, model.energy_lb, circle.dist_from_SP)
        energy_dat = {'distance': distances, 'discs': discs, 'E_lb': energy_lb}
        df = pd.DataFrame(energy_dat, index=[discs])

        df = pd.DataFrame(energy_dat, discs)
        df.round(3)
        df.plot(kind='scatter', x ='distance', y='E_lb')
        plt.xlabel('Trajectory [Å]')
        plt.ylabel('Binding energy [kcal/mol]')
        print(df)
      #  plt.show()

        name = self.name.split('.')[0]
        plt.savefig(f'graph.png')
        df.to_csv(f'{self.output}.csv', sep='\t', encoding='utf-8', index=False)

def get_argument():
    parser = ArgumentParser()

    # parser.add_argument("--tunnel_original", "-t_orig", help="Tunnel pdb", required=True)

    parser.add_argument("--tunnel_new", "-t_new", help="Tunnel pdb", required=True)

    parser.add_argument("--trajectory", "-pdbqt", help="Output from CaverDock in pdbqt file", required=True)

    parser.add_argument("--output", "-o", default='result_remapping.pdbqt', help="New remapping trajectory "
                                                                           "pdbqt file")

    return parser.parse_args()


def find_drag_atom(string):
    m = string.split()
    tunnel_index = m.index('ATOM')
    x = float(m[tunnel_index + 6])
    y = float(m[tunnel_index + 7])
    z = float(m[tunnel_index + 8])
    point = POINT(x, y, z)
    # print(point)
    return point

def find_lb(string):
    m = string.split()
    number = m.index('TUNNEL:')
    lb = float(m[number + 2])
    return lb

def find_disc(string):
    tunnel_index = string.index('TUNNEL:')
    disc_number = string[tunnel_index + 1]
    return int(disc_number)

""" nepouzivane, mozno odstranit po overeni funkcnosti druhe funkce
def parse_structures(file_name: str):
    file_string = Path(file_name).read_text()
    file_all = re.findall('MODEL.*?ENDMDL', file_string, re.DOTALL)
    file_all = [i.replace('ENDMDL', ' ') for i in file_all]
    return file_all
"""


def parse_structures(file_name: str):
    file_string = Path(file_name).read_text()
    file_models = re.findall('MODEL.*?ENDMDL', file_string, re.DOTALL)
    models = []
    for model_string in file_models:
        m = model_string.split()
        model_number = find_disc(m)
        model_instance = Model(model_number, model_string)  # model_string.replace('ENDMDL', ''))
        models.append(model_instance)

    return models





def replace_tunnel_value(text, new_value):
    # Rozdělení textu na řádky
    lines = text.split('\n')
    # Nalezení řádku obsahujícího "TUNNEL" a jeho nahrazení novou hodnotou
    for i, line in enumerate(lines):
        if "REMARK CAVERDOCK TUNNEL:" in line:
            # Nahrazení prvního čísla za "TUNNEL" novou hodnotou
            numbers = re.findall(r"[-+]?\d*\.\d+|\d+", line)
            replaced_line = re.sub(r"[-+]?\d*\.\d+|\d+", str(new_value), line, count=1)
            lines[i] = replaced_line
            break  # Řádek byl nalezen, takže můžeme ukončit hledání

    # Spojení upravených řádků zpět do jednoho textového řetězce
    modified_text = '\n'.join(lines)
    return modified_text


def find_radius(string):
    number = string.index('TUNNEL:')
    radius = string[number + 3]
    return radius


def main():
    args = get_argument()

    tunnel_new = TUNNEL(args.tunnel_new, args.output)
    tunnel_new.load_tunnel_with_circles()

    tunnel_new.model_array = parse_structures(args.trajectory)

    tunnel_new.get_closest_circle_to_models()
    tunnel_new.print_graph()

    tunnel_new.get_closest_model_to_circles() #doplni praznde circle

    tunnel_new.print_model_for_final_trajectory()
    #tunnel_new.todo_print_model_for_final_trajectory()
    tunnel_new.print_graph()


if __name__ == '__main__':
    main()
