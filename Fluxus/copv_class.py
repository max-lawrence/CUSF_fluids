import math
import CoolProp.CoolProp as CP

class copv:
    def __innit__(self, volume, pressure, temperature, downstreamconnection = None):
        """vol in litres, pressure in bar, temperature in K"""
        self.vol = volume /1000 #m^3
        self.pressure = pressure * 1E5 #Pa
        self.temp = temperature
        self.medium = None
        self.gamma = 0
        self.M = 0 #molecular mass

        self.downstream_connection = downstreamconnection
        return
    
    def assign_downstream_connection(self):
        """Assigns valve to copv, currently can only have one at a time"""
        connection = input("Enter valve name: ")
        self.downstream_connection = connection
        return
    
    def assign_fluid(self):
        """Assigns fluid to valve and finds the gamma and M of fluid"""
        while True:
            fluid_name = input("Enter a valid fluid name: ")
            if CP.AbstractState.has_fundamental_parameter("FLUID", fluid_name):
                self.medium = fluid_name
                self.gamma = self.calculate_isentropic_expansion_coefficient(fluid_name)
                self.M = CP.PropsSI("MOLAR_MASS", fluid_name)
                return
            else:
                print("Error: Invalid fluid name. Please enter a valid fluid name.")

    def update_tank(self, dt):
        """flow rate is in Nm3/s"""
        valve = self.downstream_connection
        if valve == None:
            print("no valve assigned")
            return
        flow_rate_Nm3s = valve.calculate_flow_rate(self.pressure, self.temp) #would be more complicated if valve not choked
        valve.normal_flow_rate = flow_rate_Nm3s
        valve.pi = self.pressure
        valve.ti = self.temp
        flow_rate = flow_rate_Nm3s * (1E5/self.pressure) * (self.temp/273.15) #in m^3/s

        lostvol = flow_rate * dt
        self.pressure = self.pressure * (lostvol/self.vol) ** self.gamma #using adiabatic
        self.temp = self.temp * (lostvol/self.vol) ** self.gamma
        return

