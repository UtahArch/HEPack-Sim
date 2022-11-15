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
        
        self.ksh_file = Cache("KSH File", defs.wt_file_size, defs.ksh_file_read, defs.ksh_file_write)
        # The PSUM File is actually a collection of psum_file_num files but we represent it as 1 file and do the nessacery scaling later
        self.psum_file = Cache("PSUM File", defs.if_file_size, defs.psum_file_read, defs.psum_file_write)

        # Buffer File used for different units
        self.buff_file = Cache("PSUM File", defs.if_file_size, defs.buff_file_read, defs.buff_file_write)

        self.adds = ALUUnit("ADD", defs.mac_num, defs.add_exec_time)
        self.muls = ALUUnit("MUL", defs.mac_num, defs.mul_exec_time)

        # Stats
        self.calls  = 0
        # self.cycles = 0

        # self.phops = 0
        # self.chops = 0

        self.trans = 0
        self.shift = 0
        self.benes = 0

    # Functions to print structure and stats
    def print_structure(self):
        self.if_file.print_structure()
        self.wt_file.print_structure()
        
        self.twiddle.print_structure()
        
        self.ksh_file.print_structure()
        self.psum_file.print_structure()

        self.adds.print_structure()
        self.muls.print_structure()

    def print_pe_stats(self):
        self.if_file.print_stats()
        self.wt_file.print_stats()

        self.twiddle.print_stats()

        self.ksh_file.print_stats()
        self.psum_file.print_stats()
        self.buff_file.print_stats()

        self.adds.print_stats()
        self.muls.print_stats()

    # Functions to update stats corresponding to op_* defined in funcs.py
    
    def update_mul_if_wt(self, iters):
        # Access values from where they are stored
        self.if_file.stats_accesses += self.if_file.size * iters
        self.wt_file.stats_accesses += self.wt_file.size * iters
        # Multiply the values
        self.muls.stats_accesses += self.muls.num * iters

        # Stats
        self.calls  += iters

    # Perform NTT on a specific file
    def update_ntt_baseline(self, mode, steps, iters):
        if mode == 'psum':
            reg_file_size = self.psum_file.size
        elif mode == 'wt':
            reg_file_size = self.wt_file.size
        elif mode == 'if':
            reg_file_size = self.if_file.size
        
        # Write to buffer file before performing NTT
        # Read from it once everything is done
        self.buff_file.stats_accesses += 2*reg_file_size * iters

        # Read values from twiddle
        self.twiddle.stats_accesses += steps * self.twiddle.size * iters                  
        # Each step is going to have a MAC
        self.adds.stats_accesses += steps * self.adds.num * iters
        self.muls.stats_accesses += steps * self.muls.num * iters        
        # Read 2 values from the file and write into 1 location
        self.buff_file.stats_accesses += 3 * steps * reg_file_size * iters
        
        # Stats
        self.calls  += iters
    
    def update_transpose(self, mode, iters):
        if mode == 'psum':
            reg_file_size = self.psum_file.size
        elif mode == 'wt':
            reg_file_size = self.wt_file.size
        elif mode == 'if':
            reg_file_size = self.if_file.size

        self.buff_file.stats_accesses += 2 * reg_file_size * iters
        self.trans += iters

    def update_shift(self, mode, iters):
        if mode == 'psum':
            reg_file_size = self.psum_file.size
        elif mode == 'wt':
            reg_file_size = self.wt_file.size
        elif mode == 'if':
            reg_file_size = self.if_file.size

        self.buff_file.stats_accesses += 2 * reg_file_size * iters
        self.shift += iters

    # Updates for KSHs PSUM involve accumalating the value
    def update_ksh_psum(self, iters):
        # Access values from where they are stored
        self.buff_file.stats_accesses += self.ksh_file.size * iters
        self.ksh_file.stats_accesses += self.ksh_file.size * iters
        # Multiply PSUM X KSH for rotation
        self.muls.stats_accesses += self.muls.num * iters
        self.adds.stats_accesses += self.adds.num * iters
        # Accumulate the values into psum - read then write
        self.psum_file.stats_accesses += 2 * self.psum_file.size * iters

        # Stats
        self.calls  += iters
    
    def update_ksh_if(self, iters):
        # We MAC iters KSH with IF
        self.ksh_file.stats_accesses += self.ksh_file.size * iters
        self.buff_file.stats_accesses += 2*self.if_file.size * iters
        self.muls.stats_accesses += self.muls.num * iters

        # Stats
        self.calls += iters

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
        print("Total Transpose\t:\t{}".format(self.trans))
        print("Total Benes\t:\t{}".format(self.benes))
        self.print_pe_stats()

class PIP_Stats(PE_Basic):
    
    def __init__(self):
        PE_Basic.__init__(self)

    def print_pip_stats(self):
        print("Total Shift\t:\t{}".format(self.shift))
        print("Total Transpose\t:\t{}".format(self.trans))
        print("Total Benes\t:\t{}".format(self.benes))
        self.print_pe_stats()