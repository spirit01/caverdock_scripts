#!/usr/bin/env python3

# vytahne energie z emin5.out(amber) a energy.dat(CD) a ulozi do vyxlednho souboru
# ./trajectories/result_CD_AMBER.txt

# -*- coding: utf-8 -*-
import os
import re
import shutil
import subprocess
from argparse import ArgumentParser
from pathlib import Path
import linecache


def get_argument():
    parser = ArgumentParser()

    #parser.add_argument("-file_path", type=Path)
    # soubor caverdocku
    parser.add_argument("-result_cd", type=Path)
    # soubor z ambru
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


def make_separate_directory(file_all, result_cd):
    with open(f'./trajectories/result_CD_AMBER.txt', 'w') as file_result_CD_AMBER:
        for count, file in enumerate(file_all, start=0):
            # bylo vy fajn overit, ze opravdu emin5.out ma nejlepsi energii
            subprocess.call(f'tail -40 ./trajectories/model_{count}/emin5.out > ./trajectories/model_{count}/emin_result', shell = True)
            try:
                with open(f'./trajectories/model_{count}/emin_result') as file_amber:
                    for line in file_amber:
                        if ' 1000' in line:
                        # NSTEP       ENERGY          RMS            GMAX         NAME    NUMBER
                        # 1000      -4.6779E+03     2.6479E-02     3.9058E-01     CA       1758
                            energy_amber = line.split(sep=None)[1]
            except:
                energy_amber = 0
            try:
                with open(result_cd) as file_caverdock:
                        # distance disc min UB energy, max UB energy, radius, LB energy
                        # 0.269276742244 1 -3.7 -3.6 2.0 -3.7
                        line = linecache.getline(f'./{result_cd}', count + 1)
                        try:
                            energy_cd = float(line.split(' ')[3])
                        except:
                            energy_cd = 0
                        #print(f'{count} {energy_cd} {energy_amber}')
            except:
                pass
            file_result_CD_AMBER.write(f'{count}    {energy_amber}\n')#{energy_cd}  {energy_amber}\n')



def main():
    args = get_argument()
    #file_string = make_string_from_file(args.file_path)
    #file_all = parse_structures(file_string)
    file_all = os.listdir(args.directory_source)
    make_separate_directory(file_all, args.result_cd)


if __name__ == '__main__':
    main()
