#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import os
import sys
from argparse import ArgumentParser
from spython.main import Client
from operator import itemgetter
from pathlib import Path
import subprocess



# IN: protein, ligand, tunel OR pdbqt file from CD, ligand, tunel
# OUT: new pdbqt file with better energy of trajectory OR step of trajectory with bottleneck


def get_argument():
    parser = ArgumentParser()

    parser.add_argument("-protein", help="protein.pdb or result_cd.pdbqt file ", type=Path)

    parser.add_argument("-CD_lb_ub", help="choose lb or ub ", choices=['lb', 'ub'],
                        dest= 'CD_lb_ub')

    parser.add_argument("-ligand", type=Path, required=True)

    parser.add_argument("-tunnel", type=Path, required=True)

    parser.add_argument("-results_dir", help="choose directory to save files",
                        metavar="DIR", dest="results_dir")

    return parser.parse_args()


def choose_step_from_pdbqt():
    # INPUT: pdbqt soubor
    # OUTPUT: složka s strukturou, která má v CD nejvyšší energii
    pass

def run_caverdock():
    # IN: protein, ligand, tunel
    # OUT: pdbqt lb a ub

    # mohlo by to být externě v dalším souboru
    #return ub pdbqt a lb pdbqt
    pass

def run_amber(protein):
    # IN: struktura proteinu, ligand
    # OUT: nova struktura proteinu po minimalizaci

    # mohlo by to být externě v dalším souboru
    # return optimalizovaná struktura z maxima
    pass

def run_cd_energy_profile(tunnel, protein):
    if 'pdbqt' in protein.name:
        Client.load('/home/petrahrozkova/Stažené/caverdock_1.1.sif')
        Client.execute(['ls'])
        file = Client.execute(['cd-energyprofile','-d', os.getcwd() + '/' + tunnel.name, '-t', protein.name, '-s', str('0')])

        with open(f'{os.getcwd()}/energy.dat', 'w+') as file_energy_dat:
            file_energy_dat.write(file)
    else:
        print('Run CD first.')

    if os.path.exists('energy.dat'):
        return 0
    else:
        print('energy.dat is not exist. Exit framework.')
        sys.exit(1)



def find_maximum_CD_curve(result_cd, ub_lb):
    # IN: pdbqt soubor
    # OUT: konkrétní snapchot proteinu s maximální energií

    # najít maximum na pdqt křivce, a vrátit strukturu, která odpovídá maximum a
    # na tu pustit amber
    # nejprve testova na hotově pdbqt křivce. Buď lze dát hotovou křivku
    # nebo si to nechat spošítat znovu


    num_str_energy = []
    with open(f'energy.dat') as file_energy:
        file_energy.readline()
        for line in file_energy:
            if ub_lb == 'lb':
                energy = float(line.split(' ')[5].strip())
            if ub_lb == 'ub':
                energy = int(line.split(' ')[3])
            num_str = line.split(' ')[1]
            num_str_energy.append((num_str, energy))

    max_value = max(num_str_energy,key=itemgetter(1))[1]

    return max_value

def find_strce_for_amber(strce_and_max):

    trajectories = os.listid('trajectories')
    for file in trajectories:
        if strce_and_max[0] in file:
            return file

def check_input_data():
    pass




def main():
    args = get_argument()
    print(f'Current working directory: {os.getcwd()}')
    curr_dir = os.getcwd()
    rslt_dir = args.results_dir
    if rslt_dir == '.':
        rslt_dir = os.getcwd()

    run_cd_energy_profile(args.tunnel, args.protein)
    find_maximum_CD_curve(rslt_dir, args.CD_lb_ub)
    max_value_and_strctr = find_maximum_CD_curve(rslt_dir, args.CD_lb_ub)

    strcre_for_amber = find_strce_for_amber(max_value_and_strctr)
    new_strcture = run_amber(max_value_and_strctr)



    #os.chdir(path)



if __name__ == '__main__':
    main()
