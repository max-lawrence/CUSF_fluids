import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pd_class import PDControlSystem
from control_system_tester import flowpath

csv_file_path = "C:\Cambridge\CUSF\Pressurisation\\runplan_csv\\controltest1.csv"
## variables ##
#region
#simulation variables
dt = 0.1

#HELIUM PROPERTIES
medium = 'Helium'
gamma = 1.66
M = 0.004
R = 8.31

#copv
v1 = 0.08
p1 = 300E5
t1 = 300

vtank = 0.8
ull_frac = 0.1

#tank
v2 = vtank * ull_frac
p2 = 25E5
t2 = 160
prop = 'IPA'

#valve variables
maxcv = 0.8
to = 2 #open time
tc = 2 #close time
cv = 0 #current valve cv
state = 1 #1 for closed, 2 for closing, 3 for open, 4 for opening
#endregion

def desired_curves(csvfile):
    """reads csv file of run plan and generates desired tank pressure array"""
    df = pd.read_csv(csvfile)
    data_array = df.values
    reversed_and_swapped = np.flip(data_array, axis=0)
    reversed_and_swapped = np.column_stack((reversed_and_swapped[:, -1], reversed_and_swapped[:, 1:-1], reversed_and_swapped[:, 0]))
    result_array = reversed_and_swapped[:, :-1]  # Remove the final value from each row
    
    test_length = 0
    for i,j in result_array:
        test_length += i
    print(test_length)
    #test_length = np.sum(result_array[1])
    increments = int(test_length/dt + 1)
    sim_times = np.linspace(0,test_length,increments)

    desired_p2 = np.empty(0)
    for i in range(len(result_array)):
        n = int((result_array[i][0])/dt)
        temp_arr = np.ones(n, float)*result_array[i][1]*1E5
        desired_p2 = np.append(desired_p2, temp_arr)
    desired_p2 = np.append(desired_p2, desired_p2[-1])
    arr_length = len(sim_times)
    
    return desired_p2, sim_times, arr_length 

p2_target, sim_times, arr_length = desired_curves(csv_file_path)
arr_length = len(sim_times)

class PIDControllerSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("WGTS Pressurisation System PID Controller Simulator")
        
        self.kp_value = tk.DoubleVar(value=1.0)
        self.kd_value = tk.DoubleVar(value=0.1)
        
        self.create_widgets()
        
    def create_widgets(self):
        style = ttk.Style()
        style.configure("TScale", background="white", troughcolor="gray")
        
        kp_label = tk.Label(self.root, text="KP:")
        kp_slider = ttk.Scale(self.root, from_=0, to=2, orient="horizontal", variable=self.kp_value, style="TScale")
        kp_value_label = tk.Label(self.root, textvariable=self.kp_value)

        kd_label = tk.Label(self.root, text="KD:")
        kd_slider = ttk.Scale(self.root, from_=0, to=1, orient="horizontal", variable=self.kd_value, style="TScale")
        kd_value_label = tk.Label(self.root, textvariable=self.kd_value)

        choose_file_button = tk.Button(self.root, text="Choose File", command=self.choose_file)
        run_button = tk.Button(self.root, text="Run", command=self.run_simulation)

        kp_label.pack()
        kp_slider.pack(fill="x", padx=10)
        kp_value_label.pack()

        kd_label.pack()
        kd_slider.pack(fill="x", padx=10)
        kd_value_label.pack()

        choose_file_button.pack()
        run_button.pack()

        self.figure, self.ax = plt.subplots(2, 2, figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack()

    def choose_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.csv = file_path

    def run_simulation(self):
        kp = self.kp_value.get()
        kd = self.kd_value.get()

        cs1 = PDControlSystem(kp,kd,0)
        sys1 = flowpath(arr_length, 0.094, 300E5, 300, 0.1, 0.1, 12E5, 300, 'IPA', 0.8, 2, 2)

        # Replace with your simulation logic
        print('button pressed and kp and kd values are:', cs1.kp, cs1.kd)
        prev_error = 0
        for i in range(arr_length):
            sys1.update_arrays(i)
            sys1.tank_func2()
            sys1.update_copv()
            #sys1.control_system(sys1.p2, p2_target[i])
            sys1.adjust_control_valve()

            sys1.valve_state = cs1.run_control_system(p2_target[i],sys1.p2,prev_error, dt)
            prev_error = cs1.calculate_error(p2_target[i],sys1.p2)
        
        
            #sim_times = self.data['Time']
            p1 = sys1.p1_his
            t1 = sys1.t1_his
            p2 = sys1.p2_his
            t2 = sys1.t2_his

        for ax_row, y_data_row, y_label_row in zip(self.ax, [[p1, t1], [p2, t2]], [["P1", "T1"], ["P2", "T2"]]):
            for ax, y_data, y_label in zip(ax_row, y_data_row, y_label_row) :
                ax.clear()
                ax.plot(sim_times, y_data)
                ax.set_xlabel('Time')
                ax.set_ylabel(y_label)
                #print(ax)
        
        self.canvas.draw()

            
        '''
        self.ax.clear()
        self.ax.plot(time, output, label=f"KP = {kp}, KD = {kd}")
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Output')
        self.ax.legend()
        self.canvas.draw()
        '''

if __name__ == "__main__":
    root = tk.Tk()
    app = PIDControllerSimulator(root)
    root.mainloop()
