import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
import os

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
    for d in ['./Output/Data_Correct', './Output/Data_Wrong',
              './Output/Pic_Correct',  './Output/Pic_Wrong']:
        os.makedirs(d, exist_ok=True)


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