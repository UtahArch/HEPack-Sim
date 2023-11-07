#################################################################################
##  Main file for running sumulations
##
##  Running Cheetah Packing
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

                line = "Dimensions { K: 64, C: 3, R: 7, S: 7, Y:224, X:224 }"

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
            
            # Decide Params

            # IF Packing
            P  = (IF[0] - W[0] + 1)*(IF[1] - W[1] + 1) / (S[0]*S[1])      # Total Number of Matrices
            RS = W[0]*W[1]                                   # Size of 1 Matrices

            n_ckks = cl.poly_size / 2  # Polynomial Size

            # Pack Cts
            Ct = 1
            if W[2] > 1:
                while Ct < W[2]:
                    Ct *= 2
                    if RS*Ct*Ct > n_ckks:
                        break
                Ct /= 2
            if Ct > W[2]:
                print "ERROR Hyena 1"
                exit()

            inner_loop=0
            if console_print:
                print("P:{:4d}\tRS:{:4d}\tCt:{:4d}\tRS*Ct*Ct:{:4d}\t\tPF:{:}\n".format(P, RS, Ct, W[1]*W[0]*Ct*Ct, (RS*Ct*Ct)/float(n_ckks)))
            assert(RS*Ct*Ct <= n_ckks)

            # Define Classes and globals
            cl.Ct = Ct
            
            # if console_print:
            #     continue

            if_count = 0
            mult_count = 0
            psum_count = 0

            # Perform Channel
            # For every output feature point
            for of in range(P):

                # for all channel steps
                for c_step in range(0, W[2], Ct):

                    for iters_if in range(RS):

                        # Rotate IFs
                        if_count += 1                        
                        
                    for iters_k in range(0, W[3], Ct):
                        
                        for iters_ct in range(Ct):
                            
                            for iters_mul in range(RS):
                                # Do Mult
                                mult_count += 1
                            
                            # Do Rotate and PSUM Accumulation
                            psum_count += 1
            
            num_layers += 1
            temp_time = cl.run_KSH(if_count, cl.curr_depth) + cl.run_MUL(mult_count, cl.curr_depth)
            cl.curr_depth -= 1
            temp_time += cl.run_KSH(psum_count, cl.curr_depth)
            
            if cl.curr_depth == 1:
                cl.curr_depth = cl.new_depth

            cl.run_time += temp_time
            print name, temp_time

print cl.run_time, num_layers
