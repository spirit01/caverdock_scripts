#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import os
import sys
from argparse import ArgumentParser
from pathlib import Path
import shutil
import configparser
import logging
from time import localtime, strftime
import subprocess

import pipeline_find_maximum
import pipeline_finish_experiment
import pipeline_make_graph
import pipeline_caverdock
import pipeline_prepare_experiment
import pipeline_amber
import pipeline_check_file
import pipeline_caver

class Experiment:
    def __init__(self, name, ligand, tunnel, restraint, config,
                 cd_trajectory, lb_ub, order_of_experiment):
        self.protein = name
        self.ligand = ligand
        self.tunnel = tunnel
        self.restraint = restraint
        self.config = config
        self.verbose = []
        self.CD_lb_ub = lb_ub
        self.directory_result = 'trajectory'
        self.caverdock_trajectory = cd_trajectory
        self.order_of_experiment = order_of_experiment
        self.number_of_models = 0
        self.catomnum = 'default'
        # info about bottleneck. Number of model(=disc), energy in that disc, the closest residue
        self.bottleneck = ''
        self.energy_in_bottleneck = 0
        self.residue_in_bottleneck = ''
        self.df = ''

    def __str__(self):
        return f'Experiment: {self.protein}'

    @classmethod
    def check_exist_file(file):
        if not os.path.exists(f'{file}') or os.path.getsize(file) < 0:
            print(f'File {file} does not exist. Exit framework.')
            sys.exit(1)

    def make_exp_directory(self):
        try:
            shutil.rmtree(f'{self.directory_result}_{self.order_of_experiment}')
            isdir = False
        except:
            isdir = os.path.isdir(f'{self.directory_result}_{self.order_of_experiment}')
        if not isdir:
            print('Trajectories do not exist')
            os.mkdir(f'{self.directory_result}_{self.order_of_experiment}')
        

        try:
            os.mkdir(f'receptor_{self.order_of_experiment}')
        except OSError as error:
            print(error)
        try:
            os.mkdir(f'receptor_{self.order_of_experiment}/input')
        except OSError as error:
            print(error)

    def find_near_residue_in_bottleneck(self):
        try:
            with open(f'bottleneck_{self.order_of_experiment}-model0') as file:
                file.readline()  # skip first line in file
                # PRO 144 65 (1.17336)
                data = file.readline()
                self.residue_in_bottleneck = (data.split(' ')[0], data.split(' ')[1])
        except:
            self.residue_in_bottleneck = ('None', 'None')


class Experiments:
    # identify distance between bottleneck and stop experiment
    def __init__(self):
        self.all_experiments = []
        self.all_models_residue_and_residue_number = []

    def __len__(self):
        return len(self.all_experiments)

    def __getitem__(self, item):
        return self.all_experiments[item]


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

    parser.add_argument("--caverdock_trajectory", '-cd_traj', help="Trajectory from CaverDock in format pdbqt.",
                        type=Path)

    parser.add_argument("--protein", '-p', help="Structure of protein in format pdb.", type=Path)

    parser.add_argument("--CD_lb_ub", '-ul', help="Choose lb or ub. ", choices=['lb', 'ub'],
                        dest='CD_lb_ub', default='lb')

    parser.add_argument("--ligand", '-l', help='Ligands name in pdbqt format.', type=Path, required=True)

    parser.add_argument("--tunnel", '-t', help='Tunnel name in pdb format.', required=True, type=Path)

    parser.add_argument("-tleapfile", help='Choose your own tleap file. Please, you must follow the file naming .'
                        , type=Path)

    parser.add_argument("-catomnum", help='Choose catomnum atom for caverdock.', default='default')

    parser.add_argument("-config", help='Location of config.ini file.', type=Path, required=True)

    parser.add_argument("--restraint", '-r', help='Set restrain for ligand. For example @CA,C,N|(:BEO)@C1,C2,C3',
                        required=True)

    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        dest="verbose", action="store_true")

    return parser.parse_args()


