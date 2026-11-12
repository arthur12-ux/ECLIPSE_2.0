import numpy as np
import os
import sys
from power_cable import SurfacePowerCable
from ddcu import DDCU
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '..','..'))
from thermal.heat_pipes import BasicHeatPipe
from thermal.radiators import SurfaceRadiator

class SurfacePowerCableSystem:
    """
    Sources:
    [1] https://ntrs.nasa.gov/api/citations/20220012395/downloads/TM-20220012395.pdf
    [2] 
    """

    def __init__(
        self,
        transmitted_power,
        length,
        voltage_in,
        voltage_out,
        wire_material,
        wire_type,
        wire_location,
        dielectric_material,
        voltage_list,
        line_efficiency=0.95,
        T_surface=254,  # [1]
        q_incident=1370,  # [1]
        length_margin=0.1,
        distance_btw_wires=0.01,
        breakdown_safety_factor=10,
        T_subsurface_regolith=200,  # NOTE
        k_regolith=0.008,
        wire_depth=0.25,
        secondary_dielectric_thickness=0,
        redundancy=1,
    ):

        voltage_cable = 2000  # V, initial guess
        voltage_prev = 0  # inital value for iteration
        while voltage_cable != voltage_prev:
            voltage_prev = voltage_cable

            # Size final DDCU
            ddcu_out = DDCU(
                power_output=transmitted_power/1000,  # kW
                voltage_in=voltage_cable,
                voltage_out=voltage_out
            )
            
            # Size power cables
            cables = SurfacePowerCable(
                power=ddcu_out.power_input*1000,  # W
                length=length,
                wire_material=wire_material,
                wire_type=wire_type,
                wire_location=wire_location,
                dielectric_material=dielectric_material,
                voltage_list=voltage_list,
                line_efficiency=line_efficiency,
                T_surface=T_surface,
                q_incident=q_incident,
                length_margin=length_margin,
                distance_btw_wires=distance_btw_wires,
                breakdown_safety_factor=breakdown_safety_factor,
                T_subsurface_regolith=T_subsurface_regolith,
                k_regolith=k_regolith,
                wire_depth=wire_depth,
                secondary_dielectric_thickness=secondary_dielectric_thickness,
                redundancy=redundancy,
            )
            
            # Size initial DDCU
            ddcu_in = DDCU(
                power_output=cables.calc_power()/1000,  # kW
                voltage_in=voltage_in,
                voltage_out=voltage_cable
            )
        
            voltage_cable = cables.calc_voltage()
        
        # Add heat pipes and radiator for each DDCU
        radiator_in = SurfaceRadiator(
            heat_load=ddcu_in.heat_output,
            view_factors=[[0.5, 0.5], [0.5, 0.5]],  # [1]
            surface_temps=[[T_surface, 2.7], [T_surface, 2.7]],
            incident_rad=[0, q_incident*np.sin(np.pi/4)],  # [1]
            double_sided=True,
            radiator_temperature=300,
            radiator_emissivity=0.84,
            radiator_absorptivity=0.14,
        )
        heat_pipe_in = BasicHeatPipe(
            heat_load=ddcu_in.heat_output,  # W
            heat_pipe_length=2,  # m
            heat_pipe_capacity=240,  # W
            cold_plate_capacity=1000,  # W
            radiator_mass=radiator_in.calc_mass(),  # kg
            redundancy_factor=2,
        )

        radiator_out = SurfaceRadiator(
            heat_load=ddcu_out.heat_output,
            view_factors=[[0.5, 0.5], [0.5, 0.5]],  # [1]
            surface_temps=[[T_surface, 2.7], [T_surface, 2.7]],
            incident_rad=[0, q_incident*np.sin(np.pi/4)],  # [1]
            double_sided=True,
            radiator_temperature=300,
            radiator_emissivity=0.84,
            radiator_absorptivity=0.14,
        )
        heat_pipe_out = BasicHeatPipe(
            heat_load=ddcu_out.heat_output,  # W
            heat_pipe_length=2,  # m
            heat_pipe_capacity=240,  # W
            cold_plate_capacity=1000,  # W
            radiator_mass=radiator_out.calc_mass(),  # kg
            redundancy_factor=2,
        )

        self.total_mass = ddcu_out.mass + cables.calc_mass() + ddcu_in.mass + heat_pipe_out.calc_dry_mass() + heat_pipe_in.calc_dry_mass()
        self.required_power = ddcu_in.power_input
            
    def calc_mass(self):
        return self.total_mass
    
    def calc_required_power(self):
        return self.required_power
    

if __name__ == '__main__':
    volts = [500 * (x + 1) for x in range(30)]
    cable = SurfacePowerCableSystem(
        transmitted_power=40e3,
        length=1e3,
        voltage_in=400,
        voltage_out=120,
        wire_material='aluminum',
        wire_type='coaxial',
        wire_location='on_surface',
        dielectric_material='TFE',
        voltage_list=volts,
    )
    print('mass: ', cable.calc_mass())
    print('power:', cable.calc_required_power())