import csv
import time
import sys
from datetime import datetime
from pymeasure.instruments.keithley import Keithley2400
import pandas as pd
import tkinter as tk
import os
from tkinter import messagebox
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# from matplotlib.figure import Figure
import numpy as np
import plotly.graph_objects as go
import math
from pathlib import Path



# --------------------------- 路徑工具（固定 exe 同層） ---------------------------
# ### CHANGED: 統一把輸出放在 exe 同層，打包前後行為一致
def exe_dir() -> Path:
    if getattr(sys, 'frozen', False):  # 打包後
        return Path(sys.executable).parent
    return Path(__file__).parent       # 開發時

def ensure_dir(p: Path) -> Path:
    p.mkdir(parents=True, exist_ok=True)
    return p

def data_dir() -> Path:
    return ensure_dir(exe_dir() / "testing data csv")

# def pic_dir() -> Path:
#     return ensure_dir(exe_dir() / "testing data_pic")

def html_dir() -> Path:
    return ensure_dir(exe_dir() / "testing data_html")

def run_internal_staircase(addr="GPIB0::22::INSTR", start_v=10, stop_v=90, step=10, dwell_s=0.01, nplc=0.05):
    with Keithley2400(addr) as smu:
        
        start_time = time.time()
        points1 = int(math.floor((stop_v - start_v) / step) + 1)
        points2 = int(math.floor((125 - 91) / 1) + 1)
        smu.reset()
        smu.adapter.connection.timeout = 60000
        if total_runs.get() == 0:
            
            smu.write("*CLS")
            smu.use_front_terminals()
            smu.apply_voltage(voltage_range=21, compliance_current=0.00025)
            smu.auto_zero = False
            smu.write(f"SENS:FUNC 'VOLT','CURR'")      # 併量測 V、I
            smu.write("SENS:CURR:RANG 0.001")
            smu.write("SENS:CURR:RANG:AUTO OFF")
            smu.write(f"SENS:CURR:NPLC {nplc}")
            smu.write(f"SENS:VOLT:NPLC {nplc}")
            smu.write("FORM:ELEM VOLT,CURR")           # 只回傳 V,I

            # 內建掃描（線性階梯）
            smu.write("SOUR:FUNC VOLT")
            smu.write("SOUR:VOLT:MODE SWE")
            smu.write("SOUR:SWE:SPAC LIN")
            smu.write(f"SOUR:VOLT:STAR {start_v}")
            smu.write(f"SOUR:VOLT:STOP {stop_v}")
            smu.write(f"SOUR:VOLT:STEP {step}")
            smu.write(f"SOUR:DEL {dwell_s}")

            # 緩衝/觸發
            smu.write("TRAC:CLE")
            smu.write(f"TRAC:POIN {points1}")
            smu.write("TRAC:FEED SENS")
            smu.write("TRAC:FEED:CONT NEXT")
            smu.write(f"TRIG:COUN {points1}")
            smu.write("TRIG:SOUR IMM")
            smu.write("*SAV 1")

            smu.write("*CLS")
            smu.use_front_terminals()
            smu.apply_voltage(voltage_range=21, compliance_current=0.00025)
            smu.auto_zero = False
            smu.write(f"SENS:FUNC 'VOLT','CURR'")      # 併量測 V、I
            smu.write("SENS:CURR:RANG 0.001")
            smu.write("SENS:CURR:RANG:AUTO OFF")
            smu.write(f"SENS:CURR:NPLC {nplc}")
            smu.write(f"SENS:VOLT:NPLC {nplc}")
            smu.write("FORM:ELEM VOLT,CURR")           # 只回傳 V,I

            # 內建掃描（線性階梯）
            smu.write("SOUR:FUNC VOLT")
            smu.write("SOUR:VOLT:MODE SWE")
            smu.write("SOUR:SWE:SPAC LIN")
            smu.write("SOUR:VOLT:STAR 91")
            smu.write(f"SOUR:VOLT:STOP 125")
            smu.write(f"SOUR:VOLT:STEP 1")
            smu.write(f"SOUR:DEL {dwell_s}")

            # 緩衝/觸發
            smu.write(f"TRAC:POIN {points2}")
            smu.write("TRAC:FEED SENS")
            smu.write("TRAC:FEED:CONT NEXT")
            smu.write(f"TRIG:COUN {points2}")
            smu.write("TRIG:SOUR IMM")
            smu.write("*SAV 2")
        else:
            smu.write("*RCL 1")
            smu.write("TRAC:CLE")
            smu.write(f"TRAC:POIN {points1}")
            smu.write("TRAC:FEED SENS")
            smu.write("TRAC:FEED:CONT NEXT")
            smu.write(f"TRIG:COUN {points1}")
            smu.write("TRIG:SOUR IMM")
            smu.write("*RCL 2")
            smu.write(f"TRAC:POIN {points2}")
            smu.write("TRAC:FEED SENS")
            smu.write("TRAC:FEED:CONT NEXT")
            smu.write(f"TRIG:COUN {points2}")
            smu.write("TRIG:SOUR IMM")
        print(total_runs.get())
        smu.enable_source()
        smu.write("INIT")
        smu.ask("*OPC?")                         # 等掃描完成
        raw = smu.ask("TRAC:DATA?")              # 一次讀回 V,I
        smu.write("OUTP OFF")
        print(raw)
        # vals = [float(x) for x in raw.strip().split(",") if x]
        # V = vals[0::2]
        # I = vals[1::2]
        # V_cmd = [start_v + i * step for i in range(points1)]
        # V_cmd += [91 + i * 1 for i in range(points2)]
        # # 組成 DataFrame
        # df = pd.DataFrame({
        #     "V_cmd": V_cmd,
        #     "I_meas": I,
        #     "V_meas": V,
        # })
        # print(df)
        end_time = time.time()
        function_time = end_time - start_time
        print(f"cost time: {function_time:.2f} s")
        return df.values.tolist()
    
