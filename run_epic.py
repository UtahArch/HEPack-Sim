#################################################################################
##  Main file for running sumulations
##
##  Running EPIC Packing
##
##
#################################################################################
 
import custom
import sys
import os

console_print = False

if console_print:
    os.system('clear')

network  = sys.argv[1]

done_params = set()

cl = custom.CraterLake()
num_layers = 0

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
                # line = 'Dimensions { K: 256, C: 64, R: 1, S: 1, Y: 56, X: 56 }'
                # line = "Dimensions { K: 1, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
                # line = "Dimensions { K: 64, C: 256, R: 1, S: 1, Y: 56, X: 56 }"
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
                print name, param

            IF = (param['X'], param['Y'], param['C'])
            W  = (param['R'], param['S'], param['C'], param['K'])

            # To decide Ct and XtYt - IF Packing
            Ct = 1
            XY = IF[0] * IF[1]

            n_ckks = cl.poly_size / 2  # Polynomial Size

            if XY < n_ckks:
                XtYt = XY
                if IF[2] > 1:
                    while Ct < IF[2]:
                        Ct *= 2
                        if XtYt*Ct > n_ckks:
                            break
                    Ct /= 2
            else:
                XtYt = n_ckks
            if Ct > W[2]:
                print "ERROR EPIC 1"
                exit()

            assert ( Ct * W[0] * W[1] <= n_ckks)
            
            # To decide Kt based on Ct - Wt Packing
            Kt = 1
            if W[3] > 1:
                while Kt < W[3]:
                    if Kt * Ct * W[0] * W[1] <= n_ckks:
                        Kt *= 2
                    else:
                        break
                Kt /= 2
            if Kt > W[3]:
                print "ERROR EPIC 2"
                exit()

            inner_loop=0
            if console_print:
                print("XtYt:{:4d}\tCt   :{:4d}\t\tPF:{:}".format(XtYt, Ct, (XtYt*Ct)/float(n_ckks)))
                print("Kt :{:4d}\tRS*Kt:{:4d}\t\tPF:{:}\n".format(Kt, W[1]*W[0]*Kt, (Kt*Ct*W[0]*W[1])/float(n_ckks)))
            assert(XtYt*Ct <= n_ckks)
            assert(Kt*Ct*W[0]*W[1] <= n_ckks)

            # Define Classes
            cl.Ct = Ct
            cl.Kt = Kt
            
            # if console_print:
            #     continue

            # Loop to finish all IFs
            for xy in range(0, XY, XtYt):
                    
                iters_wt = 0

                # Loop to finish all Kernels
                for k_step in range(0, W[3], Kt):
                    
                    iters_if = 0
                    
                    # Loop to finish all Channels
                    for c_step in range(0, W[2], Ct):

                        # Number of rotations = R S Ct Kt / Ct
                        inner_loop += W[1] * W[0] * Kt
                        iters_wt += 1
                        iters_if += 1

            num_layers += 1
            temp_time = cl.run_KSH(inner_loop, cl.curr_depth) + cl.run_MUL(inner_loop, cl.curr_depth)
            cl.curr_depth -= 1
            temp_time += cl.run_KSH(inner_loop, cl.curr_depth)
            
            if cl.curr_depth == 1:
                cl.curr_depth = cl.new_depth

            cl.run_time += temp_time
            print name, temp_time

print cl.run_time, num_layers