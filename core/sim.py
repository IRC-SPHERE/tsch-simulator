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

import sys, random

# Enable CCA? (It's not enabled in Contiki experiments)
DO_CCA = False

# Number of slotframes to simulate
NUM_SLOTFRAMES = 100

# Total slotframe size in slots (99 slots = approximately 1 second)
SLOTFRAME_SIZE = 100

# Maximal number of times a packet can be transmitted before its dropped
NUM_TX = 8
# Maximal queue size on each router
MAX_QUEUE = 8

# Inactive/unusable slots are marked by this
INACTIVE = -2
# Shared slots are marked by this
SHARED = -1

##############################################

# Utility function to avoid including numpy - not well supported by PyPy

def mean(lst):
    return float(sum(lst)) / len(lst)

def std(lst):
    mean = float(sum(lst)) / len(lst)
    squareSum = sum((x - mean)**2 for x in lst)
    return mean, (squareSum / len(lst))**0.5

##############################################

class Statistics:
    def __init__(self,packetsPerGw):
        self.sleeping = 0
        self.idlelistening = 0
        self.txrx = 0
        self.collisionsTx = 0
        self.collisionsRx = 0
        self.pdr = 0
        self.asn = 0
        self.traffic = sum(packetsPerGw)
        self.gwlist = []
        self.prr = None
        self.tr = None


    def energy(self):
        # These numbers are for GINA nodes taken from:
        # 
        # X. Vilajosana, Q. Wang, F. Chraim, T. Watteyne, T. Chang, and K. S. J.Pister.
        # A Realistic Energy Consumption Model for TSCH Networks. IEEE Sensors Journal, 
        # vol. 14, no. 2, pp. 482–489, Feb 2014.
        
        vcc = 3.3 # V
        idle = 47.9 # uC
        sleep = 4.9 # uC
        TxDataRxAck = 92.6 # uC
        RxDataTxAck = 96.3 # uC
        TxData = 69.6 # uC
        RxData = 72.1 # uC

        total_sleeping = (2 * sleep * vcc) * self.sleeping # uJ
        total_idle = (idle * vcc + sleep * vcc) * self.idlelistening # uJ
        total_txrx =  (TxDataRxAck * vcc + RxDataTxAck * vcc) * self.txrx #uJ
        total_collisions = (TxData * vcc) * self.collisionsTx + (RxData * vcc) * self.collisionsRx #uJ

        return (total_sleeping + total_idle + total_txrx + total_collisions) / 1000000.0 # J

    def enef(self):
        return 1000 * self.energy() / (self.traffic * NUM_SLOTFRAMES * ((self.pdr / 100.0) ** 1.2)) # mJ / reliable packet

##############################################

class SuperStatistics:
    def __init__(self,repeat):
        self.repeat = repeat
        self.stats = [None] * repeat
        self.eneflist = [None] * repeat
        self.pdrlist = [None] * repeat
        self.encolist = [None] * repeat

    def AverageEnef(self):
        for i in range(self.repeat):
            if self.stats[i] != None:
                self.eneflist[i] = self.stats[i].enef()
        return mean(self.eneflist)

    def AveragePDR(self):
        for i in range(self.repeat):
            if self.stats[i] != None:
                self.pdrlist[i] = self.stats[i].pdr
        return mean(self.pdrlist)

    def AverageEnco(self):
        for i in range(self.repeat):
            if self.stats[i] != None:
                self.encolist[i] = 1000 * self.stats[i].energy() / (self.stats[i].traffic * NUM_SLOTFRAMES) # mJ / packet
        return mean(self.encolist)

    def StdEnef(self):
        for i in range(self.repeat):
            if self.stats[i] != None:
                self.eneflist[i] = self.stats[i].enef()
        return std(self.eneflist)[1]

######################################

class Packet:
    def __init__(self, gw):
        self.tx = 0
        self.gw = gw
        self.backoff = 0

    def send(self):
        self.tx += 1
        ok = random.random() <= self.gw.prr
        if ok:
            self.gw.numOkPackets += 1
        return ok

    def __repr__(self):
        return "tx {}".format(self.tx)

