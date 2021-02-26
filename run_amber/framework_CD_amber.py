#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import os
import sys
from argparse import ArgumentParser
from spython.main import Client
from pathlib import Path
import subprocess
import operator
import shutil
import configparser
import logging
from time import localtime, strftime
import re


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

    parser.add_argument("-config", help = 'Location of config.ini file.', type=Path, required=True)

    #parser.add_argument("-results_dir", help="Choose directory to save files.",
    #                    metavar="DIR", dest="results_dir")

    parser.add_argument("-restraint", help = 'Set restrain for ligand. For example @CA,C,N|(:BEO)@C1,C2,C3', required=True)

    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                       dest="verbose", action = "store_true")

    return parser.parse_args()

def run_caverdock(ligand, tunnel, configfile, verbose):
    # IN: protein, ligand, tunel
    # OUT: pdbqt file with lb and ub
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

    mpirun= ''
    if int(configfile["SINGULARITY"]["value"]) == 1:
        mpirun = Client.execute(['mpirun', '-np', configfile["CPU"]["cpu"], 'caverdock',
                                 '--config', 'caverdock.conf', '--out', str(configfile["RESULT_CD"]["name"])])

    else:
        subprocess.call(f'/usr/bin/mpirun.mpich -np {str(configfile["CPU"]["cpu"])} {configfile["CAVERDOCK"]["path_caverdock"]}  --config caverdock.conf --out {str(configfile["RESULT_CD"]["name"])}', shell=True)

    logging.info(f'mpirun -np {str(configfile["CPU"]["cpu"])} caverdock  --config caverdock.conf --out {str(configfile["RESULT_CD"]["name"])}')
    logging.info(f'Message from mpirun: \n {mpirun}')
    if verbose:
        print(f'mpirun -np {str(configfile["CPU"]["cpu"])} caverdock  --config caverdock.conf --out {str(configfile["RESULT_CD"]["name"])}')
        print(f'Message from mpirun: \n {mpirun}')

    if not (os.path.isfile(f'{configfile["RESULT_CD"]["name"]}-lb.pdbqt') or os.path.isfile(f'{configfile["RESULT_CD"]["name"]}-ub.pdbqt')):
        print(f'{configfile["RESULT_CD"]["name"]}-lb.pdbqt')
        logging.error(f'mpirun -np {str(configfile["CPU"]["cpu"])} caverdock  --config caverdock.conf --out {str(configfile["RESULT_CD"]["name"])}')
        logging.error(f'Message from mpirun: \n {mpirun}')
        if verbose:
            print(f'ERROR: mpirun -np {str(configfile["CPU"]["cpu"])} caverdock  --config caverdock.conf --out {str(configfile["RESULT_CD"]["name"])}')
            print(f'ERROR: Message from mpirun: \n {mpirun}')
        sys.exit(1)

def check_config_file(config, verbose):
    if verbose:
        print(f'Source config: {config}')
    if os.path.exists(f'{config}'):
        return True
    else:
        print('Config.ini file does not exist!')
    return False
def prepare_data_amber(ligand, verbose):
    subprocess.call(f'antechamber -i ligand.pdb -fi pdb -o ligand.prepi -fo prepi', shell=True)
    if verbose:
        print(f'antechamber -i ligand.pdb -fi pdb -o ligand.prepi -fo prepi')
    logging.info(f'antechamber -i ligand.pdb -fi pdb -o ligand.prepi -fo prepi')
    check_exist_file('ligand.prepi')

    subprocess.call(f'parmchk2 -i ligand.prepi -f prepi -o frcmod_lig2', shell=True)
    if verbose:
        print(f'parmchk2 -i ligand.prepi -f prepi -o frcmod_lig2')
    logging.info(f'parmchk2 -i ligand.prepi -f prepi -o frcmod_lig2')
    check_exist_file('frcmod_lig2')

