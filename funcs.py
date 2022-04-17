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
        self.pip_stats = elements.PIP_Stats()

    
    
    ## Functions performed in a PE

    # Multiply IF with Wts (1 tick)
    # 
    #   PE Exec                     Order
    # 
    # 1. R IF                       1 2
    # 2. R WT                       3     
    # 3. MUL PTemp IF WT                   
    # 
    def op_mul_if_wt_cycles(self):
        CYCLE_COUNT = 0
        # Calculate Time Taken based on the order in the comments
        CYCLE_COUNT += max(self.if_file.read_time, self.wt_file.read_time)
        CYCLE_COUNT += self.muls.exec_time

        return CYCLE_COUNT

    def op_mul_if_wt(self):
        self.update_mul_if_wt()
        self.mul_stats.update_mul_if_wt()

    
    # Multiply PSUM with KSH to work for rotation
    # 
    #   PE Exec                     Order
    # 
    # 1. R PSUM                     1 2 
    # 2. R KSH                      3 4  
    # 3. MUL PTemp PSUM KSH         5 -> Hidden because of pipelining                                   
    # 4. ADD PNew PSumi PTemp -> from MUL              
    # 5. ST PSumi PNew                          
    #        
    def op_ksh_psum_cycles(self, iters=1):
        CYCLE_COUNT = 0
        # Calculate Time Taken based on the order in the comments
        CYCLE_COUNT += max(self.psum_file.read_time, self.ksh_file.read_time)
        CYCLE_COUNT += self.muls.exec_time + self.adds.exec_time

        return CYCLE_COUNT * iters

    def op_ksh_psum(self, iters=1):
        self.update_ksh_psum(iters)
        self.ksh_stats.update_ksh_psum(iters)

    
    # # Once PSUM is decoded then rotate and accumulate all values
    # # Since this is encryped we require KSH for this
    # # TODO: Confirm this, what happens to the acculuated data at the end
    # # for iter times                Order
    # #       1. R KSH                
    # #       2. Shift PSUM           1 2 3
    # #       3. R PSUM               4 5
    # #       4. MUL KSH PSUM 
    # #       5. Accumulate
    # def op_ksh_psum_acc_cycles(self, iters):
    #     CYCLE_COUNT = 0
    #     # Calculate Time Taken based on the order in the comments
    #     CYCLE_COUNT += max(self.psum_file.read_time, self.ksh_file.read_time)
    #     CYCLE_COUNT += max(self.muls.exec_time, self.adds.exec_time)
    #     # Since there are iter MACs followed by accumulates
    #     CYCLE_COUNT = iters * CYCLE_COUNT

    # def op_ksh_psum_acc(self, iters):
    #     self.update_ksh_psum_acc(iters)
    #     self.ksh_stats.update_ksh_psum_acc(iters)
    
    
    # For performing permutation on IF KSH is going to be required
    #
    #   PE Exec                     Order
    # 
    # 1. R IF                       1 2 
    # 2. R KSH                      3   
    # 3. MUL IFT IF KSH             4           # TODO: Check if there is no accumulate is happening
    # 4. ST IF IFT                  
    #        
    def op_ksh_if_cycles(self):
        CYCLE_COUNT = 0
        # Calculate Time Taken based on the order in the comments
        CYCLE_COUNT += max(self.if_file.read_time, self.ksh_file.read_time)
        CYCLE_COUNT += self.muls.exec_time

        return CYCLE_COUNT

    def op_ksh_if(self):            
        self.update_ksh_if()
        self.ksh_stats.update_ksh_if()

    
    # Rotates for F1 Arch are done by Internal Permute -> Transpose -> Internal Permute
    # Here defs.rotation caputres the time taken by the transpose unit while the internal permutes are considered free
    # Rotates for Hyena Arch use the Benes network and defs.rotation caputers that
    
    # Rotate Psums after muls and send last B and recieve new 1st B
    # This stage is what requires op_mul_psum_ksh to happen
    def op_psum_rotate_cycles(self, iters=1):        
        return defs.rotation * iters

    def op_psum_rotate(self, iters=1):
        self.update_psum_rotate(iters)
        self.rot_stats.update_psum_rotate(iters)

    
    # Rotate Wts after having used them in muls
    # We don't need KSH after this as wts are not encrypted
    # ... will this be shifts or perms ... perms for now
    # TODO: Even for the case of not doing opt_ntt, do we permute or do shifts?
    def op_wt_rotate_cycles(self):        
        return defs.rotation

    def op_wt_rotate(self):
        self.update_wt_rotate()
        self.rot_stats.update_wt_rotate()

    
    # Rotate IFs to produce a new non-overlapping matrix
    # This will always be a permutation
    def op_if_rotate_cycles(self):        
        return defs.rotation

    def op_if_rotate(self):
        self.update_if_rotate()
        self.rot_stats.update_if_rotate()
    

    # # Choose which ntt to do
    # def op_ntt_util_cycles(self, mode):
    #     if defs.ntt_type == "baseline":
    #         return self.op_ntt_baseline_cycles(mode, defs.poly_n)
    #     elif defs.ntt_type == "f1":
    #         return self.op_ntt_f1_cycles(mode)
    #     elif defs.ntt_type == "opt":
    #         return self.op_ntt_opt_cycles(mode)
    #     else:
    #         print "Error op_ntt_util 1", defs.ntt_type
    #         exit()

    # # Choice = -1 : Do whatever is mention in defs.ntt_type (if opt, do it with a stride of 1)
    # # Choice =  0 : Do F1
    # # Choice >  0 : Do opt with a stride of choice
    # def op_ntt_util(self, mode, choice = -1):
    #     if choice == -1:
    #         if defs.ntt_type == "baseline":
    #             self.op_ntt_baseline(mode, defs.poly_n)
    #         elif defs.ntt_type == "f1":
    #             self.op_ntt_f1(mode)
    #         elif defs.ntt_type == "opt":
    #             self.op_ntt_opt(mode, 1)
    #         else:
    #             print "Error op_ntt_util 1", defs.ntt_type
    #             exit()
    #     elif choice == 0:
    #             self.op_ntt_f1(mode)
    #     elif choice > 0:
    #         self.op_ntt_opt(mode, choice)
    #     else:
    #         print "Error op_ntt_util 2", choice
    #         exit()
    

    # Run NTT on the file passed through
    # repeat log(n) times 
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

    def op_ntt_baseline(self, mode, num_vals):
        temp_steps = 0

        while num_vals > 1:
            num_vals /= 2
            temp_steps += 1

        self.update_ntt_baseline(mode, temp_steps)
        self.ntt_stats.update_ntt_baseline(mode, temp_steps)


    # Run NTT on the file passed through
    # Check transpose and 2 time calling
    # Root of n NTTs on Root of n values + Permute + Root of n NTTs on Root of n values
    # The n NTTs happen parallely while the permute is handled by automorphism unit
    
    # This function models ntt on root n values
    def op_ntt_f1_cycles(self, mode):
        return self.op_ntt_baseline_cycles(mode, int(math.sqrt(defs.poly_n)))
    
    def op_ntt_f1(self, mode):
        self.op_ntt_baseline(mode, int(math.sqrt(defs.poly_n)))

    # # Transpose for NTT
    # # This is of the form of permute -> transpose (which is a rotation) -> permute
    # # The permute time can be hidden with the previous and next stages
    # # TODO: Add regs read and write time into permute and rotations
    # def op_ntt_f1_permute_cycles(self, mode):
    #     return defs.rotation # TODO: Confirm and Parametrise this number
    
    # # TODO: Does Rotation actually increase the number of accesses by a lot?
    # # TODO: This will change a lot of rotation accesses, based on arch
    # def op_ntt_f1_permute(self, mode):
    #     self.update_ntt_f1_permute(mode)
    #     # TODO: Is this part of ROT or NTT?
    #     self.ntt_stats.update_ntt_f1_permute(mode)
        

    # Run optimised NTT
    # For 1 shift : f(x) * NTT(x) + c1
    #               reg   twicoef  ????
    # For stride this is going to repeat stride times
    # TODO: What happens to twicoef? Is it c1? Then there will be an extra access to that to store the value right?
    def op_ntt_opt_cycles(self, mode, stride=1):

        if mode == 'psum':
            reg_file = self.psum_file
        elif mode == 'wt':
            reg_file = self.wt_file
        elif mode == 'if':
            reg_file = self.if_file
        else:
            print "Error op_ntt_opt 1"
            exit()
        
        # Read from regfile at the start and write to it in the end, therefore it does not come into the picture
        return (self.muls.exec_time + self.adds.exec_time) * stride + max(reg_file.read_time, self.twicoef.read_time)
    
    def op_ntt_opt(self, mode, stride=1):
        self.update_ntt_opt(mode, stride)
        self.ntt_stats.update_ntt_opt(mode, stride)