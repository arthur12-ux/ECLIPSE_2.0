"""
Collection of subelements for sizing heat pipes.
"""

import math
import numpy as np


class BasicHeatPipe:
    """
    Basic heat pipe subelement. Sizes a discrete number of loop heat pipes based
    on its heat capacity. Includes basic cold plate and working fluid sizing.

    Sources:
    [1] Ch. 16 of Human Spaceflight Mission Analysis and Design

    Input Parameters
    ------------
    heat_load (W) : float
        Heat that the radiator must dissipate.
    heat_pipe_length (m) : float
        Average heat pipe length.
    heat_pipe_capacity (W) : float
        Heat load capacity of a single heat pipe.
    cold_plate_capacity (W) : float
        Heat load capacity of a single cold plate.
    radiator_mass (kg) : float
        Basic dry mass of radiator(s) to use for loop mass estimation.
    redundancy_factor : int
        Factor to account for heat pipe redundancy.
    """

    def __init__(
        self,
        heat_load,
        heat_pipe_length,
        heat_pipe_capacity,
        cold_plate_capacity,
        radiator_mass,
        redundancy_factor,
    ):
        self.heat_load = heat_load
        self.heat_pipe_length = heat_pipe_length
        self.heat_pipe_capacity = heat_pipe_capacity
        self.cold_plate_capacity = cold_plate_capacity
        self.radiator_mass = radiator_mass
        self.redundancy_factor = redundancy_factor

    def calc_dry_mass(self):
        # Based on Table 16-7 of [1]
        num_heat_pipes = math.ceil(self.heat_load / self.heat_pipe_capacity)
        heat_pipe_mass = num_heat_pipes * \
            (0.000294 * self.heat_pipe_capacity * self.heat_pipe_length**2)
        cold_plate_mass = num_heat_pipes * \
            (12 * self.cold_plate_capacity / 1000)
        basic_mass = (heat_pipe_mass + cold_plate_mass) * \
            self.redundancy_factor

        return basic_mass

    def calc_wet_mass(self):
        # Based on Table 16-7 of [1]
        num_heat_pipes = math.ceil(self.heat_load / self.heat_pipe_capacity)
        cold_plate_mass = num_heat_pipes * \
            (12 * self.cold_plate_capacity / 1000)
        fluid_mass = (cold_plate_mass + self.radiator_mass) * 0.05

        return fluid_mass

    def calc_volume(self):
        # Based on Table 16-7 of [1]
        num_heat_pipes = math.ceil(self.heat_load / self.heat_pipe_capacity)
        heat_pipe_volume = num_heat_pipes * \
            (2.03e-7 * self.heat_pipe_capacity * self.heat_pipe_length**2)
        cold_plate_volume = num_heat_pipes * \
            (0.028 * self.cold_plate_capacity / 1000)

        basic_volume = (heat_pipe_volume + cold_plate_volume) * \
            self.redundancy_factor
        
        return basic_volume


# class LoopHeatPipe:
#     """
#     Two-phase loop heat pipe subelement. Sizes a discrete number of loop
#     heat pipes based on its heat capacity. Includes liquid and vapor transport
#     lines, along with an evaporator and wick, a compensation chamber and the
#     working fluid.

#     Sources:
#     [1] Ku, J. (1999). Operating characteristics of loop heat pipes. SAE transactions, 503-519.
#     [2] Qu, Y., Wang, S., & Tian, Y. (2018). A review of thermal performance in multiple evaporators loop heat pipe. Applied Thermal Engineering, 143, 209-224.
#     [3] Wertz, J. R., Everett, D. F., & Puschell, J. J. (2011). Space mission engineering: the new SMAD. Microcosm Press.
#     [4] Ku, J. (2015). Introduction to Loop Heat Pipes.
#     [5] Deng, D., Liang, D., Tang, Y., Peng, J., Han, X., & Pan, M. (2013). Evaluation of capillary performance of sintered porous wicks for loop heat pipe. Experimental Thermal and Fluid Science, 50, 1-9.

#     Input Parameters
#     ------------
#     heat_load (W) : float
#         Heat that the heat pipe must dissipate
#     heat_capacity (W) : float
#         Heat that the a single heat pipe is able to dissipate
#     working_fluid : str
#         Fluid loop working fluid; one of: water, ammonia, 50%_prop_glycol,
#         30%_ethylene_glycol, 60%_ethylene_glycol, 40%_glycerine, fluorinert_72,
#         HFE_7100, D_limonene, novec_7500
#     characteristic_length (m) : float
#         Characteristic length of the vehicle or system.
#     characteristic_radius (m) : float
#         Characteristic length of the vehicle or system.
#     case_material_density (kg/m**3) : float
#         Density of the material used for the loop heat pipe.
#     wick_material_density (kg/m**3) : float
#         Density of the material used for the wick.
#     wick_porosity : float
#         [Description]
#     """

