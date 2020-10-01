#!/usr/bin/env python3

# z caverdock souboru s trajektorii vytahne konformaci ligandu v kazdem kroku
# pro kazdy krok udela slozku, kam da strukturu ligandu

# -*- coding: utf-8 -*-
import os
import re
import sys
import shutil
import subprocess
from argparse import ArgumentParser
from pathlib import Path
from spython.main import Client
from Bio.PDB import *

LIGAND = 'BEO'
def get_argument():
    parser = ArgumentParser()

    parser.add_argument("-file_path", type=Path, help = 'pdbqt file from CaverDock')

    parser.add_argument("-protein", type=Path, help = 'pdb file with structure of protein')

    parser.add_argument("-source", help="choose directory to load files",
                        metavar="DIR", dest="directory_source", required=True)

    return parser.parse_args()


# pouziva hodne pameti
def make_string_from_file(file_name):
    file_string = Path(file_name).read_text()
    return file_string


# pouziva hodne pameti
def parse_structures(file_string):
    file_all = re.findall('MODEL.*?ENDMDL', file_string, re.DOTALL)
    return file_all

def check_files(source, protein):
    if not Path(f'{source}/_Xqmin_tmp.in').is_file():
        print("File _Xqmin_tmp.in not exist")
        sys.exit(1)

    if not Path(f'{source}/{protein}').is_file():
        print(f'File {protein} not exist')
        sys.exit(1)

    if not Path(f'{source}/_11_run_tleap.sh').is_file():
        print("File _11_run_tleap.sh not exist")
        sys.exit(1)

    if not Path(f'{source}/_21_run-mm_meta.sh').is_file():
        print("File _21_run-mm_meta.sh not exist")
        sys.exit(1)

    if not Path(f'{source}/ligand.prepi').is_file():
        try:
            subprocess.call("antechamber -i ligand.pdb -fi pdb -o ligand.prepi -fo prepi", shell = True)
        except:
            print("File ligand.prepi not exist")
            sys.exit(1)

def make_separate_directory(file_all, protein, source):
    #shutil.rmtree('trajectories')
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
        shutil.copy(f'{source}/_Xqmin_tmp.in', f'./trajectories/model_{count}/')
        shutil.copy(f'{source}/_11_run_tleap.sh', f'./trajectories/model_{count}/')
        shutil.copy(f'{source}/_21_run-mm_meta.sh', f'./trajectories/model_{count}/')
        shutil.copy(f'{source}/{protein}', f'./trajectories/model_{count}/')
        shutil.copy(f'{source}/ligand.prepi', f'./trajectories/model_{count}/')
        try:
            subprocess.run(f'rm ./trajectories/model_{count}/emin2*', shell = True)
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
    # convert traj_position_ligand_{count}.pdbqt to pdb -> singularity
        Client.load('/home/petrahrozkova/Stažené/caverdock_1.1.sif')

        Client.execute(['/opt/mgltools-1.5.6/bin/pythonsh',
                            '/opt/mgltools-1.5.6/MGLToolsPckgs/AutoDockTools/Utilities24/pdbqt_to_pdb.py',
                            '-f',os.getcwd()+'/trajectories/model_'+str(count)+'/position_ligand_*.pdbqt',
                            '-o', os.getcwd()+'/trajectories/model_'+str(count)+'/ligand.pdb'])

        subprocess.call(f'sed -i \'s/<0> d/TIP d/g\' ./trajectories/model_{count}/ligand.pdb', shell = True) #ligand_for_complex.pdb

        subprocess.call(f'tail -n +2 \"./trajectories/model_{count}/ligand.pdb\" > '
                        f'\"./trajectories/model_{count}/ligand_for_complex.pdb\"', shell = True)

        # spojit 'hloupe" ligand, protein do complex.pdb
        subprocess.call( #remove last line in file with END. IMPORTANT!
            f'head -n -1 ./trajectories/model_{count}/{protein} > ./trajectories/model_{count}/complex.pdb | '
            f'echo TER >> ./trajectories/model_{count}/complex.pdb',
            shell=True)
        subprocess.call(f'cat ./trajectories/model_{count}/ligand_for_complex.pdb'
                        f' >> ./trajectories/model_{count}/complex.pdb ',
                        #f'| echo TER >> ./trajectories/model_{count}/complex.pdb',
            shell=True)
        subprocess.call(f'echo END >> ./trajectories/model_{count}/complex.pdb',
            shell=True)


def main(directory_source, pdbqt_traj, protein):
    file_string = make_string_from_file(pdbqt_traj)
    file_all = parse_structures(file_string)
    check_files(directory_source, protein)
    make_separate_directory(file_all, protein, directory_source)


if __name__ == '__main__':
    args = get_argument()
    main(args.directory_source, args.file_path, args.protein)
