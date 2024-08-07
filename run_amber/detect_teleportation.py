#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import math
from argparse import ArgumentParser

import numpy as np
import pytraj as pt


class Residuum:
    def __init__(self, name, index, surrounding):
        self.name = name
        self.index = index
        self.surrounding = surrounding
        self.coordinates = []  # [line1, line2, line3,...]


class Distance:
    def __init__(self, residuum_name, residuum_index):
        self.residuum_name = residuum_name
        self.residuum_index = residuum_index
        self.distances = []  # ((atom, distance), (atom, distance),...)


class Protein:
    def __init__(self):
        self.all_residues = []


class Ligand:
    def __init__(self):
        self.protein1_all_residues = []
        self.protein2_all_residues = []
        self.ligand_surrounding = set([])
        self.ligand_double_residuum = set(
            [])  # dvojice residui ve dvou konformacich, kde alespon jedna splnuje podminku, ze je prilis blizko k ligandu
        self.result = []

        self.name = ''
        self.index = ''
        self.coordinations = []  # [line1, line2, line3,...]
        self.proteins = []

    def residue1_around_ligand(self):
        for res1 in self.protein1_all_residues:
            for p1 in res1.coordinates:
                for lig in self.coordinations:
                    # lig
                    # ATOM      1  C5  BEO d   1       1.585  -0.474   0.000  0.00  0.00      prod C
                    # protein
                    # ATOM      1  N   SER     1       3.513  18.672  -5.916  1.00  0.00           N
                    x = (float(p1[5]) - float(lig[6])) ** 2
                    y = (float(p1[6]) - float(lig[7])) ** 2
                    z = (float(p1[7]) - float(lig[8])) ** 2
                    distance = math.sqrt(x + y + z)
                    if distance < 3:
                        self.ligand_surrounding.add(res1)  # (res1.index, res1.name, p1, lig, distance))

    def residue2_around_ligand(self):
        for res2 in self.protein2_all_residues:
            for p1 in res2.coordinates:
                for lig in self.coordinations:
                    # lig
                    # ATOM      1  C5  BEO d   1       1.585  -0.474   0.000  0.00  0.00      prod C
                    # protein
                    # ATOM      1  N   SER     1       3.513  18.672  -5.916  1.00  0.00           N
                    x = (float(p1[5]) - float(lig[6])) ** 2
                    y = (float(p1[6]) - float(lig[7])) ** 2
                    z = (float(p1[7]) - float(lig[8])) ** 2
                    distance = math.sqrt(x + y + z)
                    if distance < 3:
                        self.ligand_surrounding.add(res2)  # (res2.index, res2.name, p1, lig, distance))

    # vytvori dvojice residuií ve dvou konformacích proteinu, aby se pak lepe pocitala vzdalenost
    def double_residuum_in_conformation(self):
        for res in self.ligand_surrounding:
            for res1 in self.protein1_all_residues:
                for res2 in self.protein2_all_residues:
                    if res.index == res1.index and res.index == res2.index:
                        self.ligand_double_residuum.add((res1, res2))

    def distance_for_double_R_and_ligand(self):
        residues = []
        for res1, res2 in self.ligand_double_residuum:
            distance = []
            for lig in self.coordinations:
                for p1, p2 in zip(res1.coordinates, res2.coordinates):
                    P = np.array([float(p1[5]), float(p1[6]), float(p1[7])])
                    Q = np.array([float(p2[5]), float(p2[6]), float(p2[7])])
                    R = np.array([float(lig[6]), float(lig[7]), float(lig[8])])
                    value = d(P, Q, R)
                    if points_in_cylinder(P, Q, 1, R):
                        distance.append((value, p1[2], p2[2], lig))
                        residues.append(res1.index)
            if res1.index in residues:
                print('\nTeleport')
                print(f'Residuum: {res1.index}')
                for value, atom1, atom2, lig1 in distance:
                    print(f'Distance: {value}A between residuum {atom1}-{atom2} and ligand {lig1[2]}')


