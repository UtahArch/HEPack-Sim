#################################################################################
##  Main file for running sumulations
##
##  Running Hyena Packing
##
##
#################################################################################
 
import defs
import packings
import math
import sys
import os

os.system('clear')

# Global Variables

ntttype = sys.argv[1]
poly_n  = int(sys.argv[2])
batch   = 1

done_params = set()

with open("Resnet50_model.m") as fin:
    for line in fin.readlines():
        if "Layer" in line:
            name = line.split()[1]
        elif "Dimensions" in line:
            param = {}
            # line = "Dimensions { K: 128, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
            # line = "Dimensions { K: 512, C: 512, R: 3, S: 3, Y: 7, X: 7 }"
            # line = "Dimensions { K: 64, C: 256, R: 1, S: 1, Y: 56, X: 56 }"

            if line in done_params:
                continue
            else:
                done_params.add(line)
            
            temp = line.split("{")[1].split("}")[0].split(",")
            for t in temp:
                t = [x.strip() for x in t.split(":")]
                param[t[0]] = int(t[1])
            
            print ""
            print name, param

            IF = (param['X'], param['Y'], param['C'])
            W  = (param['R'], param['S'], param['C'], param['K'])

            # IF Packing
            P  = (IF[0] - W[0] + 1)*(IF[1] - W[1] + 1)       # Total Number of Matrices
            M  = int(math.ceil(IF[0]/W[0])*math.ceil(IF[1]/W[1])) # Number of non-overlapping Matrices
            RS = W[0]*W[1]                                   # Size of 1 Matrices

            n  = defs.wt_file_size * defs.num_pe_x * defs.num_pe_y  # Polynomial Size
            Mt = min(int(n/RS), M)                                  # Number of non-overlapping Matrices in 1 poly

            C_t = 1              # Pack C_ts
            while C_t < W[2]:
                C_t *= 2
                if Mt*RS*C_t > n:
                    C_t /= 2
                    break

            # Wt Packing
            K_t = 1
            while K_t < defs.psum_file_num:
                K_t *= 2
                if RS*C_t*K_t > n:
                    K_t /= 2
                    break

            # Potential More packing
            C_t_new = 1
            while C_t*C_t_new < W[2]:
                C_t_new *= 2
                if RS*C_t*C_t_new*K_t > n:
                    C_t_new /= 2
                    break
            
            Mt /= C_t_new
            C_t *= C_t_new
            print "IF Packing:      P:{}\tM:{}\tRS:{}\tMt:{}\tC_t:{}\t:: {}".format(P, M, RS, Mt, C_t, Mt*RS*C_t/float(n))
            print "Wt Packing:     K_t:{}\tC_t_new:{}\t\t\t:: {}".format(K_t, C_t_new, RS*C_t*K_t/float(n))

            # Define Classes
            defs.c_t = C_t
            defs.k_t = K_t
            defs.packing = "hyena"
            defs.ntt_type = ntttype
            defs.batch_size = batch
            defs.poly_n = poly_n
            defs.num_chiplets = defs.poly_n / (defs.wt_file_size * defs.num_pe)

            main_chiplet = packings.Chiplet()
            
            if ntttype == 'baseline':
                main_chiplet.ntt_choice = -1
            elif ntttype == 'f1':
                main_chiplet.ntt_choice = -1
            elif ntttype == 'opt':
                # Decide on NTT to use
                # TODO: Discuss this
                f1_cost = main_chiplet.pe_array.op_ntt_f1("wt", "dry")
                opt_cost = main_chiplet.pe_array.op_ntt_opt("wt", RS, "dry") 
                                                                
                if defs.num_chiplets == 1:
                    hop_time = 2 * defs.phop_time
                else:
                    hop_time = 2 * defs.chop_time

                if f1_cost*2 + 2*hop_time < opt_cost:
                    main_chiplet.ntt_choice = 0
                    defs.ntt_type = 'f1'
                else:
                    main_chiplet.ntt_choice = RS

                print "NTT Choice", main_chiplet.ntt_choice
                print f1_cost*2 + 2*hop_time
                print opt_cost

            # Bring Values to KSH and twiddle
            # For optimised NTT Twiddle carries the hints
            # TODO: Since Re-Use distance it soo much do we have a KSH and Twiddle L2 cache? How does L2 change for large polynomials
            # TODO: main_chiplet.pe_array.ksh_file.size / C_t feels wrong
            main_chiplet.ksh_l2_cache.stats_accesses += main_chiplet.pe_array.ksh_file.size / C_t
            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.ksh_file.size / C_t
            main_chiplet.pe_array.twiddle.stats_accesses += main_chiplet.pe_array.twiddle.size
            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.twiddle.size
            
            num_k_memory = max(0, W[2]/C_t * W[3]/K_t - defs.max_c_on_chiplt)
            if W[2]/C_t > defs.max_c_on_chiplt:
                print "Handle this case for ifs
                exit()

            
            for m_step in range(0, M, Mt):              # Iterate over all non-overlapping matrices
                # Get the if from memory and put it in the L2 for the first iteration
                main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size
                main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size

                for p in range((W[0]-1)*(W[1]-1) + 1):  # Permute to create all overlappingmatrices

                    # Fill the L2 cache with wts
                    # Store C/C_t x K/K_t wts in the L2, the rest will have to be handled from memory
                    main_chiplet.memory.stats_accesses += defs.num_pe_x * defs.num_pe_y * defs.wt_file.size * min(defs.max_c_on_chiplt, W[2]/C_t * W[3]/K_t)
                    main_chiplet.wt_l2_cache.stats_accesses += defs.num_pe_x * defs.num_pe_y * defs.wt_file.size * min(defs.max_c_on_chiplt, W[2]/C_t * W[3]/K_t)

                    iters = 0
                    for k_step in range(0, W[3], K_t):        # Iterate over all kernels in K_t steps for wts
                        for c_step in range(0, W[2], C_t):    # Iterate over all channels in C_t steps for wts
                            # Access wts from the L2 or memory based on number
                            if iters < defs.max_c_on_chiplt:
                                main_chiplet.wt_l2_cache.stats_accesses += main_chiplet.pe_array.wt_file.size
                            else:
                                main_chiplet.memory.stats_accesses += main_chiplet.pe_array.wt_file.size
                            main_chiplet.wt_file.stats_accesses += main_chiplet.pe_array.wt_file.size
                            # Access ifs from L2
                            main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size
                            main_chiplet.if_file.stats_accesses += main_chiplet.pe_array.if_file.size

                            main_chiplet.run_hyena_k()
                            iters += 1
                        
                        main_chiplet.run_hyena_psum_collect(RS*C_t)
                    
                    # Flush PSUM to memory
                    main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                    main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size

                    if p != 0:
                        # Iterate over all channels in C_t steps for ifs
                        # this will happen once every permutation for every set of channel steps the first time they are called and then stored in the L2 cache
                        # there will be C/C_t ifs in the L2
                        for c_step in range(0, W[2], C_t):
                            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size
                            main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size
                            main_chiplet.run_hyena_permute_if()


            # main_chiplet.print_stats_console(IF, W)
            # break