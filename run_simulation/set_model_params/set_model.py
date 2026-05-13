from __future__ import annotations
import xmlrpc.client
from typing import TYPE_CHECKING
import math

if TYPE_CHECKING:
    from model_obj import Simulation

c_template = """
#include <math.h>
static double freq = {freq_val};  /* 开关频率，用于计算周期 T = 1/freq */
static double duty = {d_val};     /* 占空比，用于计算导通时间 t1 */
double T, t1, t2;
"""



def set_model_init(simulation: Simulation):
    
    simulation.server.plecs.set(simulation.model_name, "TimeSpan", 
                                simulation.time_span)
    simulation.server.plecs.set(simulation.model_name, "MaxStep",  
                                simulation.max_step)
    simulation.server.plecs.set(simulation.model_name, "ZCStepSize",    
                                simulation.zc_step_size)



def set_model_fixed_initcommands(simulation: Simulation, init_commands: dict):
    init_commands_set = (
        f"Tinit = {init_commands["InitializationCommands"]["Tinit"]};\n"
        f"Rcs = {init_commands["InitializationCommands"]["Rcs"]};\n"
        f"Csa = {init_commands["InitializationCommands"]["Csa"]};\n"
        f"Rsa = {init_commands["InitializationCommands"]['Rsa']};\n"
        f"Vin = {init_commands["InitializationCommands"]['Vin']};\n"
        f"RL = {init_commands["InitializationCommands"]['RL']};\n"
        f"k = {init_commands["InitializationCommands"]['k']};\n"
        f"Lt = {1.64e-6};\n"
        f"Lr = {2.79e-6};\n"
        f"M = {init_commands["InitializationCommands"]['k'] * math.sqrt(1.64e-6 * 2.79e-6)};\n"
    )
    simulation.server.plecs.set(simulation.model_name, "InitializationCommands",
                                init_commands_set)
   
    
def set_model_declarations(simulation: Simulation, freq:float, duty:float):
    block_path = f"{simulation.model_name}/C-Script"
    simulation.server.plecs.set(block_path, "Declarations", 
                                c_template.format(freq_val=freq, 
                                                  d_val=duty))

def run_batch_simulation(simulation: Simulation, params: list):
    return simulation.server.plecs.simulate(simulation.model_name, params)

def run_single_simulation(simulation: Simulation, params: dict):
    return simulation.server.plecs.simulate(simulation.model_name)