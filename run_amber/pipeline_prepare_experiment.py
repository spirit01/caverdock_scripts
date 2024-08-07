#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import shutil
import logging
from time import localtime, strftime
import pipeline_check_file

NON_STADARD_AMINOACID = ['HIE', 'HID']
logger = logging.getLogger("__main__")


# TODO check, whether setting from terminal is the same as [LIGAND][ligand] -> if not: warning.

def check_input_data(protein, ligand, tunnel):
    if not os.path.exists(protein):
        logger.error(f'{protein} does not exist')
        sys.exit(1)
    if not os.path.exists(ligand):
        logger.error(f'{ligand} does not exist')
        sys.exit(1)
    if not os.path.exists(tunnel):
        logger.error(f'{tunnel} does not exist')
        sys.exit(1)


def prepare_logfile(protein: str, ligand: str, tunnel: str, restraint: str, configfile,
                    hdlr, verbose):
    check_input_data(protein, ligand, tunnel)

    logger.info(f'#Protein: {protein}\n')
    logger.info(f'#Ligand: {ligand}  {configfile["LIGAND"]["name"]} \n')
    logger.info(f'#Tunnel: {tunnel} \n')
    logger.info(f'#Restraint: {restraint}')

    rslt_dir = os.getcwd()

    if verbose:
        logger.info("Verbosity turned on")
        logger.info(f'Output from framework*** {strftime("%Y-%m-%d__%H-%M-%S", localtime())}')
        logger.info(f'Protein : {protein}')
        logger.info(f'Ligand : {ligand} {configfile["LIGAND"]["name"]}')
        logger.info(f'Tunnel: {tunnel}')
        logger.info(f'Dir for result: {rslt_dir}')
        logger.info(f'Restraint: {restraint}')


def make_dir_for_amber(file_all, protein, trajectory):
    for count, file in enumerate(file_all, start=0):
        ismod = os.path.isdir(f'./{trajectory}/model_{count}')
        if not ismod:
            os.mkdir(f'./{trajectory}/model_{count}')
        with open(f'./{trajectory}/model_{count}/position_ligand_{count}.pdbqt', 'w') as file_traj:
            file_traj.write(file)
        shutil.copy(f'{os.getcwd()}/{protein}', f'./{trajectory}/model_{count}/')
        shutil.copy(f'{os.getcwd()}/{protein}', f'./{trajectory}/model_{count}/')
        for i in range(1, 5):
            pipeline_check_file.remove_file(f'./{trajectory}/model_{count}/emin{i}')
        pipeline_check_file.remove_file(f'./{trajectory}/model_{count}/complex.inpcrd')
        pipeline_check_file.remove_file(f'./{trajectory}/model_{count}/complex.prmtop')
        pipeline_check_file.remove_file(f'/{trajectory}/model_{count}/ligand.prepi')


def check_charge_ligand(ligand):
    total_charge = 0
    with open(ligand) as file_ligand:
        for line in file_ligand:
            if 'ATOM' in line:
                charge_atom = float(line.split()[10])
                total_charge = total_charge + charge_atom
    return round(total_charge)


def prepare_ligand_for_ammber(configfile, verbose, ligand):
    command = ['pythonsh', f'{configfile["PDBQT_TO_PDB"]["path_pdbqt_to_pdb"]}', '-f',
               f'{ligand}',
               f'-o', f'{os.getcwd()}/ligand_H.pdb']
    logger.info(command)
    subprocess.run(command)
    command = ['antechamber', '-i', 'ligand_H.pdb', '-fi', 'pdb', '-o', 'ligand.mol2',
               '-fo', 'mol2']  # ,'-c', 'bcc']
    logger.info(command)
    subprocess.run(command)
    command = ['antechamber', '-i', 'ligand.mol2', '-fi', 'mol2', '-o', 'ligand_H.pdb',
               '-fo', 'pdb']  # ,'-c', 'bcc']
    logger.info(command)
    subprocess.run(command)
    command = ['antechamber', '-i', 'ligand.mol2', '-fi', 'mol2', '-o', 'ligand.prepi',
               '-fo', 'prepi']
    logger.info(command)
    subprocess.run(command)
    logger.info(command)
    subprocess.run(command)
    pipeline_check_file.check_exist_file(f'{os.getcwd()}/ligand_H.pdb')
    subprocess.call(f'sed -i \'s/<0> d/{configfile["LIGAND"]["name"]} d/g\' ligand_H.pdb',
                    shell=True)  # ligand_for_complex.pdb

    pipeline_check_file.check_exist_file(f'{os.getcwd()}/ligand_H.pdb')
    command = ['/usr/bin/obabel', '-ipdb', 'ligand_H.pdb', '-O', 'ligand_HH.pdb', '-h']
    logger.info(command)
    subprocess.run(command)
    pipeline_check_file.check_exist_file(f'{os.getcwd()}/ligand_HH.pdb')
    command = ['antechamber', '-i', 'ligand_HH.pdb', '-fi', 'pdb', '-o', 'ligand.mol2',
               '-fo', 'mol2']  # ,'-c', 'bcc']
    logger.info(command)
    subprocess.run(command)
    command = ['antechamber', '-i', 'ligand.mol2', '-fi', 'mol2', '-o', 'ligand_HHH.pdb',
               '-fo', 'pdb']  # ,'-c', 'bcc']
    logger.info(command)
    subprocess.run(command)
    if not check_charge_ligand(ligand) == 0:
        total_charge = check_charge_ligand(ligand)
        command = [f'antechamber', '-i', f'ligand_HHH.pdb', '-fi', 'pdb', '-o',
                   f'./ligand.prepi', '-fo', 'prepi', '-c', 'bcc', '-nc', f'{total_charge}']
        logger.info(command)
        subprocess.run(command)

    else:
        command = [f'antechamber', '-i', f'./ligand_HHH.pdb', '-fi', 'pdb', '-o',
                   f'./ligand.prepi', '-fo', 'prepi', '-c', 'bcc']
        logger.info(command)
        subprocess.run(command)
    pipeline_check_file.check_exist_file(f'{os.getcwd()}/ligand.prepi')
    command = [f'parmchk2', '-i', f'./ligand.prepi', '-f',
               'prepi', '-o', f'./frcmod_lig2']
    logger.info(command)
    subprocess.run(command)
    pipeline_check_file.check_exist_file(f'frcmod_lig2')


