import xmlrpc.client
import time
import numpy as np
import pandas as pd
import os
import itertools
from datetime import datetime
import matplotlib.pyplot as plt
import sys

MODEL_NAME = "test.v1.1"
BLOCK_PATH = f"{MODEL_NAME}/C-Script"

duty = 29

def generate_params(freq, duty, rcs, rsa, csa, vin, rl, k) -> dict:
    Freq_list    = np.linspace(5.78e6, 7.78e6, 5).tolist() # 开关频率 (Hz)
    Duty_list    = np.linspace(0.2, 0.6, 5).tolist()       # 占空比
    Rsa_list    = np.linspace(0.2, 6, 6).tolist()          # heatsink-ambient热阻 (℃/W)
    Vin_list    = np.linspace(50, 400, 8).tolist()         # 输入直流电压 (V) 
    RL_list    = np.linspace(50, 200, 4).tolist()          # 负载电阻 (Ω)
    k_list    = np.linspace(0.1, 0.6, 6).tolist() 

    FIXED_Tinit = 25.1
    FIXED_Csa = 33.5
    FIXED_Rcs = 0.2
    LT = 1.64e-6
    LR = 2.79e-6

    return {
        "ModelVars": {
            "Rsa": Rsa_list,
            "Vin": Vin_list,
            "RL" : RL_list,
            "k"  : k_list,
        }
    }
    
    
    
    all_combos = list(itertools.product(
        Freq_list, Duty_list, Rsa_list,
        Vin_list, RL_list, k_list          # Tinit、Csa、Rcs 已固定，不在此扫描
    ))
    total = len(all_combos)

    task_args = [
        (i, total, f, d, r, v, rl, k) 
            for i, (f, d, r, v, rl, k) in enumerate(all_combos, 1)
    ]

    return task_args
def connect_server(port: int) -> tuple[xmlrpc.client.ServerProxy, str, str]:
    server = xmlrpc.client.ServerProxy(f'http://localhost:{port}/RPC2')
    model_name = MODEL_NAME
    block_path = BLOCK_PATH

    return server, model_name, block_path

def config_model(server: xmlrpc.client.ServerProxy, time_span: str, 
                 max_step: str, zc_step_size: str):
    server.plecs.set(model_name, "TimeSpan", time_span)
    server.plecs.set(model_name, "MaxStep",  max_step)
    server.plecs.set(model_name, "ZCStepSize",  zc_step_size)






if __name__ == '__main__':
    server, model_name, block_path = connect_server(port=1080)
    sim_list = []
    sim_list.append({"InitializationCommands": {"Tinit": 25}})
    sim_list.append({"InitializationCommands": {"Tinit": 50}})
    #sim_list.append({"ModelVars": {"vin": 10, "RL": 10}})
    #sim_list.append({"ModelVars": {"vin": 10, "RL": 10}})
    #sim_list.append({"ModelVars": {"vin": 10, "RL": 10}})


    #print(server.system.methodHelp('plecs.analyze'))

    #opts_test = {"ModelVars": {"Vin": [1,2,2,2,2,2,2,2,2,2], "RL": [10,20,10,20,10,20,10,20,10,20]}}
    print("begin")
    print(datetime.now())
    print(server.system.listMethods())
    server.plecs.set(model_name, "InitializationCommands", "Tinit=25")

    # 查询模型当前的仿真属性名
    print(server.plecs.get(model_name, ""))
    sys.exit(0)
    sim_results = server.plecs.simulate(model_name, sim_list)

    print(datetime.now())
    print(len(sim_results))

    sim_results = sim_results[1]


    time = np.array(sim_results['Time'])
    values = np.array(sim_results['Values'])

    time = time[::1000]
    values = values[:,::1000]

    df = pd.DataFrame({
        'Time': time,
        'Value': values[0]  # 取第一行，形状变为 (1414,)
    })

        # 2. 检查数据维度
        # 注意：PLECS RPC 返回的 values 通常是 (N_Channels, N_Samples) 
        # 需要转置为 (N_Samples, N_Channels) 以便绘图
    print(f"Time shape: {time.shape}")
    print(f"Values shape: {values.shape}")
    
        # 转置 values 数组，使其形状变为 (N_Samples, N_Channels)
    if len(values.shape) > 1:
        values = values.T
        print(f"Transposed Values shape: {values.shape}")

        # 3. 绘图
    plt.figure(figsize=(10, 6))
    
        # 如果有多个输出信号，循环绘制
    if len(values.shape) > 1:
        num_channels = values.shape[1]
        for i in range(num_channels):
            plt.plot(time, values[:, i], label=f'Signal {i+1}')
    else:
        plt.plot(time, values, label='Signal 1')

    plt.title(f"PLECS Simulation Results: {model_name} with duty cycle {duty:.2f}")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.legend()
    
        # 4. 保存并展示
    plt.savefig('./test_for_batch/plecs_result_' + str(int(duty * 100)) +'.png', dpi=300)
    print("图片已保存为 plecs_results.png")
        

       
        # 保存
    df.to_csv(f'./test_for_batch/duty_{duty}.csv', index=False)
        # when running loop, dont show the plot
        #plt.show()
    pass