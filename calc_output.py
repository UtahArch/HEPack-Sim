#################################################################################
##  Calculates the total number of output neurons present for every layer. 
##  Used for computing the communication cost.
##  Refer to charts.ipyb # Communication for more details.  
##  
##  Usage: python calc_output.py <network_name>
##  Example: python calc_output.py gnmt
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

total_output_neurons = 0

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
            temp = line.split("{")[1].split("}")[0].split(",")
            for t in temp:
                t = [x.strip() for x in t.split(":")]
                param[t[0]] = int(t[1])

            IF = (param['X'], param['Y'], param['C'])
            W  = (param['R'], param['S'], param['C'], param['K'])

            defs.poly_n = poly_n
            # IF Packing
            P  = (IF[0] - W[0] + 1)*(IF[1] - W[1] + 1) / (S[0]*S[1])      # Total Number of Matrices
            M  = min(P, int(math.ceil(IF[0]/W[0])*math.ceil(IF[1]/W[1]))) # Number of non-overlapping Matrices
            RS = W[0]*W[1]                                   # Size of 1 Matrices

            n_ckks = defs.poly_n / 2  # Polynomial Size
            Mt = min(int(n_ckks/RS), M)    # Number of non-overlapping Matrices in 1 poly

            # Wt Packing
            Kt = 1
            Ct = 1
            while ((Kt <= defs.psum_file_num) and (Kt <= W[3])):
                Kt *= 2
                if RS*Ct*Kt > n_ckks:
                    break
            Kt /= 2
            assert(Kt <= W[3])

            # Pack Cts
            while Ct <= W[2]:
                Ct *= 2
                if Mt*RS*Ct > n_ckks or RS*Ct*Kt > n_ckks:
                    break
            Ct /= 2
            assert(Ct <= W[2])

            if_replication = int(math.floor(float(n_ckks)/(Mt*Ct*RS)))
            
            mult_loop = 0
            psum_loop = 0
            if_loop = 0
            # if console_print:
                # print("P  :{:4d}\tM     :{:4d}\tMt    :{:4d}\tCt:{:4d}\t\tIF-PE:{:}".format(P, M, Mt, Ct, (Mt*RS*Ct)/float(n_ckks)))
                # print("Kt:{:4d}\tIFR   :{:4d}\tRS*Kt:{:4d}\tIR :{:4d}\t\tWT-PE:{:}".format(Kt, if_replication, W[1]*W[0]*Kt, if_replication, (Kt*Ct*W[0]*W[1])/float(n_ckks)))
                # print "IF:",(Mt*RS*Ct*if_replication)/float(n_ckks), "::", "WT:",(Kt*Ct*W[0]*W[1])/float(n_ckks)

            print param, S, '\t', P*W[3]

            total_output_neurons += P*W[3]
            assert(Mt*RS*Ct*if_replication <= n_ckks)
            assert(Kt*Ct*W[0]*W[1] <= n_ckks)
            assert(Kt*Ct*Mt*if_replication != 0)

print total_output_neurons