#     def __init__(
#         self,
#         heat_load,
#         heat_pipe_capacity,
#         cold_plate_capacity,
#         working_fluid,
#         case_material_density,
#         wick_material_density,
#         wick_porosity,
#         characteristic_length,
#         characteristic_radius,

#         radiator_sides=1,
#         radiator_view_factor='circular',
#         radiator_temperature=300,  # K
#         radiator_density=0.625*2+1.25,
#         radiator_emissivity=0.9,
#         radiator_absorptivity=0.1,
#         radiator_fin_efficiency=0.9,
#         operational_distance=1,
#         body_temperature=290,
#         body_radius=6378,
#         body_albedo=0.3,
#         body_orbit_altitude=6378/2,
#         radiator_body_angle=0,
#     ):

#         self.heat_load = heat_load
#         self.heat_pipe_capacity = heat_pipe_capacity
#         self.cold_plate_capacity = cold_plate_capacity
#         self.working_fluid = working_fluid
#         self.case_material_density = case_material_density
#         self.wick_material_density = wick_material_density
#         self.wick_porosity = wick_porosity
#         self.characteristic_length = characteristic_length
#         self.characteristic_radius = characteristic_radius

#         self.radiator_sides = radiator_sides
#         self.radiator_view_factor = radiator_view_factor
#         self.radiator_temperature = radiator_temperature
#         self.radiator_density = radiator_density
#         self.radiator_emissivity = radiator_emissivity
#         self.radiator_absorptivity = radiator_absorptivity
#         self.radiator_fin_efficiency = radiator_fin_efficiency
#         self.operational_distance = operational_distance
#         self.body_temperature = body_temperature
#         self.body_radius = body_radius
#         self.body_albedo = body_albedo
#         self.body_orbit_altitude = body_orbit_altitude
#         self.radiator_body_angle = radiator_body_angle

#     def calc_dry_mass(self):
#         # Based on Table 16-7 of [1]
#         cold_plate_mass = math.ceil(
#             self.heat_load / self.cold_plate_capacity) * (12 * self.cold_plate_capacity / 1000)

#         num_heat_pipes = math.ceil(self.heat_load / self.heat_pipe_capacity)

#         # Transport Lines
#         # assume length of 5m
#         transport_line_length = 5  # m
#         transport_line_inner_radius = 1.75/2/1000  # m - from Qu et al
#         transport_line_outer_radius = 2.38/2/1000  # m - from Qu et al
#         liq_line_mass = np.pi*(transport_line_outer_radius**2 -
#                                transport_line_inner_radius**2)*transport_line_length*self.case_material_density  # kg
#         vap_line_mass = np.pi*(transport_line_outer_radius**2 -
#                                transport_line_inner_radius**2)*transport_line_length*self.case_material_density  # kg

#         # Evaporator
#         # get longest component length
#         # longest_length = sorted([component_length,component_width,component_depth])[-1]
#         longest_length = 0.25
#         evap_inner_radius = 10/2/1000  # m - from Qu et al
#         evap_outer_radius = 12/2/1000  # m - from Qu et al
#         evap_mass = np.pi*(evap_outer_radius**2-evap_inner_radius **
#                            2)*longest_length*self.case_material_density  # kg

#         # Wick
#         wick_outer_radius = evap_inner_radius  # m
#         wick_inner_radius = transport_line_inner_radius
#         wick_mass = (1-self.wick_porosity)*np.pi*(wick_outer_radius**2 -
#                                                   wick_inner_radius**2)*longest_length*self.wick_material_density  # kg

#         # Compensation Chamber
#         cc_outer_radius = 37/2/1000  # m - from Qu et al
#         cc_inner_radius = 39/2/1000  # m - from Qu et al
#         cc_length = 55/1000  # m - sized to be largest volume from Qu et al
#         cc_mass = np.pi*(cc_outer_radius**2-cc_inner_radius **
#                          2)*cc_length*self.case_material_density  # kg

#         # Working Fluid
#         ammonia_mass = 0.19/2  # kg

#         loop_heat_pipe_mass = liq_line_mass + vap_line_mass + \
#             evap_mass + wick_mass + cc_mass + ammonia_mass
#         print(loop_heat_pipe_mass)
#         print(0.000294*240*5**2)
#         return num_heat_pipes * loop_heat_pipe_mass + cold_plate_mass + self.calc_radiator_mass()

#     def calc_wet_mass(self):
#         # Based on Table 16-7 of [1]
#         num_heat_pipes = math.ceil(self.heat_load / self.heat_pipe_capacity)

