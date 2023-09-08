import math
import pandas as pd
import numpy as np
import CoolProp.CoolProp as CP
import matplotlib.pyplot as plt
from pd_class import PDControlSystem

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
'''
# Read the CSV file into a Pandas DataFrame
csv_file_path = "C:\Cambridge\CUSF\Pressurisation\\runplan_csv\\12s boost.csv"

def desired_curves(csvfile):
    """reads csv file of run plan and generates desired tank pressure array"""
    df = pd.read_csv(csvfile)
    data_array = df.values
    reversed_and_swapped = np.flip(data_array, axis=0)
    reversed_and_swapped = np.column_stack((reversed_and_swapped[:, -1], reversed_and_swapped[:, 1:-1], reversed_and_swapped[:, 0]))
    result_array = reversed_and_swapped[:, :-1]  # Remove the final value from each row
    
    test_length = np.sum(result_array[1])
    increments = int(test_length/dt + 1)
    sim_times = np.linspace(0,test_length,increments)

    desired_p2 = np.empty(0)
    
    for i in range(len(result_array)):
        n = int((result_array[1][i])/dt)
        temp_arr = np.ones(n, float)*result_array[0][i]*1E5
        desired_p2 = np.append(desired_p2, temp_arr)
    desired_p2 = np.append(desired_p2, desired_p2[-1])
    
    return desired_p2, sim_times 

p2_target, sim_times = desired_curves(csv_file_path)
arr_length = len(sim_times) 
'''
class flowpath:
    def __init__(self,arr_length, v1, p1, t1, vtank, ull_frac, p2, t2, prop, maxcv, to, tc, controlsys=None):
        self.v1 = v1
        self.p1 = p1
        self.t1 = t1
        self.v2 = vtank * ull_frac
        self.p2 = p2
        self.t2 = t2
        self.prop = prop
        self.maxcv = maxcv
        self.to = to
        self.tc = tc
        self.valve_state = 0 #0 for closed, 1 for closing, 2 for open, 3 for opening
        self.cv = 0 #intially closed
        self.controlsys = controlsys

        #history arrays
        self.p1_his = np.zeros(arr_length, float)
        self.t1_his = np.zeros(arr_length, float)
        self.p2_his = np.zeros(arr_length, float)
        self.t2_his = np.zeros(arr_length, float)
        self.cv_his = np.zeros(arr_length, float)
        return

    def valve_mdot(self):
        """returns mass flow and exit enthalpy"""
        # Constants
        R = 8.314  # Universal gas constant in J/(mol*K)

        sg = M*1000/28.96469
        flow_rate = 3.2331E-8 * self.cv * self.p1 / math.sqrt(sg) #in Nm3/s
        
        normal_rho = CP.PropsSI('D', 'T', 273.15, 'P', 1E5, medium)
        mdot = normal_rho * flow_rate
        t12 = t1 * (self.p2/self.p1)**((gamma-1)/gamma) #valve exit temperature
        h12 = CP.PropsSI('H', 'T', t12, 'P', self.p2, medium)
        
        rho12 = CP.PropsSI('D', 'T', t12, 'P', self.p2, medium)
        qdot12 = mdot/rho12
        vel12 = qdot12 / (math.pi * 0.007**2)
        return mdot, h12, vel12, qdot12

    def prop_qdot(self):
        """returns the propellant volumetric flow rate"""
        if prop == 'LOX':
            bar25_qdot = 0.00755
            return bar25_qdot * (self.p2/(25*100000))** 0.7879
        elif prop == 'IPA':
            bar25_qdot = 0.00925
            return bar25_qdot * (self.p2/(25*100000))** 0.7879
        
    def tank_func1(self):
        """Uses first law to find new p2 and t2 due to added helium"""
        mdot, h12, vel12, qdot12 = self.valve_mdot()

        #find new mass of ullage gas
        rho_tank = CP.PropsSI('D', 'T', self.t2, 'P', self.p2, medium)
        u_tank = CP.PropsSI('U', 'T', self.t2, 'P', self.p2, medium)
        
        m_tank = self.v2 * rho_tank
        U2 = u_tank * m_tank

        m_tank += mdot*dt

        #update rho
        rho_tank = m_tank / self.v2

        #calculate the new internal energy of ullage gas
        Udot = mdot * (h12 + (self.p2 * qdot12) + (vel12**2/2))
        #print('h12: ', h12)
        #print('work: ', (self.p2 * qdot12))
        #print('dynamic: ', (vel12**2/2))
        U2 += Udot*dt
        u2 = U2/ m_tank
        #calculate intermediate p2, t2
        p2 = CP.PropsSI('P', 'D', rho_tank, 'U', u2, medium)
        t2 = CP.PropsSI('T', 'D', rho_tank, 'U', u2, medium)
        return p2, t2

    def tank_func2(self):
        """adjusts p2 and t2 for the increase in ullage size. Adiabatic assumed"""
        p2temp, t2temp = self.tank_func1()
        qdot = self.prop_qdot()
        dv2 = qdot * dt
        self.p2 = p2temp * (self.v2/(dv2+self.v2)) ** gamma #using adiabatic
        self.t2 = t2temp * (self.v2/(dv2+self.v2)) ** (gamma - 1)
        self.v2 += dv2
        return 

    def update_copv(self):
        """p1 and t1 found using adiabatic relations"""
        mdot, h12, vel12, qdot12 = self.valve_mdot()
        rho = CP.PropsSI('D', 'T', self.t1, 'P', self.p1, medium)
        dv1 = mdot * dt/rho
        #print(dv1)

        self.p1 = self.p1 * ((self.v1-dv1)/(self.v1)) ** gamma #using adiabatic
        self.t1 = self.t1 * ((self.v1-dv1)/(self.v1)) ** (gamma - 1)
        return

    def adjust_control_valve(self):
        if self.valve_state == 1: #closing
            self.cv -= dt * self.maxcv/self.tc
            if self.cv <= 0:
                self.cv = 0
                self.state = 0 #valve fully closed
        elif self.valve_state == 3: #opening
            self.cv += dt * self.maxcv/self.to
            if self.cv >= self.maxcv:
                self.cv = self.maxcv
                self.state = 2 #valve fully open
        return
    
    def control_system(self, p2, p2desired):
        if p2 >= p2desired:
            self.state = 1
        else:
            self.state = 3
        return

    def update_arrays(self,i):
        """adds each value to array at index i"""
        self.p1_his[i] = self.p1
        self.t1_his[i] = self.t1
        self.p2_his[i] = self.p2
        self.t2_his[i] = self.t2
        self.cv_his[i] = self.cv
        return
    
