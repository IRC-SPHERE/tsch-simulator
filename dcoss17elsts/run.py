#!/usr/bin/env python3

# Copyright (c) 2016-2017, University of Bristol - http://www.bristol.ac.uk
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
# Authors: Atis Elsts
#          Xenofon Fafoutis
#
#
# This file contains the code for the simulations inluded in the paper:
# 
# Atis Elsts, Xenofon Fafoutis, James Pope, George Oikonomou, Robert Piechocki and Ian Craddock.
# Scheduling High Rate Unpredictable Traffic in IEEE 802.15.4 TSCH Networks. In Proceedings of 
# the 13th International Conference on Distributed Computing in Sensor Systems (DCOSS), IEEE, 
# Ottawa, Canada, June 2017.

import sys, os, random

# add library directory to path
SELF_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(SELF_DIR, '..', "core"))

import sim

TOTAL_SLOTS = 80

################################################################################

def simAny(packetsPerGw, prrlist, ccaSuccessProb, algorithm, sharedslots):  
    stats = sim.Statistics(packetsPerGw)
    if sharedslots == 0:
        sim.simulateDedicated(stats, packetsPerGw, prrlist, False, TOTAL_SLOTS//len(packetsPerGw), 0)
    elif sharedslots == TOTAL_SLOTS:
        sim.simulateShared(stats, packetsPerGw, prrlist, ccaSuccessProb, TOTAL_SLOTS)
    else:
        sim.simulatePartial(stats, packetsPerGw, prrlist, ccaSuccessProb, algorithm, TOTAL_SLOTS, sharedslots)

    return stats

################################################################################

def exp1(traffic):
    print(traffic)

    slot_list = [0,8,16]
    pdr_results = [0] * len(slot_list)
    
    for sharedslots in range(len(slot_list)):
        
        i = 0
        for i1 in range(3):
            p1 = (i1/5.0)+0.5  # 0.5 to 0.9
            for i2 in range(i1, 3):
                p2 = (i2/5.0)+0.5       
                for i3 in range(i2, 3):
                    p3 = (i3/5.0)+0.5
                    for i4 in range(i3, 3):
                        p4 = (i4/5.0)+0.5       
                        i = i+1
                        #print i
                        
                        stats = simAny([traffic, traffic, traffic, traffic], [p1, p2, p3, p4], 0.7, False, slot_list[sharedslots])
                        pdr_results[sharedslots] += stats.pdr

        pdr_results[sharedslots] = pdr_results[sharedslots]/(i)
    print(pdr_results)
   

def exp2(traffic):
    print(traffic)

    slot_list = [0,2,4,6,8,10,12,14,16,18,20,22,24]
    pdr_results = [0] * len(slot_list)

    A = 0.6 # min link quality (maximal is 1.0)
    N = 8 # number of discrete steps

    for sharedslots in range(len(slot_list)):
        i = 0
        for i1 in range(N+1):
            p1 = ((1 - A)*i1/N)+A
            for i2 in range(i1, N+1):
                p2 = ((1 - A)*i2/N)+A
                for i3 in range(i2, N+1):
                    p3 = ((1 - A)*i3/N)+A
                    for i4 in range(i3, N+1):
                        p4 = ((1 - A)*i4/N)+A
                        i = i+1

                        stats = simAny([traffic, traffic, traffic, traffic], [p1, p2, p3, p4], 0.7, False, slot_list[sharedslots])
                        pdr_results[sharedslots] += stats.pdr
         
        pdr_results[sharedslots] = pdr_results[sharedslots]/i
        pdr_results[sharedslots] = 1 - pdr_results[sharedslots]/100.0
    print(pdr_results)


def exp3(traffic, algorithm):
    oldNumSlotframes = sim.NUM_SLOTFRAMES
    sim.NUM_SLOTFRAMES = 100000

    slot_list = [0,8,16]
    p1 = p2 = p3 = 0.9
    A = 0.3 # min quality

    prr = [ 0.3,  0.325,  0.35,   0.375,  0.4,    0.425,  0.45,   0.475, 0.5,    0.525, 0.55,   0.575,  0.6,    0.625,  0.65, 0.675,  0.7  ]
    N = len(prr)

    pdr_results = [0.0] * len(slot_list)
    for sharedslots in range(len(slot_list)):
        i = 0
        print("ss=", slot_list[sharedslots])
        print("[")
        for i4 in range(N):
            p4 = prr[i4]

            stats = simAny([traffic, traffic, traffic, traffic], [p1,p2, p3, p4], 0.7, algorithm, slot_list[sharedslots])
            print("PDR at {} shared slots {} link quality: {}".format(slot_list[sharedslots], p4, stats.pdr))
            i += 1
            pdr_results[sharedslots] += stats.pdr

        pdr_results[sharedslots] /= i
        print("]")
    print("")
    sim.NUM_SLOTFRAMES = oldNumSlotframes


def exp4(traffic): # Fig. 6
    REPEAT = 1000
     
    pdr_results_0 = [0] * REPEAT
    pdr_results_8 = [0] * REPEAT
    pdr_results_16 = [0] * REPEAT
    pdr_results_min = [0] * REPEAT
    pdr_results_min_i = [0] * REPEAT
    traffic_list = [0] * REPEAT

    std_list = [0] * REPEAT
    mean_list = [0] * REPEAT
        
    for i in range(REPEAT):
        p1 = random.random()/2.0 + 0.5
        p2 = random.random()/2.0 + 0.5
        p3 = random.random()/2.0 + 0.5
        p4 = random.random()/2.0 + 0.5
        
        prrlist = [p1, p2, p3, p4]
        
        mean_list[i], std_list[i] = sim.std(prrlist)
        
        stats = simAny([traffic, traffic, traffic, traffic], prrlist, 0.7, sim.ALGORITHM_CONTIKI_NEGOTIATED, 0)
        pdr_results_0[i] =  1 - stats.pdr/100.0
        stats = simAny([traffic, traffic, traffic, traffic], prrlist, 0.7, sim.ALGORITHM_CONTIKI_NEGOTIATED, 8)
        pdr_results_8[i] =  1 - stats.pdr/100.0
        stats = simAny([traffic, traffic, traffic, traffic], prrlist, 0.7, sim.ALGORITHM_CONTIKI_NEGOTIATED, 16)
        pdr_results_16[i] = 1 - stats.pdr/100.0
        
        traffic_list[i] = traffic
        
        a = [pdr_results_0[i], pdr_results_8[i], pdr_results_16[i]]
        
        pdr_results_min_i[i] = a.index(min(a))
        pdr_results_min[i] = min(a)
        print(a)
        print(pdr_results_min_i[i])
        

    print("")
    print(mean_list)
    print("")
    print(std_list)
    print("")
    print(traffic_list)
    print("")
    print(pdr_results_min_i)

################################################################################
    
# This produces data for Figure 6 from the paper
if 0:
    exp4(14)

# This produces data for Figure 7 from the paper
if 0:
    exp2(9)
    exp2(10)
    exp2(11)
    exp2(12)
    exp2(13)
    exp2(14)

# This produces data for Figure 8 from the paper
if 1:
    exp3(6, sim.ALGORITHM_CONTIKI)

# This produces improved version of the experiment with negotiated shared schedule
if 1:
    exp3(6, sim.ALGORITHM_CONTIKI_NEGOTIATED)
