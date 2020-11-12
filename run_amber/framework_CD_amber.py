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

    parser.add_argument("-traj", help="Trajectory from caverdock in format pdbqt.", type=Path)

    parser.add_argument("-protein", help="Structure of protein in format pdb.", type=Path)


    parser.add_argument("-CD_lb_ub", help="Choose lb or ub. ", choices=['lb', 'ub'],
                        dest= 'CD_lb_ub')

    parser.add_argument("-ligand", help = 'Ligands name in pdbqt format.', type=Path, required=True)

    parser.add_argument("-tunnel", help = 'Tunnel name in dsd format.', type=Path, required=True)

    parser.add_argument("-config", help = 'Location config.ini file.', type=Path, required=True)

    parser.add_argument("-results_dir", help="Choose directory to save files.",
                        metavar="DIR", dest="results_dir")

    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                       dest="verbose", action = "store_true")

    return parser.parse_args()

def run_caverdock(ligand, tunnel, configfile, verbose):
    # IN: protein, ligand, tunel
    # OUT: pdbqt file with lb and ub

    # mohlo by to být externě v dalším souboru
    prepare_conf = ''

    if int(configfile["SINGULARITY"]["value"]) == 1:
        singularity = Client.load(str(configfile["SINGULARITY"]["singularity"]))
        logging.info(f'Singularity for caverdock: {configfile["SINGULARITY"]["singularity"]} \n')
        logging.info(f'Message from singularity: \n {singularity}')
        if verbose:
            print(f'Singularity for caverdock: {configfile["SINGULARITY"]["singularity"]} \n')
            print(f'Message from singularity: \n {singularity} \n')
        prepare_conf = Client.execute([configfile["CD-PREPARECONF"]["path_cd-prepareconf"], '-r', 'protein.pdbqt', '-l',
                                       str(ligand), '-t', str(tunnel)])
        with open('caverdock.conf', 'w+') as file_conf:
            file_conf.write(prepare_conf)
        if not os.path.isfile('caverdock.conf'):
            logging.error(f'cd-prepareconf -r protein.pdbqt -l  {ligand} -t {tunnel} > caverdock.conf')
            logging.error(f'Message from cd-prepareconf: \n {prepare_conf}')
            if verbose:
                print(f'ERROR: {configfile["CD-PREPARECONF"]["path_cd-prepareconf"]} -r protein.pdbqt -l  {ligand} -t {tunnel} > caverdock.conf')
                print(f'ERROR: Message from cd-prepareconf: \n {prepare_conf}')
            sys.exit(1)

    else:
        subprocess.call(f'{configfile["CD-PREPARECONF"]["path_cd-prepareconf"]} -r protein.pdbqt -l  {ligand} -t {tunnel} > caverdock.conf', shell=True)
        logging.info(f'cd-prepareconf -r protein.pdbqt -l  {ligand} -t {tunnel} > caverdock.conf')
        #logging.info(f'Message from cd-prepareconf: \n {prepare_conf}')
        if verbose:
            print(f'{configfile["CD-PREPARECONF"]["path_cd-prepareconf"]} -r protein.pdbqt -l  {ligand} -t {tunnel} > caverdock.conf')
            #print(f'Message from cd-prepareconf: \n {prepare_conf}')

        if not os.path.isfile('caverdock.conf'):
            logging.error(f'cd-prepareconf -r protein.pdbqt -l  {ligand} -t {tunnel} > caverdock.conf')
            #logging.error(f'Message from cd-prepareconf: \n {prepare_conf}')
            if verbose:
                print(f'ERROR: {configfile["CD-PREPARECONF"]["path_cd-prepareconf"]} -r protein.pdbqt -l  {ligand} -t {tunnel} > caverdock.conf')
                #print(f'ERROR: Message from cd-prepareconf: \n {prepare_conf}')
            sys.exit(1)


    if int(configfile["SINGULARITY"]["value"]) == 1:
        mpirun = Client.execute(['mpirun', '-np', str(CPU), 'caverdock',
                                 '--config', 'caverdock.conf', '--out', str(RESULT_CD)])

    else:
        subprocess.call(f'/usr/bin/mpirun.mpich -np {str(CPU)} {configfile["CAVERDOCK"]["path_caverdock"]}  --config caverdock.conf --out {str(RESULT_CD)}', shell=True)

    logging.info(f'mpirun -np {str(CPU)} caverdock  --config caverdock.conf --out {str(RESULT_CD)}')
    logging.info(f'Message from mpirun: \n {mpirun}')
    if verbose:
        print(f'mpirun -np {str(CPU)} caverdock  --config caverdock.conf --out {str(RESULT_CD)}')
        print(f'Message from mpirun: \n {mpirun}')

    if not os.path.isfile(f'{RESULT_CD}-lb.pdbqt') or os.path.isfile(f'{RESULT_CD}-ub.pdbqt'):
        logging.error(f'mpirun -np {str(CPU)} caverdock  --config caverdock.conf --out {str(RESULT_CD)}')
        logging.error(f'Message from mpirun: \n {mpirun}')
        if verbose:
            print(f'ERROR: mpirun -np {str(CPU)} caverdock  --config caverdock.conf --out {str(RESULT_CD)}')
            print(f'ERROR: Message from mpirun: \n {mpirun}')
        sys.exit(1)

