import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from stages import *
from component_class import PowerConditioningComponent


class DDCU(PowerConditioningComponent):
    """
    The dc/dc converter model combines the chopper, inverter transformer, and
    rectifier stage equations. It is completed with the addition of input and
    output dc filtering and equations to calculate the control and monitoring,
    conductor and connector, and box and radiator masses.

    Sources:
    [1] NASA/CR-2011-217268 p.81-82
    [2] NASA-CR-189225 p.106-115

    Input Parameters
    ------------
    power_output (kW) : float or np.ndarray
        Output power level.
        If is float, will assume power_input is max power and power() method will return max input power required.
        If np.ndarray, will size mass to max value and power() method will return ndarray of input power required.
        Recommended input range: 0.5 to 250 kW.
    voltage_in (Vdc) : float
        Input voltage level.
        Recommended input range: 20 to 10,000 Vdc.
    voltage_out (Vdc) : float
        Output voltage level.
        Recommended input range: 20 to 10,000 Vdc.
    inversion_frequency (kHz) : float
        Inversion frequency.
        Recommended input range: 10 to 100 kHz.
    inversion_phases : int
        Number of phases used for inversion.
        Recommended input range: 1 or 3.
    ripple_factor_percent : float
        Ripple factor percentage.
        The amount the DC voltage output can fluctuate from the nominal output voltage.
        Ex: +/- 0.5 V ripple on a 120 V output represents corresponds to 0.004
        Recommend using 0.004 for components near sensitive loads, 0.01-0.05 for components near sources or that supply
        insensitive loads, and up to 0.20 for low frequency (~60Hz) components near sources.
        Recommended input range: 0.1 to 5% (0.001 to 0.05).
    fse_in : float
        Input DC filter stage efficiency.
        Recommended input range: 0.997 to 0.999.
    cse : float
        Chopper stage efficiency.
        Recommended input range: 0.968 to 0.984.
    itse : float
        Inverter transformer stage efficiency.
        Recommended input range: 0.986 to 0.996.
    rse : float
        Rectifier stage efficiency.
        Recommended input range: 0.983 to 0.991.
    fse_out : float
        Output DC filter stage efficiency.
        Recommended input range: 0.997 to 0.999.
    """

    def __init__(
            self,
            power_output,
            voltage_in=120.,
            voltage_out=120.,
            available_modules=1,
            required_modules=1,
            inversion_frequency=40.,
            inversion_phases=1.,
            ripple_factor_percent=0.004,
            fse_in=0.998,
            cse=None,
            itse=0.992,
            rse=None,
            fse_out=0.998,
            **kwargs
    ):
        super().__init__(
            power_output=power_output,
            voltage_in=voltage_in,
            voltage_out=voltage_out,
            num_phases_in=1.,
            num_phases_out=1.,
            frequency_in=0.,
            frequency_out=0.,
            available_modules=available_modules,
            required_modules=required_modules,
            **kwargs
        )
        if inversion_frequency is None:
            if self.max_power <= 1.:
                inversion_frequency = 100.
            elif self.max_power <= 5:
                inversion_frequency = 80.
            elif self.max_power <= 20:
                inversion_frequency = 55.
            elif self.max_power <= 40:
                inversion_frequency = 50.
            elif self.max_power <= 80:
                inversion_frequency = 40.
            elif self.max_power <= 150:
                inversion_frequency = 35.
            else:
                inversion_frequency = 30.
        self.inversion_frequency = inversion_frequency
        self.inversion_phases = inversion_phases
        self.ripple_factor_percent = ripple_factor_percent
        self.fse_in = fse_in
        self.cse = cse
        self.itse = itse
        self.rse = rse
        self.fse_out = fse_out

    def calc_power_input(self):
        self._power_input = (self.power_output / self.stages['output_dc_filter'].efficiency /
                             self.stages['rectifier'].efficiency /
                             self.stages['inverter_transformer'].efficiency /
                             self.stages['chopper'].efficiency +
                             self.control_monitoring_subsystem.power) / \
                             self.stages['input_dc_filter'].efficiency

    def initialize_stages(self):

        self._stages['output_dc_filter'] = DCFilterStage(
            power_output=self.power_output,
            voltage_in=self.voltage_out,
            voltage_out=self.voltage_out,
            num_phases=self.num_phases_out,
            available_modules=self.available_modules,
            required_modules=self.required_modules,
            efficiency=self.fse_out,
            stage_frequency=self.inversion_frequency,
            ripple_factor_percent=self.ripple_factor_percent,
            percent_margin=self.percent_margin,
            k_mass=self.k_mass_stages
        )
        self._stages['rectifier'] = RectifierStage(
            power_output=self.stages['output_dc_filter'].power,
            voltage_in=self.voltage_out,
            voltage_out=self.voltage_out,
            num_phases=self.inversion_phases,
            available_modules=self.available_modules,
            required_modules=self.required_modules,
            efficiency=self.rse,
            stage_frequency=self.inversion_frequency,
            percent_margin=self.percent_margin,
            k_mass=self.k_mass_stages
        )
        self._stages['inverter_transformer'] = InverterTransformerStage(
            power_output=self.stages['rectifier'].power,
            voltage_in=self.voltage_in,
            voltage_out=self.voltage_out,
            num_phases=self.inversion_phases,
            available_modules=self.available_modules,
            required_modules=self.required_modules,
            efficiency=self.itse,
            stage_frequency=self.inversion_frequency,
            percent_margin=self.percent_margin,
            k_mass=self.k_mass_stages
        )
        self._stages['chopper'] = ChopperStage(
            power_output=self.stages['inverter_transformer'].power,
            voltage_in=self.voltage_in,
            voltage_out=self.voltage_in,
            num_phases=self.inversion_phases,
            available_modules=self.available_modules,
            required_modules=self.required_modules,
            efficiency=self.cse,
            stage_frequency=self.inversion_frequency,
            percent_margin=self.percent_margin,
            k_mass=self.k_mass_stages
        )

        cms_power_usage = self.control_monitoring_subsystem.calc_power()

        self._stages['input_dc_filter'] = DCFilterStage(
            power_output=self.stages['chopper'].power + cms_power_usage,
            voltage_in=self.voltage_in,
            voltage_out=self.voltage_in,
            num_phases=self.num_phases_in,
            available_modules=self.available_modules,
            required_modules=self.required_modules,
            efficiency=self.fse_in,
            stage_frequency=self.inversion_frequency,
            ripple_factor_percent=self.ripple_factor_percent,
            percent_margin=self.percent_margin,
            k_mass=self.k_mass_stages
        )

        stages_mass = 0.
        stages_efficiency = 1.
        for stage in self.stages:
            stages_mass += self.stages[stage].mass
            stages_efficiency *= self.stages[stage].efficiency

        self._stages_mass = stages_mass
        self._stages_efficiency = stages_efficiency


