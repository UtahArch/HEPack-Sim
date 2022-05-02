#################################################################################
##  Main file for running sumulations
##
##  Running Cheetah Packing
##
##
#################################################################################
 
import defs
import packings
import sys
import os

console_print = False

if console_print:
    os.system('clear')

network  = sys.argv[1]
ntttype  = None
arch     = None
poly_n   = 1
num_muls = 1
batch    = 1

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
            if console_print:
                line = "Dimensions { K: 128, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
                # line = "Dimensions { K: 1, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
                # line = "Dimensions { K: 64, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
            
            # if line in done_params:
            #     continue
            # else:
            #     done_params.add(line)
            
            temp = line.split("{")[1].split("}")[0].split(",")
            for t in temp:
                t = [x.strip() for x in t.split(":")]
                param[t[0]] = int(t[1])
            if console_print:
                print name, param

            IF = (param['X'], param['Y'], param['C'])
            W  = (param['R'], param['S'], param['C'], param['K'])
            
            # Decide Params
            P  = (IF[0] - W[0] + 1)*(IF[1] - W[1] + 1) / (S[0]*S[1])      # Total Number of Matrices
            
            C_t = W[3]
            while W[0]*W[1]*C_t > defs.max_c_on_chiplt:
                C_t /= 2

            # Define Classes and globals
            defs.packing = "ngraph"
            defs.c_t = C_t

            main_chiplet = packings.Chiplet()
            main_chiplet.setup_ngraph()

            
            # Perform NGraph-HE in the output stationary format
            # For every output feature point
            for of in range(P):
                # for all channel steps
                for c_step in range(0, W[2], C_t):
    
                    # Store RSC_t ifs and wts in L2, the rest will have to handled brough in, in the next step
                    main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size * min(defs.max_c_on_chiplt, W[0]*W[1]*C_t)
                    main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size * min(defs.max_c_on_chiplt, W[0]*W[1]*C_t)
                    # main_chiplet.wt_l2_cache.stats_accesses += main_chiplet.pe_array.wt_file.size * min(defs.max_c_on_chiplt, W[0]*W[1]*C_t)
                    
                    # for every kernel - output channel
                    for k in range(W[3]):
                        # Get PSUM to memory
                        main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                        main_chiplet.pe_array.pip_stats.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                        main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size
                        
                        # Work with the RSC_t values
                        main_chiplet.run_ngraph(W[1] * W[0] * C_t)
                    
                        # Flush PSUM to memory
                        main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                        main_chiplet.pe_array.pip_stats.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                        main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size
                        

            main_chiplet.calc_time_ngraph()

            if console_print:
                main_chiplet.print_stats_console(IF, W, S)
                break
            else:
                main_chiplet.print_stats_file(IF, W, S, name, network)
