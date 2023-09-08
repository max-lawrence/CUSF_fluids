import math
import CoolProp.CoolProp as CP

class control_valve:

    def __innit__(self, maxcv, mincv, to, tc, upstreamconnection = None, downstreamconnection = None, eseod = None):
        self.maxcv = maxcv
        self.mincv = mincv
        self.to = to #opening time
        self.tc = tc #closing time
        self.eseod = eseod
        self.ofraction = 0 #closed initially
        self.cv = mincv #as closed initially
        
        self.medium = None
        self.gamma = 0
        self.M = 0 #molecular mass
        self.state = 0 #0 closed, 1 closing, 2 open, 3 opening
        
        self.upstream_connection = upstreamconnection
        self.downstream_connection = downstreamconnection
        
        self.pi = 0
        self.po = 0
        self.ti = 0
        self.to = 0

        self.normal_flow_rate = 0
        self.mdot = 0
        self.hi = 0
        self.ho = 0

        self.valvetemp = None
        
        if self.eseod != None:
            self.mincv = 0
            #add a conversion from eseod to cv
        return
    
    def calculate_isentropic_expansion_coefficient(fluid_name, temperature=273, pressure=1E5):
        try:
            isentropic_expansion_coeff = CP.isentropic_expansion_coefficient(fluid_name, "T", temperature, "P", pressure)
            return isentropic_expansion_coeff
        except ValueError:
            print("Error: Invalid input values.")
            return None
    
    def assign_downstream_connection(self):
        """Assigns tank to valve, currently can only have one at a time"""
        connection = input("Enter tank name: ")
        self.downstream_connection = connection
        return 
    
    def assign_upstream_connection(self):
        """Assigns copv to valve, currently can only have one at a time"""
        connection = input("Enter tank name: ")
        self.downstream_connection = connection
        connection.upstream_connection = self
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
    
    def calculate_flow_rate(self): #valid for choked flow condition
        """returns flow rate through valves in Nm3/s"""
        # Constants
        R = 8.314  # Universal gas constant in J/(mol*K)

        sg = self.M/28.96469
        flow_rate = 3.2331E-8 * self.cv * (self.upstream_connection).pressure / math.sqrt(sg) #in Nm

        return flow_rate    
    
    def openclose(self,dt):
        if self.state == 1: #closing
            self.cv -= dt * (self.maxcv - self.mincv)/self.tc
            if self.cv <= self.mincv:
                self.cv = self.mincv
                self.state = 0 #valve fully closed
        elif self.state == 3: #opening
            self.cv += dt * (self.maxcv - self.mincv)/self.to
            if self.cv >= self.maxcv:
                self.cv = self.maxcv
                self.state = 2
        return

    def update_mass_flow_rate(self):
        normal_rho = CP.PropsSI('D', 'T', 273.15, 'P', 1E5, self.medium)
        self.mdot = normal_rho * self.calculate_flow_rate()

    def update_ho(self):
        pd = (self.downstream_connection).pressure
        pu = self.pressure_upstream







