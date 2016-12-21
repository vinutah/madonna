#!/usr/bin/env python3

SUPPLY_VOLTAGE   = 12.19
SHUNT_RESISTANCE = 0.02
TICKS_PER_SECOND = 1735786190
SAMPLES_PER_SECOND = 10 # or 1000/<number given eServer.exe>

import numpy
import math
import subprocess as SP
import sys
import glob
import os.path as path
from pprint import pprint


def msum(iterable):
    "Full precision summation using multiple floats for intermediate values"
    # Rounded x+y stored in hi with the round-off stored in lo.  Together
    # hi+lo are exactly equal to x+y.  The inner loop applies hi/lo summation
    # to each partial so that the list of partial sums remains exact.
    # Depends on IEEE-754 arithmetic guarantees.  See proof of correctness at:
    # www-2.cs.cmu.edu/afs/cs/project/quake/public/papers/robust-arithmetic.ps
    partials = []               # sorted, non-overlapping partial sums
    for x in iterable:
        i = 0
        for y in partials:
            if abs(x) < abs(y):
                x, y = y, x
            hi = x + y
            lo = y - (hi - x)
            if lo:
                partials[i] = lo
                i += 1
            x = hi
        partials[i:] = [x]
    return sum(partials, 0.0)


def read_time_and_voltage_drop(filename):
    with open(filename, 'r') as f:
        data = [line.split() for line in f.readlines() if line.strip() != ""]
    timestamps = [int(d[0]) for d in data]
    voltage_drops = [float(d[1]) for d in data]
    return timestamps, voltage_drops

def voltage_drop_to_amperage(voltage_drops):
    return [Vd/SHUNT_RESISTANCE for Vd in voltage_drops]


def amperage_to_power(amperages, voltage_drops):
    return [I*(SUPPLY_VOLTAGE-Vd) for I,Vd in zip(amperages, voltage_drops)]

def timestamps_to_time(timestamps):
    start = timestamps[0]
    return [(t-start)/TICKS_PER_SECOND for t in timestamps]

def power_to_energy(powers, timestamps):
    energies = list()
    new_timestamps = list()
    for i in range(0, len(powers)-1):
        delta_ticks = timestamps[i+1] - timestamps[i]
        delta_time = delta_ticks / TICKS_PER_SECOND
        assert(delta_time > 0)
        # Riemann sum for integration
        e = delta_time * (powers[i]+powers[i+1])/2
        energies.append(e)
        new_timestamps.append((timestamps[i+1]+timestamps[i]) / 2)

    return energies, new_timestamps


def dump_energy(energies, timestamps, filename):
    with open(filename, 'w') as f:
        for i in range(len(energies)):
            f.write("{} {}\n".format(timestamps[i], energies[i]))

def dump_power(powers, timestamps, filename):
    dump_energy(powers, timestamps, filename)

def config_plot(xmax, ymax, filename, plotname):
    with open(filename+".gnu", 'w') as f:
        f.write("set output '{}.png'\n".format(plotname))
        f.write("set title '{}'\n".format(plotname))
        f.write("set term png size 1920,1080\n")
        f.write("set datafile missing '#'\n")
        f.write("set style data lines\n")
        f.write("set key off\n")
        f.write("set xlabel 'Time (Seconds)'\n")
        f.write("set ylabel 'Power (Watts)'\n")
        f.write("set yrange [-0.01:{}]\n".format(ymax))
        f.write("set xrange [0:{}]\n".format(xmax))
        f.write("file = '{}.dat\n".format(filename))
        f.write("cols = int(system('head -1 '.file.' | wc -w'))\n")
        f.write("plot for [i=2:cols] '{}.dat' using 1:i title columnheader(i+1)\n".format(filename))


def gnuplot(filename):
    command = "gnuplot "+filename+".gnu"
    with SP.Popen(command,
                  stdout=SP.PIPE, stderr=SP.STDOUT,shell=True) as proc:
        output = proc.stdout.read().decode("utf-8")
        proc.wait()

        if proc.returncode != 0:
            print("Unable to run gnuplot")
            print("Non-zero return code: {}".format(proc.returncode))
            print("Command used: {}".format(command))
            print("Trace:\n{}".format(output))
            sys.exit(proc.returncode)

    return output


def plot(powers, timestamps, plotname):
    plot_times = timestamps_to_time(timestamps)

    xmax = plot_times[-1]
    ymax = max(powers)

    dump_power(powers, plot_times, "temp.dat")
    config_plot(xmax, ymax, "temp", plotname)
    gnuplot("temp")


def main():
    # When ran this take in a single logfile and generates an energy logfile
    # As well as a power plot
    if len(sys.argv) != 2:
        print("usage: {} logfile".format(sys.argv[0]))
        return

    timestamps, voltage_drops = read_time_and_voltage_drop(sys.argv[1])
    amperages = voltage_drop_to_amperage(voltage_drops)
    powers = amperage_to_power(amperages, voltage_drops)
    energies, new_timestamps = power_to_energy(powers, timestamps)

    dump_energy(energies, new_timestamps, sys.argv[1]+".energy.csv")
    print("Total energy: {} Joules".format(msum(energies)))

    plot(powers, timestamps, sys.argv[1])


if __name__ == "__main__":
    main()
