import xmlrpc.client    # 用于通过 XML-RPC 协议远程控制 PLECS
import itertools        # 用于生成多参数的全组合
import time             # 用于计时
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent

# True = 扫参模式（遍历所有参数组合）；
# False = 单次仿真（用 init_ 默认值）
RUN_LOOP = False

# 连接本机 PLECS，端口 1080
server = xmlrpc.client.ServerProxy('http://localhost:1080/RPC2')
model_name = "test.v1.1"               # PLECS 中打开的模型名称
block_path = f"{model_name}/C-Script"  # C-Script 元件路径，格式：模型名/元件名

# ── 固定参数（不参与扫描，但会体现在所有输出文件中）──
FIXED_Tinit = 25.1   # 初始环境温度 (℃)
FIXED_Csa   = 33.5   # heatsink-ambient热容 (J/℃)，暂时固定
FIXED_Rcs   = 0.2    # case-heatsink热阻 (℃/W)，暂时固定

# ── 单次仿真默认值 ──
init_Freq = 6.78e6  # 开关频率 (Hz)
init_Duty = 0.5     # 占空比 (0~0.5)
init_Rsa  = 0.5     # heatsink-ambient热阻 (℃/W)
init_Vin  = 100     # 输入直流电压 (V)
init_RL   = 115     # 负载电阻 (Ω)
init_k    = 0.6     # 线圈耦合系数

# ── 扫参列表（RUN_LOOP=True 时生效）──
# 每个列表有几个值，就在该参数上扫几个点；全部参数做笛卡尔积组合
# 已固定不扫：Tinit、Csa、Rcs（见上方 FIXED_ 常量）
Freq_list    = np.linspace(5.78e6, 7.78e6, 5).tolist() # 开关频率 (Hz)
Duty_list    = np.linspace(0.2, 0.6, 5).tolist()       # 占空比
Rsa_list    = np.linspace(0.2, 6, 6).tolist()          # heatsink-ambient热阻 (℃/W)
Vin_list    = np.linspace(50, 400, 8).tolist()         # 输入直流电压 (V) 
RL_list    = np.linspace(50, 200, 4).tolist()          # 负载电阻 (Ω)
k_list    = np.linspace(0.1, 0.6, 6).tolist()          # 耦合系数


def build_init_commands(rcs, rsa, csa, vin, rl, k,
                        lt=1.64e-6, lr=2.79e-6):
    """
    生成写入 PLECS InitializationCommands 的字符串。
    变量名与 PLECS 原理图元件参数框完全一致。
    Freq/Duty 只在 C-Script Declarations 里，不在这里。
    M 由 k/Lt/Lr 自动计算，与 PLECS 原始公式 M=k*sqrt(Lt*Lr) 一致。
    """
    import math
    return (
        f"Tinit = {FIXED_Tinit};\n"
        f"Rcs = {rcs};\n"
        f"Rsa = {rsa};\n"
        f"Csa = {csa};\n"
        f"Vin = {vin};\n"
        f"RL = {rl};\n"
        f"Lt = {lt};\n"
        f"Lr = {lr};\n"
        f"k = {k};\n"
        f"M = {k * math.sqrt(lt * lr)};\n"  # 直接算好数值，避免 Octave 依赖顺序问题
    )


# C-Script Declarations 模板：注入 C 语言静态变量
# {freq_val} 和 {d_val} 是占位符，由 .format() 在每次循环中填入具体数值
# 注意：这里的 freq 是 C 变量，仅在 C-Script 内部用于计算 PWM 时序（T、t1、t2）
#       与 InitCommands 里的 Freq 是同一物理量，必须保持数值一致
c_template = """
#include <math.h>
static double freq = {freq_val};  /* 开关频率，用于计算周期 T = 1/freq */
static double duty = {d_val};     /* 占空比，用于计算导通时间 t1 */
double T, t1, t2;
"""


