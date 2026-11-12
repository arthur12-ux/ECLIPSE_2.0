"""
Collection of power cable subelement models.
"""

import numpy as np
import math
from scipy.optimize import fsolve


class SurfacePowerCable:
    """
    The surface power cable model calculates the mass of the conductors, dielectric insulator(s), emi shielding, 
    and reels to store the cable. The model sizes everything for each voltage in an input list, and selects the voltage 
    that results in the lowest total mass. It is sized using thermal assumptions for the lunar South Pole and ASTM 
    standards for copper wires on Earth.

    Sources:
    [1] Gordon, L. B., "Electrical Transmission on the Lunar Surface: Part 1 - DC Transmission," NASA/CR—2001-210759, 2001.
    [2] https://ntrs.nasa.gov/api/citations/20120003745/downloads/20120003745.pdf
    [3] Middleton, W. M., "Reference Data for Engineers: Radio, Electronics, Computer and Communications," 9th ed., Butterworth-Heinemann, Woburn, 1998.
    [4] "ASTM Standard B 258 - 02," ASTM International.
    [5] https://ntrs.nasa.gov/api/citations/20080008842/downloads/20080008842.pdf


    Inputs Parameters
    ------------ 
    power (W) - float
        Power required at the end of transmission
    length (m) - float
        Length of transmission distance not including margin
    wire_material - str
        Metal the wire is made from, options: (copper,aluminum)
    wire_type - str
        Wire configuration type, options: (coaxial,two_wires)
    wire_location - str
        Location of the wires relative to the surface, options: (suspended,on_surface,buried)
    dielectric_material - str
        Material of the dielectric insulator, options: (TFE)
    voltage_list (V) - list
        List of voltages that the lines are sized to, the final voltage is chosen
        from the list to minimize the total mass. The voltage values are assumed to
        be centered at zero (not total voltage), for example: +/- 100 VDC.


    Assumptions:
    ------------ 
    line_efficiency - float (0.95)
        Percentage of power that is transmitted.
    T_surface (K) - float (380)
        Surface temperature that the wires radiate to.
    q_incident (W/m**2) - float (1421)
        Total amount of incident radiation on the wire.
    length_margin - float (0.1)
        Fraction of the total length to account for curves / elevation changes.
    distance_btw_wires (m) - float (0.01)
        Distance between wires for the two - wire configuration.
    breakdown_safety_factor - float (10)
        Safety factor for the breakdown voltage of the dielectric insulator.
    T_subsurface_regolith (K) - float (250)
        Temperature of the regolith at the assumed wire_depth.
    k_regolith (W/m-K) - float (0.008)
        Conductivity of the regolith at the assumed wire_depth.
    wire_depth (m) - float (1)
        Buried depth of the wire below the surface.
    secondary_dielectric_thickness (m) - float (0)
        Thickness of the external dielectric thickness.
    redundancy - int (1)
        Redundancy for the number of cables (0 is no redundancy).
    """

    def __init__(
        self,
        power,
        length,
        wire_material,
        wire_type,
        wire_location,
        dielectric_material,
        voltage_list,
        line_efficiency=0.95,
        T_surface=380,
        q_incident=1371,
        length_margin=0.1,
        distance_btw_wires=0.01,
        breakdown_safety_factor=10,
        T_subsurface_regolith=250,
        k_regolith=0.008,
        wire_depth=0.25,
        secondary_dielectric_thickness=0,
        redundancy=1,
        # minimum_gauge=None  # NOTE can be implemented if necessary
    ):
        power_list = power / line_efficiency
        self.length = length
        self.wire_material = wire_material
        self.wire_type = wire_type
        self.wire_location = wire_location
        self.dielectric_material = dielectric_material
        self.voltage_list = voltage_list
        self.line_efficiency = line_efficiency
        self.T_surface = T_surface
        self.q_incident = q_incident
        self.length_margin = length_margin
        self.distance_btw_wires = distance_btw_wires
        self.breakdown_safety_factor = breakdown_safety_factor
        self.T_subsurface_regolith = T_subsurface_regolith
        self.k_regolith = k_regolith
        self.wire_depth = wire_depth
        self.secondary_dielectric_thickness = secondary_dielectric_thickness
        self.redundancy = redundancy

        # add length margin
        self.length *= 1 + self.length_margin

        # make it an ndarray if not one
        if not isinstance(power_list, np.ndarray):
            power_list = [power_list]

        if wire_type not in ['coaxial','two_wires']:
            raise KeyError('"wire_type" must be in [coaxial,two_wires]')
        if wire_material not in ['aluminum','copper']:
            raise KeyError('"wire_material" must be in [aluminum,copper]')
        if wire_location not in ['suspended','on_surface','buried']:
            raise KeyError('"wire_location" must be in [suspended,on_surface,buried]')
        
        # size for each power
        mass_out = np.zeros(len(power_list))
        T_wire_out = np.zeros(len(power_list))
        voltage_out = np.zeros(len(power_list))
        radius_out = np.zeros(len(power_list))
        for x in range(len(power_list)):
            mass_out[x], T_wire_out[x], voltage_out[x], radius_out[x] = self._calc_radius(power_list[x])
        
        # set output values for each power
        if len(power_list) == 1:
            self.mass_out = mass_out[0]
            self.power_out = power_list[0]
            self.T_wire_out = T_wire_out[0]
            self.voltage_out = voltage_out[0]
            self.radius_out = radius_out[0]
        else:
            self.mass_out = mass_out
            self.power_out = power_list
            self.T_wire_out = T_wire_out
            self.voltage_out = voltage_out
            self.radius_out = radius_out
   

    def _calc_radius(self,power):
        # Exterior surface properties [1]
        if self.secondary_dielectric_thickness != 0:
            if self.dielectric_material == 'TFE':
                epsilon = 0.9  # emittance of TFE
                alpha = 0.1  # absorptance of TFE
        else:
            if self.wire_material == 'copper':
                epsilon = 0.9  # emittance of copper
                alpha = 0.1  # absorptance of copper
            elif self.wire_material == 'aluminum':
                epsilon = 0.9  # emittance of aluminum
                alpha = 0.1  # absorptance of aluminum

        # Conductor properties [1]
        if self.wire_material == 'copper':
            T_0 = 32  # K
            rho_0 = 1.77e-8  # ohm/m
            conductivity_wire = 401  # W/m-K
            self.wire_density = 8920  # kg/m**3
            T_max = 600 + 273  # K, max operating temperature
        elif self.wire_material == 'aluminum':
            T_0 = 45  # K
            rho_0 = 2.83e-8  # ohm/m
            conductivity_wire = 237  # W/m-K
            self.wire_density = 2700  # kg/m**3
            T_max = 300 + 273  # K, max operating temperature

        # Dielectric properties [1]
        if self.dielectric_material == 'TFE':
            Eb = 430 / 2.54e-5  # V/m, breakdown voltage
            k_d = 0.251  # W/m-K
            self.dielectric_density = 2175  # kg/m**3

        sb = 5.67e-8  # W/m**2-K**4, Stefan-Boltzmann constant
        T_space = 2.7  # K

        # Calculate radii for each voltage in the list [1]
        radius = np.ones(len(self.voltage_list))
        radius_inner = np.ones(len(self.voltage_list))
        radius_outer = np.ones(len(self.voltage_list))
        radius_exterior = np.ones(len(self.voltage_list))
        mass = np.ones(len(self.voltage_list))
        T_wire = 600 * np.ones(len(self.voltage_list))  # K, initial guess for wire temperature
        count = -1
        for voltage in self.voltage_list:
            count += 1
            current = power / voltage  # A, wire current
            E0 = Eb / self.breakdown_safety_factor  # V/m
            dielectric_thickness = voltage / E0  # m
            power_lost = power * (1 - self.line_efficiency) / 2  # power lost per line due to resistance
            resistance = power_lost / current**2  # resistance per line

            error = 1
            while abs(error) > 1e-5:
                resistivity = rho_0 * (T_wire[count] - T_0) / (293 - T_0)
                radius[count] = (resistivity * self.length / (np.pi * resistance))**(1/2)  # m, radius of the inner conductor
                radius_inner[count] = radius[count] + dielectric_thickness  # m, inner radius of second conductor, outer radius of the insulation
                radius_outer[count] = (radius[count]**2 + radius_inner[count]**2)**(1/2)  # m, outer radius of second conductor

                q_dot = power_lost / (np.pi * radius[count]**2 * self.length)  # W/m**3, heat generation per volume from wire resistance
                q_rad = 2 * alpha * radius_exterior[count] * self.length * self.q_incident  # W, heat generation from incident radiation

                if self.wire_type == 'coaxial':
                    radius_exterior[count] = radius_outer[count] + self.secondary_dielectric_thickness  # m, radius to the exterior of the wire
                    match self.wire_location:
                        case 'suspended':
                            # K, outermost temperature
                            T_outer = ((2 * power_lost + q_rad) / (2 * np.pi * sb * radius_exterior[count] * self.length) 
                                    + 0.5 * T_space**4 + 0.5 * self.T_surface**4)**(1/4)  # K

                        case 'buried':
                            # K, outermost temperature
                            R_regolith = np.log(self.wire_depth / radius_exterior[count]) / (2 * np.pi * self.k_regolith * self.length)  # K/W
                            T_outer = 2 * power_lost * R_regolith + self.T_subsurface_regolith  # K

                        case 'on_surface':
                            def function(T_o):
                                area = np.pi * radius_exterior[count] * self.length  # surface area of half of the wire
                                F = 0.25  # view factor for infinite half-cylinder radiating to an infinite plane
                                R_regolith = 4.5e-3  # K-m**2/W, hard to estimate, can improve later
                                func = epsilon * sb * area * (T_o**4 - F * self.T_surface**4 - (1 - F) * T_space**4) + area / R_regolith * (T_o - self.T_surface) - \
                                2 * power_lost - self.q_incident * radius_exterior[count] * self.length  # q_incident area is halved because it is at the South Pole
                                return func
                            
                            F = 0.25
                            initial_guess = ((2 * power_lost + self.q_incident * radius_exterior[count] * self.length) / (epsilon * sb * np.pi * radius_exterior[count] * self.length / 2) + \
                                            F * self.T_surface**4 + (1 - F) * T_space**4)**(1/4) / 2
                            T_outer = fsolve(function,initial_guess)  # K, outermost temperature

                    # find temperature at the outer radius of the outer wire
                    if self.secondary_dielectric_thickness != 0:
                        T_wire_outer = 2 * power_lost * np.log(radius_exterior[count] / radius_outer[count]) / (2 * np.pi * k_d * self.length) + T_outer
                    else:
                        T_wire_outer = T_outer  # without a secondary dielectric the outermost temp is the outer wire temp

                    # K, temperature at the inner radius of the outer wire
                    T_inner = (2 * power_lost / (4 * np.pi * conductivity_wire * radius_outer[count] * self.length) - \
                            q_dot * radius_outer[count] / (2 * conductivity_wire)) * radius_outer[count] * np.log(radius_outer[count] / radius_inner[count]) + \
                            q_dot * (radius_outer[count]**2 - radius_inner[count]**2) / (4 * conductivity_wire) + T_wire_outer

                    # K, temperature of the inner wire
                    Tw = power_lost * np.log(radius_inner[count] / radius[count]) / (2 * np.pi * k_d * self.length) + T_inner
                
                elif self.wire_type == 'two_wires':
                    radius_exterior[count] = radius[count] + self.secondary_dielectric_thickness  # m, radius to the exterior of the wire
                    match self.wire_location:
                        case 'suspended':
                            # view factor between the two wires
                            F = (np.pi + (self.distance_btw_wires / radius_exterior[count] * (4 + self.distance_btw_wires / radius_exterior[count]))**0.5
                                - (2 + self.distance_btw_wires / radius_exterior[count]) - 2 * np.arccos(2 / (2 + self.distance_btw_wires / radius_exterior[count]))) / (2 * np.pi)                        
                            # K, outermost temperature
                            T_outer = (((np.pi * (1 - self.line_efficiency) / self.length)**(3/2) * (power * voltage**2 / resistivity)**(1/2)
                                + np.pi**2 * sb * epsilon * F * self.T_surface**4
                                + q_rad * np.pi / (radius_exterior[count] * self.length)) / (2 * np.pi**2 * sb * epsilon * F))**0.25

                        case 'buried':
                            # K, outermost temperature
                            T_outer = power_lost * np.log(self.wire_depth / radius_exterior[count]) / (2 * np.pi * self.k_regolith * self.length) + self.T_subsurface_regolith

                        case 'on_surface':
                            def function(T_o):
                                area = np.pi * radius_exterior[count] * self.length  # surface area of half of the wire
                                F = 0.25  # view factor for cylinder bisected by infinite plane

                                R_regolith = 4.5e-3  # K-m**2/W, hard to estimate, can improve later
                                func = epsilon * sb * area * (T_o**4 - F * self.T_surface**4 - (1 - F) * T_space**4) + area / R_regolith * (T_o - self.T_surface) - \
                                power_lost - self.q_incident * radius_exterior[count] * self.length  # q_incident area is halved because it is at the South Pole
                                return func
                            
                            F = 0.25
                            initial_guess = ((power_lost + self.q_incident * radius_exterior[count] * self.length) / 
                                (epsilon * sb * np.pi * radius_exterior[count] * self.length / 2) + F * self.T_surface**4 + (1 - F) * T_space**4)**(1 / 4) / 2
                            # K, outermost temperature
                            T_outer = fsolve(function,initial_guess)

                    # find temperature of the wire
                    if self.secondary_dielectric_thickness != 0:
                        Tw = power_lost * np.log(radius_exterior[count] / radius[count]) / (2 * np.pi * k_d * self.length) + T_outer
                    else:
                        Tw = T_outer  # without a secondary dielectric the outermost temp is the wire temp
                
                # calculate the error with the previous wire temperature
                error = (Tw - T_wire[count]) / T_wire[count]
                T_wire[count] = Tw

            # set values to be used in calc_mass each iteration
            self.radius = radius[count]
            self.radius_inner = radius_inner[count]
            self.radius_outer = radius_outer[count]
            mass[count] = self.calc_mass()

        # set any entries that are above the max temperature to 1e6 to avoid selection
        mass = [1e6 if T_wire[x] >= T_max else mass[x] for x in range(len(T_wire))]

        # find the minimum mass
        mass_min = min(mass)
        if mass_min == 1e6:
            raise Exception('The wire temperature is too high in all cases')
        
        # find where minimum mass occurs
        min_count = list(mass).index(mass_min)
        
        # openmdao bug fix        
        if math.isnan(radius[min_count]):
            radius[min_count] = 5e-5

        # set properties at the minimum mass case for _check_wire_radius
        self.radius = radius[min_count]
        self.current = power / self.voltage_list[min_count]

        if self._check_wire_radius():
            raise Exception('The wire thickness is too small to handle the current')
            # NOTE needs more work if this becomes a problem and new values are needed
        return mass_min, T_wire[min_count], self.voltage_list[min_count], radius[min_count]

    def calc_mass(self):
        if self.wire_type == 'coaxial':
            radius_exterior = self.radius_outer
        else:
            radius_exterior = self.radius

        # Add masses for wires
        if self.wire_type == 'coaxial':
            number_of_wires = 2 + 2 * np.ceil(self.redundancy / 2)  # wires added in pairs
        else:
            number_of_wires = 2 + self.redundancy  # wires added individually

        emi_density = 0.15  # kg/m, line density of EMI shielding [5] with mass reduction assumptions
        wire_mass = number_of_wires * np.pi * self.radius**2 * self.length * self.wire_density + emi_density * self.length  # kg, mass of wires and emi shielding

        # Add mass for dielectric between the coaxial wires
        if self.wire_type == 'coaxial':
            insulating_layers = number_of_wires / 2
            dielectric_mass = insulating_layers * np.pi * (self.radius_inner**2 - self.radius**2) * self.length * self.dielectric_density
        else:
            dielectric_mass = 0

        # Add mass for external dielectric
        if self.secondary_dielectric_thickness != 0:
            if self.wire_type == 'coaxial':
                additional_insulating_layers = number_of_wires / 2
            else:
                additional_insulating_layers = number_of_wires
            secondary_dielectric_mass = additional_insulating_layers * np.pi * ((radius_exterior + self.secondary_dielectric_thickness)**2 - radius_exterior**2) * self.length * self.dielectric_density
        else:
            secondary_dielectric_mass = 0

        # Calculate storage based on D-RATS [2]
        diameter_inches = 2 * (radius_exterior + self.secondary_dielectric_thickness) * 39.3701
        traverse = 10.5  # inches
        flange_diameter = 41.5  # inches
        barrel_diameter = 21.875  # inches
        storable_length = (traverse * (flange_diameter**2 - barrel_diameter**2) / (15.3 * diameter_inches**2))
        storable_meters = storable_length / 3.281

        if self.wire_type == 'coaxial':
            total_length = number_of_wires / 2 * self.length
        else:
            total_length = number_of_wires * self.length

        required_reels = np.ceil(total_length / storable_meters)
        reel_mass = 10  # kg
        total_reel_mass = required_reels * reel_mass

        total_mass = wire_mass + dielectric_mass + secondary_dielectric_mass + total_reel_mass

        try:
            return self.mass_out
        except:
            return total_mass
    
    def calc_power(self):
        return self.power_out

    def calc_wire_temp(self):
        return self.T_wire_out
    
    def calc_voltage(self):
        return self.voltage_out * 2  # Outputs total voltage for PMAD components

    def calc_radius(self):
        return self.radius_out

    def _check_wire_radius(self,minimum_awg=None):
        # Check that the wire radius is capable of handling the required current
        awg_list = ['32','30','28','26','24','22','20','18','16','14','12','10','8','6','4','2','1'] # Values given for copper, assume the same for aluminum [3-4]
        max_current = [0.53,0.86,1.4,2.2,3.5,7,11,16,22,32,41,55,73,101,135,181,211]  # amps
        awg_diameter = [0.203,0.254,0.32,0.404,0.511,0.643,0.813,1.02,1.29,1.63,2.05,2.59,3.26,4.11,5.19,6.54,7.35]  # mm
        awg_radius = [val/2/1000 for val in awg_diameter]  # m

        if minimum_awg == None:
            # Ensure wire follows ASTM standards
            for count in range(len(awg_radius)):
                if self.radius < awg_radius[count]:
                    if self.current > max_current[count-1]:
                        print('radius:',self.radius)
                        print('min_radius:',awg_radius[count-1])
                        print('current:',self.current)
                        print('max_current:',max_current[count-1])
                        return True
                    else:
                        self.awg = awg_list[count]
                        return False
                if count == len(awg_radius)-1:
                    print('radius:',self.radius)
                    print('min_radius:',awg_radius[count-1])
                    print('current:',self.current)
                    print('max_current:',max_current[count-1])
                    return True
        else:
            try:
                count = awg_list.index(minimum_awg)
            except ValueError:
                raise Exception(f'AWG must be in: {awg_list}')
            
            # Check that the wire is larger than the minimum radius and the current is below the max current
            if self.radius > awg_radius[count] and self.current < max_current[count]:
                return False
            else:
                print('radius:',self.radius)
                print('min_radius:',awg_radius[count-1])
                print('current:',self.current)
                print('max_current:',max_current[count-1])
                return True


if __name__ == '__main__':
    volts = [2000 + 50 * (x + 1) for x in range(40)]
    sys = SurfacePowerCable(
                        power=np.array([40e3,30e3,20e3]), 
                        length=1e3, 
                        wire_material='aluminum',  # aluminum,copper
                        wire_type='coaxial',  # two_wires, coaxial
                        wire_location='on_surface',  # suspended,on_surface,buried
                        dielectric_material='TFE',
                        voltage_list=volts,
                    )

    print('mass: ',sys.calc_mass())
    print('radius:', sys.calc_radius())
    print('voltage: ',sys.calc_voltage())
    print('wire temp:', sys.calc_wire_temp())


