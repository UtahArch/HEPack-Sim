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
batch    = int(sys.argv[5])

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
                line = "Dimensions { K: 2048, C: 512, R: 1, S: 1, Y: 7, X: 7 }"
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

            Kt = 1
            Ct = 1
            Bt = 1
            # Wt Packing
            if W[3] > 1:
                while ((Kt < defs.psum_file_num) and (Kt < W[3])):
                    Kt *= 2
                    if RS*Ct*Kt > n_ckks:
                        break
                Kt /= 2
            if Kt > W[3]:
                print "ERROR Hyena 2"
                exit()
            
            if batch > 1:
                while Bt < batch:
                    Bt += 1
                    if RS*Ct*Kt*Bt > n_ckks or RS*Ct*Mt*Bt > n_ckks:
                        break
                Bt -= 1
            assert(Bt <= batch)

            # Pack Cts
            if W[2] > 1:
                while Ct < W[2]:
                    Ct *= 2
                    if RS*Ct*Kt*Bt > n_ckks or RS*Ct*Mt*Bt > n_ckks:
                        break
                Ct /= 2
            if Ct > W[2]:
                print "ERROR Hyena 1"
                exit()

            if_replication = int(math.floor(float(n_ckks)/(Mt*Ct*RS*Bt)))
            
            mult_loop = 0
            psum_loop = 0
            if_loop = 0
            if console_print:
                print("P :{:4d}\tM   :{:4d}\tMt   :{:4d}\tCt :{:4d}\t\tIF-PE:{:}".format(P, M, Mt, Ct, (Mt*Bt*RS*Ct)/float(n_ckks)))
                print("Kt:{:4d}\tBt  :{:4d}\tRS*Kt:{:4d}\tIR :{:4d}\t\tWT-PE:{:}".format(Kt, Bt, W[1]*W[0]*Kt, if_replication, (Bt*Kt*Ct*W[0]*W[1])/float(n_ckks)))
            assert(Mt*RS*Ct*Bt*if_replication <= n_ckks)
            assert(Kt*Ct*RS <= n_ckks)

            # Define Classes
            defs.Ct = Ct
            defs.Kt = Kt
            defs.Bt = 1
            defs.packing = "hyenaplus"
            defs.ntt_type = ntttype
            defs.arch = arch
            defs.num_muls = num_muls
            defs.batch_size = batch
            defs.poly_n = poly_n
            defs.num_chiplets = defs.poly_n / (defs.pe_size)

            main_chiplet = packings.Chiplet()
            main_chiplet = packings.Chiplet()
            if defs.ntt_type == 'f1' and defs.arch == 'f1':
                main_chiplet.setup_hyena_f1_f1(RS*Ct, W[2], W[3])
            elif defs.ntt_type == 'f1' and defs.arch == 'hyena':
                main_chiplet.setup_hyena_f1_hyena(RS*Ct, W[2], W[3])
            else:
                print "run_hyena: Unkown Paramer for Run 1", defs.ntt_type, defs.arch
                exit()

            # if console_print:
            #     continue

            # Bring Values to N KSH values L2
            main_chiplet.ksh_l2_cache.stats_accesses += main_chiplet.pe_array.ksh_file.size * defs.poly_n
            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.ksh_file.size * defs.poly_n
            
            for b_step in range(0, batch, Bt):  # Iterate over all images in a batch

                for m_step in range(0, M, Mt):              # Iterate over all non-overlapping matrices
                    
                    # Get the if from memory and put it in the L2 for the first iteration
                    main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size * min(defs.max_if_on_chiplt, int(W[2]/Ct))
                    main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size * min(defs.max_if_on_chiplt, int(W[2]/Ct))

                    # Fill the L2 cache with wts, we will also have to account for coeff format accesses for opt_ntt's case
                    # Store C/Ct x K/Kt wts in the L2, the rest will have to be handled from memory
                    main_chiplet.memory.stats_accesses += int(math.ceil(main_chiplet.pe_array.wt_file.size * min(defs.max_wt_on_chiplt, W[2]/Ct * W[3]/Kt)))
                    main_chiplet.wt_l2_cache.stats_accesses += int(math.ceil(main_chiplet.pe_array.wt_file.size * min(defs.max_wt_on_chiplt, W[2]/Ct * W[3]/Kt)))

                    for non_over_mat in range((W[0]-1)*(W[1]-1)/(S[0]*S[1]) + 1):  # Permute to create all overlappingmatrices

                        iters_wt_inner = 0

                        for k_step in range(0, W[3], Kt):        # Iterate over all kernels in Kt steps for wts
                            
                            iters_if_inner = 0
                            
                            for c_step in range(0, W[2], Ct):    # Iterate over all channels in Ct steps for wts
                            
                                # Access wts from the L2 or memory based on number
                                if iters_wt_inner < defs.max_wt_on_chiplt:
                                    main_chiplet.wt_l2_cache.stats_accesses += main_chiplet.pe_array.wt_file.size
                                else:
                                    main_chiplet.memory.stats_accesses += main_chiplet.pe_array.wt_file.size
                                main_chiplet.pe_array.wt_file.stats_accesses += main_chiplet.pe_array.wt_file.size
                    
                                # Access IF from the L2 or memory based on number
                                if iters_if_inner < defs.max_if_on_chiplt:
                                    main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size
                                else:
                                    main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size
                                main_chiplet.pe_array.if_file.stats_accesses += main_chiplet.pe_array.if_file.size

                                mult_loop += int(math.ceil(float(Kt)/if_replication))
                                iters_wt_inner += 1
                                iters_if_inner += 1

                                # Data Movement
                                # 1 IF & Wt
                                main_chiplet.data_movmt += main_chiplet.pe_array.if_file.size + main_chiplet.pe_array.wt_file.size
                            
                            psum_loop += RS*Ct
                            
                            # Data Movement
                            # RSCt KSH
                            main_chiplet.data_movmt += main_chiplet.pe_array.ksh_file.size * (RS*Ct)

                            # Flush PSUM to memory
                            main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size

                        if non_over_mat != 0:
                            
                            iters_if = 0
                            
                            # Iterate over all channels in Ct steps for ifs
                            # this will happen once every permutation for every set of channel steps the first time they are called and then stored in the L2 cache
                            # there will be C/Ct ifs in the L2
                            for c_step in range(0, W[2], Ct):
                                # Access IF from L2 or Memory
                                # Store the value in L2
                                main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size

                                if_loop += 1
                                # Data Movement
                                # 1 KSH
                                main_chiplet.data_movmt += main_chiplet.pe_array.ksh_file.size

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

            main_chiplet.calc_hyena_pseudo()
            if console_print:
                main_chiplet.print_stats_console(IF, W, S)
                break
            else:
                main_chiplet.print_stats_file(IF, W, S, name, network)