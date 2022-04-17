#################################################################################
##  All definitions for the different structures in the Engine and the basic
##  PE definition with the associated stat collection objects
##  
##  
##  
#################################################################################

import defs


# Class for multipliers and adders
class ALUUnit:
    def __init__(self, name, num, exec_time):
        self.name = name
        self.num = num
        self.exec_time = exec_time
        self.stats_accesses = 0
    
    def print_structure(self):
        print("{}\t\t:\t{}\t{}".format(self.name, self.num, self.exec_time))

    def print_stats(self):
        print("{}\t\t:\t{}".format(self.name, self.stats_accesses))

# Class for Storing Locations
class Cache:
    def __init__(self, name, size, read_time, write_time):
        self.size = size
        self.name = name
        self.read_time = read_time
        self.write_time = write_time
        self.stats_accesses = 0
        self.stats_shifts = 0     # Non zero only for wt file

    def print_structure(self):
        print("{}\t:\t{}\t{}\t{}".format(self.name, self.size, self.read_time, self.write_time))

    def print_stats(self):
        if (self.stats_shifts == 0):
            print("{}\t:\t{}".format(self.name, self.stats_accesses))
        else:
            print("{}\t:\t{}".format(self.name, self.stats_accesses))
            print("{} Shift\t:\t{}".format(self.name, self.stats_shifts))


# Class for PEs
class PE_Basic:
    
    def __init__(self):
        assert(defs.if_file_size == defs.wt_file_size*2)
        assert(defs.if_file_size == defs.mac_num)

        # Define Structures
        self.if_file = Cache("IF File ", defs.if_file_size, defs.if_file_read, defs.if_file_write)
        self.wt_file = Cache("WT File ", defs.wt_file_size, defs.wt_file_read, defs.wt_file_write)
        
        self.twiddle = Cache("Twiddle ", defs.twiddle_size, defs.twiddle_read, defs.twiddle_write)
        if defs.ntt_type == 'opt':
            self.twicoef = Cache("TwiCoef ", defs.twicoef_size, defs.twicoef_read, defs.twicoef_write)
        
        self.ksh_file = Cache("KSH File", defs.wt_file_size, defs.ksh_file_read, defs.ksh_file_write)
        # The PSUM File is actually a collection of psum_file_num files but we represent it as 1 file and do the nessacery scaling later
        self.psum_file = Cache("PSUM File", defs.if_file_size, defs.psum_file_read, defs.psum_file_write)

        self.adds = ALUUnit("ADD", defs.mac_num, defs.add_exec_time)
        self.muls = ALUUnit("MUL", defs.mac_num, defs.mul_exec_time)

        # Stats
        self.calls  = 0
        # self.cycles = 0

        # self.phops = 0
        # self.chops = 0

        self.shift = 0
        self.permt = 0

    # Functions to print structure and stats
    def print_structure(self):
        self.if_file.print_structure()
        self.wt_file.print_structure()
        
        self.twiddle.print_structure()
        if defs.ntt_type == 'opt':
            self.twicoef.print_structure()
        
        self.ksh_file.print_structure()
        self.psum_file.print_structure()

        self.adds.print_structure()
        self.muls.print_structure()

    def print_pe_stats(self):
        self.if_file.print_stats()
        self.wt_file.print_stats()

        self.twiddle.print_stats()
        if defs.ntt_type == 'opt':
            self.twicoef.print_stats()

        self.ksh_file.print_stats()
        self.psum_file.print_stats()

        self.adds.print_stats()
        self.muls.print_stats()

    # Functions to update stats corresponding to op_* defined in funcs.py
    
    def update_mul_if_wt(self):
        # Access values from where they are stored
        self.if_file.stats_accesses += self.if_file.size
        self.wt_file.stats_accesses += self.wt_file.size
        # Multiply the values
        self.muls.stats_accesses += self.muls.num

        # Stats
        self.calls  += 1

    # Perform NTT on a specific file
    # TODO: How is the twiddle used in NTTs? Does it increase the number of mults
    def update_ntt_baseline(self, mode, steps):
        if mode == 'psum':
            reg_file = self.psum_file
        elif mode == 'wt':
            reg_file = self.wt_file
        elif mode == 'if':
            reg_file = self.if_file
        
        # Read values from twiddle
        self.twiddle.stats_accesses += steps * self.twiddle.size                  
        # Each step is going to have a MAC
        self.adds.stats_accesses += steps * self.adds.num
        self.muls.stats_accesses += steps * self.muls.num        
        # Read 2 values from the file and write into 1 location
        reg_file.stats_accesses += 3 * steps * reg_file.size
        
        # Stats
        self.calls  += 1
    
    # def update_ntt_f1_permute(self, mode):
    #     if mode == 'psum':
    #         reg_file = self.psum_file
    #     elif mode == 'wt':
    #         reg_file = self.wt_file
    #     elif mode == 'if':
    #         reg_file = self.if_file

    #     # TODO: Does Rotation actually increase the number of accesses by a lot?
    #     # Permute -> Read -> Transpose
    #     reg_file.stats_accesses += 2 * reg_file.size

    #     # stats
    #     self.permt += 1
        
    def update_ntt_opt(self, mode, stride):
        if mode == 'psum':
            reg_file = self.psum_file
        elif mode == 'wt':
            reg_file = self.wt_file
        elif mode == 'if':
            reg_file = self.if_file
                 
        # Each stride is going to have a MAC
        self.adds.stats_accesses += stride * self.adds.num
        self.muls.stats_accesses += stride * self.muls.num        
        # Read 1 values from the file do computations and finally write into that location
        # Along with Black Magic
        self.twicoef.stats_accesses += stride * reg_file.size
        reg_file.stats_accesses += 2 * reg_file.size  # This will not have stride as we do 1 read and write
        
        # Stats
        self.calls  += 1
        self.shift  += stride

    # Updates for rotates
    # TODO: Will wire energy be captured in permt? 
    # Number of permts == Number of accesses to transpose unit + internal permts (for F1 Arch) and benes network (for Hyena Arch)

    def update_psum_rotate(self, iters):
        self.psum_file.stats_accesses += 2 * iters
        self.permt += iters

    # def update_psum_wt_rotate(self):
    #     self.psum_file.stats_accesses += 2
    #     self.wt_file.stats_accesses += 2
    #     self.permt += 2
    
    def update_wt_rotate(self):
        self.wt_file.stats_accesses += 2
        self.permt += 1
    
    def update_if_rotate(self):
        self.if_file.stats_accesses += 2
        self.permt += 1

    # def update_reg_shift(self, cycles):

    #     if mode == 'psum':
    #         reg_file = self.psum_file
    #     elif mode == 'wt':
    #         reg_file = self.wt_file
    #     elif mode == 'if':
    #         reg_file = self.if_file

    #     reg_file.stats_shifts += 1
    #     reg_file.stats_accesses += 2
        
    #     self.shift += 1
    #     self.cycles += cycles

    # Updates for KSHs
    def update_ksh_psum(self, iters):
        # Access values from where they are stored
        self.ksh_file.stats_accesses += self.ksh_file.size * iters
        # Multiply PSUM X KSH for rotation
        self.muls.stats_accesses += self.muls.num * iters
        self.adds.stats_accesses += self.adds.num * iters
        # Accumulate the values into psum - read then write
        self.psum_file.stats_accesses += 2 * self.psum_file.size * iters

        # Stats
        self.calls  += iters

    # def update_ksh_psum_acc(self, iters):
    #     # TODO: Confirm number of adds here
    #     # We MAC iters KSH with PSUMs and then accumulate iter times
    #     self.ksh_file.stats_accesses += self.ksh_file.size * iters
    #     self.psum_file.stats_shifts += iters
    #     self.psum_file.stats_accesses += self.psum_file.size * iters
    #     self.muls.stats_accesses += self.muls.num * iters
    #     self.adds.stats_accesses += self.adds.num * iters

    #     self.shift += iters
    #     self.calls += 1

    def update_ksh_if(self):
        # We MAC iters KSH with IF
        self.ksh_file.stats_accesses += self.ksh_file.size
        self.if_file.stats_accesses += 2*self.if_file.size
        self.muls.stats_accesses += self.muls.num
        self.adds.stats_accesses += self.adds.num

        # Stats
        self.calls += 1


