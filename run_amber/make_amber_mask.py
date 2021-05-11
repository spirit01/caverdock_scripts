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

    #if not check_config_file(args.config, args.verbose):
    #    sys.exit(1)
    #configfile = configparser.ConfigParser()
    #configfile.read(f'{args.config}')

    #hdlr = logging.FileHandler(
    #    f'framework_{strftime("%Y-%m-%d__%H-%M-%S", localtime())}.log')
    #logging.root.addHandler(hdlr)
    #logging.root.setLevel(logging.INFO)
    #logging.root.setLevel(logging.DEBUG)
    #logging.info(f'***Output from framework*** {strftime("%Y-%m-%d__%H-%M-%S", localtime())} \n')
    #logging.info(f'#Protein : {args.protein} -> protein.pdb \n')
    #logging.info(f'#Ligand : {args.ligand}  {configfile["LIGAND"]["name"]} \n')
    #logging.info(f'#Tunnel: {args.tunnel} \n')

    pdb = pt.load("protein_with_tunnel.pdb")
    pdb_topology = pt.load_topology('protein_with_tunnel.pdb')
    restraint_residue = []

    for i in range(1, pdb_topology.n_residues):
        #print(f'\':{i} FIL T\'')
        string_index = f':{i} :FIL T'
        if pt.distance(pdb, string_index)<12.0:
        #    simp_top = pdb_topology.simplify()
            #name = simp_top.residue()
            restraint_residue.append(f'{pdb_topology.residue(i).index},')
            #string_residues.join(f':{pdb_topology.residue(i).index}')
            #restraint_residue.append(name)
    string_residues = ' '.join([str(elem) for elem in restraint_residue])
    print(string_residues)


if __name__ == '__main__':
    main()