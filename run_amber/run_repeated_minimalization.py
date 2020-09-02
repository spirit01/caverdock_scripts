#!/usr/bin/env python3
# pusti amber nad vsemi slozkami trajektorie. Mel by mit vsechny soubory k dispozici

# vezme puvodni pozici z caverdocku a vsadi do posledniho kroku minimalizace emin5.pdb
# Tento krok provede prozatim defaultne 3x

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

    parser.add_argument("-dir", help="choose directory to load files",
                        metavar="DIR", dest="dir", required=True)
    parser.add_argument("-order", help= "number of repetition", dest = "order", default = 1)

    return parser.parse_args()

def make_directory_copy_files(dir, order, models):
    for model in models:
        if "model" in model:
            try:
                os.makedirs(f'./trajectories_r_{order}/{model}_r_{order}')
            except:
                continue
            shutil.copy(f'{dir}{model}/emin5.pdb', f'./trajectories_r_{order}/{model}_r_{order}')
            shutil.copy(f'{dir}{model}/_11_run_tleap.sh', f'./trajectories_r_{order}/{model}_r_{order}')
            shutil.copy(f'{dir}{model}/_21_run-mm_meta.sh', f'./trajectories_r_{order}/{model}_r_{order}')
            shutil.copy(f'{dir}{model}/_Xqmin_tmp.in', f'./trajectories_r_{order}/{model}_r_{order}')
            shutil.copy(f'{dir}{model}/ligand.pdb', f'./trajectories_r_{order}/{model}_r_{order}')

def make_complex(dir, order):
    models = os.listdir(dir)
    for model_long in models:
        if "model" in model_long:
            #write emin5.pdb do complex.pdb
            print(model_long)
            os.mkdir(f'./trajectories_r_{order}/{model_long}/')
            with open(f'{dir}{model_long}/emin5.pdb') as file_emin:
                #model = correct_name(model_long)
                with open(f'./trajectories_r_{order}/{model_long}/complex.pdb', 'w') as file_complex:
                    for line in file_emin:
                        if line.startswith('ATOM'):
                            file_complex.write(line)
                        if line.startswith(f'TER'):
                            file_complex.write("TER \n")
                            break
            with open(f'{dir}{model_long}/ligand.pdb') as file_emin:
                #model = correct_name(model_long)
                with open(f'./trajectories_r_{order}/{model_long}/complex.pdb', 'a') as file_complex:
                    for line in file_emin:
                        if line.startswith('ATOM'):
                            file_complex.write(line)
                        if line.startswith(f'TER'):
                            file_complex.write("TER \n")
                            break
                    file_complex.write("END \n")
        # nakopiruje navic potrebna data
            shutil.copy(f'/home/petrahrozkova/Dokumenty/HPC/halogenasa/data-linb_lb_new/p3/32/_Xqmin_tmp.in', f'./trajectories_r_{order}/{model_long}/')
            shutil.copy(f'/home/petrahrozkova/Dokumenty/HPC/halogenasa/data-linb_lb_new/p3/32/_11_run_tleap.sh', f'./trajectories_r_{order}/{model_long}/')
            shutil.copy(f'/home/petrahrozkova/Dokumenty/HPC/halogenasa/data-linb_lb_new/p3/32/_21_run-mm_meta.sh', f'./trajectories_r_{order}/{model_long}/')
            #shutil.copy(f'{source}/_31_prep.sh', f'./trajectories/model_{count}/')
            shutil.copy(f'/home/petrahrozkova/Dokumenty/HPC/halogenasa/data-linb_lb_new/p3/32/NEW_PDB.pdb', f'./trajectories_r_{order}/{model_long}/')
            shutil.copy(f'/home/petrahrozkova/Dokumenty/HPC/halogenasa/data-linb_lb_new/p3/32/ligand.prepi', f'./trajectories_r_{order}/{model_long}/')
#it gives ugly name of foler and file, too long
#def correct_name(model):
#    print(model)
#    new_model = f'{model.split('_')[0]}_{model.split('_').[1]}'
#    print(new_model)
#    return new_model


def main():
    args = get_argument()
    models = os.listdir(args.dir)
    print(os.getcwd())
    try:
        os.makedirs(f'./trajectories_r_{args.order}')
    except:
        print("Directory is already exist")
        print("Continue")

    #make_directory_copy_files(args.dir, args.order, models)
    make_complex(args.dir, args.order)




if __name__ == '__main__':
    main()
