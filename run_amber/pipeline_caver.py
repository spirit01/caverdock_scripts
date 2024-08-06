#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os

import re
import shutil
import subprocess
import sys
import configparser

from pathlib import Path

from pip._vendor.requests.compat import str

import pipeline_check_file
import pipeline_prepare_experiment


class TUNNEL:
    def __init__(self, name):
        self.name = name
        self.points = []

    @property
    def begin(self):
        return self.points[0] if self.points else None

    @property
    def end(self):
        return self.points[-1] if self.points else None

    def load_tunnel(self):
        with open(f'{self.name}') as file:
            for line in file:
                if not line.strip():
                    break
                if 'ATOM' in line:
                    line = line.strip('\n')
                    array = line.split(' ')
                    array = list(filter(None, array))
                    point = POINT(float(array[6]), float(array[7]), float(array[8]))
                    self.points.append(point)



class TUNNELS:
    def __init__(self):
        self.original_tunnel = []
        self.list_tunnels = []
        self.allowed_tunnels = []

    def eliminate_divergent_tunnels(self, tolerance=3):
        if not self.original_tunnel or not self.original_tunnel.begin:
            # Pokud není žádný původní tunel nebo nemá začátek, není co porovnávat
            return

            # Vyfiltrujte tunely, které mají začátek a konec blízký začátku a konci původního tunelu s tolerancí
        self.allowed_tunnels = [
            tun for tun in self.list_tunnels
            if (
                    tun.begin and tun.end and  # Přidáme kontrolu, že begin a end existují
                    (
                            abs(tun.begin.x - self.original_tunnel.begin.x) < tolerance and
                            abs(tun.begin.y - self.original_tunnel.begin.y) < tolerance and
                            abs(tun.begin.z - self.original_tunnel.begin.z) < tolerance
                    ) and any(  # Přidáme kontrolu, že konec tunelu je blízko libovolného bodu v rámci original_tunnel
                abs(tun.end.x - orig_point.x) < tolerance and
                abs(tun.end.y - orig_point.y) < tolerance and
                abs(tun.end.z - orig_point.z) < tolerance
                for orig_point in self.original_tunnel.points
            )
            )
        ]

    def print_allowed_tunnels_coordinates(self):
        for tun in self.allowed_tunnels:
            print(f"Similar tunnel: {tun.name}")
            print(f"Tunnel Begin Coordinates: ({tun.begin.x}, {tun.begin.y}, {tun.begin.z})")
            print(f"Tunnel End Coordinates: ({tun.end.x}, {tun.end.y}, {tun.end.z})")

        if len(self.allowed_tunnels) == 0:
            print(f"Any tunnel found.")

    def print_all_tunnels_coordinates(self):
        for tun in self.list_tunnels:
            print(f"Tunnel Begin Coordinates: ({tun.begin.x}, {tun.begin.y}, {tun.begin.z})")
            print(f"Tunnel End Coordinates: ({tun.end.x}, {tun.end.y}, {tun.end.z})")


class POINT:  # tunnel's point
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def print_point(self):
        print(self.x, self.y, self.z)


def load_input(tunnel):
    tunnel_orig = TUNNEL(tunnel)
    tunnel_orig.load_tunnel()

    tunnels = TUNNELS()
    tunnels.original_tunnel = tunnel_orig

    caver_output = ['./out/data/clusters/' + file for file in os.listdir('./out/data/clusters/')]
    print(caver_output)
    for tun in caver_output:
        tunnel = Path(tun)
        print(tunnel.resolve())
        tunnel_minor = TUNNEL(tunnel.resolve())
        tunnel_minor.load_tunnel()
        print(tunnel_minor)
        tunnels.list_tunnels.append(tunnel_minor)
    print(tunnels.list_tunnels)
    return tunnels

def discretizer(tunnel):
    command=[f'discretizer', '-f', f'{tunnel.resolve()}', '--output-file', f'{tunnel.stem}.dsd']
    print(command)
    subprocess.run(command)


def run_caver(config_framework: object, orig_tunnel):
    #order_of_exoeriment = 1
    #prepare_data(order_of_exoeriment)
    #run in folder receptor_{order_of_exoeriment}
    command = ['java', '-Xmx600m', '-cp', f'{config_framework["CAVER"]["lib"]}',
               '-jar', f'{config_framework["CAVER"]["caverjar"]}', '-home',
               f'{config_framework["CAVER"]["caver"]}', '-pdb', 'input', '-conf',
               f'{config_framework["CAVER"]["config"]}',
               '-out', './out']
    subprocess.run(command)
    tunnels = load_input(orig_tunnel.resolve())
    tunnels.eliminate_divergent_tunnels()
    tunnels.print_allowed_tunnels_coordinates()
    #discretizer(tunnels.allowed_tunnels[0].name)
    tunnel_name = Path(tunnels.allowed_tunnels[0].name)
    if len(tunnels.allowed_tunnels) == 0:
        print(f'CAVER didn´t  produce similar tunnel. Framework ends.')
        sys.exit(1)
    return tunnel_name


def prepare_data(order_of_experiment):
    try:
        os.mkdir(f'receptor_{order_of_experiment}')
    except OSError as error:
        print(error)
    try:
        os.mkdir(f'receptor_{order_of_experiment}/input')
    except OSError as error:
        print(error)
    shutil.copy(f'new_protein_{order_of_experiment}.pdb', f'receptor_{order_of_experiment}/input')
    os.chdir(f'receptor_{order_of_experiment}')


def main():
    config_file = '/home/petranem/Dokumenty/HPC/caverdock_scripts/run_amber/config.ini'
    orig_tunnel = '/home/petranem/Dokumenty/HPC/CD2-DhaA/test_poznan_framework/P1/01-WT/tun_cl_001_1.pdb'
    configfile = configparser.ConfigParser()
    configfile.read(f'/home/petranem/Dokumenty/HPC/caverdock_scripts/run_amber/config.ini')
    run_caver(configfile, orig_tunnel)



if __name__ == '__main__':
    main()
