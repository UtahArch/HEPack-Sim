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

console_print = False

if console_print:
    os.system('clear')

# Global Variables

network  = sys.argv[1]
ntttype  = sys.argv[2]
arch     = sys.argv[3]
poly_n   = int(sys.argv[4])*1024
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
            # print S, line
        elif "Dimensions" in line:
            param = {}
            if console_print:
                S = [1,1]
                # line = "Dimensions { K: 24, C: 96, R: 1, S: 1, Y:56, X:56 }"
                # line = 'Dimensions { K: 1, C: 96, R: 3, S: 3, Y:56, X:56 }'
                # line = 'Dimensions { K: 256, C: 64, R: 1, S: 1, Y: 56, X: 56 }'
                # line = "Dimensions { K: 1, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
                # line = "Dimensions { K: 64, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
                # line = "Dimensions { K: 1000, C: 2048, R: 7, S: 7, Y: 7, X: 7 }"
                line = "Dimensions { K: 1, C: 96, R: 3, S: 3, Y:112, X:112 }"

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
                print ""
                print name, param

            IF = (param['X'], param['Y'], param['C'])
            W  = (param['R'], param['S'], param['C'], param['K'])

            defs.poly_n = poly_n
            # IF Packing
            P  = (IF[0] - W[0] + 1)*(IF[1] - W[1] + 1) / (S[0]*S[1])      # Total Number of Matrices
            M  = min(P, int(math.ceil(IF[0]/W[0])*math.ceil(IF[1]/W[1]))) # Number of non-overlapping Matrices
            RS = W[0]*W[1]                                   # Size of 1 Matrices

            n_ckks = defs.poly_n / 2  # Polynomial Size
            Mt = min(int(n_ckks/RS), M)    # Number of non-overlapping Matrices in 1 poly

            C_t = 1              # Pack C_ts
            if W[2] > 1:
                while C_t < W[2]:
                    C_t *= 2
                    if Mt*RS*C_t > n_ckks:
                        break
                C_t /= 2
            if C_t > W[2]:
                print "ERROR Hyena 1"
                exit()

            # Wt Packing
            K_t = 1
            if W[3] > 1:
                while ((K_t < defs.psum_file_num) and (K_t < W[3])):
                    K_t *= 2
                    if RS*C_t*K_t > n_ckks:
                        break
                K_t /= 2
            if K_t > W[3]:
                print "ERROR Hyena 2"
                exit()

            # Potential More packing
            C_t_new = 1
            if W[2] > 1:
                while C_t*C_t_new < W[2]:
                    C_t_new *= 2
                    if RS*C_t*C_t_new*K_t > n_ckks or Mt/C_t_new == 0:
                        break
                C_t_new /= 2
            # TODO: This is an assert
            if C_t*C_t_new > W[2]:
                print "ERROR Hyena 3"
                exit()

            Mt = int(math.floor(Mt/float(C_t_new)))
            C_t *= C_t_new

            if_replication = int(math.floor(float(n_ckks)/(Mt*C_t*RS)))
            
            mult_loop = 0
            psum_loop = 0
            if_loop = 0
            # if console_print:
            #     print "IF Packing:  P:{}\tM:{}\tRS:{}\tMt:{}\tC_t:{}\tRF:{}\t:: {}".format(P, M, RS, Mt, C_t, if_replication, Mt*RS*C_t/float(n_ckks))
            #     print "Wt Packing:  K_t:{}\tC_t_new:{}\t\t\t\t:: {}".format(K_t, C_t_new, RS*C_t*K_t/float(n_ckks))
            #     # print K_t
            if console_print:
                print("P  :{:4d}\tM     :{:4d}\tMt    :{:4d}\tC_t:{:4d}\t\tIF-PE:{:}".format(P, M, Mt, C_t/C_t_new, (Mt*RS*C_t)/float(n_ckks)))
                print("K_t:{:4d}\tC_t   :{:4d}\tRS*K_t:{:4d}\tIR :{:4d}\t\tWT-PE:{:}".format(K_t, C_t, W[1]*W[0]*K_t, if_replication, (K_t*C_t*W[0]*W[1])/float(n_ckks)))
                # print("\nFor Iter {:3d}:  XY_t:{:4d}  C_t:{:4d}  XY*C_t:{:4d}  RSCt:{:4d}".format(inner_loop, XY_t, C_t, XY*C_t, W[1] * W[0] * C_t))
            assert(Mt*RS*C_t*if_replication <= n_ckks)
            assert(K_t*C_t*W[0]*W[1] <= n_ckks)

            # Define Classes
            defs.c_t = C_t
            defs.k_t = K_t
            defs.packing = "hyenaV2"
            defs.ntt_type = ntttype
            defs.arch = arch
            defs.num_muls = num_muls
            defs.batch_size = batch
            defs.poly_n = poly_n
            defs.num_chiplets = defs.poly_n / (defs.pe_size)

            main_chiplet = packings.Chiplet()
            main_chiplet = packings.Chiplet()
            if defs.ntt_type == 'f1' and defs.arch == 'f1':
                main_chiplet.setup_hyena_f1_f1(RS*C_t, W[2], W[3])
            elif defs.ntt_type == 'f1' and defs.arch == 'hyena':
                main_chiplet.setup_hyena_f1_hyena(RS*C_t, W[2], W[3])
            else:
                print "run_hyena: Unkown Paramer for Run 1", defs.ntt_type, defs.arch
                exit()

            # if console_print:
            #     continue

            # Bring Values to KSH and twiddle
            # For optimised NTT Twiddle carries the hints
            # TODO: Since Re-Use distance it soo much do we have a KSH and Twiddle L2 cache? How does L2 change for large polynomials
            # TODO: main_chiplet.pe_array.ksh_file.size / C_t feels wrong
            # main_chiplet.ksh_l2_cache.stats_accesses += main_chiplet.pe_array.ksh_file.size / C_t
            # main_chiplet.memory.stats_accesses += main_chiplet.pe_array.ksh_file.size / C_t
            # main_chiplet.pe_array.twiddle.stats_accesses += main_chiplet.pe_array.twiddle.size
            # main_chiplet.memory.stats_accesses += main_chiplet.pe_array.twiddle.size
            
            # TODO: Confirm this ; also since its iso-area can't we give more cache space to this?
            # num_k_memory = max(0, W[2]/C_t * W[3]/K_t - defs.max_c_on_chiplt)
            # if W[2]/C_t > defs.max_c_on_chiplt:
            #     print "Handle this case for ifs"
            #     exit()
            # print W[2]/C_t * W[3]/K_t, defs.max_wt_on_chiplt
            
            for m_step in range(0, M, Mt):              # Iterate over all non-overlapping matrices
                # Get the if from memory and put it in the L2 for the first iteration
                # TODO: Do we even need an IF cache?
                main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size
                main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size

                # Fill the L2 cache with wts, we will also have to account for coeff format accesses for opt_ntt's case
                # Store C/C_t x K/K_t wts in the L2, the rest will have to be handled from memory
                main_chiplet.memory.stats_accesses += int(math.ceil(main_chiplet.pe_array.wt_file.size * min(defs.max_wt_on_chiplt, W[2]/C_t * W[3]/K_t)))
                main_chiplet.wt_l2_cache.stats_accesses += int(math.ceil(main_chiplet.pe_array.wt_file.size * min(defs.max_wt_on_chiplt, W[2]/C_t * W[3]/K_t)))

                for p in range((W[0]-1)*(W[1]-1)/(S[0]*S[1]) + 1):  # Permute to create all overlappingmatrices

                    iters = 0
                    for k_step in range(0, W[3], K_t):        # Iterate over all kernels in K_t steps for wts
                        for c_step in range(0, W[2], C_t):    # Iterate over all channels in C_t steps for wts
                            # Access wts from the L2 or memory based on number
                            if iters < defs.max_wt_on_chiplt:
                                main_chiplet.wt_l2_cache.stats_accesses += main_chiplet.pe_array.wt_file.size
                            else:
                                main_chiplet.memory.stats_accesses += main_chiplet.pe_array.wt_file.size
                            main_chiplet.pe_array.wt_file.stats_accesses += main_chiplet.pe_array.wt_file.size
                            main_chiplet.pe_array.pip_stats.wt_file.stats_accesses += main_chiplet.pe_array.wt_file.size
                            # Access ifs from L2
                            main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size
                            main_chiplet.pe_array.if_file.stats_accesses += main_chiplet.pe_array.if_file.size
                            main_chiplet.pe_array.pip_stats.if_file.stats_accesses += main_chiplet.pe_array.if_file.size

                            # break
                            mult_loop += int(math.ceil(float(K_t)/if_replication))
                        
                        # break
                        psum_loop += RS*C_t
                        # break

                        # Flush PSUM to memory
                        main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                        main_chiplet.pe_array.pip_stats.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                        main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size
                    # break

                    if p != 0:
                        # Iterate over all channels in C_t steps for ifs
                        # this will happen once every permutation for every set of channel steps the first time they are called and then stored in the L2 cache
                        # there will be C/C_t ifs in the L2
                        for c_step in range(0, W[2], C_t):
                            if_loop += 1

            if defs.ntt_type == 'f1' and defs.arch == 'f1':
                main_chiplet.run_hyena_mult_pipe_f1_f1(mult_loop)
                main_chiplet.run_hyena_psum_pipe_f1_f1(psum_loop)
                main_chiplet.run_hyena_if_seq_f1_f1(if_loop)
            elif defs.ntt_type == 'f1' and defs.arch == 'hyena':
                main_chiplet.run_hyena_mult_pipe_f1_hyena(mult_loop)
                main_chiplet.run_hyena_psum_pipe_f1_hyena(psum_loop)
                main_chiplet.run_hyena_if_seq_f1_hyena(if_loop)
            else:
                print "run_hyena: Unkown Paramer for Run 1", defs.ntt_type, defs.arch
                exit()

            if console_print:
                main_chiplet.print_stats_console(IF, W, S)
                break
            else:
                main_chiplet.print_stats_file(IF, W, S, name, network)