#protein is pdb file WITHOUT ligand
def run_amber(protein, CD_lb_ub, verbose, configfile, ligand, restraint):
    # IN: structure of protein and ligand
    # OUT: new structure of protein after minimization

    # return optimal structure from amber -> emin5.pdb
    # directory_source, file_path to trajectories, protein
    #protein_pdb = f'./trajectories/{protein[0]/}'
    print('Check whether input protein is without ligand.')
    logging.info(f'{os.getcwd()} {configfile["RESULT_CD"]["name"]}-{CD_lb_ub}.pdbqt {protein}')

    prepare_data_amber(ligand, verbose)

    #subprocess.call(f'chmod u+x ./_11_run_tleap; chmod u+x ./_21_run_prepare_sander', shell = True)
    print(f'{configfile["11_RUN_TLEAP"]["11_run_tleap"]}')
    subprocess.call(f'{configfile["11_RUN_TLEAP"]["11_run_tleap"]}', shell = True)
    #@CA,C,N|(:BEO)@C1,C2,C3
    subprocess.call(f'{configfile["21_RUN_SANDER"]["21_run_sander"]} \'{restraint}\'', shell = True)

    check_exist_file('complex.inpcrd')
    check_exist_file('complex.prmtop')
    #subprocess.call(f'rm emin*.out; rm emin*.rst', shell=True)

    try:
        command = configfile["SANDER"]["path_sander"] + ' -O -i emin1.in -o emin1.out -p complex.prmtop -c complex.inpcrd -ref ref.crd -x mdcrd -r emin1.rst'
        if verbose:
            print(command)
        subprocess.call(command, shell = True)
        logging.info(command)

        command = configfile["SANDER"]["path_sander"] + ' -O -i emin2.in -o emin2.out -p complex.prmtop -c emin1.rst -ref ref.crd -x mdcrd -r emin2.rst'
        if verbose:
            print(command)
        subprocess.call(command, shell = True)
        logging.info(command)

        command = configfile["SANDER"]["path_sander"] + ' -O -i emin3.in -o emin3.out -p complex.prmtop -c emin2.rst -ref ref.crd -x mdcrd -r emin3.rst'
        if verbose:
            print(command)
        subprocess.call(command, shell = True)
        logging.info(command)
        
        command = configfile["SANDER"]["path_sander"] + ' -O -i emin4.in -o emin4.out -p complex.prmtop -c emin3.rst -ref ref.crd -x mdcrd -r emin4.rst'
        if verbose:
            print(command)
        subprocess.call(command, shell = True)
        logging.info(command)

        command = configfile["SANDER"]["path_sander"] + ' -O -i emin5.in -o emin5.out -p complex.prmtop -c emin4.rst -ref ref.crd -x mdcrd -r emin5.rst'
        if verbose:
            print(command)
        subprocess.call(command, shell = True)
        logging.info(command)

        subprocess.call(f'{configfile["AMBPDB"]["path_ambpdb"]} -p complex.prmtop'
                        f' -c emin1.rst > emin1.pdb', shell = True)
        logging.info(f'{configfile["AMBPDB"]["path_ambpdb"]} -p complex.prmtop'
                     f' -c emin1.rst > emin1.pdb')

        subprocess.call(f'{configfile["AMBPDB"]["path_ambpdb"]}  -p complex.prmtop'
                        f' -c emin2.rst > emin3.pdb', shell = True)
        logging.info(f'{configfile["AMBPDB"]["path_ambpdb"]}  -p complex.prmtop'
                     f' -c emin2.rst > emin3.pdb')

        subprocess.call(f'{configfile["AMBPDB"]["path_ambpdb"]}  -p complex.prmtop'
                        f' -c emin3.rst > emin3.pdb', shell = True)
        logging.info(f'{configfile["AMBPDB"]["path_ambpdb"]}  -p complex.prmtop'
                     f' -c emin3.rst > emin3.pdb')

        subprocess.call(f'{configfile["AMBPDB"]["path_ambpdb"]}  -p complex.prmtop'
                        f' -c emin4.rst > emin4.pdb', shell = True)
        logging.info(f'{configfile["AMBPDB"]["path_ambpdb"]}  -p complex.prmtop'
                     f' -c emin3.rst > emin3.pdb')

        subprocess.call(f'{configfile["AMBPDB"]["path_ambpdb"]}  -p complex.prmtop'
                        f' -c emin5.rst > emin5.pdb', shell = True)
        logging.info(f'{configfile["AMBPDB"]["path_ambpdb"]}  -p complex.prmtop'
                     f' -c emin5.rst > emin5.pdb')
        if verbose:
            print(f'First step: \n {configfile["AMBPDB"]["path_ambpdb"]} -p complex.prmtop'
                  f' -c emin1.rst > emin1.pdb')
    except:
        logging.error('Cannot run amber. Check logfile.')
        print('Cannot run amber. Check logfile.')
        sys.exit(1)

    return 0

