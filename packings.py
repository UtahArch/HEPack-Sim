#################################################################################
##  All definitions for the different packings required to perform FHE
##  
##  Has definition of a chiplet
##  
##  
#################################################################################

import elements
import defs
import funcs
import math
import sys

# Main Class
class Chiplet(elements.PE_Basic):

    def __init__(self):
        self.pe_array = funcs.PE()

        self.if_l2_cache = elements.Cache("IF L2 Cache", defs.if_l2_size, defs.if_l2_read, defs.if_l2_write)
        self.wt_l2_cache = elements.Cache("WT L2 Cache", defs.wt_l2_size, defs.wt_l2_read, defs.wt_l2_write)
        self.ksh_l2_cache = elements.Cache("KSH L2 Cache", defs.ksh_l2_size, defs.ksh_l2_read, defs.ksh_l2_write)
        self.memory = elements.Cache("Memory  ", -1, -1, -1)

        self.mult_pipe_counts = 0
        self.psum_pipe_counts = 0
        self.if_seq_counts = 0
        self.cycles = 0
        self.stalls = 0 
        self.ntt_choice = None
        self.mult_pipe  = None
        self.psum_pipe  = None
        self.if_seq     = None
        self.mult_pipe_cost  = None
        self.psum_pipe_cost  = None
        self.if_seq_cost     = None
        self.pipe_choice = None

        
    def print_stats_console(self, IF, W, S):
        print IF[0], IF[1], IF[2]
        print W[0], W[1], W[2], W[3]
        print S[0], S[1]
        if defs.packing != 'ngraph':
            for x in self.mult_pipe:
                print x[0], x[1], "::",
            print
        if self.psum_pipe != None:
            for x in self.psum_pipe:
                print x[0], x[1], "::",
            print
            for x in self.if_seq:
                print x[0], x[1], "::",
            print
            print self.mult_pipe_cost, self.psum_pipe_cost, self.if_seq_cost, "\t", self.pipe_choice
            print self.mult_pipe_counts, self.psum_pipe_counts, self.if_seq_counts

        print defs.k_t, defs.c_t, defs.packing, defs.ntt_type, defs.arch, defs.batch_size, defs.poly_n, defs.num_chiplets, defs.cycle_time
        print("=== Stats ===")
        print("Total Cycles Taken :\t{}".format(self.cycles))
        print("Total MULT Pipe    :\t{}".format(self.mult_pipe_counts))
        print("Total PSUM Pipe    :\t{}".format(self.psum_pipe_counts))
        print("Total IF Seq       :\t{}".format(self.if_seq_counts))
        print("Total Stalls       :\t{}".format(self.stalls))
        print("Total Time Taken   :\t{}".format(self.cycles * defs.cycle_time + self.stalls))
        # print("Total PE Hops      :\t{}".format(self.pe_array.phops))
        # print("Total Chiplet Hops :\t{}".format(self.pe_array.chops))
        # print("Total PHOP Time    :\t{}".format(self.pe_array.phops * defs.phop_time))
        # print("Total CHOP Time    :\t{}".format(self.pe_array.chops * defs.chop_time))
        # print("Total Shifts       :\t{}".format(self.pe_array.shift))
        # print("Total Permutations :\t{}".format(self.pe_array.permt))
        print("=== Chiplet Stats ===")
        # self.pe_array.print_pe_stats()
        self.wt_l2_cache.print_stats()
        self.if_l2_cache.print_stats()
        self.ksh_l2_cache.print_stats()
        self.memory.print_stats()
        self.pe_array.pip_stats.print_pip_stats()

        self.pe_array.mul_stats.print_mul_stats()
        self.pe_array.ntt_stats.print_ntt_stats()
        self.pe_array.ksh_stats.print_ksh_stats()
        self.pe_array.rot_stats.print_rot_stats()

    def print_stats_file(self, IF, W, S, name, network):
        output_path = "data_{}/{}_{}_{}_{}/{}_{}_{}_{}_{}_{}_{}.data".format(network, defs.packing, defs.ntt_type, defs.arch, defs.poly_n, name, IF[0], IF[1], W[0], W[1], W[2], W[3])
        print output_path

        stout_save = sys.stdout
        sys.stdout = open(output_path, 'w')
        self.print_stats_console(IF, W, S)
        sys.stdout.close()
        sys.stdout = stout_save
    

    # Cheetah

    ## Calc Stages for cheetah
    def setup_cheetah_f1_f1(self):
        # Pipeline:
        # MUL - IF*WT
        # NI1   | 
        # TR1   - F1 NTT
        # NI2   | 
        # SH1     -     
        # TP1     | Permute PSUM  
        # SH2     | in coeff domain
        # TP2     -
        # NT1   |
        # TR2   - F1 I-NTT
        # NT2   |
        # KSH - PSUM += Partial PSUM*KSH
        self.mult_pipe = [
            ("MUL",self.pe_array.op_mul_if_wt_cycles()),

            ("NI1",self.pe_array.op_ntt_f1_cycles("psum")),
            ("TR1",self.pe_array.op_transpose_cycles("psum")),
            ("NI1",self.pe_array.op_ntt_f1_cycles("psum")),

            ("SH1",self.pe_array.op_shift_cycles("psum")),
            ("TP1",self.pe_array.op_transpose_cycles("psum")),
            ("SH2",self.pe_array.op_shift_cycles("psum")),
            ("TP2",self.pe_array.op_transpose_cycles("psum")),

            ("NT1",self.pe_array.op_ntt_f1_cycles("psum")),
            ("TR2",self.pe_array.op_transpose_cycles("psum")),
            ("NT1",self.pe_array.op_ntt_f1_cycles("psum")),
            
            ("KSH",self.pe_array.op_ksh_psum_cycles())
        ]

        defs.cycle_time = max([x[1] for x in self.mult_pipe])
        
        # print self.stages
        # print defs.cycle_time
    
    ## Run Cheetah for all wts along the channel step that are packed
    def run_cheetah(self, runs):
    
        # Processing all wts and ifs from memory to L1
        # An IF is brought for processing and run wts are brouht
        self.memory.stats_accesses  += runs * self.pe_array.wt_file.size
        self.pe_array.wt_file.stats_accesses += runs * self.pe_array.wt_file.size
        self.pe_array.pip_stats.wt_file.stats_accesses += runs * self.pe_array.wt_file.size
        # self.pe_array.if_file.stats_accesses += self.pe_array.if_file.size

        self.mult_pipe_counts += runs
        self.cycles += runs

        self.pe_array.op_mul_if_wt(runs)

        self.pe_array.op_ntt_f1("psum",runs)
        self.pe_array.op_transpose("psum",runs)
        self.pe_array.op_ntt_f1("psum",runs)

        self.pe_array.op_shift("psum",runs)
        self.pe_array.op_transpose("psum",runs)
        self.pe_array.op_shift("psum",runs)
        self.pe_array.op_transpose("psum",runs)

        self.pe_array.op_ntt_f1("psum",runs)
        self.pe_array.op_transpose("psum",runs)
        self.pe_array.op_ntt_f1("psum",runs)

        self.pe_array.op_ksh_psum(runs)

        # Access the ksh for the next rotation
        if defs.num_chiplets == 1:
            self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size
        else:
            self.memory.stats_accesses += self.pe_array.ksh_file.size