def points_in_cylinder(pt1, pt2, r, q):
    vec = pt2 - pt1
    const = r * np.linalg.norm(vec)
    return (np.dot(q - pt1, vec) >= 0 and np.dot(q - pt2, vec) <= 0 and np.linalg.norm(np.cross(q - pt1, vec)) <= const)


def get_argument():
    parser = ArgumentParser()

    parser.add_argument("-protein1", help="Structure of protein in format pdb.")

    parser.add_argument("-protein2", help="Structure of protein in format pdb.")

    parser.add_argument("-ligand", help="Structure of ligand in format pdb.")

    return parser.parse_args()


def detect_residue_around_tunnel(protein):
    pdb = pt.load(protein)
    pdb_topology = pt.load_topology(protein)
    restraint_residue = []

    for i in range(1, pdb_topology.n_residues):
        string_index = f':{i} :FIL T'
        if pt.distance(pdb, string_index) < 12.0:
            restraint_residue.append(f'{int(pdb_topology.residue(i).index)}')
    string_residues = ' '.join([str(elem) for elem in restraint_residue])
    arr = string_residues.split()
    residues_array = [int(numeric_string) for numeric_string in arr]
    residuess = []
    for i in residues_array:
        ress = []
        for j in residues_array:
            if pt.distance(pdb, f':{i} :{j}') < 10.0 and i != j:
                ress.append(j)
        if len(ress) != 0:
            res = Residuum(pdb_topology.residue(i).name, i, ress)
            residuess.append(res)
    return residuess


def count_distance(protein, protein_in):
    for res in protein:
        with open(protein_in) as file_p1:
            for line in file_p1:
                if 'ATOM' in line:
                    line = line.strip('\n')
                    array = line.split(' ')
                    array = list(filter(None, array))
                    if array[3] != 'FIL' and res.index == int(array[4]):
                        res.coordinates.append(array)


def distance_res1_res2(protein1, protein2):
    array_distances = []
    for res1 in protein1:
        for res2 in protein2:
            if res1.index == res2.index:
                residuum_double = Distance(res1.name, res1.index)
                for p1, p2 in zip(res1.coordinates, res2.coordinates):
                    sum_distance = []
                    x = (float(p1[5]) - float(p2[5])) ** 2
                    y = (float(p1[6]) - float(p2[6])) ** 2
                    z = (float(p1[7]) - float(p2[7])) ** 2
                    distance = math.sqrt(x + y + z)
                    # if distance < 1:
                    sum_distance.append(distance)
                    residuum_double.distances.append(((p1[2]), sum_distance[0]))

                array_distances.append(residuum_double)

    for i in array_distances:
        print(i.distances, '\n')


def t(p, q, r):
    x = p - q
    return np.dot(r - q, x) / np.dot(x, x)


def d(p, q, r):
    return np.linalg.norm(t(p, q, r) * (p - q) + q - r)


def load_ligand(file_ligand):
    ligand = Ligand()
    with open(file_ligand) as file:
        for line in file:
            if 'ATOM' in line:
                line = line.strip('\n')
                array = line.split(' ')
                array = list(filter(None, array))
                ligand.coordinations.append(array)
    return ligand


def main():
    args = get_argument()
    ligand = load_ligand(args.ligand)

    ligand.protein1_all_residues = detect_residue_around_tunnel(args.protein1)
    ligand.protein2_all_residues = detect_residue_around_tunnel(args.protein2)
    count_distance(ligand.protein1_all_residues, args.protein1)
    count_distance(ligand.protein2_all_residues, args.protein2)
    # distance_res1_res2(ligand.protein1_all_residues, ligand.protein2_all_residues)

    # count_distance_ligand_res1_res2(ligand.protein1_all_residues, ligand.protein2_all_residues, ligand)

    ligand.residue1_around_ligand()
    ligand.residue2_around_ligand()

    ligand.double_residuum_in_conformation()
    ligand.distance_for_double_R_and_ligand()


if __name__ == '__main__':
    main()
