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
from statistics import stdev
from fractions import Fraction as fr
import numpy

def get_argument():
    parser = ArgumentParser()

    parser.add_argument("-file", help="File's name with numbers", type=Path)
    parser.add_argument("-column", help="Number of column for analysis.",type=int, metavar = 'N')


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

def count_deviation(file, column):
    sum = 0
    array = []
    with open(file) as f:
        first_line = f.readline()
        #print(first_line)
        first_num = [float(value) for value in re.findall('\d+\.?\d*', first_line)]            #[v.translate(None, ' \t\r\n\f\x0a') for v in first_line]
        energies = []
        for line in f:
            second_num = [float(value) for value in re.findall('\d+\.?\d*', line)]
            energies.append(second_num)
            differ = numpy.power(first_num[column] - second_num[column],2)
            #print(differ, first_num[column], second_num[column], line)
            first_num[column] = second_num[column]
            sum = sum + differ
        result = numpy.sqrt(sum/(len(energies)-1))
        print(f'{result:e}')

def main():
    args = get_argument()
    #check_input_data(args)
    print(f'Current working directory: {os.getcwd()}')
    count_deviation(args.file, args.column)


if __name__ == '__main__':
    main()