# ── 通道定义（顺序与 PLECS Port 编号一致）──────────────────────
CH_NAMES = [
    'Iin',    'Vout',    'Iout',                          # Port1: VI
    'S1_Pcond','S1_Psw', 'S1_Ptot',                      # Port2: S1 Loss
    'S2_Pcond','S2_Psw', 'S2_Ptot',                      # Port3: S2 Loss
    'S3_Pcond','S3_Psw', 'S3_Ptot',                      # Port4: S3 Loss
    'S4_Pcond','S4_Psw', 'S4_Ptot',                      # Port5: S4 Loss
    'Tj_S1',  'Tj_S2',  'Tj_S3',  'Tj_S4', 'T_heatsink',# Port6: 温度
]
PORT_GROUPS = [
    ('Port1: VI',         CH_NAMES[0:3],   range(0,  3)),
    ('Port2: S1 Loss',    CH_NAMES[3:6],   range(3,  6)),
    ('Port3: S2 Loss',    CH_NAMES[6:9],   range(6,  9)),
    ('Port4: S3 Loss',    CH_NAMES[9:12],  range(9,  12)),
    ('Port5: S4 Loss',    CH_NAMES[12:15], range(12, 15)),
    ('Port6: Temperature',CH_NAMES[15:20], range(15, 20)),
]
ERROR_LOG = './Output/error_log.csv'


def classify_error(error_msg):
    """从报错信息提取分类标签，用于 error_log 的 category 列。"""
    msg = error_msg.lower()
    if 'temperature' in msg or 'thermal' in msg:
        return 'thermal_limit'
    if 'convergence' in msg or 'diverge' in msg or 'singular' in msg:
        return 'convergence'
    if 'assertion' in msg:
        return 'assertion'
    if 'timeout' in msg:
        return 'timeout'
    if 'connection' in msg or 'rpc' in msg:
        return 'connection'
    return 'other'


def log_error_case(freq, duty, rcs, rsa, csa, vin, rl, k, error_msg):
    """将报错工况（参数+分类）追加写入 error_log.csv，不含波形数据。"""
    import os
    row = pd.DataFrame([{
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'category':  classify_error(error_msg),
        'freq': freq, 'duty': duty, 'rcs': rcs, 'rsa': rsa,
        'csa': csa,   'vin': vin,   'rl': rl,   'k': k,
        'error_msg': error_msg,
    }])
    write_header = not os.path.exists(ERROR_LOG)
    row.to_csv(ERROR_LOG, mode='a', header=write_header, index=False)
    print(f"  工况已记录 → {ERROR_LOG}  [类别: {classify_error(error_msg)}]")


