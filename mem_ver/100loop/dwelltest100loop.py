import csv
import time
import sys
from datetime import datetime
from pymeasure.instruments.keithley import Keithley2400
import pandas as pd
import tkinter as tk
import os
from tkinter import messagebox

import numpy as np
import plotly.graph_objects as go
import math
from pathlib import Path

def run_internal_staircase(addr="GPIB0::22::INSTR", start_v=1, stop_v=125, step=1, dwell_s=0.01, nplc=0.1,fscan=0):
    with Keithley2400(addr) as smu:
        
        start_time = time.time()
        points = int(math.floor((stop_v - start_v) / step) + 1)
        smu.reset()
        smu.adapter.connection.timeout = 60000
        if fscan==0:
            smu.write("*RST")
            smu.adapter.connection.timeout = 60000
            smu.write("*CLS")
            smu.use_front_terminals()
            smu.apply_voltage(voltage_range=21, compliance_current=0.00025)
            smu.auto_zero = True
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
            smu.write(f"TRAC:POIN {points}")
            smu.write("TRAC:FEED SENS")
            smu.write("TRAC:FEED:CONT NEXT")
            smu.write(f"TRIG:COUN {points}")
            smu.write("TRIG:SOUR IMM")
            smu.write("*SAV 2")
        else:
            smu.write("*RCL 2")
            smu.write("TRAC:CLE")
            # smu.write(f"TRAC:POIN {points}")
            smu.write("TRAC:FEED SENS")
            smu.write("TRAC:FEED:CONT NEXT")
            # smu.write(f"TRIG:COUN {points}")
            # smu.write("TRIG:SOUR IMM")
            
            
        smu.enable_source()
        smu.write("INIT")
        smu.ask("*OPC?")                         # 等掃描完成
        raw = smu.ask("TRAC:DATA?")              # 一次讀回 V,I
        smu.write("OUTP OFF")
        
        vals = [float(x) for x in raw.strip().split(",") if x]
        V = vals[0::2]
        I = vals[1::2]
        V_cmd = [start_v + i * step for i in range(points)]
        # 組成 DataFrame
        df = pd.DataFrame({
            "V_cmd": V_cmd,
            "I_meas": I,
            "V_meas": V,
        })
        
        end_time = time.time()
        function_time = end_time - start_time
        print(f"cost time: {function_time:.2f} s")
    return df.values.tolist()
    
    
def repeat_tests_and_save_multiple_csv():
    # dwell_values = [round(x, 2) for x in [0.01 * i for i in range(1, 11)]]

    # for dwell in dwell_values:
    #     print(f"Running tests for dwell_s = {dwell}")
    dwell=0.01
    for run_idx in range(50):  # 每個 dwell_s 做 10 組測試
        print(f"  Test pair {run_idx+1}/10")
        # 第一次測試
        df1 = run_internal_staircase(dwell_s=dwell, fscan=run_idx)
        df1 = pd.DataFrame(df1, columns=["V_cmd", "I_meas", "V_meas"])

        # 第二次測試
        df2 = run_internal_staircase(dwell_s=dwell, fscan=run_idx)
        df2 = pd.DataFrame(df2, columns=["V_cmd", "I_meas", "V_meas"])

        # 計算比值
        ratio = df2["I_meas"] / df1["I_meas"]

        # 合併 df1 和 df2 並加上 ratio
        merged_df = pd.DataFrame({
            "V_cmd": df1["V_cmd"],
            "I_meas_1": df1["I_meas"],
            "V_meas_1": df1["V_meas"],
            "I_meas_2": df2["I_meas"],
            "V_meas_2": df2["V_meas"],
            "ratio_I2_I1": ratio
        })
        filename = f"dwell_{dwell:.2f}_0{run_idx}_NPLC0.1.csv"
        merged_df.to_csv(filename, index=False)
        print(f"已存檔：{filename}")

# 呼叫主函式
repeat_tests_and_save_multiple_csv()
