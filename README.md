**This work is deprecated, please use https://github.com/edi-riga/tsch-sim instead!**

## Overview ##

Discrete-time event simulator for IEEE 802.15.4 TSCH networks.

Supports:

* configurable slotframe size
* configurable number of dedicated and shared slots
* configurable number of retransmissions per packet
* configurable queue sizes
* configurable link-layer PRR per each link
* CCA (optional)

Does not support:

* multihop (only star network topology with a single receiver is supported)
* the capture effect

## Repository structure ##

* `core` - the simulator code
* `dcoss17elsts` - code for experiments for our DCOSS 2017 publication [1]
* `adaptive_static_scheduling` - code for experiments for our IEEE WF-IoT 2018 publication [2]

## Getting started ##

The core file contains a small example. Running the file should produce:


```
$ pypy3 ./sim.py 
Example Simulation
Nodes: 4
Traffic: 5 packets per frame
Link Quality: 0.9 reception probability
Allocated Slots: 10
Reliability: 100.0 PDR
Total Energy 1.88402643 J
Energy Efficiency: 0.942013215 uJ per reliably delivered packet
```


The simulator is compatible with both Python2 and Python3 (recommended). We additionally strongly recommend using the PyPy implementation for much better performance, unless matplotlib or numpy is required.

## Attribution ##

Please cite the following paper if you use the simulator:

[1] Atis Elsts, Xenofon Fafoutis, James Pope, George Oikonomou, Robert Piechocki and Ian Craddock. Scheduling High Rate Unpredictable Traffic in IEEE 802.15.4 TSCH Networks. In Proceedings of the 13th International Conference on Distributed Computing in Sensor Systems (DCOSS), IEEE, Ottawa, Canada, June 2017.

The energy levels, energy efficiency and adaptive scheduling functionality are added in the subsequent paper:

[2] Xenofon Fafoutis, Atis Elsts, George Oikonomou, Robert Piechocki and Ian Craddock. Adaptive Static Scheduling in IEEE 802.15.4 TSCH Networks. In Proceedings of the 4th IEEE World Forum on Internet of Things (IEEE 
WF-IoT), Singapore, Singapore, February 2018.

## Acknowledgments ##

This code was developed as part of the EPSRC-funded IRC-SPHERE project (http://irc-sphere.ac.uk/).