def check_config_file(config, verbose):
    if verbose:
        print(f'{config}')
    if os.path.exists(f'{config}'):
        return True
    else:
        print('Config.ini file does not exist!')
    return False

#protein is pdb file WITHOUT ligand
def run_amber(protein, CD_lb_ub, verbose, configfile):
    # IN: struktura proteinu, ligand
    # OUT: nova struktura proteinu po minimalizaci

    # return optimal structure from amber -> emin5.pdb
    # directory_source, file_path to trajectories, protein
    #protein_pdb = f'./trajectories/{protein[0]/}'
    print('Check whether input protein is without ligand.')
   # parse_cd.main('.', RESULT_CD, CD_lb_ub, '.pdbqt')
    logging.info(f'{os.getcwd()} {RESULT_CD}-{CD_lb_ub}.pdbqt {protein}')
    if verbose:
        print(f'{(configfile["SANDER"]["path_sander"])} -O -i emin1.in '
              f'-o emin1.out -p complex.prmtop -c complex.inpcrd -ref ref.crd '
              f'-x mdcrd -r emin1.rst')
    # run _11_run_tleap.sh
    # tun _21_run-mm_meta.sh

    try:
        subprocess.call(f'{configfile["SANDER"]["path_sander"]} -O -i emin1.in '
                        f'-o emin1.out -p complex.prmtop -c complex.inpcrd -ref ref.crd '
                        f'-x mdcrd -r emin1.rst', shell = True)
        logging.info(f'{configfile["SANDER"]["path_sander"]} -O -i emin1.in '
                     f'-o emin1.out -p complex.prmtop -c complex.inpcrd -ref ref.crd '
                     f'-x mdcrd -r emin1.rst')

        subprocess.call(f'{configfile["SANDER"]["path_sander"]} -p complex.prmtop'
                        f' -c emin1.rst > emin1.pdb', shell = True)
        subprocess.call(f'{configfile["SANDER"]["path_sander"]}  -p complex.prmtop'
                        f' -c emin2.rst > emin3.pdb', shell = True)
        subprocess.call(f'{configfile["SANDER"]["path_sander"]}  -p complex.prmtop'
                        f' -c emin3.rst > emin3.pdb', shell = True)
        subprocess.call(f'{configfile["SANDER"]["path_sander"]}  -p complex.prmtop'
                        f' -c emin4.rst > emin4.pdb', shell = True)
        subprocess.call(f'{configfile["SANDER"]["path_sander"]}  -p complex.prmtop'
                        f' -c emin5.rst > emin5.pdb', shell = True)

        if verbose:
            print(f'{configfile["SANDER"]["path_sander"]} -O -i emin1.in '
                  f'-o emin1.out -p complex.prmtop -c complex.inpcrd -ref ref.crd '
                  f'-x mdcrd -r emin1.rst')
    except:
        logging.error('Cannot run amber.')
        print('Cannot run amber.')
        sys.exit(1)

    return 0

