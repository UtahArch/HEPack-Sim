#################################################################################
##  Main file for running sumulations
##  Running Epic Packing
##
##  Usage: python run_epic.py <network> <ntttype> <arch> <poly_n>
##  Example: python run_epic.py resnet f1 f1 1
#################################################################################
 
import defs
import packings
import sys
import os

console_print = False

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

            # To decide Ct and XtYt - IF Packing
            Ct = 1
            XY = IF[0] * IF[1]

            defs.poly_n = poly_n
            n_ckks = defs.poly_n / 2

            if XY < n_ckks:
                XtYt = XY
                while Ct <= IF[2]:
                    Ct *= 2
                    if XtYt*Ct > n_ckks:
                        break
                Ct /= 2
            else:
                XtYt = n_ckks
            assert(Ct <= W[2])
            assert(Ct*XtYt <= n_ckks)
            
            # To decide Kt based on Ct - Wt Packing
            Kt = 1
            while Kt <= W[3]:
                if Kt * Ct * W[0] * W[1] <= n_ckks:
                    Kt *= 2
                else:
                    break
            Kt /= 2
            assert(Kt <= W[3])

            inner_loop=0
            if console_print:
                # print("XtYt:{:4d}\tCt   :{:4d}\t\tPF:{:}".format(XtYt, Ct, (XtYt*Ct)/float(n_ckks)))
                # print("Kt :{:4d}\tRS*Kt:{:4d}\t\tPF:{:}\n".format(Kt, W[1]*W[0]*Kt, (Kt*Ct*W[0]*W[1])/float(n_ckks)))
                print "IF:",(XtYt*Ct)/float(n_ckks), "::", "WT:",(W[0]*W[1]*Ct*Kt)/float(n_ckks)
            assert(XtYt*Ct <= n_ckks)
            assert(Kt*Ct*W[0]*W[1] <= n_ckks)
            assert(XtYt*Ct*Kt != 0)

            # Define Classes
            defs.Ct = Ct
            defs.Kt = Kt
            defs.packing = "epic"
            defs.ntt_type = ntttype
            defs.arch = arch
            defs.batch_size = batch
            defs.poly_n = poly_n
            defs.num_chiplets = defs.poly_n / (defs.pe_size)

            main_chiplet = packings.Chiplet()
            if defs.ntt_type == 'f1' and defs.arch == 'f1':
                main_chiplet.setup_epic_f1_f1()
            elif defs.ntt_type == 'f1' and defs.arch == 'hyena':
                main_chiplet.setup_epic_f1_hyena()
            else:
                print "run_epic: Unkown Paramer for Run 1", defs.ntt_type, defs.arch
                exit()
            
            if console_print:
                continue

            # Bring Values to N KSH values L2
            main_chiplet.ksh_l2_cache.stats_accesses += main_chiplet.pe_array.ksh_file.size * defs.poly_n
            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.ksh_file.size * defs.poly_n

            # Loop to finish all IFs
            for xy in range(0, XY, XtYt):
                
                # Store C/Ct ifs in L2, the rest will have to handled from memory
                main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size * min(defs.max_if_on_chiplt, W[2]/Ct)
                main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size * min(defs.max_if_on_chiplt, W[2]/Ct)

                # Fill the L2 cache with wts
                # Store C/Ct x K/Kt wts in the L2, the rest will have to be handled from memory
                main_chiplet.memory.stats_accesses += main_chiplet.pe_array.wt_file.size * min(defs.max_wt_on_chiplt, W[2]/Ct * W[3]/Kt)
                main_chiplet.wt_l2_cache.stats_accesses += main_chiplet.pe_array.wt_file.size * min(defs.max_wt_on_chiplt, W[2]/Ct * W[3]/Kt)
                    
                iters_wt = 0

                # Loop to finish all Kernels
                for k_step in range(0, W[3], Kt):
                    
                    iters_if = 0
                    
                    # Loop to finish all Channels
                    for c_step in range(0, W[2], Ct):
                        
                        # An IF is brought for processing and run wts are brought                        
                        if iters_if < defs.max_if_on_chiplt:
                            main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size
                        else:
                            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size
                        main_chiplet.pe_array.if_file.stats_accesses += main_chiplet.pe_array.if_file.size

                        if iters_wt < defs.max_wt_on_chiplt:
                            main_chiplet.wt_l2_cache.stats_accesses += main_chiplet.pe_array.wt_file.size
                        else:
                            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.wt_file.size
                        main_chiplet.pe_array.wt_file.stats_accesses += main_chiplet.pe_array.wt_file.size

                        # Number of rotations = R S Ct Kt / Ct
                        inner_loop += W[1] * W[0] * Kt
                        iters_wt += 1
                        iters_if += 1

                        # Data Movement
                        # 1 IF & Wt
                        # RSKt KSH
                        main_chiplet.data_movmt["IF"] += main_chiplet.pe_array.if_file.size 
                        main_chiplet.data_movmt["WT"] += main_chiplet.pe_array.wt_file.size
                        main_chiplet.data_movmt["KSH"] += main_chiplet.pe_array.ksh_file.size * (W[1]*W[0]*Kt)
                    
                    # Flush PSUM to memory
                    main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                    main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size


            if defs.ntt_type == 'f1' and defs.arch == 'f1':
                main_chiplet.run_epic_f1_f1(inner_loop)
            elif defs.ntt_type == 'f1' and defs.arch == 'hyena':
                main_chiplet.run_epic_f1_hyena(inner_loop)
            else:
                print "run_epic: Unkown Paramer for Run 1", defs.ntt_type, defs.arch
                exit()

            main_chiplet.calc_epic_pseudo()
            if console_print:
                main_chiplet.print_stats_console(IF, W, S)
                break
            else:
                main_chiplet.print_stats_file(IF, W, S, name, network)