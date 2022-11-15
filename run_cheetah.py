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

            IF = (2*param['X'], param['Y'], param['C'])
            W  = (2*param['R'], param['S'], param['C'], param['K'])
            
            # Decide Params
            ## To decide C_t and XY_t - IF packing
            C_t = 1
            XY = IF[0] * IF[1]

            defs.poly_n = poly_n

            if XY < defs.poly_n:
                XY_t = XY
                while C_t < IF[2]:
                    C_t *= 2
                    if XY*C_t > defs.poly_n:
                        C_t /= 2
                        break
            else:
                XY_t = defs.poly_n

            i=0
            if console_print:
                print("\nFor Iter {:3d}:  XY_t:{:4d}  C_t:{:4d}  XY*C_t:{:4d}".format(i, XY_t, C_t, XY*C_t))

            # Define Classes and globals
            defs.c_t = C_t
            defs.packing = "cheetah"
            defs.ntt_type = ntttype
            defs.arch = arch
            defs.batch_size = batch
            defs.poly_n = poly_n
            defs.num_chiplets = defs.poly_n / (defs.pe_size)

            main_chiplet = packings.Chiplet()
            
            if defs.ntt_type == 'f1' and defs.arch == 'f1':
                main_chiplet.setup_cheetah_f1_f1()
            else:
                print "run_cheetah: Unkown Paramer for Setup 1"
                exit()

            # Bring Values to KSH and twiddle
            # For optimised NTT Twiddle carries the hints
            # TODO: Since Re-Use distance it soo much do we have a KSH and Twiddle L2 cache? How does L2 change for large polynomials
            # TODO: main_chiplet.pe_array.ksh_file.size / C_t feels wrong
            # main_chiplet.ksh_l2_cache.stats_accesses += main_chiplet.pe_array.ksh_file.size / C_t
            # main_chiplet.memory.stats_accesses += main_chiplet.pe_array.ksh_file.size / C_t
            # main_chiplet.pe_array.twiddle.stats_accesses += main_chiplet.pe_array.twiddle.size
            # main_chiplet.pe_array.pip_stats.twiddle.stats_accesses += main_chiplet.pe_array.twiddle.size
            # main_chiplet.memory.stats_accesses += main_chiplet.pe_array.twiddle.size

            # Loop to finish all XYs of the IF
            for if_step in range(0, XY, XY_t):
                
                # Store C/C_t ifs in L2, the rest will have to handled from memory
                main_chiplet.memory.stats_accesses += defs.if_file_size * min(defs.max_c_on_chiplt, W[2]/C_t)
                main_chiplet.if_l2_cache.stats_accesses += defs.if_file_size * min(defs.max_c_on_chiplt, W[2]/C_t)

                # Loop to finish all Kernels
                for k in range(W[3]):
                    iters_if = 0
                    # Loop to finish all Channels
                    # print if_step, k
                    for c_step in range(0, W[2], C_t):
                        # print("Running Iters {} : {} {} {}".format(i, if_step, k_step, c_step))
                        main_chiplet.pe_array.if_file.stats_accesses += main_chiplet.pe_array.if_file.size
                        main_chiplet.pe_array.pip_stats.if_file.stats_accesses += main_chiplet.pe_array.if_file.size
                        if iters_if < defs.max_c_on_chiplt:
                            main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size
                        else:
                            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size

                        # break
                        # print if_step, k, c_step
                        main_chiplet.run_cheetah(W[1] * W[0] * C_t)

                        # Flush PSUM to memory
                        main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                        main_chiplet.pe_array.pip_stats.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                        main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size
                    # break
                # break

            if console_print:
                main_chiplet.print_stats_console(IF, W, S)
                break
            else:
                main_chiplet.print_stats_file(IF, W, S, name, network)
