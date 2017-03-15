#!/usr/bin/env python3

#
# Copyright (c) 2017, University of Bristol - http://www.bristol.ac.uk
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#  * Redistributions of source code must retain the above copyright notice,
#    this list of  conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#
# Authors: Xenofon Fafoutis
#
# This file contains the code for the simulations inluded in the paper:
# 
# Xenofon Fafoutis, Atis Elsts, George Oikonomou, Robert Piechocki and Ian Craddock.
# Adaptive Static Scheduling IEEE 802.15.4 TSCH Networks, manuscript under review, 2017.


import sys, os
import matplotlib.pyplot as plt
import matplotlib

# add library directory to path
SELF_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SELF_DIR, '..', "core"))

import sim

PRINTTOFILE = True
MAX_SLOT = 12
REPETITIONS = 100
NODES = 4

######################################

def simulate(packetsPerGw, prrlist, adaptive, slots):  
    stats = sim.Statistics(packetsPerGw)
    sim.simulateDedicated(stats, packetsPerGw, prrlist, adaptive, slots, MAX_SLOT)
    return stats

def printReport(stats, adaptive):
    print("Report")

    if adaptive == True:
        print("Adaptive Static Scheduling")
    else:
        print("Static Scheduling")

    for gw in stats.gwlist:
        print(gw.id, gw.u, gw.aslot)

    print(stats.pdr, stats.asn, stats.txrx, stats.sleeping, stats.idlelistening, stats.collisionsRx)

    print(stats.energy())
    print(stats.enef())   
    print("")

def run4nodes(p,t,a,slots):
    repeat = REPETITIONS
    N = NODES
    traffic = [t] * N
    prr = [p] * N
    adaptive = a

    sstats = sim.SuperStatistics(repeat)

    for i in range(0,sstats.repeat):

        sstats.stats[i] = simulate(traffic, prr, adaptive, slots)
        sstats.stats[i].adaptive = adaptive
        sstats.stats[i].prr = prr
        sstats.stats[i].tr = traffic

    return sstats

def runOracle(p,t,a,maxTraffic):

    lists = [None] * maxTraffic

    minv = 100000.0
    mini = None
    for i in range(0,maxTraffic):
        lists[i] = run4nodes(p,t,a,i+1)

        if lists[i].AverageEnef() < minv:
            minv = lists[i].AverageEnef()
            mini = i
    
    return lists[mini]

######################################################

def exp1(p,slots,filename):

    maxTraffic = MAX_SLOT
    adaptive = [None] * maxTraffic
    static = [None] * maxTraffic
    oracle = [None] * maxTraffic

    for i in range(0,maxTraffic):
        adaptive[i] = run4nodes(p, i+1, True, slots)
        static[i] = run4nodes(p, i+1, False, slots)
        oracle[i] = runOracle(p,i+1,False, maxTraffic)

    traffic = [None] * len(adaptive)
    enef = [None] * len(adaptive)
    enef_static = [None] * len(static)
    enef_oracle = [None] * len(oracle)

    for i in range(len(adaptive)):
        traffic[i] = adaptive[i].stats[0].tr[0]
        enef[i] = adaptive[i].AverageEnef()
        enef_static[i] = static[i].AverageEnef()
        enef_oracle[i] = oracle[i].AverageEnef()
        #print(adaptive[i].StdEnef() / adaptive[i].AverageEnef())
        #print(static[i].StdEnef() / static[i].AverageEnef())
        #print(oracle[i].StdEnef() / oracle[i].AverageEnef())

    matplotlib.rcParams.update({'font.size': 18})
    plt.figure(figsize=(8,6))

    plt.plot(traffic,enef, linestyle="-", label="Adaptive")
    plt.plot(traffic,enef_static, "--", label="Static")
    plt.plot(traffic,enef_oracle,"-.", label="Oracle")

    plt.grid()
    plt.xlabel("Traffic (packets per frame)")
    plt.ylabel("Energy Efficiency")

    plt.legend()

    if PRINTTOFILE == True:
        plt.savefig(filename)
    else:    
        plt.show()

