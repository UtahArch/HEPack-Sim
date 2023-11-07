#################################################################################
##  
##  
##  
##  
##  
#################################################################################

import math
import sys


class CraterLake():

    def __init__(self):
        
        self.poly_size   = 65536

        self.mult_depth  = 60
        self.new_depth   = 57
        self.lane_groups = 8
        self.lane_size   = 256
        self.steps_poly  = self.poly_size / (self.lane_groups*self.lane_size)

        assert(self.poly_size % (self.lane_groups*self.lane_size) == 0)

        self.curr_depth = self.mult_depth
        self.run_time   = 0

        print(self.steps_poly)

 
    
    def run_KSH(self, runs, L):
        # return (32*L*2 + 32*2*L*2 + 32*2*2*L + 32*2*2*L*2 + 2*L*32*2 + 32*2*L*2 + 32*L*2) * runs
        # return 32*2*L * runs
        return runs
    
    def run_MUL(self, runs, L):
        # return (32*L*2 + 32*2*L*2 + 32*2*2*L + 32*2*2*L*2 + 2*L*32*2 + 32*2*L*2 + 32*L*2) * runs
        # return 32*2*L * runs
        return runs