#         # Transport Lines
#         # assume length of 5m
#         transport_line_length = 5  # m
#         transport_line_inner_radius = 1.75/2/1000  # m - from Qu et al
#         transport_line_outer_radius = 2.38/2/1000  # m - from Qu et al
#         liq_line_mass = np.pi*(transport_line_outer_radius**2 -
#                                transport_line_inner_radius**2)*transport_line_length*self.case_material_density  # kg
#         vap_line_mass = np.pi*(transport_line_outer_radius**2 -
#                                transport_line_inner_radius**2)*transport_line_length*self.case_material_density  # kg

#         # Evaporator
#         # get longest component length
#         # longest_length = sorted([component_length,component_width,component_depth])[-1]
#         longest_length = 0.25
#         evap_inner_radius = 10/2/1000  # m - from Qu et al
#         evap_outer_radius = 12/2/1000  # m - from Qu et al

#         # Wick
#         wick_outer_radius = evap_inner_radius  # m
#         wick_inner_radius = transport_line_inner_radius

#         # Compensation Chamber
#         cc_outer_radius = 37/2/1000  # m - from Qu et al
#         cc_inner_radius = 39/2/1000  # m - from Qu et al
#         cc_length = 55/1000  # m - sized to be largest volume from Qu et al

#         # Working Fluid
#         fittings_factor = 0.2
#         line_volume = (1 + fittings_factor) * self.line_length * \
#             np.pi * (self.line_inner_diameter**2) / 4  # m**3
#         accumulator_volume_factor = 650 / 16.4 / \
#             231  # [12], based of ISS ITCS values
#         accumulator_volume = accumulator_volume_factor * line_volume  # m**3
#         working_fluid_mass = (accumulator_volume +
#                               line_volume) * self.density  # kg

#         unit_wet_mass = working_fluid_mass  # kg
#         total_wet_mass = self.redundancy_factor * unit_wet_mass

#         return total_wet_mass

#     def calc_radiator_mass(self):
#         radiator = sm.SpacecraftRadiator(
#             heat_load=self.heat_load,  # W
#             radiator_sides=self.radiator_sides,
#             radiator_view_factor=self.radiator_view_factor,
#             radiator_temperature=self.radiator_temperature,  # K
#             radiator_density=self.radiator_density,
#             radiator_emissivity=self.radiator_emissivity,
#             radiator_absorptivity=self.radiator_absorptivity,
#             radiator_fin_efficiency=self.radiator_fin_efficiency,
#             operational_distance=self.operational_distance,
#             body_temperature=self.body_temperature,
#             body_radius=self.body_radius,
#             body_albedo=self.body_albedo,
#             body_orbit_altitude=self.body_orbit_altitude,
#             radiator_body_angle=self.radiator_body_angle,
#         )

#         radiator_mass = radiator.calc_mass()

#         return radiator_mass


if __name__ == "__main__":
    model = 'BasicHeatPipe'  # BasicHeatPipe, LoopHeatPipe
    print_options = np.get_printoptions()
    np_precision = print_options['precision']

    match model:
        case 'BasicHeatPipe':
            heat_pipe = BasicHeatPipe(
                heat_load=29400,  # W
                heat_pipe_length=5,  # m
                heat_pipe_capacity=240,  # W
                cold_plate_capacity=1000,  # W
                radiator_mass=1672,  # kg
                redundancy_factor=2,
            )

            dry_mass = heat_pipe.calc_dry_mass()
            dry_mass = np.round(dry_mass, np_precision)
            wet_mass = heat_pipe.calc_wet_mass()
            wet_mass = np.round(wet_mass, np_precision)
            volume = heat_pipe.calc_volume()
            volume = np.round(volume, np_precision)

            print(f'dry_mass = {dry_mass} (kg)')
            print(f'wet_mass = {wet_mass} (kg)')
            print(f'volume = {volume} (m**3)')

        # case 'LoopHeatPipe':
        #     loop_heat_pipe = LoopHeatPipe(
        #         heat_load=240,  # W
        #         heat_pipe_capacity=240,  # W
        #         cold_plate_capacity=1000,  # W
        #         working_fluid='ammonia',
        #         characteristic_length=2,  # m
        #         characteristic_radius=2,  # m
        #         case_material_density=7930,  # kg/m**3
        #         wick_material_density=7930,  # kg/m**3
        #         wick_porosity=0.72  # from Deng et al
        #     )

        #     dry_mass = loop_heat_pipe.calc_dry_mass()
        #     dry_mass = np.round(dry_mass, np_precision)
        #     # wet_mass = loop_heat_pipe.calc_wet_mass()
        #     # wet_mass = np.round(wet_mass, np_precision)
        #     # volume = loop_heat_pipe.calc_volume()
        #     # volume = np.round(volume, np_precision)

        #     print(f'dry_mass = {dry_mass} (kg)')
        #     # print(f'wet_mass = {wet_mass} (kg)')
        #     # print(f'volume = {volume} (m**3)')
