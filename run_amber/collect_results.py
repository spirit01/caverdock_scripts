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
    # soubor caverdocku
    parser.add_argument("-result_cd", help = 'file.dat from caverdock', type=Path, required=True)
    parser.add_argument("-source_cd", help = 'file.pdbqt from caverdock', type=Path, required=True)
    # soubor z ambru
    parser.add_argument("-source_trajectories", help="directory with trajectory from amber withn emins file",
                        metavar="DIR", dest="directory_source_trajectories", required=True)

    parser.add_argument("-save_destination", help="choose directory to saverfiles",
                        metavar="DEST", dest="save_destination", required=True)

    return parser.parse_args()

# pouziva hodne pameti
def make_string_from_file(file_name):
    file_string = Path(file_name).read_text()
    return file_string

# pouziva hodne pameti
def parse_structures(file_string):
    file_all = re.findall('MODEL.*?ENDMDL', file_string, re.DOTALL)
    return file_all

def make_separate_directory(file_all, result_cd, final_dest, source_trajectories):
    energy_cd_lb = -1000
    energy_cd_ub = -1000
    energy_amber = 0
    with open(f'{final_dest}/result_CD_AMBER.txt', 'w') as file_result_CD_AMBER:
        for count, file in enumerate(file_all, start=0):
            print(file)
            # bylo vy fajn overit, ze opravdu emin5.out ma nejlepsi energii
            subprocess.call(f'tail -40 {source_trajectories}/{file}/emin5.out > {source_trajectories}/model_{count}/emin_result', shell = True)
            try:
                with open(f'{source_trajectories}/model_{count}/emin_result') as file_amber:
                    for line in file_amber:
                        if 'NSTEP' in line:
                            nextLine = next(file_amber)
                    # NSTEP       ENERGY          RMS            GMAX         NAME    NUMBER
                    # 1000      -4.6779E+03     2.6479E-02     3.9058E-01     CA       1758
                            energy_amber = nextLine.split(sep=None)[1]
                            #nstep = nextLine.split(sep=None)[0]
            except:
                energy_amber = 0
            with open(f'{final_dest}/{result_cd}') as file_caverdock:
                    # distance disc min UB energy, max UB energy, radius, LB energy
                    # 0.269276742244 1 -3.7 -3.6 2.0 -3.7
                    line = linecache.getline(f'{final_dest}/{result_cd}', count + 1)
                    try:
                        energy_cd_ub = float(line.split(' ')[3])
                        energy_cd_lb = float(line.split(' ')[5])

                    except:
                        energy_cd_lb = -1000
                    print(f'{count} {energy_cd_lb} {energy_cd_ub} {energy_amber} \n')

            if not energy_cd_lb == -1000: 
                file_result_CD_AMBER.write(f'{count} {energy_cd_lb} {energy_cd_ub} {energy_amber}\n')#{energy_cd}  {energy_amber}\n')



def main():
    args = get_argument()
    print(f'Current working directory: {os.getcwd()}')
    #os.chdir(path)
    #file_string = make_string_from_file(args.file_path)
    #file_all = parse_structures(file_string)

    #model = os.listdir(args.directory_source_trajectories)
    #file_all = (i for i in model if 'model' in i)
    #print('XXX', file_all)
    file_all = []

    i = 0
    old_disc = -1
    with open(f'{args.save_destination}/{args.source_cd}') as file_cds:
        for line in file_cds:
            if 'REMARK CAVERDOCK TUNNEL' in line:
                disc = int(line.split(' ')[3])
                if disc > old_disc:
                    file_all.append('model_' + str(i))
                    old_disc = disc
                i = i+1
    print('YYY', file_all)

    make_separate_directory(file_all, args.result_cd, args.save_destination, args.directory_source_trajectories)


if __name__ == '__main__':
    main()