def run_cd_energy_profile(tunnel, traj, configfile, verbose):
    file = ''
    try:
        if int(configfile["SINGULARITY"]["value"]) == 1:
            Client.load(str(configfile['SINGULARITY']['singularity']))
        if verbose:
            print(f'{configfile["CD-ENERGYPROFILE"]["path_cd-energyprofile"]} -d {os.getcwd()}/{str(tunnel)} -t {str(traj)} -s {str(configfile["CPU"]["cpu"])}')
        if int(configfile["SINGULARITY"]["value"]) == 1:
            file = Client.execute(['cd-energyprofile','-d',
                               os.getcwd() + '/' + str(tunnel), '-t', str(traj),
                               '-s', str(configfile['CPU']['cpu'])])
            with open(f'{os.getcwd()}/energy.dat', 'w') as file_energy_dat:
                file_energy_dat.write(str(file))
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
    if not os.path.exists('energy.dat'):
        logging.error(f'Cannot make energy.dat')
        if verbose:
            print('Energy.dat not exists')
        sys.exit(1)



def find_maximum_CD_curve(result_cd, ub_lb, verbose):
    # IN: pdbqt soubor
    # OUT: protein's snapchot with highest energy.

    # find max. energy value and return strucutre with this energy. Then run amber and try to find better conformation
    # of protein.
    # You can insert pdbqt file with trajectory or use CD to calculate the new trajectory.

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
        if file == 'model_'+strce_and_max[0]:
        #if str(strce_and_max[0]) in file:
            return (file, strce_and_max[1])

    return 0

def remove_ligand_from_emin(protein, verbose, configfile):
    #  ted defaultne vypocitany emin5.pdb
    with open(protein) as oldfile, open('protein.pdb', 'w+') as newfile:
        for line in oldfile:
            if not configfile["LIGAND"]["name"] in line:
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
    check_exist_file('protein.pdbqt')
# parse trajectory from CD into separate step
def parse_structures(file_name):
    file_string = Path(file_name).read_text()
    file_all = re.findall('MODEL.*?ENDMDL', file_string, re.DOTALL)
    return file_all

# check input for amber. Source is set in working directroy default.
"""
def check_files(source, protein, configfile):

    if not Path(f'{source}/{protein}').is_file():
        print(f'File {protein} not exist')
        sys.exit(1)

    if not Path(f'{configfile["11_RUN_TLEAP"]["11_run_tleap"]}').is_file():
        print("File _11_run_tleap not exist")
        sys.exit(1)

    if not Path(f'{configfile["11_RUN_TLEAP"]["11_run_tleap"]}').is_file():
        print("File _21_run_prepare_sander not exist")
        sys.exit(1)
"""