if __name__ == "__main__":
    component = DDCU(
        power_output=6.25,
        voltage_in=160.,
        voltage_out=124.5,
        available_modules=1,
        required_modules=1,
        inversion_frequency=20.,
        ripple_factor_percent=0.004,
        fse_in=0.99715,
        cse=0.983,
        itse=0.995,
        rse=0.987,
        fse_out=0.99715,
        conductor_material='copper',
        enclosure_baseplate_type='finned',
        enclosure_material='al',
        packaged_electronics_density=0.197*1.05,
        include_enclosure=True,
        include_radiator=False,
        radiator_material_coff=13.6,
        radiator_sides=2,
        radiator_temperature_delta=11.,
        radiator_temperature_sink=294.,
        radiator_temperature_baseplate=336.,
        auto_baseplate_dimensions=False,
        baseplate_length=0.591,
        baseplate_width=0.590,
    )

    for element in component.mass_breakdown:
        print(f'{element}: {component.mass_breakdown[element]} kg')

    ddcu_filter_mass = component.stages['input_dc_filter'].mass + component.stages['output_dc_filter'].mass
    print('Metcalf model predicted ISS DDCU total filter mass: 7.35 kg')
    print(f'Model predicted total filter mass: {ddcu_filter_mass} kg')

    ddcu_dce_mass = component.stages['chopper'].mass + component.stages['inverter_transformer'].mass + \
        component.stages['rectifier'].mass
    print('Metcalf model predicted ISS DDCU DCE mass: 8.9 kg')
    print(f'Model predicted DCE mass: {ddcu_dce_mass} kg')

    print('Metcalf model predicted ISS DDCU mass: 62 kg')
    print(f'Model predicted mass: {component.mass} kg')

    print('ISS DDCU efficiency: 95 %')
    print(f'Model predicted efficiency: {component.efficiency} %')

    # component = DDCU(
    #     power_output=6.6,
    #     voltage_in=124.,
    #     voltage_out=130.,
    #     available_modules=1,
    #     required_modules=1,
    #     inversion_frequency=80.,
    #     ripple_factor_percent=0.004,
    #     fse_in=0.998,
    #     cse=0.976,
    #     itse=0.992,
    #     rse=0.987,
    #     fse_out=0.998,
    #     conductor_material='copper',
    #     enclosure_baseplate_type='finned',
    #     enclosure_material='al',
    #     packaged_electronics_density=0.197 * 1.05,
    #     include_enclosure=True
    # )
    #
    # for element in component.mass_breakdown:
    #     print(f'{element}: {component.mass_breakdown[element]} kg')
