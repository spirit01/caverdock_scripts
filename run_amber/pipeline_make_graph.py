#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import matplotlib

matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np

# Definition of colors
BLUE = ['blue', 'mediumblue', 'cornflowerblue', 'lightsteelblue', 'steelblue', 'dodgerblue']
GREEN = ['lime', 'limegreen', 'lawngreen', 'greenyellow', 'springgreen']
RED = ['red', 'firebrick', 'tomato', 'salmon', 'coral']
CYAN = ['cyan', 'darkturquoise', 'cadetblue', 'lightblue']


def make_single_graph(num_str, index, rgb_colour, df, exps):
    plt.clf()
    plt.xticks(np.arange(0, float(num_str) + 2, 1.0))
    plt.xlabel(r'Trajectory [Å]')
    plt.ylabel('Binding energy [kcal/mol]')
    plt.title(f'Result of {index} iteration')
    fig = df.plot(x='discs', y=['E_lb', 'SavGoy_lb'], kind='line',
                  color=[rgb_colour, 'red'])
    plt.savefig(f'graph_SavGoy_{index}.png')
    plt.clf()


def make_collective_graph(all_experiments, item_on_x_scale, number_of_iteration, rgb_colours, exps):
    diff_lines = ['solid', 'dashed', 'dashdot', 'dotted']
    for i in range(0, int(number_of_iteration) + 1):
        plt.xticks(np.arange(0, item_on_x_scale + 2, 2.0))
        # plt.plot(*zip(*all_experiments[i]), label=f'Iteration {i}', color = rgb_colours[i%4], linestyle = diff_lines[i])#[0.0,0.0,1.0])
        plt.xlabel(r'Trajectory [Å]')
        plt.ylabel('Binding energy [kcal/mol]')
        # TODO only for report loschmidt
        if i <= 2:
            plt.plot(*zip(*all_experiments[i]), label=f'Iteration {i}', color=BLUE[i % 3],
                     linestyle=diff_lines[i % 4])  # [0.0,0.0,1.0])
        if i > 2 and i <= 5:
            plt.plot(*zip(*all_experiments[i]), label=f'Iteration {i}', color=GREEN[i % 3],
                     linestyle=diff_lines[i % 4])  # [0.0,0.0,1.0])
        if i > 5 and i <= 8:
            plt.plot(*zip(*all_experiments[i]), label=f'Iteration {i}', color=RED[i % 3],
                     linestyle=diff_lines[i % 4])  # [0.0,0.0,1.0])

        plt.legend()
        plt.plot([exps[i].bottleneck], [exps[i].energy_in_bottleneck], 'v')
        plt.annotate(f'{i}', (exps[i].bottleneck, exps[i].energy_in_bottleneck))

    plt.savefig(f'graph_energy_all.png')
    plt.clf()


def plot_graph(number_of_iteration, ub_lb, df, exps, configfile):
    rgb_colours = make_read_rgb_file(configfile)
    all_experiments = []
    for i in range(0, number_of_iteration + 1):
        num_str_energy = []
        with open(f'energy_{i}.dat', 'r') as file_energy:
            file_energy.readline()
            for line in file_energy:
                if ub_lb == 'lb':
                    energy = float(line.split(' ')[5].strip())
                if ub_lb == 'ub':
                    energy = float(line.split(' ')[3])
                num_str = float(line.split(' ')[0])
                num_str_energy.append((round(num_str, 3), energy))
        all_experiments.append(num_str_energy)
        make_single_graph(num_str, i, rgb_colours[i], df, exps)
    make_collective_graph(all_experiments, num_str, number_of_iteration, rgb_colours, exps)


def make_read_rgb_file(configfile):
    rgb_colours = []
    with open(f'{configfile["RGB"]["rgb"]}') as rgb_file:
        for line in rgb_file:
            if line.startswith('cmd'):
                rgb = line[line.find("[") + 1:line.find("]")]
                rgb_colours.append([float(x) for x in rgb.split(',')])

    return rgb_colours


def plot_used_model_and_method():
    pass


def main():
    index = 9
    exps = 0
    # plot_graph(index, 'lb', exps, configfile)


if __name__ == '__main__':
    main()