######################################

class Gw:
    def __init__(self, id, p, s, s_max):
        self.id = id
        self.queue = []
        self.numOkPackets = 0
        self.numLostPackets = 0
        self.prr = p
        self.col = 0


        self.aslot = s
        self.aslotmax = s_max
        self.u = 0.95
        self.alpha = 0.1

    def schedulePacket(self, packet):
        if packet.tx >= NUM_TX:
            self.numLostPackets += 1
            return
        if len(self.queue) >= MAX_QUEUE:
            self.numLostPackets += 1
            return
        self.queue.append(packet)

    def scheduleNewPacket(self, slotIndex, traffic):
        if traffic[self.id][slotIndex] == 1:
            if len(self.queue) >= MAX_QUEUE:
                self.numLostPackets += 1
            else:
                self.queue.append(Packet(self))

    def __repr__(self):
        #print(self.queue)
        return "\n{}, {}, {}, {:.6f}".format(
            self.id, self.numOkPackets, self.numLostPackets, 100.0 * self.numOkPackets / (self.numOkPackets + self.numLostPackets))


######################################

#
# This simulates collision-free usage of all available shared slots
# (the theoretical optimum usage)
#
def getPacketsOptimal(senderSlot, gws):
    bestgw = None
    if senderSlot != SHARED:
        # dedicated slot
        gw = gws[senderSlot]
        if len(gw.queue):
            bestgw = gw
    else:
        # shared slot
        maxlen = 0
        for gw in gws:
            if len(gw.queue) > maxlen:
                maxlen = len(gw.queue)
                bestgw = gw
    if bestgw is None:
        return []
    packet = bestgw.queue[0]
    bestgw.queue = bestgw.queue[1:]
    return [packet]


#
# This algorithm is suboptimal, but compared to the optimal on,
# actually and easily implementable (autonomously on each node).
# It is used in our Contiki C code implementation.
#
def getPacketsContiki(senderSlot, gws, numSharedSlots):
    packets = []

    if senderSlot == INACTIVE:
        return packets

    if senderSlot != SHARED:
        # dedicated slot
        gw = gws[senderSlot]
        if len(gw.queue):
            packet = gw.queue[0]
            gw.queue = gw.queue[1:]
            packets.append(packet)
    else:
        bestgw = None
        # shared slot
        for gw in gws:
            #if len(gw.queue) <= 2:
                #pass
            #else:
                r = random.random()
                C = len(gw.queue) # use linear dependence on queue size
                #C = max(0, C - gw.col)
                #C = max(0, C - 4) # use less agressive sending
                #C = C**1.5      # use more agressive sending
                #C = C**2        # use even more agressive sending
                #print(C  * float(numSharedSlots) / SLOTFRAME_SIZE)
                ok = r <= (C / float(numSharedSlots))
                if ok:
                    packet = gw.queue[0]
                    gw.queue = gw.queue[1:]
                    packets.append(packet)               
                #else:
                    #print("backoff")
    return packets


def updateSlotFrame(slotframe, gws, asn, gw):
    if gw.u > 0.9:
        gw.aslot = min(gw.aslotmax, gw.aslot + 1)
    elif gw.u < 0.8 and len(gw.queue)<1:
        gw.aslot = max(1, gw.aslot - 1)
    else:
        return

    count = gw.aslot
    for i in range(len(slotframe)):
        if i % len(gws) == gw.id:
            if count > 0:
                slotframe[i] = gw.id
                count -= 1
            else:
                slotframe[i] = INACTIVE


