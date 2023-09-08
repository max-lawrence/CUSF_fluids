import math
import CoolProp.CoolProp as CP

class tank:
    def __innit__(self, volume, u_pressure, u_temperature, u_frac, upstreamconnection, f_temperature = None):
        """vol in litres, pressure in bar, temperature in K, ullsge_frac in decimal"""
        self.vol = volume /1000 #m^3
        self.pressure = u_pressure * 1E5 #Pa
        self.temp = u_temperature
        self.ullage = u_frac * self.vol
        self.propvol = self.vol - self.ullage
        self.prop = None

        self.upstream_connection = upstreamconnection
        self.downstream_connection = None  

        self.medium = (self.upstreamconnection).medium
        self.gamma = (self.upstreamconnection).gamma
        self.M = (self.upstreamconnection).M


        return
    
    def assign_prop(self):
        """Assigns fluid to valve and finds the gamma and M of fluid"""
        while True:
            fluid_name = input("Enter either IPA or LOX name: ")
            if fluid_name == 'IPA' or fluid_name == 'LOX':
                self.prop = fluid_name
                return
            else:
                print("Error: Invalid propellant fluid. Please enter a valid fluid name.")

    def update_tank(self, dt):
        """flow rate is in Nm3/s"""
        valve = self.upstream_connection
        flow_rate_Nm3s = valve.calculate_flow_rate(self.pressure, self.temp) #would be more complicated if valve not choked
        flow_rate = flow_rate_Nm3s * (1E5/self.pressure) * (self.temp/273.15) #in m^3/s

        lostvol = flow_rate * dt
        self.pressure = self.pressure * (lostvol/self.vol) ** self.gamma #using adiabatic
        self.temp = self.temp * (lostvol/self.vol) ** self.gamma

    def prop_flow_rate(self):
        """calculates the flow rate through the main valves"""
        if self.prop == 'LOX':
            bar25_qdot = 0.00755
            return bar25_qdot * (self.pressure/(25*100000))** 0.7879
        elif self.prop == 'IPA':
            bar25_qdot = 0.00925
            return bar25_qdot * (self.pressure/(25*100000))** 0.7879
        else:
            print('Invalid propellant fluid')
            return 0
    
    def update_prop_ullage_vol(self, dt):
        #step calculate mass flow of gas in
        mdot = (self.upstream_connection).up
        R = 8.314  # Ideal gas constant in J/(mol*K)
        volchange = self.prop_flow_rate() * dt
        self.propvol -= volchange
        self.ullage += volchange


        return
    