def run_cd_energy_profile(tunnel, traj, configfile, verbose):
    try:
        if int(configfile["SINGULARITY"]["value"]) == 1:
            Client.load(str(configfile['SINGULARITY']['singularity']))
        if verbose:
            print(f'{configfile["CD-ENERGYPROFILE"]["path_cd-energyprofile"]} -d {os.getcwd()}/{str(tunnel)} -t {str(traj)} -s {str(configfile["CPU"]["cpu"])}')
        if int(configfile["SINGULARITY"]["value"]) == 1:
            file = Client.execute(['cd-energyprofile','-d',
                               os.getcwd() + '/' + str(tunnel), '-t', str(traj),
                               '-s', str(configfile['CPU']['cpu'])])

        else:
            subprocess.call(f'{configfile["CD-ENERGYPROFILE"]["path_cd-energyprofile"]} -d {os.getcwd()}/{str(tunnel)} -t {str(traj)} -s {str(configfile["CPU"]["cpu"])} > energy.dat', shell=True)
        if verbose:
            print(f'Message from cd-energyprofile: \n {file}')
        logging.info(f'Message from cd-energyprofieL: \n {file}')

    except:
        if verbose:
            print('cd-energyprofile returncode is not 0. Check logfile.')
        logging.error(f'cd-energyprofile returncode is not 0.')
        sys.exit(1)
    with open(f'{os.getcwd()}/energy.dat', 'w') as file_energy_dat:
        file_energy_dat.write(str(file))


    if os.path.exists('energy.dat'):
        return 0
    else:
        print('energy.dat does not exist. Exit framework.')
        sys.exit(1)



def find_maximum_CD_curve(result_cd, ub_lb, verbose):
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
    logging.info(f'Model:  {num_str_energy[0][0]} and value  {num_str_energy[0][1]}')
    if verbose:
        print(f'Model: {num_str_energy[0][0]} and value {num_str_energy[0][1]} ')

    return max_value

def find_strce_for_amber(strce_and_max, verbose, configfile):
    trajectories = ""
    try:
        trajectories = os.listdir(configfile["TRAJECTORIES"]["path_trajectories"])
    except:
        logging.error('Dir Trajectories is not in the right place')
        if verbose:
            print('Dir trajectories is not in the right place.')
            sys.exit(1)
    for file in trajectories:
        if str(strce_and_max[0]) in file:
            return (file, strce_and_max[1])

    return 0

def remove_ligand_from_emin(protein, verbose, configfile):
    #  ted defaultne vypocitany emin5.pdb
    with open(protein) as oldfile, open('protein.pdb', 'w+') as newfile:
        for line in oldfile:
            if not LIGAND in line:
                    newfile.write(line)
    # convert pdb to pdbqt
    prepare_receptor = ''
    if int(configfile["SINGULARITY"]["value"]) == 1:
        Client.load(configfile["SINGULARITY"]["singularity"])
        prepare_receptor = Client.execute([configfile["PREPARE_RECEPTOR"]["path_prepare_receptor"], '-r', 'protein.pdb'])
        if verbose:
            print(f'{configfile["PREPARE_RECEPTOR"]["path_prepare_receptor"]} -r protein.pdb')
        if not os.path.isfile('protein.pdbqt'):
            logging.error(f'Cannot run prepare_receptor. Try: \n {configfile["PREPARE_RECEPTOR"]["path_prepare_receptor"]} -r protein.pdb \n Message: \n {prepare_receptor}')
            if verbose:
                print(f'Cannot run prepare_receptor. Try: \n {configfile["PREPARE_RECEPTOR"]["path_prepare_receptor"]} -r protein.pdb \n {prepare_receptor}')
            sys.exit(1)

    else:
        subprocess.call(f'{configfile["PREPARE_RECEPTOR"]["path_prepare_receptor"]} -r protein.pdb', shell=True)
        logging.info(f'Run prepare_receptor. Message: \n {configfile["PREPARE_RECEPTOR"]["path_prepare_receptor"]} -r protein.pdb ')
        if verbose:
            print(f'{configfile["PREPARE_RECEPTOR"]["path_prepare_receptor"]} -r protein.pdb')
            print(f'Message{prepare_receptor}')
        if not os.path.isfile('protein.pdbqt'):
            logging.error(f'Cannot run prepare_receptor. Try: \n {configfile["PREPARE_RECEPTOR"]["path_prepare_receptor"]} -r protein.pdb \n')
            if verbose:
                print(f'Cannot run prepare_receptor. Try: \n {configfile["PREPARE_RECEPTOR"]["path_prepare_receptor"]} -r protein.pdb')
            sys.exit(1)




