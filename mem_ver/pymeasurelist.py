from pymeasure.instruments.keithley import Keithley2400
from pymeasure.experiment import Procedure, Results, IntegerParameter, FloatParameter
from pymeasure.experiment import unique_filename
import numpy as np
import time
import pandas as pd
 
class Keithley2410_TwoStepSweep(Procedure):
    compliance_current = FloatParameter("Compliance Current (A)", default=0.01, minimum=1e-6, maximum=1.05)
    source_delay = FloatParameter("Source Delay (s)", default=0.1, minimum=0, maximum=10)
    
    DATA_COLUMNS = ['Set_V', 'Meas_V', 'Meas_I']
 
    def startup(self):
        # 建立儀器連線（請改成你的 GPIB 或 RS232 位址）
        self.smu = Keithley2400("GPIB0::22::INSTR")   # 改這裡！！！
        # 如果用 RS-232： "ASRL3::INSTR" 或 "ASRL/dev/ttyUSB0::INSTR"
        
        self.smu.reset()
        self.smu.clear()
        self.smu.use_front_terminals()
        self.smu.apply_voltage()
        self.smu.compliance_current = self.compliance_current
        self.smu.source_voltage_range = 1100      # 2410 最大 1100V
        self.smu.measure_current()
        self.smu.write("SENS:CURR:RANG:AUTO OFF")
        self.smu.nplc = 1
        self.smu.source_delay = self.source_delay
        
        # 同時測 V 與 I，並存到 buffer
        self.smu.enable_concurrent_measurements()
        self.smu.write(":FORM:ELEM VOLT,CURR")
        
        # 設定 buffer 100 點（遠大於 44）
        self.smu.write(":TRAC:POIN 100")
        self.smu.write(":TRAC:FEED SENS")
        self.smu.write(":TRAC:FEED:CONT NEXT")
        self.smu.write(":TRAC:CLE")
 
    def execute(self):
        # 產生兩段電壓序列
        v_coarse = np.arange(10, 91, 10)     # 10~90V, step 10V → 9 點
        v_fine   = np.arange(91, 126, 1)     # 91~125V, step 1V → 35 點
        voltage_list = np.concatenate([v_coarse, v_fine])   # 總共 44 點
        
        self.log(f"開始兩段掃描，共 {len(voltage_list)} 點")
        
        # 建立 list sweep
        volt_str = ",".join(f"{v:.6f}" for v in voltage_list)
        self.smu.write(f":SOUR:LIST:VOLT {volt_str}")
        self.smu.write(":SOUR:VOLT:MODE LIST")
        self.smu.write(f":TRIG:COUN {len(voltage_list)}")
        
        # 開啟輸出並開始掃描
        self.smu.enable_source()
        time.sleep(0.5)
        self.smu.write(":INIT")
        
        # 等待完成（*OPC? 或檢查 buffer 填滿）
        self.smu.wait_for_completion()
        
        # 讀取全部資料（一次讀完）
        n = int(self.smu.query(":TRAC:POIN:ACT?"))
        raw = self.smu.query(f":TRAC:DATA? 1,{n}").strip()
        
        # 解析
        data = [float(x) for x in raw.split(",")]
        meas_v = data[0::2]
        meas_i = data[1::2]
        
        # 關輸出
        self.smu.shutdown()
        
        # 輸出到 pymeasure 的 data
        for i, v_set in enumerate(voltage_list):
            self.emit('results', {
                'Set_V': v_set,
                'Meas_V': meas_v[i],
                'Meas_I': meas_i[i]
            })
            # 即時顯示
            if (i+1) % 5 == 0 or i == len(voltage_list)-1:
                self.log(f"已完成 {i+1}/{len(voltage_list)} 點 → {v_set:.1f}V, {meas_i[i]:.6e}A")
 
    def shutdown(self):
        try:
            self.smu.shutdown()
        except:
            pass
 
# ====================== 直接執行範例 ======================
if __name__ == "__main__":
    procedure = Keithley2410_TwoStepSweep()
    procedure.compliance_current = 0.00025   # 10mA，可自行改
    procedure.source_delay = 0.1
    
    # 自動產生資料夾與檔案名稱
    filename = unique_filename("data", prefix="K2410_TwoStep")
    results = Results(procedure, filename)
    
    print("開始測量，請稍候...")
    procedure.startup()
    # while not procedure.is_completed():
    #     time.sleep(0.5)
    
    # 存成 CSV（超漂亮的格式）
    df = pd.read_csv(results.data_filename)
    print(df)
    print(f"\n資料已存檔：{results.data_filename}.csv")