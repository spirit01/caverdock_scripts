#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import logging
import pipeline_check_file
logger = logging.getLogger("__main__")

def minimalization(protein: str, restraint: str, configfile, verbose: bool, CD_lb_ub: str, index: int) -> str:
    logger.info(f'Working directory: {os.getcwd()}')
    logger.info(f'{os.getcwd()} {(configfile["RESULT_CD"]["name"])}_{index}-{CD_lb_ub}.pdbqt {protein}')
    string = ['bash', f'{configfile["11_RUN_TLEAP"]["11_run_tleap"]}']
    logger.info(string)
    subprocess.run(string)
    # @CA,C,N|(:BEO)@C1,C2,C3
    string = ['bash',f'{configfile["21_RUN_SANDER"]["21_run_sander"]}', f'{restraint}']
    logger.info(string)
    subprocess.run(string)
    pipeline_check_file.check_exist_file('complex.inpcrd')
    pipeline_check_file.check_exist_file('complex.prmtop')
    logger.info('Run sander')
    try:
        command = [f'{configfile["SANDER"]["path_sander"]}','-O', '-i', 'emin1.in', '-o', 'emin1.out', '-p',
                   'complex.prmtop', '-c', 'complex.inpcrd', '-ref', 'complex.inpcrd', '-x', 'mdcrd', '-r', 'emin1.rst']
        logger.info(command)
        subprocess.run(command)
        for i in range(1, 5):
            command = [f'{configfile["SANDER"]["path_sander"]}', '-O', '-i', f'emin{str(i + 1)}.in', '-o',
                       f'emin{str(i + 1)}.out', '-p', 'complex.prmtop','-c', f'emin{str(i)}.rst', '-ref', 'complex.inpcrd',
                       '-x', 'mdcrd', '-r', f'emin{str(i + 1)}.rst']
            logger.info(command)
            subprocess.run(command)

        for i in range(1, 6):
            command = [f'{configfile["AMBPDB"]["path_ambpdb"]}', '-p', 'complex.prmtop', '-c', f'emin{str(i)}.rst']
            logger.info(command)

            with open(f'emin{str(i)}.pdb', 'w') as file_emin:
                p = subprocess.Popen(command, stdout = file_emin)
                p.wait()
    except:
        logger.error('Cannot run amber. Check logfile.')
        logger.info('Cannot run amber. Check logfile.')
        sys.exit(1)
    new_protein = remove_ligand_from_emin(verbose, configfile, index)
    return new_protein


def remove_ligand_from_emin(verbose: bool, configfile, index: int) -> str:
    logger.info(os.getcwd())
    pipeline_check_file.check_exist_file('emin5.pdb')
    num = index + 1
    with open(f'{os.getcwd()}/emin5.pdb') as oldfile, open(f'{os.getcwd()}/new_protein_H_{num}.pdb', 'w') as newfile:
        for line in oldfile:
            if not configfile["LIGAND"]["name"] in line:
                newfile.write(line)
    pipeline_check_file.check_exist_file(f'{os.getcwd()}/new_protein_H_{num}.pdb')
    logger.info(f'New structure from experiment: {os.getcwd()}/new_protein_H_{num}.pdb')

    return f'{os.getcwd()}/new_protein_H_{num}.pdb'
