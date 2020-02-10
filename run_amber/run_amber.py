#!/usr/bin/env python3
# pusti amber nad vsemi slozkami trajektorie. Mel by mit vsechny soubory k dispozici

# z caverdock souboru s trajektorii vytahne konformaci ligandu v kazdem kroku
# pro kazdy krok udela slozku, kam da strukturu ligandu

# -*- coding: utf-8 -*-
import os
import re
import shutil
import subprocess
from argparse import ArgumentParser
from pathlib import Path
import glob


def get_argument():
    parser = ArgumentParser()

    #parser.add_argument("-file_path", type=Path)

    # parser.add_argument("-protein", type=Path)

    parser.add_argument("-source", help="choose directory to load files",
                        metavar="DIR", dest="directory_source", required=True)

    return parser.parse_args()


def make_separate_directory(file_all, directory_source):
    path = os.getcwd()
    for count, file in enumerate(file_all, start=0):
        os.chdir("%s/%s" %(path, directory_source))
        # vytvorit ligand.prepi
        print(os.getcwd())
        #try:
            #subprocess.call(f'rm ./trajectories/model_{count}/ligand.prepi', shell = True)
        #except:
        #    break
        #subprocess.call(f'antechamber -i ./trajectories/model_{count}/ligand.pdb -fi pdb -o ./trajectories/model_{count}/ligand.prepi -fo prepi', shell = True)
        os.chdir("./model_%d/" %(count))
        #subprocess.call("antechamber -i ./trajectories/model_%d/ligand.pdb -fi pdb -o ./trajectories/model_%d/ligand.prepi -fo prepi" %(count, count), shell = True)
        subprocess.call("antechamber -i ligand.pdb -fi pdb -o ligand.prepi -fo prepi", shell = True)
        # nutno dodrzet presny odstup mezi sloupci!!!:
        # ATOM      9  H6  TIP d   1      79.318   8.180 -26.934  1.00  0.00      posi H
        #subprocess.call(f'sed -i \'s/<0>/TIP/g\' ./trajectories/model_{count}/ligand.prepi', shell = True)
        #subprocess.call("sed -i \'s/<0>/TIP/g\' ./trajectories/model_%d/ligand.prepi" %(count), shell = True)
        subprocess.call("sed -i \'s/<0>/TIP/g\' ligand.prepi", shell = True)

        #subprocess.call(f'parmchk2 -f prepi -i ./trajectories/model_{count}/ligand.prepi -o ./trajectories/model_{count}/frcmod_lig2', shell = True)
        #subprocess.call("parmchk2 -f prepi -i ./trajectories/model_%d/ligand.prepi -o ./trajectories/model_%d/frcmod_lig2" %(count, count),
        #    shell=True)
        subprocess.call(
            "parmchk2 -f prepi -i ligand.prepi -o frcmod_lig2", shell=True)
        #subprocess.call(f'./trajectories/model_{count}/_11_run_tleap.sh', shell = True)
        subprocess.call("./_11_run_tleap.sh" , shell=True)
        #subprocess.call(f'./trajectories/model_{count}/_11_run_tleap.sh', shell = True)
        subprocess.call("./_11_run_tleap.sh", shell=True)

def main():
    args = get_argument()
    file_all = os.listdir(args.directory_source)
    make_separate_directory(file_all, args.directory_source)


if __name__ == '__main__':
    main()