def on_input_change(*args):
    if entry_var.get().strip():
        before_button.config(state=tk.NORMAL)
    else:
        before_button.config(state=tk.DISABLED)
# --------------------------- 圖表輸出 ---------------------------
# def show_and_save_pic(fp_csv: str, fn: str):
#     df = pd.read_csv(fp_csv)

#     # ### CHANGED: 固定輸出到 exe 同層資料夾
#     fp_pic = pic_dir() / f"{fn}.png"

#     V_before = df["Voltage(V)"]
#     I_before = df["I_before"]
#     V_after  = df["Voltage(V).1"]
#     I_after  = df["I_after"]

#     ratio = I_before / I_after.replace(0, pd.NA)
#     df['I_ratio'] = ratio

#     V_max_number = 125
#     Xaxis = np.linspace(0, V_max_number, num=int(V_max_number / 5) + 1)

#     fig = Figure(figsize=(10, 6), dpi=100)
#     ax1 = fig.add_subplot(111)
#     ax1.plot(V_before, I_before * 1000, label='I_before', color='red')
#     ax1.plot(V_after,  I_after  * 1000, label='I_after',  color='green')
#     ax1.set_xlabel('Voltage (V)')
#     ax1.set_ylabel('Current (mA)')
#     ax1.grid(True)
#     ax1.legend(loc='upper left')
#     ax1.set_xticks(Xaxis)
#     ax1.set_xticklabels(Xaxis, rotation=45)

#     ax2 = ax1.twinx()
#     ax2.plot(V_after, ratio, label='I_before / I_after', color='blue')
#     ax2.set_ylabel('Ratio')
#     ax2.legend(loc='upper right')

#     fig.tight_layout()
#     fig.savefig(fp_pic)

#     # 清掉舊的 canvas
#     for widget in plot_frame.winfo_children():
#         widget.destroy()

#     canvas = FigureCanvasTkAgg(fig, master=plot_frame)
#     canvas.draw()
#     canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# def save_html(fp_csv: str, fn: str):
#     df = pd.read_csv(fp_csv)

#     # ### CHANGED: 固定輸出到 exe 同層資料夾
#     fp_html = html_dir() / f"{fn}.html"

#     V_before = df["Voltage(V)"]
#     I_before = df["I_before"]
#     V_after  = df["Voltage(V).1"]
#     I_after  = df["I_after"]

#     ratio = I_before / I_after.replace(0, pd.NA)
#     V_max_number = 125
#     Xaxis = np.linspace(0, V_max_number, num=int(V_max_number / 5) + 1)

#     fig = go.Figure()
#     fig.add_trace(go.Scatter(
#         x=V_before, y=I_before * 1000, mode='lines+markers',
#         name='I_before', line=dict(color='red'),
#         hovertemplate='%{y:.4f} mA<br>Voltage: %{x:.2f}'
#     ))
#     fig.add_trace(go.Scatter(
#         x=V_after, y=I_after * 1000, mode='lines+markers',
#         name='I_after', line=dict(color='green'),
#         hovertemplate='%{y:.4f} mA<br>Voltage: %{x:.2f}'
#     ))
#     fig.add_trace(go.Scatter(
#         x=V_after, y=ratio, mode='lines+markers',
#         name='I_Ratio', line=dict(color='blue'),
#         yaxis='y2',
#         hovertemplate='%{y:.4f}<br>Voltage: %{x:.2f}'
#     ))
#     fig.update_layout(
#         title='Current and Ratio vs Voltage',
#         xaxis=dict(title='Voltage (V)', type='linear', tickvals=Xaxis, tickformat='.2f'),
#         yaxis=dict(title='Current (mA)', side='left'),
#         yaxis2=dict(title='Ratio', overlaying='y', side='right'),
#         legend=dict(x=0.01, y=0.99),
#         hovermode='x unified'
#     )
#     fig.write_html(str(fp_html))  # Path 轉 str

