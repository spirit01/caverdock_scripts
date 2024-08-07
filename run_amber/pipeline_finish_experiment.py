#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# compare size of list with duplicity and without them: if residue appears again,
# set without duplicity is smaller than original one
import logging
import subprocess
import pipeline_check_file

logger = logging.getLogger("__main__")


def stop_experiment(model_with_maximum_energy_and_energy):
    set_full_list = set(model_with_maximum_energy_and_energy)
    contains_duplicates = len(model_with_maximum_energy_and_energy) != len(set_full_list)
    return contains_duplicates


def summary_result_and_setting(exps, args):
    logger.info(f'INPUT : \n Protein: {args.protein} \n Ligand: {args.ligand} '
                f'\n Tunnel: {args.tunnel} \n Catomnum: {args.catomnum} \n'
                f'Restraint: {args.restraint} ')
    for exp in exps.all_experiments[:-1]:
        logger.info(f'RESULT')

        logger.info(f'Order of experiment: {exp.order_of_experiment}')
        logger.info(f'Maximum in model number {exp.number_of_models} \n'
                    f'Distance of bottleneck from the start of tunnel {exp.bottleneck} \n'
                    f'Energy in bottleneck {exp.energy_in_bottleneck} kcal/mol \n'
                    f'Bottleneck on residue {exp.residue_in_bottleneck[0]} with number '
                    f'{exp.residue_in_bottleneck[1]} \n'
                    f'Catomnum atom in ligand: {args.catomnum}')
        logger.info(f'Input structure to CaverDock: {exp.protein} \n'
                    f'Ligand {exp.ligand} \n')


def make_caverdock_config(exps, args, configfile):
    string_prepare = [f'{configfile["CD-PREPARECONF"]["path_cd-prepareconf"]}', '-r', f'{exps[0].protein}qt', '-l',
                      f'{args.ligand}', '-t', f'{args.tunnel}']
    with open(f'caverdock_flex.conf', 'w') as cd_prepare:
        subprocess.run(string_prepare, stdout=cd_prepare)
    logger.info(string_prepare)
    pipeline_check_file.check_exist_file(f'caverdock_flex.conf')
    receptors_index = []
    with open('caverdock_flex.conf', 'a') as file:
        for exp in exps.all_experiments[1:-1]:
            file.write(f'receptor = {exp.protein}qt \n')
        for exp in exps.all_experiments[:-1]:
            file.write(f'load_lb = {configfile["RESULT_CD"]["name"]}_{exp.order_of_experiment}-lb.pdbqt \n')
        for exp in exps.all_experiments[:-1]:
            receptors_index.append(exp.number_of_models)


def main():
    model_with_maximum_energy_and_energy = [('ALA', 11), ('ALA', 12)]
    stop_experiment(model_with_maximum_energy_and_energy)


if __name__ == '__main__':
    a = 5
    main()
