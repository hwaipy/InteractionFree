from Instrument.WaveformGenerator.USTCDAC.da_board import *
import filecmp
from Instrument.WaveformGenerator.USTCDAC.data_waves import *
import matplotlib.pyplot as plt

new_ip = '172.16.60.199'
da = DABoard(id=new_ip, ip=new_ip, port=40230, batch_mode=False)
board_status = da.connect()
# da.Run_Command(26,0,0)
# da.Init()
# da.InitBoard()
# da.ClearTrigCount()
# time.sleep(1)
da.set_loop(1, 1, 1, 1)
# da.SetGain(3, 123)
# rd_data = da.Read_RAM(0,1024)
# print(rd_data)
# wave = range(0,65536)#[1,2,3,1111,2222,2222]
# print(len(wave))

# da.Write_RAM(0,wave)
# da.StartStop(240)
# da.SetDefaultVolt(1,0)
# da.SetDefaultVolt(2,15000)
# da.SetDefaultVolt(3,30000)
# da.SetDefaultVolt(4,60000)
da_ctrl = waveform()
# da_ctrl.generate_seq()
freq = 5e6
step = int(2e9 / freq)
print(step)
da_ctrl.generate_sin(repeat=8, cycle_count=step)
# da_ctrl.generate_trig_seq()
da_ctrl.generate_seq()
# da_ctrl.generate_trig_seq(loopcnt=1024)
# print(len(da_ctrl.seq))
# print(len(da_ctrl.wave))
# print("wave")

# plt.figure()
# plt.plot(da_ctrl.wave)
# plt.show()
# print(len(da_ctrl.wave))
# cnt = 0

da.set_multi_board(0)
# for i in range(100):
da.stop_output_wave(1)
da.stop_output_wave(2)
da.stop_output_wave(3)
da.stop_output_wave(4)
da.write_seq_fast(1, seq=da_ctrl.seq)
da.write_wave_fast(1, wave=da_ctrl.wave)
da.write_seq_fast(2, seq=da_ctrl.seq)
da.write_wave_fast(2, wave=da_ctrl.wave)
da.write_seq_fast(3, seq=da_ctrl.seq)
da.write_wave_fast(3, wave=da_ctrl.wave)
da.write_seq_fast(4, seq=da_ctrl.seq)
da.write_wave_fast(4, wave=da_ctrl.wave)
# cnt += 1

da.start_output_wave(1)
da.start_output_wave(2)
da.start_output_wave(3)
da.start_output_wave(4)
da.set_trig_count_l1(100000)
da.set_trig_interval_l1(200e-6)
da.set_trig_select(1)
da.send_int_trig()
time.sleep(2)

# da.StartStop(240)
da.disconnect()
if board_status < 0:
    print('Failed to find board')
