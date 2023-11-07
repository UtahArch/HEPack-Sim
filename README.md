# ML-FHE Simulator


## Using the Simulator

## About the Codebase

### Simulation

- defs.py: Defines architectural and secutrity parameters used for the simulation.
- elements.py: All definitions for the different structures and their stat collection.
- funcs.py: All definitions for the different functions used by the workloads.
- packings.py: All definitions for the different packings and pipelines implemented.

Different packings implemented:

- run_channel.py: Channel Packing as defined in [FILL]()
- run_cheetah.py: Cheetah Packing as defined in [FILL]()
- run_epic.py   : Packing as described in [FILL]()
- run_gala.py   : Packing as described in [FILL]()
- run_hyena.py  : Packing discussed in [FILL]()
- run_lion.py   : Packing as described in [FILL]()
- run_ngraph.py : Packing as described in [FILL]()
- run_<packing>plus.py : Packing with smart batching

### Scripts

- calc_output.py: Calculates the total number of output neurons present for every layer. Used for computing the communication cost.
- charts.ipyb: Used for plotting all the charts (and more) present in the paper. Also contains energy numbers extracted from cacti.
- make_folders.sh: Used to create folders for storing the data being generated by the different simulations.
- run_all.sh: Used to run multiple different experiments.

### Workloads

Parameters for the neural networks have been obtained from [Maestro](All definitions for the different structures in the Engine and the basic) (for ...) while resnet20 ... .