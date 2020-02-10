#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import shutil
import subprocess
from argparse import ArgumentParser
from pathlib import Path
import glob

class Model:
    def __init__(self):
        self.name = 0
        self.energy_r_0 = "\t"
        self.energy_r_1 = "\t"
        self.energy_r_2 = "\t"

    def write(self):
        line = f'model_{self.name} {self.energy_r_0} {self.energy_r_1} {self.energy_r_2}'

        return line

def get_argument():
    parser = ArgumentParser()

    parser.add_argument("-dir", help="choose directory to load files",
                        metavar="DIR", dest="dir", required=True)

    parser.add_argument("-emin", help = "choose emin",
                        choices=['emin1.out', 'emin2.out', 'emin3.out', 'emin4.out', 'emin5.out' ])

    return parser.parse_args()

# tail -32 emin1.out | head -1 -> tahani energie
def make_file_for_graph(trajectories, dir, emin, model):
    model_energy = {}
    #for traj in trajectories:
    repeated = os.listdir(f'{os.getcwd()}/{dir}')#{traj}')
    for name in repeated:
        #print(model)
        #energy = subprocess.call(f'tail -31 {os.getcwd()}/{dir}{traj}/{model}/{emin} | head -1', shell=True)
        if "model" in name:
            with open (f'{os.getcwd()}/{dir}{name}/{emin}') as file_tmp:#(f'{os.getcwd()}/{dir}{traj}/{name}/{emin}') as file_tmp:
                for line in file_tmp:
                    #if "NSTEP       ENERGY          RMS            GMAX         NAME    NUMBER" in line:
                    if "FINAL RESULTS" in line:
                        for line in file_tmp:
                            if "  1000      " in line:
                                tmp_energy = float(line.split()[1])
                                if tmp_energy > -4600 or tmp_energy < -5000:
                                    tmp_energy = "\t"
                                tmp_name = int(name.split('_')[1])
                                tmp_repeatition = '0' if (len(name.split('_', 2)) < 3) else name.split('_', 2)[2]

                                #print(name,  tmp_name, tmp_repeatition)
                                if  tmp_name in model_energy:
                                    if tmp_repeatition == '0':
                                        model_energy[tmp_name].energy_r_0 = tmp_energy
                                    if tmp_repeatition == 'r_1':
                                        model_energy[tmp_name].energy_r_1 = tmp_energy
                                    if tmp_repeatition == 'r_1_r_2':
                                        model_energy[tmp_name].energy_r_2 = tmp_energy
                                else:
                                    model_tmp = Model()
                                    model_tmp.name = tmp_name
                                    if tmp_repeatition == '0':
                                        model_tmp.energy_r_0 = tmp_energy
                                    if tmp_repeatition == 'r_1':
                                        model_tmp.energy_r_1 == tmp_energy
                                    if tmp_repeatition == 'r_1_r_2':
                                        model_tmp.energy_r_2 == tmp_energy
                                    model_energy[tmp_name] = model_tmp
    #print(model_energy)
    return model_energy

def write_to_file(model_energy):
    sorted_model = sorted(model_energy)
    with open(f'{os.getcwd()}/result_porovnani_repeated', 'w') as file_result:
        for result in sorted_model:
            print(model_energy[result].write())
            #if result.energy > -4900 or result.energy < -4600:
            file_result.write(f'{model_energy[result].write()} \n')

def main():
    model = Model()
    args = get_argument()
    trajectories = os.listdir(args.dir)
    model_energy = make_file_for_graph(trajectories, args.dir, args.emin, model)
    write_to_file(model_energy)





if __name__ == '__main__':
    main()
