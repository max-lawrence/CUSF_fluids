import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pd_class import PDControlSystem
from control_system_tester import flowpath
from ttkthemes import ThemedTk
from PIL import Image, ImageTk

csv_file_path = "C:\Cambridge\CUSF\Pressurisation\\runplan_csv\\controltest1.csv"
## variables ##
#region
#simulation variables
dt = 0.01
'''
#HELIUM PROPERTIES
medium = 'Helium'
gamma = 1.66
M = 0.004
R = 8.31
'''
medium = 'Nitrogen'
gamma = 1.4
M = 0.028
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

class PIDControllerSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("WGTS Pressurisation System PID Controller Simulator")
        self.root.geometry("1000x600")  # Set window size
        self.current_theme = tk.StringVar(value="scidgrey")

        self.kp_value = tk.DoubleVar(value=1.0)
        self.kd_value = tk.DoubleVar(value=0.1)
        self.cv_value = tk.DoubleVar(value=0.5)
        self.opening_time_value = tk.DoubleVar(value=1.0)
        self.closing_time_value = tk.DoubleVar(value=1.0)
        self.p1_value = tk.DoubleVar(value=30000000)
        self.t1_value = tk.DoubleVar(value=300)
        self.v1_value = tk.DoubleVar(value=0.094)

        self.custom_style = ttk.Style()
        self.custom_style.configure(".", font=("TkDefaultFont", 16))

        self.create_widgets()

    def desired_curves(self):
        """reads csv file of run plan and generates desired tank pressure array"""
        df = pd.read_csv(self.csv)
        data_array = df.values
        reversed_and_swapped = data_array
        #reversed_and_swapped = np.flip(data_array, axis=0)
        reversed_and_swapped = np.column_stack((reversed_and_swapped[:, -1], reversed_and_swapped[:, 1:-1], reversed_and_swapped[:, 0]))
        result_array = reversed_and_swapped[:, :-1]  # Remove the final value from each row
        print(result_array)
        test_length = 0
        for i,j in result_array:
            test_length += i
        #print(test_length)
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
    
    def create_widgets(self):
        self.root.configure(bg="white")  # Set background color

        self.theme_frame = ttk.LabelFrame(self.root, text="Select Theme")
        self.theme_combobox = ttk.Combobox(self.theme_frame, values=ttk.Style().theme_names(), textvariable=self.current_theme)
        self.theme_combobox.bind("<<ComboboxSelected>>", self.change_theme)
        self.theme_combobox.pack(padx=10, pady=10)

        self.kp_frame = ttk.Frame(self.root, padding=20)
        self.kd_frame = ttk.Frame(self.root, padding=20)

        self.kp_label = ttk.Label(self.kp_frame, text="Enter KP:")
        self.kp_entry = ttk.Entry(self.kp_frame, textvariable=self.kp_value)

        self.kd_label = ttk.Label(self.kd_frame, text="Enter KD:")
        self.kd_entry = ttk.Entry(self.kd_frame, textvariable=self.kd_value)

        self.kp_label.pack(pady=5)
        self.kp_entry.pack(pady=5)

        self.kd_label.pack(pady=5)
        self.kd_entry.pack(pady=5)

        self.figure, self.ax = plt.subplots(3, 2, figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack(pady=20, padx=20, anchor="w")

        self.root.style = ttk.Style()
        self.root.style.configure("Black.TButton",
            background="black", foreground="white", borderwidth=2, relief="solid", font = ('TkDefaultFont', 16))

        self.root.style.configure("TLabelframe", background="light blue")
        self.root.style.configure("TLabelframe.Label", background="light blue")

        self.image = Image.open("fluxus_logo.jpg")  # Replace with the actual image path
        self.image = self.image.resize((200, 200), Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(self.image)
        self.image_label = ttk.Label(self.root, image=self.image)
        self.image_label.pack(padx=20, pady=20, anchor="n")

        self.button_frame = ttk.Frame(self.root)
        self.choose_file_button = ttk.Button(self.button_frame, text="Choose File", command=self.choose_file, style="Black.TButton")
        self.run_button = tk.Button(root, bg='light blue',fg='#000000',relief='flat',text='Run',width=20,command=self.run_simulation)
        self.choose_file_button.pack(pady=10)
        self.run_button.pack(pady=10)
        self.button_frame.pack(padx=20, pady=20, anchor="n")

        self.inputs_frame = ttk.Frame(self.root)
        cv_label = ttk.Label(self.inputs_frame, text="CV:")
        opening_time_label = ttk.Label(self.inputs_frame, text="Opening Time (s):")
        closing_time_label = ttk.Label(self.inputs_frame, text="Closing Time (s):")

        cv_entry = ttk.Entry(self.inputs_frame, textvariable=self.cv_value)
        opening_time_entry = ttk.Entry(self.inputs_frame, textvariable=self.opening_time_value)
        closing_time_entry = ttk.Entry(self.inputs_frame, textvariable=self.closing_time_value)

        p1_label = ttk.Label(self.inputs_frame, text="P1:", font=('TkDefaultFont', 16))
        t1_label = ttk.Label(self.inputs_frame, text="T1:", font=('TkDefaultFont', 16))
        v1_label = ttk.Label(self.inputs_frame, text="V1:", font=('TkDefaultFont', 16))

        p1_entry = ttk.Entry(self.inputs_frame, textvariable=self.p1_value, font=('TkDefaultFont', 16))
        t1_entry = ttk.Entry(self.inputs_frame, textvariable=self.t1_value, font=('TkDefaultFont', 16))
        v1_entry = ttk.Entry(self.inputs_frame, textvariable=self.v1_value, font=('TkDefaultFont', 16))

        cv_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        opening_time_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        closing_time_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")

        cv_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        opening_time_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        closing_time_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        p1_label.grid(row=0, column=2, padx=10, pady=5, sticky="e")
        t1_label.grid(row=1, column=2, padx=10, pady=5, sticky="e")
        v1_label.grid(row=2, column=2, padx=10, pady=5, sticky="e")

        p1_entry.grid(row=0, column=3, padx=10, pady=5, sticky="w")
        t1_entry.grid(row=1, column=3, padx=10, pady=5, sticky="w")
        v1_entry.grid(row=2, column=3, padx=10, pady=5, sticky="w")

        self.inputs_frame.pack(padx=20, pady=20, anchor="n")

        self.theme_frame.pack(padx=20, pady=10, fill="both", anchor="w")
        self.kp_frame.pack(padx=20, pady=10, fill="both", anchor="w")
        self.kd_frame.pack(padx=20, pady=10, fill="both", anchor="w")

        self.canvas.get_tk_widget().pack(side="left", padx=20, pady=20, anchor="n")        

    def change_theme(self, event):
        selected_theme = self.current_theme.get()
        self.root.set_theme(selected_theme)

    def choose_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.csv = file_path

    def run_simulation(self):
        p2_target, sim_times, arr_length = self.desired_curves()
        arr_length = len(sim_times)
        
        kp = self.kp_value.get()
        kd = self.kd_value.get()
        p1 = self.p1_value.get()
        t1 = self.t1_value.get()
        v1 = self.v1_value.get()
        cv = self.cv_value.get()
        to = self.opening_time_value.get()
        tc = self.closing_time_value.get()

        cs1 = PDControlSystem(kp,kd,0)
        sys1 = flowpath(arr_length, v1, p1, t1, 0.1, 0.1, 20E5, 300, 'IPA', cv, to, tc)

        # Replace with your simulation logic
        print('button pressed and kp and kd values are:', cs1.kp, cs1.kd)
        prev_error = 0
        count = 10
        for i in range(arr_length):
            sys1.update_arrays(i)
            sys1.tank_func2()
            sys1.update_copv()
            #sys1.control_system(sys1.p2, p2_target[i])
            sys1.adjust_control_valve()

            if count != 10:
                count += 1
            else:
                count = 0
                sys1.valve_state = cs1.run_control_system(p2_target[i],sys1.p2,prev_error, dt)
   
            prev_error = cs1.calculate_error(p2_target[i],sys1.p2)
        
        
        #sim_times = self.data['Time']
        p1 = sys1.p1_his
        t1 = sys1.t1_his
        p2 = sys1.p2_his
        t2 = sys1.t2_his
        cv = sys1.cv_his

        for ax_row, y_data_row, y_label_row in zip(self.ax, [[p1, t1], [p2, t2], [cv]], [["P1", "T1"], ["P2", "T2"], ["CV"]]):
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
    root = ThemedTk(theme="arc")
    app = PIDControllerSimulator(root)
    root.mainloop()
