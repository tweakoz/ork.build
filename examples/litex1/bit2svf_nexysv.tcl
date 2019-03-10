global env
open_hw
connect_hw_server -quiet
set bld_dir $env(build_dir)
puts $bld_dir
create_hw_target my_svf_target
open_hw_target [get_hw_targets -regexp .*/my_svf_target]
set device0 [create_hw_device -part xc7a200t]

set_property PROGRAM.FILE $bld_dir/gateware/top.bit $device0
set_param xicom.config_chunk_size 0
program_hw_devices -force -svf_file $bld_dir/gateware/top.svf $device0