# Classes for Stats

class NTT_Stats(PE_Basic):
    
    def __init__(self):
        PE_Basic.__init__(self)

    def print_ntt_stats(self):
        print("=== NTT Stats ===")
        print("Calls\t\t:\t{}".format(self.calls))
        self.print_pe_stats()

class MUL_Stats(PE_Basic):
    
    def __init__(self):
        PE_Basic.__init__(self)

    def print_mul_stats(self):
        print("=== MUL Stats ===")
        print("Calls\t\t:\t{}".format(self.calls))
        self.print_pe_stats()

class KSH_Stats(PE_Basic):
    
    def __init__(self):
        PE_Basic.__init__(self)

    def print_ksh_stats(self):
        print("=== KSH Stats ===")
        print("Calls\t\t:\t{}".format(self.calls))
        self.print_pe_stats()

class ROT_Stats(PE_Basic):
    
    def __init__(self):
        PE_Basic.__init__(self)

    def print_rot_stats(self):
        print("=== ROT Stats ===")
        print("Total Shift\t:\t{}".format(self.shift))
        print("Total Perms\t:\t{}".format(self.permt))
        self.print_pe_stats()

class PIP_Stats(PE_Basic):
    
    def __init__(self):
        PE_Basic.__init__(self)

    def print_pip_stats(self):
        print("Total Shift\t:\t{}".format(self.shift))
        print("Total Perms\t:\t{}".format(self.permt))
        self.print_pe_stats()