#
# This simulates the operation of a single TSCH timeslot on all nodes.
#
def simSlot(stats, gws, asn, slotframe, traffic, ccaSuccessProb, doOptimal, numSharedSlots, adaptive):

    si = asn % SLOTFRAME_SIZE
    for gw in gws:
        a = gw.scheduleNewPacket(si, traffic)

    if doOptimal:
        packets = getPacketsOptimal(slotframe[si], gws)
    else:
        packets = getPacketsContiki(slotframe[si], gws, numSharedSlots)

    # Single packet, no collisions
    if len(packets) == 1:
        packet = packets[0]
        packet.gw.u = (1 - packet.gw.alpha) * packet.gw.u + packet.gw.alpha * 1
        if not packet.send():
            # reschedule it
            packet.gw.schedulePacket(packet)
        else:
            # successful txrx
            if adaptive == True:
                updateSlotFrame(slotframe, gws, asn, packet.gw)
        packet.gw.col = 0
        stats.txrx += 1

    # More than one packet, a collision unless DO_CCA configured and CCA succeeds
    elif len(packets) > 1:
        # for 2 packets, it's one check that must succeed, for n packets: n-1 checks
        if DO_CCA:
            numChecks = len(packets) - 1
            if random.random() <= ccaSuccessProb ** numChecks:
                # cca ok; the one of packets went through, the rest back off
                okpacket = random.randint(0, len(packets) - 1)
                for i in range(len(packets)):
                    packet = packets[i]
                    if i == okpacket:
                        if not packet.send():
                            # reschedule it
                            packet.gw.schedulePacket(packet)
                    else:
                        # reschedule it without increasing Tx count
                        packet.backoff += 1
                        packet.gw.schedulePacket(packet)
            else:
                # CCA failed to detect concurrent transmissions
                for packet in packets:
                    packet.tx += 1
                    packet.gw.schedulePacket(packet)
        else:
            # no CCA
            for packet in packets:
                packet.tx += 1
                packet.gw.schedulePacket(packet)
                packet.gw.col += 1
                stats.collisionsTx += 1   
            stats.collisionsRx += 1

    # No packets, idle slot
    else:
        if (slotframe[si] == INACTIVE):
            stats.sleeping += 1
        else:
            stats.idlelistening += 1
            g = gws[slotframe[si]]
            g.u = (1 - g.alpha) * g.u + g.alpha * 0

#######################################################

#
# This generates a list of "packets" distributed across timeslots,
# depending on the slotframe size and the number of packets per slotframe,
# passed as `packetsPerGw` parameter.
#
def getTraffic(packetsPerGw):
    traffic = [[0] * SLOTFRAME_SIZE for _ in range(len(packetsPerGw))]
    for gw in range(len(packetsPerGw)):
        skip = SLOTFRAME_SIZE // packetsPerGw[gw]
        for i in range(packetsPerGw[gw]):
            traffic[gw][i * skip] = 1 # generate a new packet here
    return traffic


#
# Simulates an operation with only shared slots (slotted Aloha).
#
def simulateShared(stats, packetsPerGw, prrlist, ccaSuccessProb, total_shared):
    slotframe = [INACTIVE] * SLOTFRAME_SIZE
    traffic = getTraffic(packetsPerGw)

    gws = []
    for gw in range(len(packetsPerGw)):
        gws.append(Gw(gw,prrlist[gw],0,0))

    sn = 0
    for slot in range(total_shared):
        slotframe[sn] = SHARED
        sn += 1

    for s in range(NUM_SLOTFRAMES):
        for slot in range(SLOTFRAME_SIZE):
            asn = s * SLOTFRAME_SIZE + slot
            simSlot(stats, gws, asn, slotframe, traffic, ccaSuccessProb, False, total_shared, False)

    stats.gwlist = gws
    stats.asn += 1

    S = 0
    T = 0
    for i in range(len(packetsPerGw)):
        if(gws[i].numOkPackets + gws[i].numLostPackets) > 0:
            print(gws[i].numLostPackets)
            S = S + 100.0 * gws[i].numOkPackets / (gws[i].numOkPackets + gws[i].numLostPackets)
            T = T + 1        
    stats.pdr = S/T

