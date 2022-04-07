#################################################################################
##  Defining all the values being used
##
##
##
##
#################################################################################

# Global Definitions

## Params
k_t = -1
c_t = -1

packing    = "cheetah"
ntt_type   = "baseline"
batch_size = 1
poly_n     = 1024

num_chiplets  = -1

# Processor
cycle_time = 5     # In ns


# PE

## MACs
mac_num         = 128
mul_exec_time   = 1     # In Cycles
add_exec_time   = 0     

## L1 Caches
if_file_size    = 128   # Num of 8 b registers / cache blocks
if_file_read    = 0
if_file_write   = 0

wt_file_size    = 64    # Num of 8 b registers / cache blocks
wt_file_read    = 0
wt_file_write   = 0

ksh_file_size   = wt_file_size
ksh_file_read   = 0
ksh_file_write  = 0

psum_file_size  = if_file_size
psum_file_num   = 64
psum_file_read  = 0
psum_file_write = 0

twiddle_size    = wt_file_size
twiddle_read    = 0
twiddle_write   = 0

twicoef_size    = wt_file_size
twicoef_read    = 0
twicoef_write   = 0


# Chiplet
num_pe_x  = 4
num_pe_y  = 4
num_pe    = num_pe_x * num_pe_y
phop_time = 1

## L2 Caches
max_c_on_chiplt   = 512
max_ksh_on_chiplt = 1024

### IFs
if_l2_size  = num_pe_x * num_pe_y * if_file_size * max_c_on_chiplt
if_l2_read  = 1
if_l2_write = 1

### WTs
wt_l2_size  = num_pe_x * num_pe_y * wt_file_size * max_c_on_chiplt
wt_l2_read  = 1
wt_l2_write = 1

### KSH
ksh_l2_size  = num_pe_x * num_pe_y * wt_file_size * max_ksh_on_chiplt
ksh_l2_read  = 1
ksh_l2_write = 1


# Package   # TODO: Discuss
chop_time    = 2 + 2*phop_time