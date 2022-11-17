#################################################################################
##  Main file for running sumulations
##
##  Running EPIC Packing
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
            if console_print:
                S = [1,1]
                # line = "Dimensions { K: 24, C: 96, R: 1, S: 1, Y:56, X:56 }"
                # line = 'Dimensions { K: 1, C: 96, R: 3, S: 3, Y:56, X:56 }'
                # line = "Dimensions { K: 512, C: 512, R: 3, S: 3, Y: 7, X: 7 }"
                # line = "Dimensions { K: 1, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
                # line = "Dimensions { K: 64, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
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
                print name, param

            IF = (param['X'], param['Y'], param['C'])
            W  = (param['R'], param['S'], param['C'], param['K'])

            # To decide C_t and XY_t - IF Packing
            C_t = 1
            XY = IF[0] * IF[1]

            defs.poly_n = poly_n
            n_ckks = defs.poly_n / 2

            if XY < n_ckks:
                XY_t = XY
                if IF[2] > 1:
                    while C_t < IF[2]:
                        C_t *= 2
                        if XY_t*C_t > n_ckks:
                            break
                    C_t /= 2
            else:
                XY_t = n_ckks
            if C_t > W[2]:
                print "ERROR EPIC 1"
                exit()

            assert ( C_t * W[0] * W[1] <= n_ckks)
            
            # To decide K_t based on C_t - Wt Packing
            K_t = 1
            if W[3] > 1:
                while K_t < W[3]:
                    if K_t * C_t * W[0] * W[1] <= n_ckks:
                        K_t *= 2
                    else:
                        break
                K_t /= 2
            if K_t > W[3]:
                print "ERROR EPIC 2"
                exit()

            inner_loop=0
            if console_print:
                print("XY_t:{:4d}\tC_t   :{:4d}\t\tPF:{:}".format(XY_t, C_t, (XY_t*C_t)/float(n_ckks)))
                print("K_t :{:4d}\tRS*K_t:{:4d}\t\tPF:{:}\n".format(K_t, W[1]*W[0]*K_t, (K_t*C_t*W[0]*W[1])/float(n_ckks)))
                # print("\nFor Iter {:3d}:  XY_t:{:4d}  C_t:{:4d}  XY*C_t:{:4d}  RSCt:{:4d}".format(inner_loop, XY_t, C_t, XY*C_t, W[1] * W[0] * C_t))
            assert(XY_t*C_t <= n_ckks)
            assert(K_t*C_t*W[0]*W[1] <= n_ckks)

            # Define Classes
            defs.c_t = C_t
            defs.k_t = K_t
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
            
            # if console_print:
            #     continue

            # # Bring Values to KSH and twiddle
            # # For optimised NTT Twiddle carries the hints
            # # TODO: Since Re-Use distance it soo much do we have a KSH and Twiddle L2 cache? How does L2 change for large polynomials
            # # TODO: main_chiplet.pe_array.ksh_file.size / C_t feels wrong
            # main_chiplet.ksh_l2_cache.stats_accesses += main_chiplet.pe_array.ksh_file.size / C_t
            # main_chiplet.memory.stats_accesses += main_chiplet.pe_array.ksh_file.size / C_t
            # main_chiplet.pe_array.twiddle.stats_accesses += main_chiplet.pe_array.twiddle.size
            # main_chiplet.memory.stats_accesses += main_chiplet.pe_array.twiddle.size

            # Loop to finish all IFs
            for if_step in range(0, XY, XY_t):
                # print("Running Iters {} : {}".format(i, if_step))
                # Store C/C_t ifs in L2, the rest will have to handled from memory
                main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size * min(defs.max_c_on_chiplt, W[2]/C_t)
                main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size * min(defs.max_c_on_chiplt, W[2]/C_t)

                # Fill the L2 cache with wts
                # Store C/C_t x K/K_t wts in the L2, the rest will have to be handled from memory
                main_chiplet.memory.stats_accesses += main_chiplet.pe_array.wt_file.size * min(defs.max_wt_on_chiplt, W[2]/C_t * W[3]/K_t)
                main_chiplet.wt_l2_cache.stats_accesses += main_chiplet.pe_array.wt_file.size * min(defs.max_wt_on_chiplt, W[2]/C_t * W[3]/K_t)
                    
                    
                iters_wt = 0
                # Loop to finish all Kernels
                for k_step in range(0, W[3], K_t):
                    iters_if = 0
                    # Loop to finish all Channels
                    for c_step in range(0, W[2], C_t):
                        # print("Running Iters {} : {} {} {}".format(i, if_step, k_step, c_step))
                        # An IF is brought for processing and run wts are brought                        
                        if iters_if < defs.max_c_on_chiplt:
                            main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size
                        else:
                            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size
                        main_chiplet.pe_array.if_file.stats_accesses += main_chiplet.pe_array.if_file.size
                        # main_chiplet.pe_array.pip_stats.if_file.stats_accesses += main_chiplet.pe_array.if_file.size

                        if iters_wt < defs.max_wt_on_chiplt:
                            main_chiplet.wt_l2_cache.stats_accesses += main_chiplet.pe_array.wt_file.size
                        else:
                            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.wt_file.size
                        main_chiplet.pe_array.wt_file.stats_accesses += main_chiplet.pe_array.wt_file.size
                        # main_chiplet.pe_array.pip_stats.wt_file.stats_accesses += main_chiplet.pe_array.wt_file.size

                        # break
                        # Number of rotations = R S C_t K_t / C_t
                        inner_loop += W[1] * W[0] * K_t
                        iters_wt += 1
                        iters_if += 1
                        # break
                    
                    # Flush PSUM to memory
                    main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                    main_chiplet.pe_array.pip_stats.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                    main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size
                    # break
                # break

            if defs.ntt_type == 'f1' and defs.arch == 'f1':
                main_chiplet.run_epic_f1_f1(inner_loop)
            elif defs.ntt_type == 'f1' and defs.arch == 'hyena':
                main_chiplet.run_epic_f1_hyena(inner_loop)
            else:
                print "run_epic: Unkown Paramer for Run 1", defs.ntt_type, defs.arch
                exit()

            if console_print:
                main_chiplet.print_stats_console(IF, W, S)
                break
            else:
                main_chiplet.print_stats_file(IF, W, S, name, network)