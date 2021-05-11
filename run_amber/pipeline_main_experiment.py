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
import pytraj as pt
from Bio.PDB import NeighborSearch, PDBParser, Selection

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

    #parser.add_argument("-protein", help="Structure of protein in format pdb.", type=Path)

    #parser.add_argument("-ligand", help = 'Ligands name in pdbqt format.', type=Path, required=True)

    #parser.add_argument("-tunnel", help = 'Tunnel name in dsd format.', type=Path, required=True)

    #parser.add_argument("-config", help = 'Location of config.ini file.', type=Path, required=True)

    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        dest="verbose", action = "store_true")

    return parser.parse_args()

def check_config_file(config, verbose):
    if verbose:
        print(f'Source config: {config}')
    if os.path.exists(f'{config}'):
        return True
    else:
        print('Config.ini file does not exist!')

def main():
    args = get_argument()
    #check_input_data(args)
    print(f'Current working directory: {os.getcwd()}')



if __name__ == '__main__':
    main()