def check_input_data():
    pass

def main():
    args = get_argument()
    print(f'Current working directory: {os.getcwd()}')
    print(f'Check whether protein is WITHOUT ligand.')

    if not check_config_file(args.config, args.verbose):
        sys.exit(1)
    configfile = configparser.ConfigParser()
    configfile.read(f'{args.config}')


    hdlr = logging.FileHandler(
        f'framework_{strftime("%Y-%m-%d__%H-%M-%S", localtime())}.log')
    curr_dir = os.getcwd()
    logging.root.addHandler(hdlr)
    logging.root.setLevel(logging.INFO)
    logging.root.setLevel(logging.DEBUG)
    logging.info(f'***Output from framework*** {strftime("%Y-%m-%d__%H-%M-%S", localtime())} \n')
    logging.info(f'#Protein : {args.protein} -> protein.pdb \n')
    logging.info(f'#Ligand : {args.ligand} \n')
    logging.info(f'#Tunnel: {args.tunnel} \n')
    rslt_dir = args.results_dir
    if rslt_dir == '.':
        rslt_dir = os.getcwd()

    if args.verbose:
        print("Verbosity turned on")
        print(f'Output from framework*** {strftime("%Y-%m-%d__%H-%M-%S", localtime())}')
        print(f'Protein : {args.protein} -> protein.odb')
        print(f'Ligand : {args.ligand}')
        print(f'Tunnel: {args.tunnel}')
        print(f'Dir for result: {rslt_dir}')

    remove_ligand_from_emin(args.protein, args.verbose, configfile) # rename file to protein.pdb and remove ligand if it is necessary

    if not args.traj:
        run_caverdock(args.ligand, args.tunnel, configfile, args.verbose)
        logging.info(f'#File from CaverDock: result_CD-{args.CD_lb_ub}.pdbq \n')
        args.traj = f'result_CD-{args.CD_lb_ub}.pdbqt'
        if args.verbose:
            print(f'Run CD and create new traj pdbqt result_CD-{args.CD_lb_ub}.pdbqt')


    run_cd_energy_profile(args.tunnel, args.traj, configfile, args.verbose)
    max_value_and_strctr = find_maximum_CD_curve(rslt_dir, args.CD_lb_ub, args.verbose)
    strcre_for_amber_energy = find_strce_for_amber(max_value_and_strctr, args.verbose, configfile)
    run_amber('protein.pdb', args.CD_lb_ub, args.verbose, configfile) # create new emin5.pdb with better structure

    #subprocess.call(f'{configfile["AMBPDB"]["path_ambpdb"]} -p complex.prmtop '
    #                f'< {configfile["TRAJECTORIES"]["path_trajectories"]}{strcre_for_amber_energy[0]}/emin5.rst '
    #                f'> {configfile["TRAJECTORIES"]["path_trajectories"]}{strcre_for_amber_energy[0]}/emin5.pdb', shell = True)

    shutil.copy(f'{str(configfile["TRAJECTORIES"]["path_trajectories"])}{strcre_for_amber_energy[0]}/emin5.pdb', 'new_protein_from_amber.pdb')




if __name__ == '__main__':
    main()