def main():
    args = get_argument()

    hdlr = logging.FileHandler(f'framework_{strftime("%Y-%m-%d__%H-%M-%S", localtime())}.log')
    hdlr.setLevel(logging.DEBUG)
    sh = logging.StreamHandler()
    sh.setLevel(logging.DEBUG)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.FileHandler("debug.log"),
                                  logging.StreamHandler()])

    # logFormatter = logging.Formatter(fmt=' %(name)s :: %(levelname)-8s :: %(message)s')

    logger = logging.getLogger(__name__)
    # logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(hdlr)
    logger.addHandler(sh)
    if args.verbose:
        logger.info(f'Current working directory: {os.getcwd()}')
    source = os.getcwd()
    if not pipeline_check_file.check_config_file(args.config):
        sys.exit(1)

    configfile = configparser.ConfigParser()
    configfile.read(f'{args.config}')
    logger.info(f'***Output from framework*** {strftime("%Y-%m-%d__%H-%M-%S", localtime())} \n')
    order_of_experiment = 0
    shutil.copy(args.protein, f'new_protein_H_{order_of_experiment}.pdb')
    new_structure = args.protein
    exps = Experiments()
    model_with_maximum_energy_and_energy = []

    pipeline_prepare_experiment.prepare_ligand_for_ammber(configfile, args.verbose, args.ligand)
    shutil.copy(str(args.tunnel), f'tunnel_{order_of_experiment}.pdb')
    tunnel = Path(f'tunnel_{order_of_experiment}.pdb')
    pipeline_caver.discretizer(tunnel)

    while not pipeline_finish_experiment.stop_experiment(exps.all_models_residue_and_residue_number):
        # skip first CD calculation
        # if args.caverdock_trajectory:
        #    exp1 = Experiment(f'new_protein_H_{order_of_experiment}.pdb', args.ligand,
        #                      args.tunnel, args.restraint, args.config,
        #                      args.caverdock_trajectory, args.CD_lb_ub, order_of_experiment)
        #    args.caverdock_trajectory = False
        # else:
        exp1 = Experiment(f'new_protein_H_{order_of_experiment}.pdb', args.ligand, tunnel,
                          args.restraint, args.config,
                          f'{configfile["RESULT_CD"]["name"]}_{order_of_experiment}-lb.pdbqt',
                          args.CD_lb_ub, order_of_experiment)
        if args.catomnum:
            exp1.catomnum = args.catomnum

        exps.all_experiments.append(exp1)
        logger.info(f'Protein: {exps.all_experiments[order_of_experiment].protein}')
        logger.info(f'Trajectory: {os.getcwd()}/{exps[order_of_experiment].directory_result}'
                    f'{exps.all_experiments[order_of_experiment].order_of_experiment}')
        logger.info(f'Index, number of runs {order_of_experiment}')
        exps[order_of_experiment].make_exp_directory()
        if args.verbose:
            logger.info(f'Directory with result: {os.getcwd()}/{exps[order_of_experiment].directory_result}_'
                        f'{exps.all_experiments[order_of_experiment].order_of_experiment}')
        logger.info(f'Directory with result: {os.getcwd()}/{exps[order_of_experiment].directory_result}_'
                    f'{exps.all_experiments[order_of_experiment].order_of_experiment}')
        # change directory to actual bottleneck and its trajectory
        pipeline_prepare_experiment.check_input_data(exps[order_of_experiment].protein,
                                                     exps[order_of_experiment].ligand, exp1.tunnel)
        exps[order_of_experiment].protein = pipeline_prepare_experiment.prepare_protein(configfile,
                                                                                        exps[
                                                                                            order_of_experiment].protein,
                                                                                        args.verbose, exps[
                                                                                            order_of_experiment].order_of_experiment)
        pipeline_prepare_experiment.prepare_logfile(exps[order_of_experiment].protein,
                                                    exps[order_of_experiment].ligand,
                                                    exps[order_of_experiment].tunnel,
                                                    exps[order_of_experiment].restraint,
                                                    configfile,
                                                    hdlr, args.verbose)
        pipeline_caverdock.caverdock(exps[order_of_experiment].protein, exps[order_of_experiment].ligand,
                                     exps[order_of_experiment].tunnel,
                                     configfile, exps[order_of_experiment].verbose,
                                     exps[order_of_experiment].CD_lb_ub, args.caverdock_trajectory,
                                     exp1, exps[order_of_experiment].order_of_experiment, args.catomnum)

        model_with_maximum_energy_and_energy = pipeline_find_maximum.find_maximum(exps[order_of_experiment].CD_lb_ub,
                                                                                  exps[
                                                                                      order_of_experiment].order_of_experiment,
                                                                                  exps, configfile)

        logger.info(f'Bottleneck is {model_with_maximum_energy_and_energy}')
        exps[order_of_experiment].number_of_models = model_with_maximum_energy_and_energy[0]
        exps[order_of_experiment].energy_in_bottleneck = model_with_maximum_energy_and_energy[1]
        exps[order_of_experiment].bottleneck = model_with_maximum_energy_and_energy[2]
        if order_of_experiment != 0:
            shutil.copy(f'new_protein_{order_of_experiment}.pdb', f'receptor_{order_of_experiment}/input')
            logger.info(f'Prepare the new tunnel with CAVER.')
            shutil.copy(f'{args.tunnel}',
                        f'./receptor_{order_of_experiment}/tunnel_0.pdb')
            os.chdir(f'receptor_{order_of_experiment}')

            exps[order_of_experiment].tunnel = pipeline_caver.run_caver(configfile, Path('tunnel_0.pdb'))
            print(exps[order_of_experiment].tunnel)
            shutil.copy(f'{exps[order_of_experiment].tunnel}',
                        Path(f'tunnel_{order_of_experiment}.pdb'))
            shutil.copy(f'{exps[order_of_experiment].tunnel}',
                        Path(f'{source}/tunnel_{order_of_experiment}.pdb'))
            #tunnel_dsd = exps[order_of_experiment].tunnel.split('.')[0]

            #shutil.copy(f'./out/data/clusters/{tunnel_dsd}.dsd',
            #            f'{source}/receptor_tunnel_{order_of_experiment}.dsd')
            os.chdir(source)
            pipeline_caver.discretizer(Path(f'tunnel_{order_of_experiment}.pdb'))
        pipeline_prepare_experiment.prepare_complex_for_amber(exps[order_of_experiment].protein, configfile,
                                                              f'{exps[order_of_experiment].directory_result}_{exps[order_of_experiment].order_of_experiment}',
                                                              exps[order_of_experiment].number_of_models)

        dir = (f'{os.getcwd()}/{exps[order_of_experiment].directory_result}_'
               f'{exps[order_of_experiment].order_of_experiment}/'
               f'model_{exps[order_of_experiment].number_of_models}')
        os.chdir(dir)
        new_structure = pipeline_amber.minimalization(exps[order_of_experiment].protein,
                                                      exps[order_of_experiment].restraint, configfile,
                                                      args.verbose, exps[order_of_experiment].CD_lb_ub,
                                                      exps[order_of_experiment].order_of_experiment)

        os.chdir(source)
        shutil.copy(new_structure, source)
        if args.verbose:
            logger.info(f'{exps.all_experiments[order_of_experiment].order_of_experiment} run of framework is done.')
        logger.info(f'{exps.all_experiments[order_of_experiment].order_of_experiment} run of framework is done')
        # TODO could be better. AMBER has one redundant run.
        exps[order_of_experiment].find_near_residue_in_bottleneck()
        exps.all_models_residue_and_residue_number.append(exps[order_of_experiment].residue_in_bottleneck)
        print(exps[order_of_experiment].find_near_residue_in_bottleneck())
        order_of_experiment = order_of_experiment + 1

    # -2: je to kvuli tomu, ze posledni iterace obsahuje uz opakujicic se residuum, takze to muzeme odstranit. Na
    #  [('ARG', '155'), ('ILE', '210'), ('TRP', '139'), ('ILE', '210')] s -2 udělá správně jenom 3 iterace a posledni,
    # kde uz se opakuje residuum vynecha z grafu.
    #  -2: last iteration contains repeted residuum. In the example [('ARG', '155'), ('ILE', '210'), ('TRP', '139'),
    #  ('ILE', '210')] with '-2( makes it 3 iterations and skip the last one -
    # correct behavior
    if exps.all_experiments[order_of_experiment-1] == 2:  # speial condition for only two runs of framework
        pipeline_make_graph.plot_graph(exps.all_experiments[order_of_experiment - 1].order_of_experiment,
                                       exps[order_of_experiment - 1].CD_lb_ub, exps[order_of_experiment - 1].df, exps,
                                       configfile)
    else:
        pipeline_make_graph.plot_graph(exps.all_experiments[order_of_experiment - 2].order_of_experiment,
                                       exps[order_of_experiment - 2].CD_lb_ub, exps[order_of_experiment - 2].df, exps,
                                       configfile)
    pipeline_finish_experiment.summary_result_and_setting(exps, args)
    #pipeline_finish_experiment.make_caverdock_config(exps, args, configfile)


if __name__ == '__main__':
    main()
