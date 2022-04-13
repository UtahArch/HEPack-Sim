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

# Main Class
class Chiplet(elements.PE_Basic):

    def __init__(self):
        self.pe_array = funcs.PE()

        self.if_l2_cache = elements.Cache("IF L2 Cache", defs.if_l2_size, defs.if_l2_read, defs.if_l2_write)
        self.wt_l2_cache = elements.Cache("WT L2 Cache", defs.wt_l2_size, defs.wt_l2_read, defs.wt_l2_write)
        self.ksh_l2_cache = elements.Cache("KSH L2 Cache", defs.ksh_l2_size, defs.ksh_l2_read, defs.ksh_l2_write)
        self.memory = elements.Cache("Memory  ", -1, -1, -1)

        
    def print_stats_console(self, IF, W):
        print IF[0], IF[1], IF[2]
        print W[0], W[1], W[2], W[3]
        print defs.k_t, defs.c_t, defs.packing, defs.ntt_type, defs.batch_size, defs.poly_n, defs.num_chiplets
        print("=== Stats ===")
        print("Total Cycles Taken :\t{}".format(self.pe_array.cycles))
        print("Total PE Hops      :\t{}".format(self.pe_array.phops))
        print("Total Chiplet Hops :\t{}".format(self.pe_array.chops))
        print("Total PHOP Time    :\t{}".format(self.pe_array.phops * defs.phop_time))
        print("Total CHOP Time    :\t{}".format(self.pe_array.chops * defs.chop_time))
        print("Total Shifts       :\t{}".format(self.pe_array.shift))
        print("Total Permutations :\t{}".format(self.pe_array.permt))
        print("=== Chiplet Stats ===")
        self.pe_array.print_pe_stats()
        self.if_l2_cache.print_stats()
        self.ksh_l2_cache.print_stats()
        self.memory.print_stats()

        self.pe_array.mul_stats.print_mul_stats()
        self.pe_array.ntt_stats.print_ntt_stats()
        self.pe_array.ksh_stats.print_ksh_stats()


    # Run Cheetah for all wts along the channel step that are packed
    def run_cheetah(self, runs):
        
        # return
        # Processing all wts and ifs from memory to L1
        # An IF is brought for processing and run wts are brouht
        self.memory.stats_accesses  += runs * self.pe_array.wt_file.size
        self.pe_array.wt_file.stats_accesses += runs * self.pe_array.wt_file.size
        # self.pe_array.if_file.stats_accesses += self.pe_array.if_file.size

        # return
        for i in range(runs):
            # Perform mult
            self.pe_array.op_mul_if_wt_ksh()
            # return

            # Rotate PSUM for next mult
            self.pe_array.op_ntt_util('psum')
            # return
            self.pe_array.op_psum_rotate()
            self.pe_array.op_ntt_util('psum')

            # Access the ksh for the next rotation
            # TODO: What is the L2 cache size required for this?
            self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size

    # Run Cheetah for all wts and ifs that are packed
    def run_epic(self, runs):

        for i in range(runs):
            # Perform mult
            self.pe_array.op_mul_if_wt_ksh()
            # return

            # Rotate PSUM and wts for next mult
            # TODO: Is this okay?
            self.pe_array.op_ntt_util('psum')
            # return
            self.pe_array.op_ntt_util('wt')
            # return
            self.pe_array.op_psum_wt_rotate()
            self.pe_array.op_ntt_util('psum')
            self.pe_array.op_ntt_util('wt')

            # Access the ksh for the next rotation
            # TODO: What is the L2 cache size required for this?
            self.ksh_l2_cache.stats_accesses += self.pe_array.ksh_file.size

    
    # Run Hyena for all wts and ifs that are packed
    def run_hyena_k(self):
        
        for k in range(defs.k_t):
            # Perform mult
            self.pe_array.op_mul_if_wt()

            # Rotate wts with an RSCt stride
            if self.ntt_choice <= 0:
                # print self.pe_array.cycles
                temp = self.pe_array.op_ntt_util('wt', self.ntt_choice)
                # print self.pe_array.cycles, temp
                temp = self.pe_array.op_wt_rotate()
                # print self.pe_array.cycles, temp
                temp = self.pe_array.op_ntt_util('wt', self.ntt_choice)
                # print self.pe_array.cycles, temp
            else:
                self.pe_array.op_ntt_util('wt', self.ntt_choice)

            return

    # Collate all psums present in it
    def run_hyena_psum_collect(self, iters):
        if self.ntt_choice <= 0:
            temp = self.pe_array.op_ntt_util('psum', self.ntt_choice)
            # print self.pe_array.cycles, temp
            self.pe_array.op_ksh_psum(iters)
            # print self.pe_array.cycles, temp
            temp = self.pe_array.op_ntt_util('psum', self.ntt_choice)
        else:
            temp = self.pe_array.op_ntt_util('psum', 0)
            # print self.pe_array.cycles, temp
            self.pe_array.op_ksh_psum(iters)
            # print self.pe_array.cycles, temp
            temp = self.pe_array.op_ntt_util('psum', 0)

    # Permute the IF
    def run_hyena_permute_if(self):
        if self.ntt_choice <= 0:
            temp = self.pe_array.op_ntt_util('if', self.ntt_choice)
            # print self.pe_array.cycles, temp
            self.pe_array.op_ksh_if()
            # print self.pe_array.cycles, temp
            temp = self.pe_array.op_ntt_util('if', self.ntt_choice)
        else:
            temp = self.pe_array.op_ntt_util('if', 0)
            # print self.pe_array.cycles, temp
            self.pe_array.op_ksh_if()
            # print self.pe_array.cycles, temp
            temp = self.pe_array.op_ntt_util('if', 0)