#################################################################################
##  Defining all the values being used
##
##
##
##
#################################################################################

# Global Definitions

## Params
Kt = None
Ct = None

packing    = "cheetah"
ntt_type   = "baseline"
arch       = "f1"
poly_n     = 1024
batch_size = 1
num_chiplets  = None

# Arch Choices
pe_size        = 1024
transpose_f1    = 32     # Rotation for n = 1024
shift_f1        = 1
permute_hyena   = 1      # Benes network FTW!

# Processor
cycle_time = None     # In Ticks
tick_time  = 1        # In ns

# PE

## MACs
mac_num         = poly_n*2
mul_exec_time   = 5     # In Ticks
add_exec_time   = 0     

## L1 Caches
if_file_size    = poly_n*2   # Num of 8 b registers / cache blocks
if_file_read    = 0
if_file_write   = 0

wt_file_size    = poly_n     # Num of 8 b registers / cache blocks
wt_file_read    = 0
wt_file_write   = 0

ksh_file_size   = if_file_size
ksh_file_read   = 0
ksh_file_write  = 0

psum_file_size  = if_file_size
psum_file_num   = 64        # PSUM will have to be multiplied by this in post processing
psum_file_read  = 0
psum_file_write = 0

buff_file_read  = 0
buff_file_write = 0

twiddle_size    = wt_file_size
twiddle_read    = 0
twiddle_write   = 0

twicoef_size    = wt_file_size
twicoef_read    = 0
twicoef_write   = 0


# Chiplet

## L2 Caches
max_c_on_chiplt   = 512
max_ksh_on_chiplt = 1024
max_wt_on_chiplt  = max_c_on_chiplt
max_if_on_chiplt  = max_c_on_chiplt

### IFs
if_l2_size  = if_file_size * max_c_on_chiplt
if_l2_read  = 1
if_l2_write = 1

### WTs
wt_l2_size  = wt_file_size * max_wt_on_chiplt
wt_l2_read  = 1
wt_l2_write = 1

### KSH
ksh_l2_size  = wt_file_size * max_ksh_on_chiplt
ksh_l2_read  = 1
ksh_l2_write = 1