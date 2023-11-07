#################################################################################
##  Main file for running sumulations
##  Running Channel Packing
##  
##  Usage: python run_channel.py <network> <ntttype> <arch> <poly_n>
##  Example: python run_channel.py resnet f1 f1 1
#################################################################################
 
import defs
import packings
import sys
import os
import math

console_print = True

if console_print:
    os.system('clear')

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
        elif "Dimensions" in line:
            param = {}
            # if console_print:
            #     S = [1,1]
            #     # line = "Dimensions { K: 24, C: 96, R: 1, S: 1, Y:56, X:56 }"
            #     # line = 'Dimensions { K: 1, C: 96, R: 3, S: 3, Y:56, X:56 }'
            #     # line = 'Dimensions { K: 256, C: 64, R: 1, S: 1, Y: 56, X: 56 }'
            #     # line = "Dimensions { K: 1, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
            #     # line = "Dimensions { K: 64, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
            #     # line = "Dimensions { K: 1000, C: 2048, R: 7, S: 7, Y: 7, X: 7 }"
            #     # line = "Dimensions { K: 1, C: 96, R: 3, S: 3, Y:112, X:112 }"

            #     line = "Dimensions { K: 64, C: 3, R: 7, S: 7, Y:224, X:224 }"
            # line = "Dimensions { K: 3072, C: 4096, Y: 320, X: 1, R: 1, S: 1 }"

            if console_print:
                if line in done_params:
                    continue
                else:
                    done_params.add(line)
            
            temp = line.split("{")[1].split("}")[0].split(",")
            for t in temp:
                t = [x.strip() for x in t.split(":")]
                param[t[0]] = int(t[1])
            # if console_print:
            #     print name, param

            IF = (param['X'], param['Y'], param['C'])
            W  = (param['R'], param['S'], param['C'], param['K'])
            
            # Decide Params

            # IF Packing
            P  = (IF[0] - W[0] + 1)*(IF[1] - W[1] + 1) / (S[0]*S[1])      # Total Number of Matrices
            RS = W[0]*W[1]                                   # Size of 1 Matrices

            n_ckks = defs.poly_n / 2  # Polynomial Size

            # Pack Cts
            Ct = 1
            while (Ct <= W[2]) and (Ct <= W[3]):
                Ct *= 2
                if RS*Ct*Ct > n_ckks:
                    break
            Ct /= 2
            assert((Ct <= W[2]) and (Ct <= W[3]))
            # Pack Faces
            Pt = int(n_ckks/(RS*Ct*Ct))            

            inner_loop=0
            if console_print:
                # print("P:{:4d}\tRS:{:4d}\tCt:{:4d}\tRS*Ct*Ct:{:4d}\t\tPF:{:}\n".format(P, RS, Ct, W[1]*W[0]*Ct*Ct, (RS*Ct*Ct)/float(n_ckks)))
                # print "IF:{:.4f}\tWT:{:.4f}\tPE:{}".format((RS*Ct*Pt)/float(n_ckks), (1*Ct*Ct)/float(n_ckks), RS*Ct*Ct*Pt)
                print (Ct*Ct)/float(n_ckks),",",
            assert(RS*Ct*Ct*Pt <= n_ckks)
            assert(Ct != 0)

            # Define Classes and globals
            defs.Ct = Ct
            defs.packing = "channel"
            defs.ntt_type = ntttype
            defs.arch = arch
            defs.batch_size = batch
            defs.poly_n = poly_n
            defs.num_chiplets = defs.poly_n / (defs.pe_size)

            main_chiplet = packings.Chiplet()
            
            if defs.ntt_type == 'f1' and defs.arch == 'f1':
                main_chiplet.setup_channel_f1_f1()
            elif defs.ntt_type == 'f1' and defs.arch == 'hyena':
                main_chiplet.setup_channel_f1_hyena()
            else:
                print "run_cheetah: Unkown Paramer for Setup 1", defs.ntt_type, defs.arch
                exit()
            
            if console_print:
                continue

            if_count = 0
            mult_count = 0
            psum_count = 0

            # Bring Values to N KSH values L2
            main_chiplet.ksh_l2_cache.stats_accesses += main_chiplet.pe_array.ksh_file.size * defs.poly_n
            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.ksh_file.size * defs.poly_n

            # Perform Channel
            # For every output feature point
            for of in range(int(math.ceil(float(P)/Pt))):

                # for all channel steps
                for c_step in range(0, W[2], Ct):

                    # Load IF from Memory
                    main_chiplet.memory.stats_accesses += defs.if_file_size
                    main_chiplet.pe_array.if_file.stats_accesses += defs.if_file_size

                    # Data Movement
                    # 1 IF
                    main_chiplet.data_movmt["IF"] += main_chiplet.pe_array.if_file.size

                    for iters_if in range(RS):
                        if_count += 1
                        # Data Movement
                        # 1 KSH
                        main_chiplet.data_movmt["KSH"] += main_chiplet.pe_array.ksh_file.size

                        # Store Rotated IFs in L2 if they fit
                        if iters_if < defs.max_if_on_chiplt:
                            main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size
                            iters_if += 1
                        else:
                            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size
                        
                    for iters_k in range(0, W[3], Ct):
                        
                        for iters_ct in range(Ct):
                            
                            for iters_mul in range(RS):
                                # Access Rotated Ifs from L2 if they fit
                                if iters_mul < defs.max_if_on_chiplt:
                                    main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size
                                    iters_if += 1
                                else:
                                    main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size
                                mult_count += 1
                                
                                # Data Movement
                                # 1 IF W
                                main_chiplet.data_movmt["IF"] += main_chiplet.pe_array.if_file.size
                                main_chiplet.data_movmt["WT"] += main_chiplet.pe_array.wt_file.size
                            
                            psum_count += 1
                            # Data Movement
                            # 1 KSH
                            main_chiplet.data_movmt["KSH"] += main_chiplet.pe_array.ksh_file.size

                        # Flush PSUM to memory
                        main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                        main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size

            if defs.ntt_type == 'f1' and defs.arch == 'f1':
                main_chiplet.run_channel_mult_pipe_f1_f1(mult_count)
                main_chiplet.run_channel_psum_pipe_f1_f1(psum_count)
                main_chiplet.run_channel_if_seq_f1_f1(if_count)
            elif defs.ntt_type == 'f1' and defs.arch == 'hyena':
                main_chiplet.run_channel_mult_pipe_f1_hynea(mult_count)
                main_chiplet.run_channel_psum_pipe_f1_hynea(psum_count)
                main_chiplet.run_channel_if_seq_f1_hynea(if_count)
            else:
                print "run_channel: Unkown Paramer for Run 1", defs.ntt_type, defs.arch
                exit()

            main_chiplet.calc_channel_pseudo()
            if console_print:
                main_chiplet.print_stats_console(IF, W, S)
                break
            else:
                main_chiplet.print_stats_file(IF, W, S, name, network)
