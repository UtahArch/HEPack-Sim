#################################################################################
##   Defines architectural and secutrity parameters used for the simulation
##   Change packing, ntt_type, arch to vary the simulation runs
##   Our architecture and assumptions are better described in the paper 
##   
##   These are the default parameters used by the runs, it is recommended to change
##   them in the run_<packing>.py rather than here
##
##   TODO: Remove Legacy Parameters
#################################################################################

# Global Definitions

## Params
Kt = None
Ct = None
Bt = 1

# Parameters used for naming the file
packing    = "cheetah"      # Packing Scheme
ntt_type   = "baseline"     # NTT Type: baseline, f1
arch       = "f1"           # Accelerator Hardware: f1, hyena
poly_n     = 1024
batch_size = 1
num_chiplets  = None

# Arch Choices
pe_size        = 1024    # Number of PEs per accelerator
transpose_f1    = 32     # Rotation for n = 1024 in ticks
shift_f1        = 1      # In ticks
permute_hyena   = 1      # Benes network FTW, in ticks

# Processor
cycle_time = None     # In Ticks defined by arch choices
tick_time  = 1        # In ns

# PE

## MACs
mac_num         = poly_n*2  # Since CKKS is complex
mul_exec_time   = 5         # In Ticks
add_exec_time   = 0         # Since we use MAC units Add is free

## L1 Caches                 # These are techinically registers inside MAC units so reads are immediate, writes are hidden behind the pipeline
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
max_c_on_chiplt   = 512             # Max number of channels that can be supported on chiplet
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