# --------------------------- 關鍵修正：補齊兩清單 ---------------------------
# ### CHANGED: 修正索引邏輯，避免越界；列長不足自動補到可寫入第 2 欄；comp_i 由參數傳入
def pad_lists(list_before, list_after, comp_i_value=None):

    max_len = max(len(list_before), len(list_after))
    padded_before = []
    padded_after  = []

    def set_col_safe(row, idx, value):
        r = list(row)
        if len(r) <= idx:
            r += [None] * (idx + 1 - len(r))
        r[idx] = value
        return r

    for i in range(max_len):
        if i < len(list_before):
            padded_before.append(list_before[i])
        else:
            padded_before.append(set_col_safe(list_after[i], 1, comp_i_value))

        if i < len(list_after):
            padded_after.append(list_after[i])
        else:
            padded_after.append(set_col_safe(list_before[i], 1, comp_i_value))

    return padded_before, padded_after

def pass_judge(fp, fn):
    df = pd.read_csv(fp)
    check_fp_csv = data_dir() / f"{fn}"
    
    V_before = df["Voltage(V)"]
    I_before = df["I_before"]
    V_after  = df["Voltage(V).1"]
    I_after  = df["I_after"]
    
    ratio = I_after / I_before.replace(0, pd.NA)
    ratio = ratio.replace([np.inf, -np.inf], pd.NA)
    df["I_ratio"] = ratio
    df["I_ratio_ok"] = (df["I_ratio"] >= 0.9) & (df["I_ratio"] <= 1.15)
    mask = (V_before >= 5) & (V_before <= 100)
    subset = df[mask]

    # 判斷：資料不足或有 False → fail
    if subset.empty or (subset["I_ratio_ok"] == False).any():
        judge = "fail"
    else:
        judge = "pass"
    check_fp_csv = str(check_fp_csv)+f"_{judge}.csv"
    print(check_fp_csv)
    df.to_csv(check_fp_csv,
              index=False, encoding="utf-8-sig", float_format="%.6g", na_rep="")
    return judge
        
# --------------------------- UI 行為 ---------------------------
def on_before_click():
    global list_before
    list_before = run_internal_staircase()
    total_runs.set(total_runs.get() + 1)
    before_button.config(state=tk.DISABLED)
    after_button.config(state=tk.NORMAL)
    entry.config(state="disabled")
    messagebox.showinfo("micross尚未壓力測試", "請先壓力測試再按確定")

# ### CHANGED: 路徑固定到 exe 同層；傳 comp_i 給 pad_lists；原子寫入 CSV
def on_after_click():

    list_after = run_internal_staircase()

    user_input = entry_var.get().strip()
    now = datetime.now()
    filename = f"{user_input}_{now:%Y%m%d_%H%M%S}"
    csv_filename = f"{user_input}_{now:%Y%m%d_%H%M%S}.csv"
    file_path = data_dir() / csv_filename

    padded_before, padded_after = pad_lists(list_before, list_after, comp_i_value=0.00025)

    tmp = file_path.with_suffix(file_path.suffix + ".tmp")
    with tmp.open(mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Voltage(V)', 'I_before', 'V_before',
                         'Voltage(V)', 'I_after', 'V_after'])
        for a, b in zip(padded_before, padded_after):
            writer.writerow(list(a) + list(b))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, file_path)
    
    check_pass_fail = pass_judge(file_path, filename)
    print(check_pass_fail)

    before_button.config(state=tk.DISABLED)
    after_button.config(state=tk.DISABLED)

    entry.config(state="normal")
    entry.delete(0, tk.END)
    
    messagebox.showinfo("micross已測試", check_pass_fail)

    # 後續輸出也使用固定路徑策略
    # show_and_save_pic(str(file_path), filename+f"_{check_pass_fail}")
    # save_html(str(file_path), filename+f"_{check_pass_fail}")
    print(file_path)

# --------------------------- Tkinter 主視窗 ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    root.title("micross testing")
    root.geometry("400x300")

    tk.Label(root, text="Key in SN:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
    entry_var = tk.StringVar()
    entry_var.trace_add('write', on_input_change)
    entry = tk.Entry(root, textvariable=entry_var, width=30)
    entry.grid(row=0, column=1, padx=10, pady=10)
    
    total_runs = tk.IntVar(value=0)

    # before_button = tk.Button(root, text="before", state=tk.DISABLED, command=on_before_click)
    # before_button.pack(pady=5)
    
    tk.Label(root, text="1. Diode reverse leakage current (before)", font=("Arial", 10)).grid(row=1, column=0, columnspan=2, sticky="w", padx=10)
    before_button = tk.Button(root, text="Test before", state=tk.DISABLED, bg="gray", fg="white", font=("Arial", 12), command=on_before_click)
    before_button.grid(row=2, column=0, columnspan=1, pady=5)
    
    
    tk.Label(root, text="3. Diode reverse leakage current (after)", font=("Arial", 10)).grid(row=3, column=0, columnspan=2, sticky="w", padx=10)
    after_button = tk.Button(root, text="Test after", state=tk.DISABLED, bg="gray", fg="white", font=("Arial", 12), command=on_after_click)
    after_button.grid(row=4, column=0, columnspan=1, pady=5)


    # after_button = tk.Button(root, text="after", state=tk.DISABLED, command=on_after_click)
    # after_button.pack(pady=5)

    # entry.select_clear()
    # plot_frame = tk.Frame(root)
    # plot_frame.pack(fill=tk.BOTH, expand=True)

    root.mainloop()
