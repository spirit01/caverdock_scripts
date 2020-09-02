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
        self.emin1 = "\t"
        self.emin2 = "\t"
        self.emin3 = "\t"
        self.emin4 = "\t"
        self.emin5 = "\t"

    def write(self):
        line = f'model_{self.name} {self.emin1} {self.emin2} {self.emin3} {self.emin4} {self.emin5}'
        return line

def get_argument():
    parser = ArgumentParser()

    parser.add_argument("-dir", help="choose directory to load files",
                        metavar="DIR", dest="dir", required=True)

    parser.add_argument("-dir_final", help="choose directory to save files",
                    metavar="DIR", dest="dir_final", required=True)

    return parser.parse_args()

# tail -32 emin1.out | head -1 -> tahani energie
def make_file_for_graph(trajectories, dir):
    model_energy = {}
    emins = {"emin1.out", "emin2.out", "emin3.out", "emin4.out", "emin5.out"}
    for model in trajectories:
        for emin in emins:
            with open(f'{dir}{model}/{emin}') as file_tmp:
                    for line in file_tmp:
                        #if "NSTEP       ENERGY          RMS            GMAX         NAME    NUMBER" in line:
                        if "FINAL RESULTS" in line:
                            for line in file_tmp:
                                if "  1000      " in line:
                                    tmp_energy = float(line.split()[1])
                                    print(tmp_energy)
                                    #if tmp_energy > -4600 or tmp_energy < -5000:
                                    #    tmp_energy = "\t"
                                    tmp_name = int(model.split('_')[1])
                                    print(f'{dir}{model}/{emin}')

                                #print(name,  tmp_name, tmp_repeatition)
                                    if  tmp_name in model_energy:
                                        if emin == "emin1.out":
                                            model_energy[tmp_name].emin1 = tmp_energy
                                        if emin == "emin2.out":
                                            model_energy[tmp_name].emin2 = tmp_energy
                                        if emin == "emin3.out":
                                            model_energy[tmp_name].emin3 = tmp_energy
                                        if emin == "emin4.out":
                                            model_energy[tmp_name].emin4 = tmp_energy
                                        if emin == "emin5.out":
                                            model_energy[tmp_name].emin5 = tmp_energy

                                    else:
                                        model_tmp = Model()
                                        model_tmp.name = tmp_name
                                        if emin == "emin1.out":
                                            model_tmp.emin1 = tmp_energy
                                        if emin == "emin2.out":
                                            model_tmp.emin2 = tmp_energy
                                        if emin == "emin3.out":
                                            model_tmp.emin3 = tmp_energy
                                        if emin == "emin4.out":
                                            model_tmp.emin4 = tmp_energy
                                        if emin == "emin5.out":
                                            model_tmp.emin5 = tmp_energy

                                        model_energy[tmp_name] = model_tmp
    #print(model_energy)
    return model_energy

def write_to_file(model_energy, dir_final, ):
    sorted_model = sorted(model_energy)
    with open(f'{dir_final}/result_porovnani_repeated', 'w') as file_result:
        for result in sorted_model:
            #if result.energy > -4900 or result.energy < -4600:
            file_result.write(f'{model_energy[result].write()} \n')

def main():
    args = get_argument()
    tmp_trajectories = os.listdir(args.dir)
    trajectories = []
    for traj in tmp_trajectories:
        if "model_" in traj:
            trajectories.append(traj)
    model_energy = make_file_for_graph(trajectories, args.dir)
    write_to_file(model_energy, args.dir_final)





if __name__ == '__main__':
    main()
