#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import os
import sys
from argparse import ArgumentParser
from spython.main import Client
from operator import itemgetter
from pathlib import Path
import subprocess
import operator
import parse_structures_from_caverdock as parse_cd
import shutil
import configparser
import logging
from time import localtime, strftime

LIGAND = 'BEO'
CPU = 2
RESULT_CD = 'result_CD'

# IN: protein, ligand, tunel,  traj in PDBQT format OR run CD and calculate PDBQT
# OUT: new pdbqt file with better energy of trajectory OR step of trajectory with bottleneck


class SpecialFormatter(logging.Formatter):
    FORMATS = {logging.DEBUG: logging._STYLES['{'][0]("DEBUG: {message}"),
               logging.ERROR: logging._STYLES['{'][0]("{module} : {lineno}: {message}"),
               logging.INFO: logging._STYLES['{'][0]("{message}"),
               'DEFAULT': logging._STYLES['{'][0](" {message}")}

    def format(self, record):
        # Ugly. Should be better
        self._style = self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT'])
        return logging.Formatter.format(self, record)

def get_argument():
    parser = ArgumentParser()

    parser.add_argument("-traj", help="trajectory from caverdock in format pdbqt ", type=Path)

    parser.add_argument("-protein", help="structure of protein in format pdb", type=Path)


    parser.add_argument("-CD_lb_ub", help="choose lb or ub ", choices=['lb', 'ub'],
                        dest= 'CD_lb_ub')

    parser.add_argument("-ligand", type=Path, required=True)

    parser.add_argument("-tunnel", type=Path, required=True)

    parser.add_argument("-results_dir", help="choose directory to save files",
                        metavar="DIR", dest="results_dir")

    return parser.parse_args()

def run_caverdock(protein, ligand, tunnel):
    # IN: protein, ligand, tunel
    # OUT: pdbqt file with lb and ub

    # mohlo by to být externě v dalším souboru
    try:
        Client.load('/home/petrahrozkova/Stažené/caverdock_1.1.sif')
        logging.INFO(f'Singularity for caverdock: /home/petrahrozkova/Stažené/caverdock_1.1.sif')

        Client.execute(['mpirun', '-np', str(CPU), 'caverdock',  '--config', 'caverdock.conf', '--out', str(RESULT_CD)])
        logging.INFO(f'mpirun -np {str(CPU)} caverdock  --config caverdock.conf --out {str(RESULT_CD)}')

        Client.execute(['cd-prepareconf.py', '-r', protein, '-l',  ligand, '-t', tunnel, '>', 'caverdock.conf'])
        logging.INFO(f'cd-prepareconf.py -r {protein} -l  {ligand} -t {tunnel} > caverdock.conf')

    except:
        logging.ERROR(f'mpirun -np {str(CPU)} caverdock  --config caverdock.conf --out {str(RESULT_CD)}')
        logging.ERROR(f'cd-prepareconf.py -r {protein} -l  {ligand} -t {tunnel} > caverdock.conf')
        logging.ERROR(f'Cannot run Caverdock or cd-preparconf.')

        print('Cannot run Caverdock or cd-preparconf.')
        sys.exit(1)

def check_config_file():
    if os.path.exists(f'{os.getcwd()}/config.ini'):
        return True
    else:
        print('Config file does not exist!')
    return False

#protein is pdb file WITHOUT ligand
def run_amber(protein, CD_lb_ub):
    # IN: struktura proteinu, ligand
    # OUT: nova struktura proteinu po minimalizaci

    # return optimal structure from amber -> emin5.pdb
    # directory_source, file_path to trajectories, protein
    #protein_pdb = f'./trajectories/{protein[0]/}'
    print('Check whether input protein is without ligand.')
    parse_cd.main('.', RESULT_CD, CD_lb_ub, '.pdbqt')
    logging.INFO(f'{os.getcwd()} {RESULT_CD}-{CD_lb_ub}.pdbqt {protein}')
    # run _11_run_tleap.sh
    # tun _21_run-mm_meta.sh
    try:
        subprocess.call(f'/home/petrahrozkova/Stažené/AmberTools20/amber20/bin/sander -O -i emin1.in '
                                   f'-o emin1.out -p complex.prmtop -c complex.inpcrd -ref ref.crd '
                                   f'-x mdcrd -r emin1.rst')
        logging.INFO(f'/home/petrahrozkova/Stažené/AmberTools20/amber20/bin/sander -O -i emin1.in '
                     f'-o emin1.out -p complex.prmtop -c complex.inpcrd -ref ref.crd '
                     f'-x mdcrd -r emin1.rst')
    except:
        logging.ERROR('Cannot run amber.')
        print('Cannot run amber.')
        #sys.exit(1)

    return 0