#
# Simulates an operation with both shared and dedicated (collision free) slots.
#
def simulatePartial(stats, packetsPerGw, prrlist, ccaSuccessProb, doOptimal, totalSlots, sharedSlots):
    slotframe = [INACTIVE] * SLOTFRAME_SIZE
    traffic = getTraffic(packetsPerGw)       
    
    NUM_SHARED_SLOTS_PER_SECOND = sharedSlots
    NUM_DEDICATED_SLOTS = (totalSlots - sharedSlots) // len(packetsPerGw)

    gws = []
    for gw in range(len(packetsPerGw)):
        gws.append(Gw(gw, prrlist[gw], NUM_DEDICATED_SLOTS, NUM_DEDICATED_SLOTS))

    sn = 0
    for slot in range(NUM_DEDICATED_SLOTS):
        for gw in range(len(packetsPerGw)):
            slotframe[sn] = gw
            sn += 1

        for slot in range(NUM_SHARED_SLOTS_PER_SECOND // NUM_DEDICATED_SLOTS):
            slotframe[sn] = SHARED
            sn += 1

    for slot in range(NUM_SHARED_SLOTS_PER_SECOND - NUM_SHARED_SLOTS_PER_SECOND // NUM_DEDICATED_SLOTS * NUM_DEDICATED_SLOTS):
        slotframe[sn] = SHARED
        sn += 1

    for s in range(NUM_SLOTFRAMES):
        for slot in range(SLOTFRAME_SIZE):
            asn = s * SLOTFRAME_SIZE + slot
            simSlot(stats, gws, asn, slotframe, traffic, ccaSuccessProb, doOptimal, NUM_SHARED_SLOTS_PER_SECOND, False)

    stats.gwlist = gws
    stats.asn += 1

    S = 0
    T = 0
    for i in range(len(packetsPerGw)):
        if(gws[i].numOkPackets + gws[i].numLostPackets) > 0:
            S = S + 100.0 * gws[i].numOkPackets / (gws[i].numOkPackets + gws[i].numLostPackets)
            T = T + 1
    stats.pdr = S/T


#
# Simulates an operation with only dedicated (collision free) slots.
#  
def simulateDedicated(stats, packetsPerGw, prrlist, adaptive, slots, slotsMax):

    slotframe = [INACTIVE] * SLOTFRAME_SIZE
    traffic = getTraffic(packetsPerGw)
    gws = []
    for gw in range(len(packetsPerGw)):
        gws.append(Gw(gw, prrlist[gw], slots, slotsMax))

    sn = 0
    for slot in range(slots):
        for gw in range(len(packetsPerGw)):
            slotframe[sn] = gw
            sn += 1

    for s in range(NUM_SLOTFRAMES):
        for slot in range(SLOTFRAME_SIZE):
            asn = s * SLOTFRAME_SIZE + slot
            simSlot(stats, gws, asn, slotframe, traffic, 0.0, False, 0, adaptive)

    stats.gwlist = gws
    stats.asn = asn+1

    S = 0
    T = 0
    for i in range(len(packetsPerGw)):
        if(gws[i].numOkPackets + gws[i].numLostPackets) > 0:
            S = S + 100.0 * gws[i].numOkPackets / (gws[i].numOkPackets + gws[i].numLostPackets)
            T = T + 1
    stats.pdr = S/T

#######################################################

def main():
    print("Example Simulation")

    trafficRate = 5
    p = 0.9
    nodes = 4
    packetsPerGw = [trafficRate] * nodes         
    prrlist = [p] * nodes
    slots = 10                         

    print("Nodes:", nodes)
    print("Traffic:", trafficRate, "packets per frame")
    print("Link Quality:", p, "reception probability")
    print("Allocated Slots:", slots)

    stats = Statistics(packetsPerGw)
    simulateDedicated(stats, packetsPerGw, prrlist, False, slots, 0)

    print("Reliability:", stats.pdr, "PDR")
    print("Total Energy", stats.energy(), "J")
    print("Energy Efficiency:", stats.enef(), "uJ per reliably delivered packet")

if __name__ == "__main__":
    main()

