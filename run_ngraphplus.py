#################################################################################
##  Main file for running sumulations
##  Running Packing based on NGraph-HE with Smart Batching
##
##  Usage: python run_ngraph.py <network> <poly_n> <batch>
##  Example: python run_ngraph.py resnet 1 1
#################################################################################
 
import defs
import packings
import sys
import os
import math

console_print = False

if console_print:
    os.system('clear')

network  = sys.argv[1]
ntttype  = None
arch     = None
poly_n   = int(sys.argv[3])*1024
num_muls = 1
batch    = int(sys.argv[2])

done_params = set()

with open("{}.m".format(network)) as fin:
    for line in fin.readlines():
        if "Layer" in line:
            name = line.split()[1]
            S = [1,1]
        if "Stride" in line:
            temp = line.split("{")[1].split("}")[0].split(",")
            S[0] = int(temp[0].split(":")[-1].strip())
            S[1] = int(temp[1].split(":")[-1].strip())
        elif "Dimensions" in line:
            param = {}
            # if console_print:
            #     S = [1,1]
                # line = "Dimensions { K: 24, C: 96, R: 1, S: 1, Y:56, X:56 }"
                # line = 'Dimensions { K: 1, C: 96, R: 3, S: 3, Y:56, X:56 }'
                # line = 'Dimensions { K: 256, C: 64, R: 1, S: 1, Y: 56, X: 56 }'
                # line = "Dimensions { K: 1, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
                # line = "Dimensions { K: 64, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
                # line = "Dimensions { K: 1000, C: 2048, R: 7, S: 7, Y: 7, X: 7 }"
                # line = "Dimensions { K: 1, C: 96, R: 3, S: 3, Y:112, X:112 }"
            
            if console_print:
                if line in done_params:
                    continue
                else:
                    done_params.add(line)
            
            temp = line.split("{")[1].split("}")[0].split(",")
            for t in temp:
                t = [x.strip() for x in t.split(":")]
                param[t[0]] = int(t[1])
            if console_print:
                print name, param

            IF = (param['X'], param['Y'], param['C'])
            W  = (param['R'], param['S'], param['C'], param['K'])

            defs.poly_n = poly_n
            n_ckks = defs.poly_n / 2  # Polynomial Size
            
            # Decide Params
            P  = (IF[0] - W[0] + 1)*(IF[1] - W[1] + 1) / (S[0]*S[1])      # Total Number of Matrices
            inner_loop = 0
            
            # Figure out Kt packing for wts
            assert (n_ckks >= batch)
            Kt = min(n_ckks / batch, W[3])
            Keff = int(math.ceil(W[3] / float(Kt)))

            # RS*if_c_cache caching of IFs
            if W[0]*W[1]*W[2] <= defs.max_if_on_chiplt:
                if_c_cache = W[2]
            else:
                if_c_cache = defs.max_if_on_chiplt/(W[0]*W[1])
            assert(if_c_cache <= W[2])

            # max_if_on_chiplt caching of PSUMs
            psum_k_cache = min(Keff, defs.max_if_on_chiplt/2)
            # /2 as we are storing it in the Wt L2 Cache that has half the size PSUM requires

            # Define Classes and globals
            defs.packing = "ngraphplus"
            defs.batch_size = batch
            defs.Kt = Kt

            main_chiplet = packings.Chiplet()
            main_chiplet.setup_ngraph()
            if console_print:
                print "Values: ", P, if_c_cache, psum_k_cache, "\t", Keff, Kt
                print
            
            if console_print:
                continue

            # Perform NGraph-HE in the output stationary format
            # For every output feature point
            for of in range(P):

                for p_step in range(0, Keff, psum_k_cache):

                    # Store Kt PSums in WT L2 Cache
                    main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size * psum_k_cache
                    main_chiplet.wt_l2_cache.stats_accesses += main_chiplet.pe_array.psum_file.size * psum_k_cache
                
                    # for all channel steps
                    for c_step in range(0, W[2], if_c_cache):
        
                        # Store RS*if_c_cache ifs and wts in L2, the rest will have to handled brough in, in the next step
                        main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size * if_c_cache
                        main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size * if_c_cache
                        
                        # for every kernel - output channel
                        for k in range(psum_k_cache):
                            
                            # Get PSUM from L2
                            main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                            main_chiplet.wt_l2_cache.stats_accesses += main_chiplet.pe_array.psum_file.size
                            
                            # Work with the RS*if_c_cache values
                            inner_loop += W[1] * W[0] * if_c_cache
                        
                            # Flush PSUM to L2
                            main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                            main_chiplet.wt_l2_cache.stats_accesses += main_chiplet.pe_array.psum_file.size
                    
                    # Store Kt PSums back to memory
                    main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size * psum_k_cache
                    main_chiplet.wt_l2_cache.stats_accesses += main_chiplet.pe_array.psum_file.size * psum_k_cache
                        
            main_chiplet.run_ngraph(inner_loop)

            if console_print:
                main_chiplet.print_stats_console(IF, W, S)
                break
            else:
                main_chiplet.print_stats_file(IF, W, S, name, network)