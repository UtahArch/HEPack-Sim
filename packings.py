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
        self.cycles = 0
        self.ntt_choice = None
        self.stages = None
        self.seq    = None
        self.seq2   = None
        self.seq_cost  = None
        self.seq2_cost = None
        self.seq_stall = None    # 0 - no stalls ; > 0 - seq_stall number of stalls
        self.seq2stall = None    # 0 - no stalls ; > 0 - seq_stall number of stalls

        
    def print_stats_console(self, IF, W):
        print IF[0], IF[1], IF[2]
        print W[0], W[1], W[2], W[3]
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
            print self.seq_cost, self.seq2_cost, self.seq_stall, self.seq2stall

        print defs.k_t, defs.c_t, defs.packing, defs.ntt_type, defs.batch_size, defs.poly_n, defs.num_chiplets, defs.rotation, defs.cycle_time
        print("=== Stats ===")
        print("Total Cycles Taken :\t{}".format(self.cycles))
        print("Total Steps        :\t{}".format(self.pipeline_counts))
        print("Total Time Taken   :\t{}".format(self.cycles * defs.cycle_time))
        # print("Total PE Hops      :\t{}".format(self.pe_array.phops))
        # print("Total Chiplet Hops :\t{}".format(self.pe_array.chops))
        # print("Total PHOP Time    :\t{}".format(self.pe_array.phops * defs.phop_time))
        # print("Total CHOP Time    :\t{}".format(self.pe_array.chops * defs.chop_time))
        # print("Total Shifts       :\t{}".format(self.pe_array.shift))
        # print("Total Permutations :\t{}".format(self.pe_array.permt))
        print("=== Chiplet Stats ===")
        # self.pe_array.print_pe_stats()
        self.if_l2_cache.print_stats()
        self.ksh_l2_cache.print_stats()
        self.memory.print_stats()
        self.pe_array.pip_stats.print_pip_stats()

        self.pe_array.mul_stats.print_mul_stats()
        self.pe_array.ntt_stats.print_ntt_stats()
        self.pe_array.ksh_stats.print_ksh_stats()
        self.pe_array.rot_stats.print_rot_stats()

    def print_stats_file(self, IF, W, name):
        output_path = "data/{}_{}_{}/{}_{}_{}_{}_{}_{}_{}.data".format(defs.packing, defs.ntt_type, defs.arch, name, IF[0], IF[1], W[0], W[1], W[2], W[3])
        print output_path

        stout_save = sys.stdout
        sys.stdout = open(output_path, 'w')
        self.print_stats_console(IF, W)
        sys.stdout.close()
        sys.stdout = stout_save
    

    # Cheetah

    ## Calc Stages for cheetah
    def setup_cheetah(self):
        # Pipeline:
        # MUL
        # NT1
        # TR1   ==> Permute withing NTT Unit registers -> Transpose -> Permute in registers
        # NT2
        # ROT (PSUM)
        # NI1
        # TR2
        # NI2
        # KSH
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
            
            # TODO: What is the L2 cache size required for this?
            self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size

    def calc_time_cheetah(self):
        self.cycles = self.pipeline_counts + len(self.stages)

    
    # EPIC
    ## Calc Stages for Epic
    def setup_epic(self):
        # Pipeline:
        # I1W
        # T1W
        # I2W
        # ROW
        # MUL
        # N1P
        # T1P
        # N2P
        # ROP
        # I1P
        # T2P
        # I2P
        # KSH
        self.stages = [
            ("I1W",self.pe_array.op_ntt_f1_cycles("wt")),
            ("T1W",self.pe_array.op_wt_rotate_cycles()),
            ("I2W",self.pe_array.op_ntt_f1_cycles("wt")),
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

            self.pe_array.op_ntt_f1("wt")
            self.pe_array.op_wt_rotate()
            self.pe_array.op_ntt_f1("wt")
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
            # TODO: What is the L2 cache size required for this?
            self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size

    def calc_time_epic(self):
        self.cycles = self.pipeline_counts + len(self.stages)

     
    # Hyena

    ## Setup 
    def setup_hyena(self, rsct, C, K):
        
        # Check if shifting RSC_t times for NTT is better than using F1 NTT (in case defs.ntt_type is opt)
        self.ntt_choice = 'f1'
        f1_cost  = 2*self.pe_array.op_ntt_f1_cycles("wt")+2*self.pe_array.op_wt_rotate_cycles()
        if defs.ntt_type == 'opt':
            opt_cost = self.pe_array.op_ntt_opt_cycles("wt", rsct)

            if f1_cost > opt_cost:
                self.ntt_choice = 'opt'

        if self.ntt_choice != 'opt':
            # Pipeline:
            # I1W
            # T1W
            # I2W
            # ROW   
            # MUL
            self.stages = [
                ("I1W",self.pe_array.op_ntt_f1_cycles("wt")),
                ("T1W",self.pe_array.op_wt_rotate_cycles()),
                ("I2W",self.pe_array.op_ntt_f1_cycles("wt")),
                ("ROW",self.pe_array.op_wt_rotate_cycles()),
                ("MUL",self.pe_array.op_mul_if_wt_cycles()),
            ]
        else:
            # Pipeline:
            # I1W
            # MUL
            self.stages = [
                ("I1W",self.pe_array.op_ntt_opt_cycles("wt")),
                ("MUL",self.pe_array.op_mul_if_wt_cycles()),
            ]

        defs.cycle_time = max([x[1] for x in self.stages])
        
        # Psum Collection is a separate sequence
        if self.ntt_choice != 'opt':
            # NTT -> RSCt Rotations -> NTT -> RSCt Accumulation
            # N1P
            # T1P
            # N2P
            # ROP - RSC_t times to generate all partial sums (will also have accumulate)
            # I1P
            # T2P
            # I2P
            # KSH - RSC_t times (due to NTT Property) TODO: Confirm why this can be done again, Also as we are doing it on 1 value can that be exploited?
            self.seq = [
                ("N1P",self.pe_array.op_ntt_f1_cycles("psum")),
                ("T1P",self.pe_array.op_psum_rotate_cycles()),
                ("N2P",self.pe_array.op_ntt_f1_cycles("psum")),
                ("ROP",self.pe_array.op_psum_rotate_cycles(rsct)),
                ("I1P",self.pe_array.op_ntt_f1_cycles("psum")),
                ("T2P",self.pe_array.op_psum_rotate_cycles()),
                ("I2P",self.pe_array.op_ntt_f1_cycles("psum")),
                # TODO: /defs.num_muls on this value
                ("KSH",self.pe_array.op_ksh_psum_cycles(rsct)),
            ]
            self.seq_cost  = int(math.ceil(sum([x[1] for x in self.seq]) / float(defs.cycle_time)))
        
        else:
            # NTT -> RSCt pipeline of OPNTT-KSH
            self.seq = [
                ("N1P",self.pe_array.op_ntt_f1_cycles("psum"), 1),
                ("T1P",self.pe_array.op_psum_rotate_cycles(), 1),
                ("N2P",self.pe_array.op_ntt_f1_cycles("psum"), 1),
                ("ONT",self.pe_array.op_ntt_opt_cycles("psum"), rsct),
                ("KSH",self.pe_array.op_ksh_psum_cycles(), rsct),
            ]
            
            # 3 cycles for NTT and 2*RSCt cycls for OPNTT-KSH
            self.seq_cost = int(math.ceil(3*self.seq[0][1]/float(defs.cycle_time))) + 2*rsct

        # IF Permutation is a separate sequence
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
        # TODO: Is it going to be a sum or the len?
        self.seq2_cost = len(self.seq2)


        # print self.stages
        # print self.seq
        # print self.seq2

        # Check if psum collection will cause stalls to happen
        if float(C)*defs.k_t/defs.c_t > self.seq_cost:
            self.seq_stall = 0
        else:
            self.seq_stall = int(self.seq_cost - float(C)*defs.k_t/defs.c_t)

        # Check if if permutation will cause stalls to happen
        temp = (float(C)*defs.k_t/defs.c_t + self.seq_stall)*K/defs.k_t
        if self.seq_stall > 0:
            # Schedule on #1
            self.seq2stall = max(0, self.seq2_cost - self.seq_stall)
        else:
            # Schedule on #2
            self.seq2stall = max(0, self.seq2_cost - (float(C)*defs.k_t/defs.c_t - self.seq_cost))


        # if defs.ntt_type == 'opt':
        #     print defs.cycle_time, "\t", self.seq_cost, self.seq2_cost, "\t", self.seq_stall, self.seq2stall, "\t", self.ntt_choice, f1_cost, opt_cost
        # else:
        #     print defs.cycle_time, "\t", self.seq_cost, self.seq2_cost, "\t", self.seq_stall, self.seq2stall, "\t", self.ntt_choice, f1_cost

    # Run Hyena for all wts and ifs that are packed
    def run_hyena_k(self):
        
        for k in range(defs.k_t):
            self.pipeline_counts += 1

            # TODO: Is there an extra access that I have to make? Yes for c1, essentially double wt accesses from memory

            if self.ntt_choice != 'opt':
                self.pe_array.op_ntt_f1("wt")
                self.pe_array.op_wt_rotate()
                self.pe_array.op_ntt_f1("wt")
                self.pe_array.op_wt_rotate()
                self.pe_array.op_mul_if_wt()
            else:
                self.pe_array.op_ntt_opt("wt")
                self.pe_array.op_mul_if_wt()

    # Collate all psums present in it
    # This will be performed on a different set of hardware and so can happen in the background
    # If run_hyena_k finishes before this, then it has to wait until this is complete before we can proceed
    # TODO: This will have some extra copies happening -- heck all stages will have some extra back and forth
    def run_hyena_psum_collect(self, rsct):
        
        if self.ntt_choice != 'opt':
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_psum_rotate()
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_psum_rotate(rsct)
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_psum_rotate()
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_ksh_psum(rsct)    
            # TODO: Confirm why this can be done again, Also as we are doing it on 1 value can that be exploited?
            #       Will there be the same number of accesses or will it be a little less?
            #       How can that be optimised for the next case? Or can it not be done for that?
        else:
            self.pe_array.op_ntt_f1("psum")
            self.pe_array.op_psum_rotate()
            self.pe_array.op_ntt_f1("psum")
            for _ in range(rsct):
                self.pe_array.op_ntt_opt("psum")
                self.pe_array.op_ksh_psum()

        self.cycles += self.seq_stall
        

    # Permute the IF
    def run_hyena_permute_if(self):
        self.pe_array.op_ntt_f1("if")
        self.pe_array.op_if_rotate()
        self.pe_array.op_ntt_f1("if")
        self.pe_array.op_if_rotate()
        self.pe_array.op_ntt_f1("if")
        self.pe_array.op_if_rotate()
        self.pe_array.op_ntt_f1("if")
        self.pe_array.op_ksh_if()

        self.cycles += self.seq2stall

    def calc_time_hyena(self):
        self.cycles += self.pipeline_counts + len(self.stages)