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

    ## Functions performed in a PE

    # TODO: Math is followed by NTT not anything else, can we really pipeline it?
    # Multiply IF with Wts and do all that stuff
    # 
    #   PE Exec                     Order
    # 
    # 1. R IF                       1 2 4
    # 2. R WT                    -> 3 5     1 2 4
    # 3. MUL PTemp IF WT            6       3 5
    # 4. R PSumi                            6
    # 5. ADD PNew PSumi PTemp               
    # 6. ST PSumi PNew
    # 
    def op_mul_if_wt(self):

        # Calculate Time Taken based on the steady state in the comments
        # This is going to be the max of a read, write and a multiply ++ which is always a multiply
        CYCLE_COUNT = max(self.muls.exec_time, self.psum_file.write_time, self.if_file.read_time, self.wt_file.read_time)

        self.update_mul_if_wt(CYCLE_COUNT)
        self.mul_stats.update_mul_if_wt(CYCLE_COUNT)

        return CYCLE_COUNT

    # Multiple IF with Wts and KSH and do all that stuff
    # 
    #   PE Exec                     Order
    # 
    # 1. R IF                       1 2 4
    # 2. R WT                    -> 3 5 6
    # 3. MUL PTemp IF WT         -> 7
    # 4. R PSumi                    8       1 2 4       -- #1  
    # 5. ADD PNew PSumi PTemp               3 5 6
    # 6. R KSH                              7
    # 7. MUL Pn PNew KSH                    8                   
    # 8. ST PSumi Pn                                            
    # 
    # This will be followed by the rotation of the PSUM         
    # 
    def op_mul_if_wt_ksh(self):
        
        # Calculate Time Taken based on the steady state in the comments
        
        # defs.CYCLE_COUNT += max(self.if_file.read_time, self.wt_file.read_time, self.psum_file[i].read_time, self.psum_file[i].write_time)
        # defs.CYCLE_COUNT += max(self.muls.exec_time, self.adds.exec_time, self.ksh_file.read_time)
        # defs.CYCLE_COUNT += self.muls.exec_time
        # This is the correct thing, but it can be reduced based on domain knowledge
        CYCLE_COUNT = max(2*self.muls.exec_time, self.psum_file.write_time, self.if_file.read_time, self.wt_file.read_time)

        self.update_mul_if_wt_ksh(CYCLE_COUNT)
        self.mul_stats.update_mul_if_wt_ksh(CYCLE_COUNT)

        return CYCLE_COUNT

    # Rotate Psums after muls and send last B and recieve new 1st B
    def op_psum_rotate(self):

        # In worst case the value has to go through 2 hops
        if defs.num_chiplets == 1:
            CYCLE_COUNT = 2 * defs.phop_time
        else:
            CYCLE_COUNT = 2 * defs.chop_time

        self.cycles += CYCLE_COUNT

        self.update_psum_rotate(CYCLE_COUNT)
        self.rot_stats.update_psum_rotate(CYCLE_COUNT)

        return CYCLE_COUNT

    # Rotate Psums and wts after muls and send last B and recieve new 1st B
    def op_psum_wt_rotate(self):

        # In worst case the value has to go through 2 hops
        if defs.num_chiplets == 1:
            CYCLE_COUNT = 2 * defs.phop_time
        else:
            CYCLE_COUNT = 2 * defs.chop_time

        self.update_psum_wt_rotate(CYCLE_COUNT)
        self.rot_stats.update_psum_wt_rotate(CYCLE_COUNT)

        return CYCLE_COUNT

    # Rotate Psums and wts after muls and send last B and recieve new 1st B
    def op_wt_rotate(self):

        # In worst case the value has to go through 2 hops
        if defs.num_chiplets == 1:
            CYCLE_COUNT = 2 * defs.phop_time
        else:
            CYCLE_COUNT = 2 * defs.chop_time

        self.update_wt_rotate(CYCLE_COUNT)
        self.rot_stats.update_wt_rotate(CYCLE_COUNT)

        return CYCLE_COUNT

    # TODO: Check if pipline is correct
    # TODO: Why do we need KSH once NTT has been applied?
    # Decode PSUM then rotate and add
    def op_ksh_psum(self, iters):
        # Since there are iter MACs followed by accumulates
        CYCLE_COUNT = iters * (max(self.muls.exec_time, self.psum_file.write_time, self.psum_file.read_time, self.wt_file.read_time) + self.adds.exec_time)

        self.update_ksh_psum(CYCLE_COUNT, iters)
        self.ksh_stats.update_ksh_psum(CYCLE_COUNT, iters)
    
    # Permute KSH
    def op_ksh_if(self):
        CYCLE_COUNT = max(self.muls.exec_time, self.if_file.write_time, self.if_file.read_time, self.ksh_file.read_time)

        self.update_ksh_if(CYCLE_COUNT)
        self.ksh_stats.update_ksh_if(CYCLE_COUNT)

    
    # Choose which ntt to do
    # Choice = -1 : Do whatever is mention in defs.ntt_type (if opt, do it with a stride of 1)
    # Choice =  0 : Do F1
    # Choice >  0 : Do opt with a stride of choice
    def op_ntt_util(self, mode, choice = -1):

        if choice == -1:
            if defs.ntt_type == "baseline":
                return self.op_ntt_baseline(mode)
            elif defs.ntt_type == "f1":
                return self.op_ntt_f1(mode)
            elif defs.ntt_type == "opt":
                return self.op_ntt_opt(mode, 1)
            else:
                print "Error op_ntt_util 1", defs.ntt_type
                exit()
        elif choice == 0:
                return self.op_ntt_f1(mode)
        elif choice > 0:
            return self.op_ntt_opt(mode, choice)
        else:
            print "Error op_ntt_util 2", choice
            exit()
    
    # Run NTT on the file passed through
    # TODO: Explain it somehow here?
    def op_ntt_baseline(self, mode):
        temp_cycles = 0
        temp_steps = 0
        temp_chops = 0
        temp_phops = 0

        if mode == 'psum':
            reg_file = self.psum_file
        elif mode == 'wt':
            reg_file = self.wt_file
        elif mode == 'if':
            reg_file = self.if_file
        else:
            print "Error op_ntt_baseline 1"
            exit()

        num_vals = defs.poly_n

        while num_vals > 1:
            num_vals /= 2
            pe_diff = num_vals / defs.wt_file_size
            temp_steps += 1

            if pe_diff in [32, 16]: # requires access to next chiplet for multiplication 
                temp_cycles += max(self.twiddle.read_time, reg_file.read_time) + 1 * defs.chop_time + self.muls.exec_time + self.adds.exec_time  
                temp_chops += 1
            elif pe_diff in [8, 2]:  # requires 2 hops for multiplication
                temp_cycles += max(self.twiddle.read_time, reg_file.read_time) + 2 * defs.phop_time + self.muls.exec_time + self.adds.exec_time  
                temp_phops += 2
            elif pe_diff in [4, 1]: # requires 1 hops for multiplication
                temp_cycles += max(self.twiddle.read_time, reg_file.read_time) + 1 * defs.phop_time + self.muls.exec_time + self.adds.exec_time  
                temp_phops += 1
            elif pe_diff == 0: # no hops
                temp_cycles += max(self.twiddle.read_time, reg_file.read_time) + self.muls.exec_time + self.adds.exec_time  
            else:
                print "Error op_ntt_baseline 2 :: {}".format(pe_diff)
                exit()

            if defs.num_chiplets == 1:
                # for storing we always need 2 hops [pe_diff == 8]
                temp_cycles += 2 * defs.phop_time + max(self.twiddle.write_time, reg_file.write_time)
                temp_phops += 2
            else:
                # for storing we always need to store on the next chiplet [pe_diff == 16, 32]
                temp_cycles += defs.chop_time + max(self.twiddle.write_time, reg_file.write_time)
                temp_chops += 1

            # print("{} \t {} \t {} \t {} {} {}".format(num_vals, temp_steps, pe_diff, temp_cycles, temp_phops, temp_chops))

        self.update_ntt(temp_cycles, mode, temp_steps, temp_chops, temp_phops)
        self.ntt_stats.update_ntt(temp_cycles, mode, temp_steps, temp_chops, temp_phops)

        return temp_cycles

    # Run NTT on the file passed through
    # Check transpose and 2 time calling
    # Root of n NTTs on Root of n values + Transpose + Root of n NTTs on Root of n values
    def op_ntt_f1(self, mode, param = -1):
        temp_cycles = 0
        temp_steps = 0
        temp_chops = 0
        temp_phops = 0

        if mode == 'psum':
            reg_file = self.psum_file
        elif mode == 'wt':
            reg_file = self.wt_file
        elif mode == 'if':
            reg_file = self.if_file
        else:
            print "Error op_ntt_f1 1"
            exit()

        num_vals = int(math.sqrt(defs.poly_n))

        while num_vals > 1:
            num_vals /= 2
            pe_diff = num_vals / defs.wt_file_size
            temp_steps += 1

            if pe_diff in [32, 16]: # requires access to next chiplet for multiplication 
                temp_cycles += max(self.twiddle.read_time, reg_file.read_time) + 1 * defs.chop_time + self.muls.exec_time + self.adds.exec_time  
                temp_chops += 1
            elif pe_diff in [8, 2]:  # requires 2 hops for multiplication
                temp_cycles += max(self.twiddle.read_time, reg_file.read_time) + 2 * defs.phop_time + self.muls.exec_time + self.adds.exec_time  
                temp_phops += 2
            elif pe_diff in [4, 1]: # requires 1 hops for multiplication
                temp_cycles += max(self.twiddle.read_time, reg_file.read_time) + 1 * defs.phop_time + self.muls.exec_time + self.adds.exec_time  
                temp_phops += 1
            elif pe_diff == 0: # no hops
                temp_cycles += max(self.twiddle.read_time, reg_file.read_time) + self.muls.exec_time + self.adds.exec_time  
            else:
                print "Error op_ntt_f1 2 :: {}".format(pe_diff)
                exit()

            if defs.num_chiplets == 1:
                # for storing we always need 2 hops [pe_diff == 8]
                temp_cycles += 2 * defs.phop_time + max(self.twiddle.write_time, reg_file.write_time)
                temp_phops += 2
            else:
                # for storing we always need to store on the next chiplet [pe_diff == 16, 32]
                temp_cycles += defs.chop_time + max(self.twiddle.write_time, reg_file.write_time)
                temp_chops += 1

            # print("{} \t {} \t {} \t {} {} {}".format(num_vals, temp_steps, pe_diff, temp_cycles, temp_phops, temp_chops))

        if param == -1:
            # This will be called twice
            self.update_ntt(temp_cycles * 2, mode, temp_steps * 2, temp_chops * 2, temp_phops * 2)
            self.ntt_stats.update_ntt(temp_cycles * 2, mode, temp_steps * 2, temp_chops * 2, temp_phops * 2)

        return temp_cycles * 2

    # Run optimised NTT
    # (Twiddle Hint * Wts) + Twiddle Coeff -> Wts happens c_t times
    # TODO: What are the Hops ?
    def op_ntt_opt(self, mode, stride, param = -1):

        if mode == 'psum':
            reg_file = self.psum_file
        elif mode == 'wt':
            reg_file = self.wt_file
        elif mode == 'if':
            reg_file = self.if_file
        else:
            print "Error op_ntt_opt 1"
            exit()

        temp_steps = defs.c_t * stride

        if defs.num_chiplets == 1:
            temp_cycles = (max(self.twiddle.read_time, self.twicoef.read_time, reg_file.read_time) + self.muls.exec_time + defs.phop_time) * temp_steps
            if param == -1:
                self.update_ntt(temp_cycles, mode, temp_steps, 0, 1)
                self.ntt_stats.update_ntt(temp_cycles, mode, temp_steps, 0, 1)
        elif defs.num_chiplets > 1:
            temp_cycles = (max(self.twiddle.read_time, self.twicoef.read_time, reg_file.read_time) + self.muls.exec_time + defs.chop_time) * temp_steps
            if param == -1:
                self.update_ntt(temp_cycles, mode, temp_steps, 1, 0)
                self.ntt_stats.update_ntt(temp_cycles, mode, temp_steps, 1, 0)
        else:
            print "Error op_ntt_opt 2"
            exit()

        if param == -1:
            # Since this acts as a shift
            # TODO: This is not refelcted in stat collections
            reg_file.stats_shifts += 1
            reg_file.stats_accesses += 2
            self.shift += 1
        # print max(self.twiddle.read_time, self.twicoef.read_time, reg_file.read_time), self.muls.exec_time,  defs.phop_time, "*", temp_steps, temp_cycles
        return temp_cycles