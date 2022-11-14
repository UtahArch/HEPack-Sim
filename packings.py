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

        self.pipeline_counts = 0
        self.seq_counts = 0
        self.seq2_counts = 0
        self.cycles = 0
        self.stalls = 0 
        self.ntt_choice = None
        self.stages = None
        self.seq    = None
        self.seq2   = None
        self.seq_s  = None
        self.seq2_s = None
        self.stage_cost  = None
        self.seq_cost  = None
        self.seq2_cost = None
        self.pipe_choice = None

        
    def print_stats_console(self, IF, W, S):
        print IF[0], IF[1], IF[2]
        print W[0], W[1], W[2], W[3]
        print S[0], S[1]
        if defs.packing != 'ngraph':
            for x in self.stages:
                print x[0], x[1], "::",
            print
        if self.seq != None:
            for x in self.seq:
                print x[0], x[1], "::",
            print
            for x in self.seq2:
                print x[0], x[1], "::",
            print
            print self.stage_cost, self.seq_cost, self.seq2_cost, "\t", self.seq_s, self.seq2_s, "\t", self.pipe_choice
            print self.pipeline_counts, self.seq_counts, self.seq2_counts

        print defs.k_t, defs.c_t, defs.packing, defs.ntt_type, defs.arch, defs.batch_size, defs.poly_n, defs.num_chiplets, defs.rotation, self.ntt_choice, defs.cycle_time
        print("=== Stats ===")
        print("Total Cycles Taken :\t{}".format(self.cycles))
        print("Total Steps        :\t{}".format(self.pipeline_counts))
        print("Total Time Taken   :\t{}".format(self.cycles * defs.cycle_time))
        print("Total Stalls       :\t{}".format(self.stalls))
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
    def setup_cheetah(self):
        # Pipeline:
        # MUL - IF*WT
        # NT1   | 
        # TR1   - F1 NTT
        # NT2   | 
        # ROT - Permute PSUM in coeff domain
        # NI1   |
        # TR2   - F1 I-NTT
        # NI2   |
        # KSH - PSUM += Partial PSUM*KSH
        self.stages = [
            ("MUL",self.pe_array.op_mul_if_wt_cycles()),
            ("NT1",self.pe_array.op_ntt_f1_cycles("psum")),
            ("TR1",self.pe_array.op_psum_rotate_cycles()),
            ("NT2",self.pe_array.op_ntt_f1_cycles("psum")),
            ("ROT",self.pe_array.op_psum_rotate_cycles()),
            ("NI1",self.pe_array.op_ntt_f1_cycles("psum")),
            ("TR2",self.pe_array.op_psum_rotate_cycles()),
            ("NI2",self.pe_array.op_ntt_f1_cycles("psum")),
            ("KSH",self.pe_array.op_ksh_psum_cycles())
        ]

        defs.cycle_time = max([x[1] for x in self.stages])
        
        # print self.stages
        # print defs.cycle_time

    ## Run Cheetah for all wts along the channel step that are packed
    def run_cheetah(self, runs):
        
        # return
        # Processing all wts and ifs from memory to L1
        # An IF is brought for processing and run wts are brouht
        self.memory.stats_accesses  += runs * self.pe_array.wt_file.size
        self.pe_array.wt_file.stats_accesses += runs * self.pe_array.wt_file.size
        self.pe_array.pip_stats.wt_file.stats_accesses += runs * self.pe_array.wt_file.size
        # self.pe_array.if_file.stats_accesses += self.pe_array.if_file.size

        for i in range(runs):
            self.pipeline_counts += 1

            self.pe_array.op_mul_if_wt()
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_psum_rotate()
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_psum_rotate()
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_psum_rotate()
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_ksh_psum()

            # Access the ksh for the next rotation
            if defs.num_chiplets == 1:
                self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size
            else:
                self.memory.stats_accesses += self.pe_array.ksh_file.size

    def calc_time_cheetah(self):
        self.cycles = self.pipeline_counts

    
    # EPIC
    ## Calc Stages for Epic
    def setup_epic(self):
        # Pipeline:
        # ROW - Permute Wts in eval domain (shift in coeff domain)
        # MUL - IF*WT
        # N1P   | 
        # T1P   - F1 NTT
        # N2P   | 
        # ROP - Permute PSUM in coeff domain
        # I1P   |
        # T2P   - F1 I-NTT
        # I2P   |
        # KSH - PSUM += Partial PSUM*KSH
        self.stages = [
            ("ROW",self.pe_array.op_wt_rotate_cycles()),
            ("MUL",self.pe_array.op_mul_if_wt_cycles()),
            ("N1P",self.pe_array.op_ntt_f1_cycles("psum")),
            ("T1P",self.pe_array.op_psum_rotate_cycles()),
            ("N2P",self.pe_array.op_ntt_f1_cycles("psum")),
            ("ROP",self.pe_array.op_psum_rotate_cycles()),
            ("I1P",self.pe_array.op_ntt_f1_cycles("psum")),
            ("T2P",self.pe_array.op_psum_rotate_cycles()),
            ("I2P",self.pe_array.op_ntt_f1_cycles("psum")),
            ("KSH",self.pe_array.op_ksh_psum_cycles())
        ]
        
        defs.cycle_time = max([x[1] for x in self.stages])
        
        # print self.stages
        # print defs.cycle_time
        
    
    ## Run EPIC for all wts and ifs that are packed
    def run_epic(self, runs):

        for i in range(runs):
            self.pipeline_counts += 1

            self.pe_array.op_wt_rotate()
            self.pe_array.op_mul_if_wt()
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_psum_rotate()
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_psum_rotate()
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_psum_rotate()
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_ksh_psum()

            # Access the ksh for the next rotation
            if defs.num_chiplets == 1:
                self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size
            else:
                self.memory.stats_accesses += self.pe_array.ksh_file.size

    def calc_time_epic(self):
        self.cycles = self.pipeline_counts

     
    # Hyena

    ## Setup 
    def setup_hyena(self, rsct, C, K):
        
        # Pipeline:
        # ROW - Permute Wts in eval domain (shift in coeff domain)   
        # MUL - IF*WT
        self.stages = [
            ("ROW",self.pe_array.op_wt_rotate_cycles()),
            ("MUL",self.pe_array.op_mul_if_wt_cycles()),
        ]
        self.stage_cost = int(math.ceil(float(C)*defs.k_t/defs.c_t)) * max([x[1] for x in self.stages])
        
        # Psum Collection is a separate sequence
        # RSC_t times to generate all partial sums (will also have accumulate) (can be pipelined)
        #   ROP - Permute PSUM in eval domain (shift in coeff domain)   
        #   KSH - KSH*PSUM Partial += PSUM
        self.seq = [
            ("ROP",self.pe_array.op_psum_rotate_cycles()),
            ("KSH",self.pe_array.op_ksh_psum_cycles()),
        ]
        self.seq_cost  = rsct*max([x[1] for x in self.seq])

        # Either the MULT Pipeline of the PSUM Collection is going to be the dominant stage
        defs.cycle_time = max(self.seq_cost, self.stage_cost)
        
        # IF Permutation is a separate sequence
        # N1I   |
        # T1I   - F1 NTT
        # N2I   | 
        # ROI - Permute IF in coeff domain
        # I1I   |
        # T2I   - F1 I-NTT
        # I2I   |
        self.seq2 = [
            ("N1I",self.pe_array.op_ntt_f1_cycles("if")),
            ("T1I",self.pe_array.op_if_rotate_cycles()),
            ("N2I",self.pe_array.op_ntt_f1_cycles("if")),
            ("ROI",self.pe_array.op_if_rotate_cycles()),
            ("I1I",self.pe_array.op_ntt_f1_cycles("if")),
            ("T2I",self.pe_array.op_if_rotate_cycles()),
            ("I2I",self.pe_array.op_ntt_f1_cycles("if")),
            ("KSH",self.pe_array.op_ksh_if_cycles()),
        ]
        self.seq2_cost = sum([x[1] for x in self.seq2])

        print self.stages
        print self.stage_cost, int(math.ceil(float(C)*defs.k_t/defs.c_t)), max([x[1] for x in self.stages])
        print self.seq
        print self.seq_cost, rsct, max([x[1] for x in self.seq])
        print self.seq2
        print self.seq2_cost
        print max(self.seq_cost, self.seq2_cost) - self.seq_cost
        print "\t\t\t\t >> ", self.stage_cost > self.seq_cost, self.stage_cost > self.seq2_cost, self.seq_cost > self.seq2_cost
        print defs.cycle_time
        print

    # Run Hyena for all wts and ifs that are packed
    def run_hyena_k(self):
        
        for k in range(defs.k_t):
            self.pe_array.op_wt_rotate()
            self.pe_array.op_mul_if_wt()


            # Access the ksh for the next rotation
            if defs.num_chiplets == 1:
                self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size
            else:
                self.memory.stats_accesses += self.pe_array.ksh_file.size

            self.pipeline_counts += 1
        

    # Collate all psums present in it
    # This will be performed on a different set of hardware and so can happen in the background
    # If run_hyena_k finishes before this, then it has to wait until this is complete before we can proceed
    # TODO: This will have some extra copies happening -- heck all stages will have some extra back and forth
    def run_hyena_psum_collect(self, rsct):
        for _ in range(rsct):
            self.pe_array.op_psum_rotate()
            self.pe_array.op_ksh_psum()

        self.seq_counts += 1
        self.cycles += 1

    # Permute the IF
    def run_hyena_permute_if(self):
        # Time due to Permute IF not hidden behind PSUM Collection
        self.stalls += max(self.seq_cost, self.seq2_cost) - self.seq_cost
        self.seq2_counts += 1

        self.pe_array.op_ntt_f1("if")
        self.pe_array.op_if_rotate()
        self.pe_array.op_ntt_f1("if")
        self.pe_array.op_if_rotate()
        self.pe_array.op_ntt_f1("if")
        self.pe_array.op_if_rotate()
        self.pe_array.op_ntt_f1("if")
        self.pe_array.op_ksh_if()

    # def calc_time_hyena(self):
    #     if self.pipe_choice == 'mult':
    #         self.cycles += self.pipeline_counts
    #     elif self.pipe_choice == 'psum':
    #         self.cycles += self.pipeline_counts


    # NGraph-HE Packing
    
    ## NGraph is only going to be limited by the number of multiplications it can do
    def setup_ngraph(self):
        defs.cycle_time = self.pe_array.op_mul_if_wt_cycles()
    
    ## Run for all wts
    def run_ngraph(self, runs):
        
        # Get IFs from L2 and Wts from Mem
        self.pe_array.if_file.stats_accesses += runs * self.pe_array.if_file.size
        self.pe_array.pip_stats.if_file.stats_accesses += runs *  self.pe_array.if_file.size
        self.if_l2_cache.stats_accesses += runs * self.pe_array.if_file.size
        # self.memory.stats_accesses += runs * self.pe_array.if_file.size
        
        self.pe_array.wt_file.stats_accesses += runs * self.pe_array.wt_file.size
        self.pe_array.pip_stats.wt_file.stats_accesses += runs * self.pe_array.wt_file.size
        # self.pe_array.wt_l2_cache.stats_accesses += runs * self.pe_array.wt_file.size
        self.memory.stats_accesses += runs * self.pe_array.wt_file.size

        self.pipeline_counts += runs
        self.pe_array.op_mul_if_wt(runs)
    
    def calc_time_ngraph(self):
        self.cycles = self.pipeline_counts