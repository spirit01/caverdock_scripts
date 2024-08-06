#!/usr/bin/env python
"""
This code was developed with the assistance of the ChatGPT model from OpenAI.
The ChatGPT model was used for consultations and ideas during the creation of this project.
"""

import math
from argparse import ArgumentParser
import sys
import os
from pathlib import Path


def get_argument():
    parser = ArgumentParser()

    parser.add_argument("--tunnel_original", "-t_orig", help="Tunnel pdb", required=True)

    parser.add_argument("--tunnel_minor", "-t_min", help="Tunnel pdb", nargs='+', required=True)

    #parser.add_argument("--output", "-o", default='tunnel.pdb', help="Output file.")

    return parser.parse_args()


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
        with open(self.name) as file:
            for line in file:
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


def main():
    args = get_argument()
    tunnel_orig = TUNNEL(args.tunnel_original)
    tunnel_orig.load_tunnel()

    tunnels = TUNNELS()
    tunnels.original_tunnel = tunnel_orig

    for tun in args.tunnel_minor:
        tunnel_minor = TUNNEL(tun)
        tunnel_minor.load_tunnel()
        tunnels.list_tunnels.append(tunnel_minor)

    tunnels.eliminate_divergent_tunnels()
    tunnels.print_allowed_tunnels_coordinates()


if __name__ == '__main__':
    main()
