#!/usr/bin/env python3
# pusti amber nad vsemi slozkami trajektorie. Mel by mit vsechny soubory k dispozici


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


def make_separate_directory(models, directory_source):
    os.chdir(directory_source)
    for model in models:
        os.chdir("{}".format(model))
        subprocess.call("antechamber -i ligand.pdb -fi pdb -o ligand.prepi -fo prepi", shell = True)
        # nutno dodrzet presny odstup mezi sloupci!!!:
        # ATOM      9  H6  TIP d   1      79.318   8.180 -26.934  1.00  0.00      posi H
        #subprocess.call("sed -i \'s/<0>/TIP/g\' ligand.prepi", shell = True)
        subprocess.call("parmchk2 -f prepi -i ligand.prepi -o frcmod_lig2", shell=True)
        subprocess.call("./_11_run_tleap.sh" , shell=True)
        subprocess.call("./_11_run_tleap.sh", shell=True)
        os.chdir("../")


def main():
    args = get_argument()
    file_all = os.listdir(args.directory_source)
    make_separate_directory(file_all, args.directory_source)


if __name__ == '__main__':
    main()
