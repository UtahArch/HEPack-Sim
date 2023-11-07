#################################################################################
##  Main file for running sumulations
##
##  Running Cheetah 2 Packing
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
poly_n = 1024

done_params = set()
total_time = 0

def opt_HwWw():

    def func(Hw, Ww):
        Hw = float(Hw)
        Ww = float(Ww)
        return math.ceil(C/(N/(Hw*Ww)))*math.ceil((H-h+1)/(Hw-h+1))*math.ceil((W-h+1)/(Ww-h+1))

    min_val = func(1,1)
    mins = (1,1)

    for Hw in range(h,H+1):
        for Ww in range(h, W+1):
            if Hw*Ww > N:
                continue
            temp = func(Hw, Ww)
            # print Hw, Ww, temp, temp < min_val
            if temp < min_val:
                mins = (Hw,Ww)
                min_val = temp
    
    return mins

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
                line = "Dimensions { K: 1000, C: 1280, R: 7, S: 7, Y: 7, X: 7 }"

            temp = line.split("{")[1].split("}")[0].split(",")
            for t in temp:
                t = [x.strip() for x in t.split(":")]
                param[t[0]] = int(t[1])

            IF = (param['X'], param['Y'], param['C'])
            W_old  = (param['R'], param['S'], param['C'], param['K'])
            
            if console_print:
                if line in done_params:
                    continue
                else:
                    done_params.add(line)

            N = defs.poly_n / 2  # Polynomial Size

            if console_print:
                print
                print name, param, S
            
            M = W_old[3]
            C = W_old[2]
            assert(W_old[1] == W_old[0])
            h = W_old[1]
            H = IF[1]
            W = IF[0]

            (Hw, Ww) = opt_HwWw()
            # print N, Hw, Ww
            Cw = min(C, int(math.floor(N/float(Hw*Ww))))
            # print N, Hw, Ww, Cw
            Mw = min(M, int(math.floor(N/float(Cw*Hw*Ww))))

            assert(Mw*Cw*Hw*Ww <= N)

            if console_print == True:
                if Mw*Cw*Hw*Ww <= N:
                    print "Yes Mw/Kt:{}  Cw/Ct:{}  Hw,Ww:{},{}  Eff:{}".format(Mw, Cw, Hw, Ww, Mw*Cw*Hw*Ww/float(N))
                else:
                    print "No", Mw*Cw*Hw*Ww/N
                    exit()

            
            # Define Classes
            defs.Ct = Cw
            defs.Kt = Mw
            defs.packing = "lion"
            defs.ntt_type = "f1"
            defs.arch = "f1"
            defs.poly_n = poly_n

            main_chiplet = packings.Chiplet()
            
            main_chiplet.setup_lion(30)

            # Bring Values to N KSH values L2
            main_chiplet.ksh_l2_cache.stats_accesses += main_chiplet.pe_array.ksh_file.size * defs.poly_n
            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.ksh_file.size * defs.poly_n

            mul_count = 0            
            for of in range(int(math.ceil((H-h+1)/(Hw-h+1)))*int(math.ceil((W-h+1)/(Ww-h+1)))):

                # Get the if from memory and put it in the L2 for the first iteration
                main_chiplet.memory.stats_accesses    += main_chiplet.pe_array.if_file.size * min(defs.max_if_on_chiplt, int(W_old[2]/Cw))
                main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size * min(defs.max_if_on_chiplt, int(W_old[2]/Cw))

                iters_wt_inner = 0
                for k_ in range(0, M, Mw):

                    iters_if_inner = 0
                    for c_ in range(0, C, Cw):
                        
                        # Access IF from the L2 or memory based on number
                        if iters_if_inner < defs.max_if_on_chiplt:
                            main_chiplet.if_l2_cache.stats_accesses += main_chiplet.pe_array.if_file.size
                        else:
                            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.if_file.size
                        main_chiplet.pe_array.if_file.stats_accesses += main_chiplet.pe_array.if_file.size
                        
                        for m_ in range(Mw):

                            main_chiplet.memory.stats_accesses += main_chiplet.pe_array.wt_file.size
                            main_chiplet.pe_array.wt_file.stats_accesses += main_chiplet.pe_array.wt_file.size

                            mul_count += 1
                            # Data Movement
                            # 1 Wt
                            main_chiplet.data_movmt["WT"] += main_chiplet.pe_array.wt_file.size
                        
                        # Data Movement
                        # 1 IF
                        main_chiplet.data_movmt["IF"] += main_chiplet.pe_array.if_file.size

                    # Flush PSUM to memory
                    main_chiplet.pe_array.psum_file.stats_accesses += main_chiplet.pe_array.psum_file.size
                    main_chiplet.memory.stats_accesses += main_chiplet.pe_array.psum_file.size
            
            main_chiplet.run_lion(mul_count)
            if console_print:
                main_chiplet.print_stats_console(IF, W_old, S)
                # break
                # print main_chiplet.cycles * defs.cycle_time + main_chiplet.stalls
                print main_chiplet.memory.stats_accesses
            else:
                main_chiplet.print_stats_file(IF, W_old, S, name, network)