def run_cd_energy_profile(tunnel, traj):
    Client.load('/home/petrahrozkova/Stažené/caverdock_1.1.sif')
    Client.execute(['ls'])
    file = Client.execute(['cd-energyprofile','-d', os.getcwd() + '/' + tunnel.name, '-t', traj.name, '-s', str('0')])

    with open(f'{os.getcwd()}/energy.dat', 'w+') as file_energy_dat:
        file_energy_dat.write(file)

    if os.path.exists('energy.dat'):
        return 0
    else:
        print('energy.dat does not exist. Exit framework.')
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
                energy = float(line.split(' ')[3])
            num_str = line.split(' ')[1]
            num_str_energy.append((num_str, energy))
    num_str_energy.sort(key = operator.itemgetter(1), reverse = True)
    max_value = num_str_energy[0]

    return max_value

def find_strce_for_amber(strce_and_max):
    trajectories = os.listdir('../trajectories')
    for file in trajectories:
        if str(strce_and_max[0]) in file:
            return (file, strce_and_max[1])

    return 0

def remove_ligand_from_emin(protein):
    #  ted defaultne vypocitany emin5.pdb
    with open(protein) as oldfile, open('protein.pdb', 'w') as newfile:
        for line in oldfile:
            if not LIGAND in line:
                newfile.write(line)

def check_input_data():
    pass

def main():
    args = get_argument()
    print(f'Current working directory: {os.getcwd()}')
    print(f'Check whether protein is WITHOUT ligand.')
    config = configparser.ConfigParser()
    config.read(f'{os.getcwd()}/config.ini')
    if not check_config_file():
        sys.exit(1)

    hdlr = logging.FileHandler(
        f'framework_{strftime("%Y-%m-%d__%H-%M-%S", localtime())}.log')
    curr_dir = os.getcwd()
    logging.root.addHandler(hdlr)
    logging.root.setLevel(logging.INFO)
    logging.root.setLevel(logging.DEBUG)
    logging.info(f'***Output from framework*** {strftime("%Y-%m-%d__%H-%M-%S", localtime())} \n')
    logging.info(f'#Protein : {args.protein} \n')
    logging.info(f'#Ligand : {args.ligand} \n')
    logging.info(f'#Tunnel: {args.tunnel} \n')
    rslt_dir = args.results_dir
    if rslt_dir == '.':
        rslt_dir = os.getcwd()

    if not args.traj:
        run_caverdock(args.protein, args.ligand, args.tunnel)
        logging.info(f'#File from CaverDock: result_CD-{args.CD_lb_ub}.pdbq \n')
        args.traj = f'result_CD-{args.CD_lb_ub}.pdbqt'
        print('Run CD and create new traj pdbqt')

    remove_ligand_from_emin(args.protein) # rename file to protein.pdb and remove ligand if it is necessary

    run_cd_energy_profile(args.tunnel, args.traj)
    max_value_and_strctr = find_maximum_CD_curve(rslt_dir, args.CD_lb_ub)
    strcre_for_amber_energy = find_strce_for_amber(max_value_and_strctr)
    run_amber('protein.pdb', args.CD_lb_ub) # create new emin5.pdb with better structure

    shutil.move(f'./trajectories/{strcre_for_amber_energy[0]}/emin5.pdb', 'new_protein_from_amber.pdb')




if __name__ == '__main__':
    main()
