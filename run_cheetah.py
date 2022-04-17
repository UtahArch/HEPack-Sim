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

os.system('clear')

ntttype  = sys.argv[1]
arch     = sys.argv[2]
poly_n   = int(sys.argv[3])
num_muls = int(sys.argv[4])
batch    = 1


with open("Resnet50_model.m") as fin:
    for line in fin.readlines():
        if "Layer" in line:
            name = line.split()[1]
        elif "Dimensions" in line:
            param = {}
            # line = "Dimensions { K: 128, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
            line = "Dimensions { K: 512, C: 512, R: 3, S: 3, Y: 7, X: 7 }"
            # line = "Dimensions { K: 64, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
            
            temp = line.split("{")[1].split("}")[0].split(",")
            for t in temp:
                t = [x.strip() for x in t.split(":")]
                param[t[0]] = int(t[1])
            print name, param

            IF = (param['X'], param['Y'], param['C'])
            W  = (param['R'], param['S'], param['C'], param['K'])
            
            # Decide Params
            ## To decide C_t and XY_t - IF packing
            C_t = 1
            XY = IF[0] * IF[1]

            if XY < defs.wt_file_size * defs.num_pe_x * defs.num_pe_y:
                XY_t = XY
                while C_t < IF[2]:
                    C_t *= 2
                    if XY*C_t > defs.wt_file_size * defs.num_pe_x * defs.num_pe_y:
                        C_t /= 2
                        break
            else:
                XY_t = defs.wt_file_size * defs.num_pe_x * defs.num_pe_y

            i=0
            print("\nFor Iter {:3d}:  XY_t:{:4d}  C_t:{:4d}  XY*C_t:{:4d}".format(i, XY_t, C_t, XY*C_t))

            # Define Classes and globals
            defs.c_t = C_t
            defs.packing = "cheetah"
            defs.ntt_type = ntttype
            defs.arch = arch
            defs.batch_size = batch
            defs.poly_n = poly_n
            defs.num_chiplets = defs.poly_n / (defs.wt_file_size * defs.num_pe)

            if defs.arch == 'f1':
                defs.rotation = defs.rotation_f1
            elif defs.arch == 'hyena':
                defs.rotation = defs.rotation_hyena
            else:
                print "Error with def.rotation", defs.rotation

            main_chiplet = packings.Chiplet()
            main_chiplet.setup_cheetah()


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
                
                # TODO: Discuss this again
                if W[2]/C_t <= defs.max_c_on_chiplt:
                    main_chiplet.memory.stats_accesses += defs.num_pe_x * defs.num_pe_y * defs.if_file_size * min(defs.max_c_on_chiplt, W[2]/C_t)
                    main_chiplet.if_l2_cache.stats_accesses += defs.num_pe_x * defs.num_pe_y * defs.if_file_size * min(defs.max_c_on_chiplt, W[2]/C_t)
                else:
                    print("\t[ERROR] Handle This Case!!!")
                    exit()

                # Loop to finish all Kernels
                for k in range(W[3]):
                    # Loop to finish all Channels
                    # print if_step, k
                    for c_step in range(0, W[2], C_t):
                        # print("Running Iters {} : {} {} {}".format(i, if_step, k_step, c_step))
                        main_chiplet.pe_array.if_file.stats_accesses += main_chiplet.pe_array.if_file.size
                        main_chiplet.pe_array.pip_stats.if_file.stats_accesses += main_chiplet.pe_array.if_file.size
                        main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size

                        # break
                        # print if_step, k, c_step
                        main_chiplet.run_cheetah(W[1] * W[0] * C_t)

                        # Flush PSUM to memory
                        main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                        main_chiplet.pe_array.pip_stats.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                        main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size
                    # break
                # break
                        

            main_chiplet.calc_time_cheetah()
            main_chiplet.print_stats_console(IF, W)
            break
