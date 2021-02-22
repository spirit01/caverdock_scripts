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
from contextlib import ExitStack




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

    parser.add_argument("-config", help="Config file with traj, energies and proteins", type=Path, required = True)

    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        dest="verbose", action = "store_true")

    return parser.parse_args()

def check_config_file(config, verbose):
    if verbose:
        print(f'{config}')
    if os.path.exists(f'{config}'):
        return True
    else:
        print('Config.ini file does not exist!')
    return False

    #with open(traj1) as file_traj1, open(traj2) as file_traj2:
    #        for line1, line2 in zip(file_traj1, file_traj2):



def make_trajectory(filenames):
    with ExitStack() as stack:
        files = [stack.enter_context(open(fname)) for fname in filenames]

    return 0

def make_traj_dat_filename(configfile):
    trajs = configfile['TRAJ']['traj'].split('|')
    trajs = [x.strip(' ') for x in trajs]

    energies = configfile['ENERGY']['energy'].split('|')
    energies = [x.strip(' ') for x in energies]

    proteins = configfile['PROTEIN']['protein'].split('|')
    proteins = [x.strip(' ') for x in proteins]

    traj_energy_protein = list(zip(trajs, energies, proteins))
    return traj_energy_protein

def generate_new_trajectory(traj_energy_protein):
    energy = [traj_energy_protein[1] for en in traj_energy_protein]
    with ExitStack() as stack:
        #for traj, energy, protein in traj_energy_protein:
        files = [stack.enter_context(open(fname)) for fname in energy]
        print(files)


def main():
    args = get_argument()

    if not check_config_file(args.config, args.verbose):
        sys.exit(1)
    configfile = configparser.ConfigParser()
    configfile.read(f'{args.config}')

    hdlr = logging.FileHandler(
        f'common_point_{strftime("%Y-%m-%d__%H-%M-%S", localtime())}.log')
    curr_dir = os.getcwd()
    logging.root.addHandler(hdlr)
    logging.root.setLevel(logging.INFO)
    logging.root.setLevel(logging.DEBUG)
    logging.info(f'*** Make new trajectory according to energy*** {strftime("%Y-%m-%d__%H-%M-%S", localtime())} \n')

    traj_energy_protein = make_traj_dat_filename(configfile)
    generate_new_trajectory(traj_energy_protein)

if __name__ == '__main__':
    main()