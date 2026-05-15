import xmlrpc.client
from set_model_params.set_model import set_model_init
from set_model_params.set_model import run_batch_simulation
from set_model_params.set_model import set_model_declarations
from set_model_params.set_model import set_model_fixed_initcommands
from set_model_params.set_model import run_single_simulation

class Simulation:
    def __init__(self, server: xmlrpc.client.ServerProxy, model_name: str,
                 time_span: str,
                 max_step: str,
                 zc_step_size: str,
                 freq: float,
                 duty: float
                 ):
        self.server = server
        self.model_name = model_name
        self.time_span = time_span
        self.max_step = max_step
        self.zc_step_size = zc_step_size
        self.freq = freq
        self.duty = duty
        self.enable_output = True
        set_model_init(self)
    

    def set_model_fixed_initcommands(self, init_commands: dict):
        set_model_fixed_initcommands(self, init_commands)

    def set_model_declarations(self, freq:float, duty:float):
        set_model_declarations(self, freq, duty)

    def run_single_simulation(self, params: dict):
        return run_single_simulation(self, params)
    def run_batch_simulation(self, params: list):
        return run_batch_simulation(self, params)