def make_separate_directory(file_all, protein, source, configfile):
    try:
        shutil.rmtree('trajectories')
        isdir = False
    except:
        isdir = os.path.isdir('trajectories')
    if isdir == False:
        print('Trajectories do not exist')
        os.mkdir('trajectories')
    else:
        print('exist')

    for count, file in enumerate(file_all, start=0):
        ismod = os.path.isdir(f'./trajectories/model_{count}')
        if ismod == False:
            os.mkdir(f'./trajectories/model_{count}')
        with open(f'./trajectories/model_{count}/position_ligand_{count}.pdbqt', 'w') as file_traj:
            file_traj.write(file)
        shutil.copy(protein, f'./trajectories/model_{count}/')
        # nakopiruje navic potrebna data
        #shutil.copy(f'{source}/_11_run_tleap', f'./trajectories/model_{count}/')
        #shutil.copy(f'{source}/_21_run_prepare_sander', f'./trajectories/model_{count}/')
        shutil.copy(f'{source}/{protein}', f'./trajectories/model_{count}/')

        try:
            subprocess.run(f'rm ./trajectories/model_{count}/emin*', shell = True)
        except:
            pass
        try:
            subprocess.run(f'rm ./trajectories/model_{count}/complex.inpcrd', shell = True)
        except:
            pass
        try:
            subprocess.run(f'rm ./trajectories/model_{count}/complex.prmtop', shell = True)
        except:
            pass
        try:
            subprocess.run(f'rm ./trajectories/model_{count}/ligand.prepi', shell = True)
        except:
            pass
        # convert traj_position_ligand_{count}.pdbqt to pdb -> singularity
        if int(configfile["SINGULARITY"]["value"]) == 1:
            Client.load('/home/petrahrozkova/Stažené/caverdock_1.1.sif')
            Client.execute(['/opt/mgltools-1.5.6/bin/pythonsh',
                            '/opt/mgltools-1.5.6/MGLToolsPckgs/AutoDockTools/Utilities24/pdbqt_to_pdb.py',
                            '-f',os.getcwd()+'/trajectories/model_'+str(count)+'/position_ligand_*.pdbqt',
                            '-o', os.getcwd()+'/trajectories/model_'+str(count)+'/ligand_H.pdb'])
        else:
            subprocess.call(f'{configfile["PDBQT_TO_PDB"]["path_pdbqt_to_pdb"]} -f {os.getcwd()}/trajectories/model_{str(count)}/position_ligand_{str(count)}.pdbqt '
                            f'-o {os.getcwd()}/trajectories/model_{str(count)}/ligand_H.pdb', shell=True)
        check_exist_file(f'{os.getcwd()}/trajectories/model_{str(count)}/ligand_H.pdb')
        subprocess.call(f'sed -i \'s/<0> d/{configfile["LIGAND"]["name"]} d/g\' ./trajectories/model_{count}/ligand_H.pdb', shell = True) #ligand_for_complex.pdb
        subprocess.call(f'pdb4amber -i ./trajectories/model_{count}/ligand_H.pdb -o ./trajectories/model_{count}/ligand.pdb --nohyd', shell = True)
        check_exist_file(f'{os.getcwd()}/trajectories/model_{str(count)}/ligand.pdb')

        #subprocess.call(f'antechamber -i {ligand} -fi pdbqt -o ligand.pdb -if pdb', shell = True)
        subprocess.call(f'antechamber -i ./trajectories/model_{count}/ligand.pdb -fi pdb -o ./trajectories/model_{count}/ligand.prepi -fo prepi', shell = True)
        check_exist_file(f'{os.getcwd()}/trajectories/model_{str(count)}/ligand.prepi')

        subprocess.call(f'cat \"./trajectories/model_{count}/ligand.pdb\" > '
                        f'\"./trajectories/model_{count}/ligand_for_complex.pdb\"', shell = True)

        # split (ugly) ligand and protein into complex.pdb
        subprocess.call( #remove last line in file with END. IMPORTANT!
            f'head -n -1 ./trajectories/model_{count}/{protein} > ./trajectories/model_{count}/complex_H.pdb | '
            f'echo TER >> ./trajectories/model_{count}/complex_H.pdb',
            shell=True)
        subprocess.call(f'cat ./trajectories/model_{count}/ligand_for_complex.pdb'
                        f' >> ./trajectories/model_{count}/complex_H.pdb ',
                        #f'| echo TER >> ./trajectories/model_{count}/complex.pdb',
                        shell=True)
        subprocess.call(f'echo END >> ./trajectories/model_{count}/complex_H.pdb',
                        shell=True)
        check_exist_file(f'{os.getcwd()}/trajectories/model_{str(count)}/complex_H.pdb')
        print(f'{os.getcwd()}')

        subprocess.call(f'pdb4amber -i ./trajectories/model_{count}/complex_H.pdb -o ./trajectories/model_{count}/complex.pdb --nohyd', shell = True)
        check_exist_file(f'{os.getcwd()}/trajectories/model_{str(count)}/complex.pdb')

