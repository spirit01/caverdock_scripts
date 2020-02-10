#!/usr/bin/env python3

# z caverdock souboru s trajektorii vytahne konformaci ligandu v kazdem kroku
# pro kazdy krok udela slozku, kam da strukturu ligandu

# -*- coding: utf-8 -*-
import os
import re
import shutil
import subprocess
from argparse import ArgumentParser
from pathlib import Path


def get_argument():
    parser = ArgumentParser()

    parser.add_argument("-file_path", type=Path)

    parser.add_argument("-protein", type=Path)

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


def make_separate_directory(file_all, protein, source):
    os.mkdir('trajectories')
    for count, file in enumerate(file_all, start=0):
        os.mkdir(f'./trajectories/model_{count}')
        with open(f'./trajectories/model_{count}/position_ligand_{count}.pdbqt', 'w') as file_traj:
            file_traj.write(file)
        shutil.copy(protein, f'./trajectories/model_{count}/')
        # nakopiruje navic potrebna data
        shutil.copy(f'{source}/_Xqmin_tmp.in', f'./trajectories/model_{count}/')
        shutil.copy(f'{source}/_11_run_tleap.sh', f'./trajectories/model_{count}/')
        shutil.copy(f'{source}/_21_run-mm_meta.sh', f'./trajectories/model_{count}/')
        #shutil.copy(f'{source}/_31_prep.sh', f'./trajectories/model_{count}/')
        shutil.copy(f'{source}/NEW_PDB.pdb', f'./trajectories/model_{count}/')
        # convert traj_position_ligand_{count}.pdbqt to pdb
        subprocess.call(f'/home/petrahrozkova/MGLTools-1.5.6/MGLToolsPckgs/AutoDockTools/Utilities24/pdbqt_to_pdb.py -f ./trajectories/model_{count}/position_ligand_{count}.pdbqt -o ./trajectories/model_{count}/ligand.pdb',
                        shell = True)
        #subprocess.call(
        #    f'/home/petrahrozkova/MGLTools-1.5.6/MGLToolsPckgs/AutoDockTools/Utilities24/pdbqt_to_pdb.py -f ./trajectories/model_{count}/position_ligand_{count}.pdbqt -o ./trajectories/model_{count}/ligand_for_complex.pdb',
        #    shell=True)
        subprocess.call(f'sed -i \'s/<0> d/TIP d/g\' ./trajectories/model_{count}/ligand.pdb', shell = True) #ligand_for_complex.pdb

        subprocess.call(f'tail -n +2 \"./trajectories/model_{count}/ligand.pdb\" > \"./trajectories/model_{count}/ligand_for_complex.pdb\"', shell = True)

        # spojit 'hloupe" ligand, protein do complex.pdb
        subprocess.call(
            f'cat ./trajectories/model_{count}/NEW_PDB.pdb > ./trajectories/model_{count}/complex.pdb | echo TER >> ./trajectories/model_{count}/complex.pdb',
            shell=True)
        subprocess.call(f' cat ./trajectories/model_{count}/ligand_for_complex.pdb >> ./trajectories/model_{count}/complex.pdb |  echo TER >> ./trajectories/model_{count}/complex.pdb',
            shell=True)
        subprocess.call(f' echo END >> ./trajectories/model_{count}/complex.pdb',
            shell=True)

        # vytvorit ligand.prepi
        # 	antechamber -i $traj -fi pdb -o ${traj%.*}.prepi -fo prepi
        # parmchk2 -f prepi -i ligand.prepi -o frcmod_lig2



def main():
    args = get_argument()
    file_string = make_string_from_file(args.file_path)
    file_all = parse_structures(file_string)
    make_separate_directory(file_all, args.protein, args.directory_source)


if __name__ == '__main__':
    main()
