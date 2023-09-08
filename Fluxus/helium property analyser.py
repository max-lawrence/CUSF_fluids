import CoolProp.CoolProp as CP

internal_energy = 800000  # Internal energy in J/kg
density = 10  # Density in kg/m³
fluid = 'Helium'  # Fluid identity (e.g., 'Air', 'Water', 'CO2', etc.)

# Since we need more than two independent properties to solve for pressure and temperature,
# let's calculate pressure and temperature for a specific value of entropy (S) as well.
entropy = 2000  # Entropy in J/(kg·K)

pressure = CP.PropsSI('P', 'D', density, 'U', internal_energy, fluid)
temperature = CP.PropsSI('T', 'D', density, 'U', internal_energy, fluid)
calculated_entropy = CP.PropsSI('S', 'D', density, 'U', internal_energy, fluid)

print(f"Pressure: {pressure} Pa")
print(f"Temperature: {temperature} K")
print(f"Calculated Entropy: {calculated_entropy} J/(kg·K)")