def save_data_and_plot(sim_results, freq, duty, rcs, rsa, csa, vin, rl, k, folder):
    """
    保存温度曲线图和 CSV 到指定子目录（Correct 或 Wrong）。
    - 全部 20 通道：取最后 100 个开关周期求均值，存为标量（第 1 行）
    - 温度 5 通道额外：按 [::1000] 降采样保留时间序列（第 2 行起）
    CSV 格式：
      第 0 行：仿真参数（freq/duty/rcs/rsa/csa/vin/rl/k）
      第 1 行：全部 20 通道均值
      第 2 行起：Time + 5 条温度时间序列
    图表：仅画温度 5 条曲线随时间变化
    """
    t_full = np.array(sim_results['Time'])
    v_full = np.array(sim_results['Values'])  # (n_ch, n_samples)
    n_ch   = v_full.shape[0]

    period = 1.0 / freq

    # ── 1. VI / Loss（索引 0~14）：最后 100 个周期内降采 1000 点求均值 ──
    mask_last100 = t_full >= (t_full[-1] - 100 * period)
    idx_last100  = np.where(mask_last100)[0]
    step_loss    = max(1, len(idx_last100) // 1000)
    idx_loss_ds  = idx_last100[::step_loss]
    scalar_means = {}
    for i, name in enumerate(CH_NAMES[:min(15, n_ch)]):
        scalar_means[name] = float(np.mean(v_full[i, idx_loss_ds]))

    # ── 2. 温度（索引 15~19）：全程降采 1000 点，再取最后 100 个周期范围内的点求均值 ──
    step_temp  = max(1, len(t_full) // 1000)
    t_temp     = t_full[::step_temp]
    temp_names = [CH_NAMES[15 + i] for i in range(5) if (15 + i) < n_ch]
    temp_data  = {CH_NAMES[15 + i]: v_full[15 + i, ::step_temp]
                  for i in range(5) if (15 + i) < n_ch}
    mask_temp_last100 = t_temp >= (t_temp[-1] - 100 * period)
    for name in temp_names:
        scalar_means[name] = float(np.mean(temp_data[name][mask_temp_last100]))

    # ── 3. 构建 CSV ──
    _t = time.time()
    param_row = {'freq': freq, 'duty': duty, 'rcs': rcs, 'rsa': rsa,
                 'csa': csa,   'vin': vin,   'rl': rl,   'k': k}
    ts_names  = [n + '_ts' for n in temp_names]
    df_meta = pd.DataFrame([param_row, scalar_means])
    df_ts   = pd.DataFrame({'Time': t_temp,
                            **{ts: temp_data[n] for ts, n in zip(ts_names, temp_names)}})
    df = pd.concat([df_meta, df_ts], ignore_index=True)
    print(f"  [计时] CSV构建: {time.time()-_t:.1f}s")

    # ── 4. 画图：仅温度 5 条曲线 ──
    _t = time.time()
    fig, ax = plt.subplots(figsize=(12, 4))
    fig.suptitle(f"[{folder}] duty={duty}  Rsa={rsa}  RL={rl}  k={k}  freq={freq:.2e}")
    for name in temp_names:
        ax.plot(t_temp, temp_data[name], label=name)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Temperature (℃)")
    ax.legend(fontsize=7, ncol=5)
    ax.grid(True)
    plt.tight_layout()

    tag = (f"freq{freq:.2e}_duty{int(duty*100)}"
           f"_rcs{rcs}_rsa{rsa}_csa{csa}_vin{vin}_rl{rl}_k{k}")
    plt.savefig(f'./Output/Pic_{folder}/{tag}.png', dpi=300)
    plt.close()
    print(f"  [计时] 画图保存: {time.time()-_t:.1f}s")

    _t = time.time()
    df.to_csv(f'./Output/Data_{folder}/{tag}.csv', index=False)
    print(f"  [计时] CSV保存: {time.time()-_t:.1f}s")

    return n_ch, tag


def run_single_simulation(params):
    idx, total, freq, duty, rsa, vin, rl, k = params

    try:
        server.plecs.set(model_name, "InitializationCommands",
                             build_init_commands(FIXED_Rcs, rsa, FIXED_Csa, vin, rl, k))
            # ② 把频率和占空比写入 C-Script Declarations
        server.plecs.set(block_path, "Declarations",
                             c_template.format(freq_val=freq, d_val=duty))
            # ③ 触发仿真并保存结果
        main(freq, duty, FIXED_Rcs, rsa, FIXED_Csa, vin, rl, k)
        elapsed = time.time() - t_start
        print(f"  累计耗时 {elapsed:.0f}s，预计剩余 {elapsed/i*(total-i):.0f}s")

    except Exception as e:
        return log_error_case(freq, duty, FIXED_Rcs, rsa, FIXED_Csa, vin, rl, k, str(e))



def main(freq, duty, rcs, rsa, csa, vin, rl, k):
    """
    触发一次仿真，按结果分类保存：
    - 正常完成        → Pic_Correct / Data_Correct
    - 仿真中途报错有数据 → Pic_Wrong   / Data_Wrong  + error_log 记录工况
    - 仿真前就报错     → 仅 error_log 记录工况，无数据保存
    """
    print(f"运行: freq={freq:.2e} duty={duty} rcs={rcs} rsa={rsa} "
          f"csa={csa} vin={vin} rl={rl} k={k}")

    sim_results = None
    sim_error   = None

    # ── 第一层：触发仿真 ──────────────────────────────────────
    try:
        server.plecs.set(model_name, "TimeSpan", "0.02")
        server.plecs.set(model_name, "MaxStep",  "5e-8")
        t0 = time.time()
        sim_results = server.plecs.simulate(model_name)
        t_sim = time.time() - t0
        print(f"  仿真完成，仿真耗时 {t_sim:.1f}s")
    except Exception as e:
        sim_error = str(e)
        print(f"  仿真报错: {sim_error}")

    # ── 第二层：有数据就保存，按是否报错分目录 ───────────────
    if sim_results is not None:
        folder = 'Wrong' if sim_error else 'Correct'
        try:
            t1 = time.time()
            n_ch, tag = save_data_and_plot(sim_results, freq, duty, rcs, rsa, csa, vin, rl, k, folder)
            t_total = t_sim + (time.time() - t1)
            print(f"  实际通道数: {n_ch}  |  总耗时 {t_total:.1f}s  |  数据已保存 → Data_{folder}/{tag}")
        except Exception as save_err:
            import traceback
            print(f"  保存失败: {save_err}")
            traceback.print_exc()

    # ── 第三层：有报错就记录工况到 error_log ─────────────────
    if sim_error is not None:
        log_error_case(freq, duty, rcs, rsa, csa, vin, rl, k, sim_error)


if __name__ == "__main__":
    # 自动创建所需目录（已存在则跳过）
    import os
    for d in ['./Output/Data_Correct', './Output/Data_Wrong',
              './Output/Pic_Correct',  './Output/Pic_Wrong']:
        os.makedirs(d, exist_ok=True)

    if RUN_LOOP:
        # 全组合扫参：各列表长度之积 = 总仿真次数
        all_combos = list(itertools.product(
            Freq_list, Duty_list, Rsa_list,
            Vin_list, RL_list, k_list          # Tinit、Csa、Rcs 已固定，不在此扫描
        ))
        total = len(all_combos)

        task_args = [
            (i, total, f, d, r, v, rl, k) 
            for i, (f, d, r, v, rl, k) in enumerate(all_combos, 1)
        ]
        t_start = time.time()


        MAX_WORKERS = 8 
        
        print(f"开始多线程仿真，总任务数: {total}，线程数: {MAX_WORKERS}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交任务
            futures = [executor.submit(run_single_simulation, arg) for arg in task_args]
            
            # 实时获取完成情况
            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                result = future.result()
                elapsed = time.time() - t_start
                print(f"{result} | 累计耗时 {elapsed:.0f}s | 进度: {i}/{total}")

        #for i, (freq, duty, rsa, vin, rl, k) in enumerate(all_combos, 1):
        #    print(f"\n[{i}/{total}]", end=" ")
            # ① 把热路/电路参数写入 PLECS InitializationCommands（Tinit/Csa/Rcs 取固定值）
        #    server.plecs.set(model_name, "InitializationCommands",
        #                     build_init_commands(FIXED_Rcs, rsa, FIXED_Csa, vin, rl, k))
            # ② 把频率和占空比写入 C-Script Declarations
        #    server.plecs.set(block_path, "Declarations",
        #                     c_template.format(freq_val=freq, d_val=duty))
            # ③ 触发仿真并保存结果
        #    main(freq, duty, FIXED_Rcs, rsa, FIXED_Csa, vin, rl, k)
        #    elapsed = time.time() - t_start
        #    print(f"  累计耗时 {elapsed:.0f}s，预计剩余 {elapsed/i*(total-i):.0f}s")

    else:
        # 单次仿真：使用顶部定义的 init_ 默认值，Rcs 取固定值
        server.plecs.set(model_name, "InitializationCommands",
                         build_init_commands(FIXED_Rcs, init_Rsa,
                                             FIXED_Csa, init_Vin, init_RL, init_k))
        server.plecs.set(block_path, "Declarations",
                         c_template.format(freq_val=init_Freq, d_val=init_Duty))
        main(init_Freq, init_Duty, FIXED_Rcs, init_Rsa, FIXED_Csa, init_Vin, init_RL, init_k)

        