def prepare_complex_for_amber(protein, configfile, trajectory, number_of_model):
    model = f'model_{number_of_model}'
    shutil.copy(f'{os.getcwd()}/ligand.prepi', f'./{trajectory}/model_{number_of_model}/')
    shutil.copy(f'{os.getcwd()}/frcmod_lig2', f'./{trajectory}/model_{number_of_model}/')

    command = ['pythonsh', f'{configfile["PDBQT_TO_PDB"]["path_pdbqt_to_pdb"]}', '-f',
               f'{os.getcwd()}/{trajectory}/{model}/position_ligand_{number_of_model}.pdbqt',
               f'-o', f'{os.getcwd()}/{trajectory}/{model}/ligand_HHH.pdb']
    logger.info(command)
    subprocess.run(command)
    pipeline_check_file.check_exist_file(f'{os.getcwd()}/{trajectory}/{model}/ligand_HHH.pdb')
    subprocess.call(f'sed -i \'s/<0> d/{configfile["LIGAND"]["name"]} d/g\' ./{trajectory}/{model}/ligand_HHH.pdb',
                    shell=True)

    pipeline_check_file.check_exist_file(f'{os.getcwd()}/{trajectory}/{model}/ligand_HHH.pdb')

    subprocess.call(  # remove last line in file with END. IMPORTANT!
        f'head -n -1 ./{trajectory}/{model}/{protein} > ./{trajectory}/{model}/complex.pdb | '
        f'echo TER >> ./{trajectory}/{model}/complex.pdb',
        shell=True)
    subprocess.call(f'cat ./{trajectory}/{model}/ligand_HHH.pdb'
                    f' >> ./{trajectory}/{model}/complex.pdb ',
                    # f'| echo TER >> ./{trajectory}/{model}/complex.pdb',
                    shell=True)
    subprocess.call(f'echo END >> ./{trajectory}/{model}/complex.pdb',
                    shell=True)
    pipeline_check_file.check_exist_file(f'{os.getcwd()}/{trajectory}/{model}/complex.pdb')
    pipeline_check_file.check_exist_file(f'{os.getcwd()}/{trajectory}/{model}/complex.pdb')


# check non-standard amino-acid. Hie, hid -> remove all hydrogens from protein
def check_non_standard_amino_aic(protein):
    with open(protein) as protein_file:
        for line in protein_file:
            # residue = line.split(' ')[3]
            if any(word in line for word in NON_STADARD_AMINOACID):
                return False
    return True


def remove_hydrogens(protein, index, configfile):
    command = [f'pdb4amber', '-i', f'{protein}', '-o', f'new_protein_{index}.pdb',
               '--nohyd']
    logger.info(command)
    subprocess.run(command)


def prepare_protein(configfile, protein, verbose, index):
    # prepare_receptor = ''
    logger.info(f'working directory {os.getcwd()}')
    if not check_non_standard_amino_aic(protein):
        logger.info(f'remove histidin')
        remove_hydrogens(f'{protein}', index, configfile)
        command = ['pythonsh', f'{configfile["PREPARE_RECEPTOR"]["path_prepare_receptor"]}', '-r',
                   protein, '-o',
                   f'new_protein_{index}.pdbqt']
        logger.info(command)
        subprocess.run(command)
        protein = f'new_protein_{index}.pdb'

    else:
        command = ['pythonsh', f'{configfile["PREPARE_RECEPTOR"]["path_prepare_receptor"]}',
                   '-r', f'{protein}', '-o',
                   f'new_protein_H_{index}.pdbqt']

        logger.info(command)
        subprocess.run(command)

    return protein
