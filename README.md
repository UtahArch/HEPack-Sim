# HEPack Simulator

HEPack-Sim is an open-source tool for modeling and evaluating the performance and energy efficiency of performing Homomorphic Encryption based Machine Learning inference tasks on an accelerator. HEPack-Sim is built to evaluate a range of data packing, dataflow designs, and accelerator parameters.  HEPack-Sim was developed by the [Utah Arch Research Group](https://arch.cs.utah.edu/) at the [Kahlert School of Computing, University of Utah](https://www.cs.utah.edu/), to explore novel techniques to optimize private inference and demonstrate reproducibility of results presented in the work [Hyena: Balancing Packing, Reuse, and Rotations for Encrypted Inference (yet to appear in SP'24)](). 

## Using the Simulator

To run a specific packing method, refer to the `USAGE:` mentioned in the python script. For example to run the simulation for hyena packing on F1 architecture and using F1 NTT you would do:

```bash
python run_hyena.py resnet f1 f1 1
```

To reproduce the results presented in the paper it is important to not change any values in the python files and interface with them using the command line options. The `console_print` and other commented lines of code can be used to debug experiments. An example `run_all.sh` to run experiments would be:

```bash
# Single Input Runs
for network in mobile resnet gnmt resnet20
do
    python run_ngraph.py ${network} 1 1 &
    for pack in hyena epic cheetah channel
    do
        for n in 1
        do
            python run_${pack}.py ${network} f1 f1 ${n} &
            python run_${pack}.py ${network} f1 hyena ${n} &
        done    
    done
    wait
done
wait

# Batching Runs
for network in resnet
do
    for batch in 1 8 64 512
    do
        python run_ngraphplus.py ${network} ${batch} 1 &
        python run_ngraph.py     ${network} ${batch} 1 &
        python run_hyenaplus.py  ${network} f1 hyena 1 ${batch} &
    done
    # wait
done
wait
```

## About the Codebase

### Simulation

- defs.py: Defines architectural and security parameters used for the simulation.
- elements.py: All definitions for the hardware structures (Multiplier, Caches, etc) and their stat collection.
- funcs.py: All definitions for the different Functional Units (ModMult, NTT, Automorph, etc) used by the workloads.
- packings.py: All definitions for the different packings and pipelines implemented.

Different packings implemented:

- run_channel.py: (Ch-Pack) Channel Packing as defined in [GAZELLE: A Low Latency Framework for Secure Neural Network Inference](https://www.usenix.org/conference/usenixsecurity18/presentation/juvekar)
- run_cheetah.py: (LoLa-Pack) Cheetah Packing as defined in [Low Latency Privacy Preserving Inference](https://arxiv.org/abs/1812.10659)
- run_epic.py   : (A+W-Pack) Packing as described in [EPIC: Efficient Packing for Inference using Cheetah](https://sarabjeetsingh007.github.io/files/cogarch22.pdf)
- run_gala.py   : (Ga-Pack) Packing as described in [GALA: Greedy ComputAtion for Linear Algebra in Privacy-Preserved Neural Networks](https://arxiv.org/abs/2105.01827)
- run_hyena.py  : (Hyena-Pack) Packing discussed in [Hyena: Balancing Packing, Reuse, and Rotations for Encrypted Inference (yet to appear in SP'24)]()
- run_lion.py   : (C2PC-Pack) Packing as described in [Cheetah: Lean and Fast Secure Two-Party Deep Neural Network Inference](https://www.usenix.org/conference/usenixsecurity22/presentation/huang-zhicong)
- run_ngraph.py : (BatchWise-Pack) Packing as described in [nGraph-HE: a graph compiler for deep learning on homomorphically encrypted data](https://dl.acm.org/doi/abs/10.1145/3310273.3323047)
- run_\<packing\>plus.py : Packing with smart batching

### Scripts

- calc_output.py: Calculates the total number of output neurons present for every layer. Used for computing the communication cost.
- charts.ipyb: Used for plotting all the charts (and more) present in [Hyena](). Also contains energy numbers extracted from cacti.
- make_folders.sh: Used to create folders for storing the data being generated by the different simulations.
- run_all.sh: Used to run multiple different experiments.

### Workloads

Parameters for the neural networks have been obtained from [Maestro](https://github.com/maestro-project/maestro/tree/master/data/model) (Resnet50, MobileNetV2, gnmt) while the resnet20 parameters are based on [Privacy-Preserving Machine Learning with Fully Homomorphic Encryption for Deep Neural Network](https://arxiv.org/abs/2106.07229).


### Adding Functionality

To add new functionality you would have to:

1. Add any new functional units to `funcs.py` and their associated hardware and stat collection code to `elements.py`.
2. Update `defs.py` with any new parameters.
3. Define a pipeline structre in `packings.py`.
4. Add any new mode parameters in format that is similar to `resnet.m`
5. Add a new file based on the other `run_<packing>.py` scripts to parse the input, calculate packing parameters and perform the dataflow.

## License

HEPack-Sim is released under the [MIT License](LICENSE).

## Contact

For questions or further information, please contact the [Utah Arch Research Group](https://arch.cs.utah.edu/).