def exp2(t,slots,filename):

    p = [0.4,0.5,0.6,0.7,0.8,0.9,1.0]
    
    adaptive = [None] * len(p)
    static = [None] * len(p)
    oracle = [None] * len(p)

    for i in range(0,len(p)):
        adaptive[i] = run4nodes(p[i], t, True, slots)
        static[i] = run4nodes(p[i], t, False, slots)
        oracle[i] = runOracle(p[i],t,False, MAX_SLOT)

    traffic = [None] * len(adaptive)
    enef = [None] * len(adaptive)
    enef_static = [None] * len(static)
    enef_oracle = [None] * len(oracle)

    for i in range(len(adaptive)):
        enef[i] = adaptive[i].AverageEnef()
        enef_static[i] = static[i].AverageEnef()
        enef_oracle[i] = oracle[i].AverageEnef()
        #print(adaptive[i].StdEnef() / adaptive[i].AverageEnef())
        #print(static[i].StdEnef() / static[i].AverageEnef())
        #print(oracle[i].StdEnef() / oracle[i].AverageEnef())

    matplotlib.rcParams.update({'font.size': 18})
    plt.figure(figsize=(8,6))

    plt.plot(p,enef, linestyle="-", label="Adaptive")
    plt.plot(p,enef_static, "--", label="Static")
    plt.plot(p,enef_oracle,"-.", label="Oracle")

    plt.grid()
    plt.xlabel("PRR")
    plt.ylabel("Energy Efficiency")

    plt.legend()

    if PRINTTOFILE == True:
        plt.savefig(filename)
    else:    
        plt.show()

def motivating_enef(p,t,filename):

    maxTraffic = MAX_SLOT
    lists = [None] * maxTraffic

    for i in range(0,maxTraffic):
        lists[i] = run4nodes(p,t,False,i+2)


    slots = [None] * len(lists)
    enef = [None] * len(lists)

    for i in range(len(lists)):
        slots[i] = lists[i].stats[0].gwlist[0].aslot
        enef[i] = lists[i].AverageEnef()
        #print(lists[i].StdEnef() / lists[i].AverageEnef())

    matplotlib.rcParams.update({'font.size': 18})
    plt.figure(figsize=(8,6))

    plt.plot(slots,enef, linestyle="-")

    plt.grid()
    plt.xlabel("Active Slots")
    plt.ylabel("Energy Efficiency")
    
    if PRINTTOFILE == True:
        plt.savefig(filename)
    else:    
        plt.show()

def motivating_enco(p,t,filename):

    maxTraffic = MAX_SLOT
    lists = [None] * maxTraffic

    for i in range(0,maxTraffic):
        lists[i] = run4nodes(p,t,False,i+2)


    slots = [None] * len(lists)
    enco = [None] * len(lists)

    for i in range(len(lists)):
        slots[i] = lists[i].stats[0].gwlist[0].aslot
        enco[i] = lists[i].AverageEnco()
        #print(lists[i].StdEnef() / lists[i].AverageEnef())

    matplotlib.rcParams.update({'font.size': 18})
    plt.figure(figsize=(8,6))

    plt.plot(slots,enco, "-")

    plt.grid()
    plt.xlabel("Active Slots")
    plt.ylabel("Energy per Packet (mJ)")
    
    if PRINTTOFILE == True:
        plt.savefig(filename)
    else:    
        plt.show()

def motivating_pdr(p,t,filename):

    maxTraffic = MAX_SLOT
    lists = [None] * maxTraffic

    for i in range(0,maxTraffic):
        lists[i] = run4nodes(p,t,False,i+2)


    slots = [None] * len(lists)
    pdrl = [None] * len(lists)

    for i in range(len(lists)):
        slots[i] = lists[i].stats[0].gwlist[0].aslot
        pdrl[i] = lists[i].AveragePDR()
        #print(lists[i].StdEnef() / lists[i].AverageEnef())

    matplotlib.rcParams.update({'font.size': 18})
    plt.figure(figsize=(8,6))

    plt.plot(slots,pdrl,"-")

    plt.grid()
    plt.xlabel("Active Slots")
    plt.ylabel("PDR (%)")
    
    if PRINTTOFILE == True:
        plt.savefig(filename)
    else:    
        plt.show()

######################################

exp1(0.8,12,"exp1-pdr-good.pdf")
print("done")
exp1(0.8,6,"exp1-ec-good.pdf")
print("done")

exp2(6,12,"exp2-pdr.pdf")
print("done")
exp2(6,6,"exp2-ec.pdf")
print("done")

motivating_pdr(0.7,4,"mot-pdr.pdf")
print("done")
motivating_enef(0.7,4,"mot-enef.pdf")
print("done")
motivating_enco(0.7,4,"mot-enco.pdf")
print("done")
