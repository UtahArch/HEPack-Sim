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
        # self.pe_array.pip_stats.print_pip_stats()

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

    def setup_cheetah_f1_hyena(self):
        # Pipeline:
        # MUL - IF*WT
        # NI1   | 
        # PR1   - F1 NTT
        # NI2   | 
        # PR2     - Permute PSUM in Coeff Domain
        # NT1   |
        # PR3   - F1 I-NTT
        # NT2   |
        # KSH - PSUM += Partial PSUM*KSH
        self.mult_pipe = [
            ("MUL",self.pe_array.op_mul_if_wt_cycles()),

            ("NI1",self.pe_array.op_ntt_f1_cycles("psum")),
            ("PR1",self.pe_array.op_permute_cycles("psum")),
            ("NI1",self.pe_array.op_ntt_f1_cycles("psum")),

            ("PR2",self.pe_array.op_permute_cycles("psum")),

            ("NT1",self.pe_array.op_ntt_f1_cycles("psum")),
            ("PR3",self.pe_array.op_permute_cycles("psum")),
            ("NT1",self.pe_array.op_ntt_f1_cycles("psum")),
            
            ("KSH",self.pe_array.op_ksh_psum_cycles())
        ]

        defs.cycle_time = max([x[1] for x in self.mult_pipe])
    
    ## Run Cheetah for all wts along the channel step that are packed
    def run_cheetah_f1_f1(self, runs):
    
        # Processing all wts and ifs from memory to L1
        # An IF is brought for processing and run wts are brouht
        self.memory.stats_accesses  += runs * self.pe_array.wt_file.size
        self.pe_array.wt_file.stats_accesses += runs * self.pe_array.wt_file.size
        # self.pe_array.pip_stats.wt_file.stats_accesses += runs * self.pe_array.wt_file.size
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
            self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size * runs 
        else:
            self.memory.stats_accesses += self.pe_array.ksh_file.size * runs
    
    ## Run Cheetah for all wts along the channel step that are packed
    def run_cheetah_f1_hyena(self, runs):
    
        # Processing all wts and ifs from memory to L1
        # An IF is brought for processing and run wts are brouht
        self.memory.stats_accesses  += runs * self.pe_array.wt_file.size
        self.pe_array.wt_file.stats_accesses += runs * self.pe_array.wt_file.size
        # self.pe_array.pip_stats.wt_file.stats_accesses += runs * self.pe_array.wt_file.size
        # self.pe_array.if_file.stats_accesses += self.pe_array.if_file.size

        self.mult_pipe_counts += runs
        self.cycles += runs

        self.pe_array.op_mul_if_wt(runs)

        self.pe_array.op_ntt_f1("psum",runs)
        self.pe_array.op_permute("psum",runs)
        self.pe_array.op_ntt_f1("psum",runs)

        self.pe_array.op_permute("psum",runs)

        self.pe_array.op_ntt_f1("psum",runs)
        self.pe_array.op_permute("psum",runs)
        self.pe_array.op_ntt_f1("psum",runs)

        self.pe_array.op_ksh_psum(runs)

        # Access the ksh for the next rotation
        if defs.num_chiplets == 1:
            self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size * runs 
        else:
            self.memory.stats_accesses += self.pe_array.ksh_file.size * runs

    
    # EPIC
    ## Calc Stages for Epic
    def setup_epic_f1_f1(self):
        # Pipeline:
        # SW1   -     
        # TW1   | Permute Wts  
        # SW2   | in eval domain
        # TW2   -
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
            ("SW1",self.pe_array.op_shift_cycles("wt")),
            ("TW1",self.pe_array.op_transpose_cycles("wt")),
            ("SW2",self.pe_array.op_shift_cycles("wt")),
            ("TW2",self.pe_array.op_transpose_cycles("wt")),

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
    
    ## Run EPIC for all wts and ifs that are packed
    def run_epic_f1_f1(self, runs):
        
        self.mult_pipe_counts += runs
        self.cycles += runs

        self.pe_array.op_shift("wt",runs)
        self.pe_array.op_transpose("wt",runs)
        self.pe_array.op_shift("wt",runs)
        self.pe_array.op_transpose("wt",runs)

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
    
    ## Calc Stages for Epic
    def setup_epic_f1_hyena(self):
        # Pipeline:
        # PW1   - Permute Wt in Eval Domain
        # MUL - IF*WT
        # NI1   | 
        # PR1   - F1 NTT
        # NI2   | 
        # PP1   - Permute PSum in Coeff Domain
        # NT1   |
        # PR2   - F1 I-NTT
        # NT2   |
        # KSH - PSUM += Partial PSUM*KSH
        self.mult_pipe = [
            ("PW1",self.pe_array.op_permute_cycles("wt")),

            ("MUL",self.pe_array.op_mul_if_wt_cycles()),

            ("NI1",self.pe_array.op_ntt_f1_cycles("psum")),
            ("TR1",self.pe_array.op_permute_cycles("psum")),
            ("NI1",self.pe_array.op_ntt_f1_cycles("psum")),

            ("PP1",self.pe_array.op_permute_cycles("psum")),

            ("NT1",self.pe_array.op_ntt_f1_cycles("psum")),
            ("TR2",self.pe_array.op_permute_cycles("psum")),
            ("NT1",self.pe_array.op_ntt_f1_cycles("psum")),
            
            ("KSH",self.pe_array.op_ksh_psum_cycles())
        ]
        
        defs.cycle_time = max([x[1] for x in self.mult_pipe])
    
    ## Run EPIC for all wts and ifs that are packed
    def run_epic_f1_hyena(self, runs):
        
        self.mult_pipe_counts += runs
        self.cycles += runs

        self.pe_array.op_mul_if_wt(runs)

        self.pe_array.op_permute("wt",runs)
        
        self.pe_array.op_ntt_f1("psum",runs)
        self.pe_array.op_permute("psum",runs)
        self.pe_array.op_ntt_f1("psum",runs)

        self.pe_array.op_permute("psum",runs)

        self.pe_array.op_ntt_f1("psum",runs)
        self.pe_array.op_permute("psum",runs)
        self.pe_array.op_ntt_f1("psum",runs)

        self.pe_array.op_ksh_psum(runs)

        # Access the ksh for the next rotation
        if defs.num_chiplets == 1:
            self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size
        else:
            self.memory.stats_accesses += self.pe_array.ksh_file.size
    

    # Hyena

    ## Setup 
    def setup_hyena_f1_f1(self, rsct, C, K):
        # Mult Pipeline:
        # SW1   -     
        # TW1   | Permute Wts  
        # SW2   | in Eval domain
        # TW2   -
        # MUL - IF*WT
        self.mult_pipe = [
            ("SW1",self.pe_array.op_shift_cycles("wt")),
            ("TW1",self.pe_array.op_transpose_cycles("wt")),
            ("SW2",self.pe_array.op_shift_cycles("wt")),
            ("TW2",self.pe_array.op_transpose_cycles("wt")),

            ("MUL",self.pe_array.op_mul_if_wt_cycles())
        ]

        # Psum Pipeline
        # SP1   -     
        # TP1   | Permute PSums
        # SP2   | in Eval domain
        # TP2   -
        # KSH - IF*WT
        self.psum_pipe = [
            ("SP1",self.pe_array.op_shift_cycles("psum")),
            ("TP1",self.pe_array.op_transpose_cycles("psum")),
            ("SP2",self.pe_array.op_shift_cycles("psum")),
            ("TP2",self.pe_array.op_transpose_cycles("psum")),

            ("KSH",self.pe_array.op_ksh_psum_cycles())
        ]
        
        # IF Permutation is a separate sequence
        # NI1   | 
        # TR1   - F1 NTT
        # NI2   | 
        # SH1     -     
        # TI1     | Permute IF  
        # SH2     | in coeff domain
        # TI2     -
        # NT1   |
        # TR2   - F1 I-NTT
        # NT2   |
        # KSI - KSH*IF
        self.if_seq = [
            ("NI1",self.pe_array.op_ntt_f1_cycles("if")),
            ("TR1",self.pe_array.op_transpose_cycles("if")),
            ("NI1",self.pe_array.op_ntt_f1_cycles("if")),

            ("SH1",self.pe_array.op_shift_cycles("if")),
            ("TI1",self.pe_array.op_transpose_cycles("if")),
            ("SH2",self.pe_array.op_shift_cycles("if")),
            ("TI2",self.pe_array.op_transpose_cycles("if")),

            ("NT1",self.pe_array.op_ntt_f1_cycles("if")),
            ("TR2",self.pe_array.op_transpose_cycles("if")),
            ("NT1",self.pe_array.op_ntt_f1_cycles("if")),

            ("KSI",self.pe_array.op_ksh_if_cycles()),
        ]

        defs.cycle_time = max([x[1] for x in self.mult_pipe])

    # Run Hyena for all wts and ifs that are packed
    def run_hyena_mult_pipe_f1_f1(self, runs):

        self.mult_pipe_counts += runs
        self.cycles += runs

        self.pe_array.op_shift("wt",runs)
        self.pe_array.op_transpose("wt",runs)
        self.pe_array.op_shift("wt",runs)
        self.pe_array.op_transpose("wt",runs)

        self.pe_array.op_mul_if_wt(runs)

        # Access the ksh for the next rotation
        if defs.num_chiplets == 1:
            self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size * runs
        else:
            self.memory.stats_accesses += self.pe_array.ksh_file.size * runs
        
        # TODO: This and FC Handling!
        # for k in range(defs.k_t):
        #     self.pe_array.op_wt_rotate()
        #     self.pe_array.op_mul_if_wt()
        #

    # Collate all psums present in it
    def run_hyena_psum_pipe_f1_f1(self, runs):

        self.psum_pipe_counts += runs
        self.cycles += runs

        self.pe_array.op_shift("psum",runs)
        self.pe_array.op_transpose("psum",runs)
        self.pe_array.op_shift("psum",runs)
        self.pe_array.op_transpose("psum",runs)

        self.pe_array.op_ksh_psum(runs)
    
    # Permute the IF
    def run_hyena_if_seq_f1_f1(self, runs):
        
        # TODO: Add Stall Calculation
        self.if_seq_counts += runs

        self.pe_array.op_ntt_f1("if",runs)
        self.pe_array.op_transpose("if",runs)
        self.pe_array.op_ntt_f1("if",runs)

        self.pe_array.op_shift("if",runs)
        self.pe_array.op_transpose("if",runs)
        self.pe_array.op_shift("if",runs)
        self.pe_array.op_transpose("if",runs)

        self.pe_array.op_ntt_f1("if",runs)
        self.pe_array.op_transpose("if",runs)
        self.pe_array.op_ntt_f1("if",runs)

        self.pe_array.op_ksh_if(runs)
    
    ## Setup 
    def setup_hyena_f1_hyena(self, rsct, C, K):
        # Mult Pipeline:
        # PRW - Permute Wt in Eval Domain
        # MUL - IF*WT
        self.mult_pipe = [
            ("PRW",self.pe_array.op_permute_cycles("wt")),

            ("MUL",self.pe_array.op_mul_if_wt_cycles())
        ]

        # Psum Pipeline
        # PRP - Permute PSum in Eval Domain
        # KSH - IF*WT
        self.psum_pipe = [
            ("PRP",self.pe_array.op_permute_cycles("psum")),

            ("KSH",self.pe_array.op_ksh_psum_cycles())
        ]
        
        # IF Permutation is a separate sequence
        # NI1   | 
        # TR1   - F1 NTT
        # NI2   | 
        # PRI - Permute IF in Coeff Domain
        # NT1   |
        # TR2   - F1 I-NTT
        # NT2   |
        # KSI - KSH*IF
        self.if_seq = [
            ("NI1",self.pe_array.op_ntt_f1_cycles("if")),
            ("TR1",self.pe_array.op_transpose_cycles("if")),
            ("NI1",self.pe_array.op_ntt_f1_cycles("if")),

            ("PRI",self.pe_array.op_permute_cycles("if")),

            ("NT1",self.pe_array.op_ntt_f1_cycles("if")),
            ("TR2",self.pe_array.op_transpose_cycles("if")),
            ("NT1",self.pe_array.op_ntt_f1_cycles("if")),

            ("KSI",self.pe_array.op_ksh_if_cycles()),
        ]

        defs.cycle_time = max([x[1] for x in self.mult_pipe])

    # Run Hyena for all wts and ifs that are packed
    def run_hyena_mult_pipe_f1_hyena(self, runs):

        self.mult_pipe_counts += runs
        self.cycles += runs

        self.pe_array.op_permute("wt",runs)

        self.pe_array.op_mul_if_wt(runs)

        # Access the ksh for the next rotation
        if defs.num_chiplets == 1:
            self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size * runs
        else:
            self.memory.stats_accesses += self.pe_array.ksh_file.size * runs

    # Collate all psums present in it
    def run_hyena_psum_pipe_f1_hyena(self, runs):

        self.psum_pipe_counts += runs
        self.cycles += runs

        self.pe_array.op_permute("psum",runs)

        self.pe_array.op_ksh_psum(runs)
    
    # Permute the IF
    def run_hyena_if_seq_f1_hyena(self, runs):
        
        # TODO: Add Stall Calculation
        self.if_seq_counts += runs

        self.pe_array.op_ntt_f1("if",runs)
        self.pe_array.op_transpose("if",runs)
        self.pe_array.op_ntt_f1("if",runs)

        self.pe_array.op_permute("if",runs)

        self.pe_array.op_ntt_f1("if",runs)
        self.pe_array.op_transpose("if",runs)
        self.pe_array.op_ntt_f1("if",runs)

        self.pe_array.op_ksh_if(runs)