'''
    def control_system(self, p2, p2desired):
        self.valve_state = self.controlsys.run_control_system()
'''
'''   
## main program ##
##region
#initialise system (v1, p1, t1, vtank, ull_frac, p2, t2, prop, maxcv, to, tc, controlsys=None)
sys1 = flowpath(arr0.094, 300E5, 300, 0.1, 0.1, 12E5, 300, 'IPA', 0.8, 2, 2)

cs1 = PDControlSystem(1,0,0)
#sys1.cv = sys1.maxcv
#print(sys1.cv)
#print(sys1.valve_mdot())
prev_error = 0
for i in range(arr_length):
    sys1.update_arrays(i)
    sys1.tank_func2()
    sys1.update_copv()
    sys1.control_system(sys1.p2, p2_target[i])
    sys1.adjust_control_valve()

    cs1.run_control_system(p2_target[i],sys1.p2,prev_error, dt)
    prev_error = cs1.calculate_error(p2_target[i],sys1.p2)
    
'''
'''
#endregion

## plotting ##
#region
plt.figure(figsize=(12, 8))

# Plotting the first graph
plt.subplot(2, 2, 1)
plt.plot(sim_times, sys1.p1_his)
plt.title('P1')

# Plotting the second graph
plt.subplot(2, 2, 2)
plt.plot(sim_times, sys1.t1_his)
plt.title('T1')

# Plotting the third graph
plt.subplot(2, 2, 3)
plt.plot(sim_times, sys1.p2_his)
plt.title('P2')

# Plotting the fourth graph
plt.subplot(2, 2, 4)
plt.plot(sim_times, sys1.t2_his)
plt.title('T2')

plt.tight_layout()  # To prevent overlapping of subplots
plt.show()
#endregion
'''