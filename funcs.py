#################################################################################
##  All definitions for the different functions required to perform FHE
##  done associated with the PE basic
##  
##  
##  
#################################################################################

import elements
import defs
import math

# Main Class
class PE(elements.PE_Basic):

    def __init__(self):
        elements.PE_Basic.__init__(self)

        self.ntt_stats = elements.NTT_Stats()
        self.mul_stats = elements.MUL_Stats()
        self.ksh_stats = elements.KSH_Stats()
        self.rot_stats = elements.ROT_Stats()

    ### Functions performed in a PE

    # Multiply IF with Wts (1 tick)
    # 
    #   PE Exec                     Order
    # 
    # 1. R IF                       1 2
    # 2. R WT                       3     
    # 3. MUL PT1 IF WT                   
    # 
    def op_mul_if_wt_cycles(self):
        CYCLE_COUNT = 0
        # Calculate Time Taken based on the order in the comments
        CYCLE_COUNT += max(self.if_file.read_time, self.wt_file.read_time)
        CYCLE_COUNT += self.muls.exec_time
    
        return CYCLE_COUNT

    def op_mul_if_wt(self, iters):
        self.update_mul_if_wt(iters)
        self.mul_stats.update_mul_if_wt(iters)

    # Multiply PSUM with KSH to work for rotation
    # 
    #   PE Exec                     Order
    # 
    # 1. R PSUM                     1 2 
    # 2. R KSH                      3 4  
    # 3. MUL PT2 PSUM KSH         5 -> Hidden because of pipelining                                   
    # 4. ADD PNew PSumi PTemp -> from MUL              
    # 5. ST PSumi PNew                          
    #        
    def op_ksh_psum_cycles(self):
        CYCLE_COUNT = 0
        # Calculate Time Taken based on the order in the comments
        CYCLE_COUNT += max(self.buff_file.read_time, self.ksh_file.read_time)
        CYCLE_COUNT += self.muls.exec_time + self.adds.exec_time

        return CYCLE_COUNT

    def op_ksh_psum(self, iters):
        self.update_ksh_psum(iters)
        self.ksh_stats.update_ksh_psum(iters)
    
    # For performing permutation on IF KSH is going to be required
    #
    #   PE Exec                     Order
    # 
    # 1. R IF                       1 2 
    # 2. R KSH                      3   
    # 3. MUL IFT IF KSH             4           
    # 4. ST IF IFT                  
    #        
    def op_ksh_if_cycles(self):
        CYCLE_COUNT = 0
        # Calculate Time Taken based on the order in the comments
        CYCLE_COUNT += max(self.buff_file.read_time, self.ksh_file.read_time)
        CYCLE_COUNT += self.muls.exec_time

        return CYCLE_COUNT

    def op_ksh_if(self, iters):            
        self.update_ksh_if(iters)
        self.ksh_stats.update_ksh_if(iters)


    ### Data Movement Operations in a PE

    ## F1 Arch
    # Permutation/Automorphism in F1 Arch is done by
    # Shift (Corssbar) => Transpose => Shift (Crossbar) => Transpose
    # F1 NTT uses the same Transpose Unit but does not require Shifts
    def op_transpose_cycles(self, mode):
        return defs.transpose_f1
    
    def op_transpose(self, mode, iters):
        self.update_transpose(mode, iters)
        self.rot_stats.update_transpose(mode, iters)

    def op_shift_cycles(self, mode):
        return defs.shift_f1
    
    def op_shift(self, mode, iters):
        self.update_shift(mode, iters)
        self.rot_stats.update_shift(mode, iters)

    ## Hyena Arch
    # Permutation/Automorphism in F1 Arch is done by
    # a Benes Network
    def op_permute_cycles(self, mode):
        return defs.permute_hyena
    
    def op_permute(self, mode, iters):
        self.update_permute(mode, iters)
        self.rot_stats.update_permute(mode, iters)


    ### NTT Operations in a PE

    # Run NTT on the file passed through
    #   repeat log(n) times 
    #       read 2 values from reg and 1 from twiddle <== this will change based on which step we are at
    #       multiply twiddle with 1 reg valye
    #       add/sub to other value
    #
    #
    def op_ntt_baseline_cycles(self, mode, num_vals):
        temp_cycles = 0

        if mode == 'psum':
            reg_file = self.psum_file
        elif mode == 'wt':
            reg_file = self.wt_file
        elif mode == 'if':
            reg_file = self.if_file
        else:
            print "Error op_ntt_baseline 1"
            exit()

        while num_vals > 1:
            num_vals /= 2
            temp_cycles += max(self.twiddle.read_time, reg_file.read_time) + self.muls.exec_time + self.adds.exec_time  
        
        return temp_cycles

    def op_ntt_baseline(self, mode, num_vals, iters):
        temp_steps = 0

        while num_vals > 1:
            num_vals /= 2
            temp_steps += 1

        self.update_ntt_baseline(mode, temp_steps, iters)
        self.ntt_stats.update_ntt_baseline(mode, temp_steps, iters)

    ## F1 NTT
    # Run NTT on the file passed through
    # Check transpose and 2 time calling
    # Root of n NTTs on Root of n values + Transpose + Root of n NTTs on Root of n values
    # The n NTTs happen parallely while the Transpose is handled by Transpose Unit
    
    # This function models ntt on root n values
    def op_ntt_f1_cycles(self, mode):
        return self.op_ntt_baseline_cycles(mode, int(math.sqrt(defs.poly_n)))
    
    def op_ntt_f1(self, mode,iters):
        self.op_ntt_baseline(mode, int(math.sqrt(defs.poly_n)), iters)