import pyvisa
import time
 
# ==================== 請修改這裡的GPIB位址 ====================
GPIB_ADDR = "GPIB0::22::INSTR"   # 改成你的Keithley 2410 GPIB位址
# ===========================================================
 
rm = pyvisa.ResourceManager()
keithley = rm.open_resource(GPIB_ADDR)
keithley.timeout = 60000
keithley.clear()
 
# 基本設定
keithley.write("*RST")
keithley.write("*CLS")
keithley.write(":SYST:AZER:STAT OFF")                # 加快測量速度
keithley.write(":SOUR:FUNC VOLT")
keithley.write(":SOUR:VOLT:RANG 200")                # 200V範圍(2410最大1100V，125V用200V範圍最準)
keithley.write(":SOUR:CURR:PROT 0.01")               # 電流compliance 10mA (請根據你的DUT調整，必要時改成0.001(1mA)或0.05(50mA)
keithley.write(":SENS:FUNC:CONC ON")                # 同時測V與I
keithley.write(":SENS:CURR:RANG:AUTO ON")            # 電流自動量程
keithley.write(":SENS:CURR:NPLC 1")                 # 可改成0.1~10，1是標準
keithley.write(":FORM:ELEM VOLT,CURR")              # buffer只存電壓與電流
keithley.write(":TRAC:POIN 100")                    # buffer大小設100(大於44)
keithley.write(":TRAC:FEED SENS")
keithley.write(":TRAC:FEED:CONT NEXT")
keithley.write(":TRAC:CLE")                          # 清buffer
 
# 產生連續的電壓list (10~90 step10 + 91~125 step1)
v1 = range(10,91,10)          # 10,20,...,90
v2 = range(91,126,1)          # 91~125
volt_list = list(v1) + list(v2)
volt_str = ','.join([str(v) for v in volt_list])
 
print("總點數:", len(volt_list))    # 應顯示44
 
# 設定list sweep
keithley.write(f":SOUR:LIST:VOLT {volt_str}")
keithley.write(":SOUR:VOLT:MODE LIST")
keithley.write(":TRIG:COUN 44")           # 觸發44次
keithley.write(":SOUR:DEL 0.1")         # 每次source後延遲0.1秒(可根據需要調整)
 
# 開始掃描
keithley.write(":OUTP ON")
keithley.write(":INIT")
print("開始掃描，請等待...")
time.sleep(0.5)            # 給點時間讓儀器開始
 
# 等待掃描完成(用*OPC?是最穩的方式)
while int(keithley.query("*OPC?")) == 0:
    time.sleep(0.1)
 
keithley.write(":OUTP OFF")
 
# 讀取全部資料(一次讀完)
n = int(keithley.ask(":TRAC:POIN:ACT?"))   # 實際儲存點數
data_str = keithley.ask(f":TRAC:DATA? 1,{n}")
keithley.close()
 
# 解析資料
data = [float(x) for x in data_str.split(',') if x.strip()]
 
V_meas = data[0::2]   # 測得的電壓
I_meas = data[1::2]   # 測得的電流
 
# 印出結果(或存檔)
print("\n第 i\t設定電壓\t測量電壓\t測量電流")
for i in range(len(V_meas)):
    print(f"{i+1:3d}\t{volt_list[i]:6.1f}V\t{V_meas[i]:.6f}V\t{I_meas[i]:.6f}A")
 
# 如果要存成csv
# import pandas as pd
# df = pd.DataFrame({
#     'Set_V': volt_list,
#     'Meas_V': V_meas,
#     'Meas_I': I_meas
# })
# df.to_csv("IV_sweep_10-125V.csv", index=False)
# print("\n已存檔IV_sweep_10-125.csv")