def check_input_data(args):
        if not os.path.exists(args.protein):
            print(f'{args.protein} does not exist')
            logging.error(f'{args.protein} does not exist')
            sys.exit(1)
        if not os.path.exists(args.ligand):
            print(f'{args.ligand} does not exist')
            logging.error(f'{args.ligand} does not exist')
            sys.exit(1)
        if not os.path.exists(args.tunnel):
            print(f'{args.tunnel} does not exist')
            logging.error(f'{args.tunnel} does not exist')
            sys.exit(1)

def check_exist_file(file):
    if not os.path.exists(f'{file}') or os.path.getsize(file) < 0:
        print(f'File {file} does not exist. Exit framework.')
        sys.exit(1)
def main():
    args = get_argument()
    check_input_data(args)
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
    logging.info(f'#Ligand : {args.ligand}  {configfile["LIGAND"]["name"]} \n')
    logging.info(f'#Tunnel: {args.tunnel} \n')
    logging.info(f'#Restraint: {args.restraint}')
    hash = subprocess.Popen(['git', 'rev-parse', '--short', 'HEAD'], cwd = "/shared/caverdock_scripts/run_amber", stdout=subprocess.PIPE)
    #print(f'hash je {hash.stdout.read().rstrip()}')
    logging.info(f'Hash from github: {hash.stdout.read().rstrip()}')
    rslt_dir = os.getcwd() #args.results_dir
    source = os.getcwd()

    if args.verbose:
        print("Verbosity turned on")
        print(f'Output from framework*** {strftime("%Y-%m-%d__%H-%M-%S", localtime())}')
        print(f'Protein : {args.protein} -> protein.odb')
        print(f'Ligand : {args.ligand} {configfile["LIGAND"]["name"]}')
        print(f'Tunnel: {args.tunnel}')
        print(f'Dir for result: {rslt_dir}')
        print(f'Restraint: {args.restraint}')
        print(f'Hash from git: {hash.stdout.read().rstrip()}')

    # rename file to protein.pdb and remove ligand if it is necessary
    remove_ligand_from_emin(args.protein, args.verbose, configfile)
    #check_files(source, 'protein.pdb', args.config)
    if not args.traj:
        run_caverdock(args.ligand, args.tunnel, configfile, args.verbose)
        logging.info(f'#File from CaverDock: {str(configfile["RESULT_CD"]["name"])}-{args.CD_lb_ub}.pdbqt \n')
        args.traj = f'{str(configfile["RESULT_CD"]["name"])}-{args.CD_lb_ub}.pdbqt'
        if args.verbose:
            print(f'Run CD and create new traj pdbqt {str(configfile["RESULT_CD"]["name"])}-{args.CD_lb_ub}.pdbqt')

        file_all = parse_structures(f'{str(configfile["RESULT_CD"]["name"])}-{args.CD_lb_ub}.pdbqt' )
        make_separate_directory(file_all, 'protein.pdb', source, configfile)

    else:
        file_all = parse_structures(args.traj)
        make_separate_directory(file_all, 'protein.pdb', source, configfile)

    run_cd_energy_profile(args.tunnel, args.traj, configfile, args.verbose)
    max_value_and_strctr = find_maximum_CD_curve(rslt_dir, args.CD_lb_ub, args.verbose)
    strcre_for_amber_energy = find_strce_for_amber(max_value_and_strctr, args.verbose, configfile)
    print(strcre_for_amber_energy)
    # use new structure of protein  with ligand from amber
    dir=(f'{source}/trajectories/{strcre_for_amber_energy[0]}')
    os.chdir(dir)
    run_amber('protein.pdb', args.CD_lb_ub, args.verbose, configfile, args.ligand, args.restraint) # create new emin5.pdb with better structure
    os.chdir(source)
    if args.verbose:
        print(f'{str(configfile["TRAJECTORIES"]["path_trajectories"])}{strcre_for_amber_energy[0]}/emin5.pdb', 'new_protein_from_amber.pdb')
    try:
        shutil.copy(f'{str(configfile["TRAJECTORIES"]["path_trajectories"])}{strcre_for_amber_energy[0]}/emin5.pdb', 'new_protein_from_amber.pdb')
    except:
        print(f'Cannot copy final file {str(configfile["TRAJECTORIES"]["path_trajectories"])}{strcre_for_amber_energy[0]}/emin5.pdb')
if __name__ == '__main__':
    main()
