"""
Collection of power management and distribution (PMAD) stage and ancillary
hardware models.
"""

import numpy as np
from abc import ABC, abstractmethod


class PowerConditioningStage(ABC):
    """
    This is defined as a class for specific power conditioning stages defined in
    'Power Management and Distribution (PMAD) Model Development Final Report' to
    inherit from. Consolidates common methods for calculating power and heat
    loads.

    Sources:
    [1] NASA/CR-2011-217268
    [2] NASA-CR-189225

    Input Parameters
    ------------
    power_output (kW) : float
        Maximum output power load.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 V.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 V.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    efficiency : float
        Stage efficiency.
    stage_frequency (kHz) : float
        Stage frequency. Equal to 0 for DC stages.
    rated_power (kW) : float
        Rated power of stage. If None, will be set to max of power_output.
    percent_margin : float
        Amount by which the max power, which the element is sized to, exceeds rated power.
        percent_margin * max power output required = margin
    k_mass : float
        k-factor for scaling mass output. 1 is unscaled.
    """

    def __init__(
        self,
        power_output,
        voltage_in,
        voltage_out,
        num_phases,
        available_modules,
        required_modules,
        efficiency,
        stage_frequency,
        rated_power=None,
        percent_margin=0.,
        k_mass=1.,
    ):
        self.power_output = power_output
        self.voltage_in = voltage_in
        self.voltage_out = voltage_out
        if num_phases == 1 or num_phases == 3:
            self.num_phases = num_phases
        else:
            raise RuntimeError(
                'Invalid number of phases. Must be either 1-phase or 3-phase.')
        self.available_modules = available_modules
        self.required_modules = required_modules
        self.efficiency = efficiency
        self.stage_frequency = stage_frequency
        if rated_power is None:
            self.rated_power = np.max(power_output)
        else:
            self.rated_power = max(np.max(power_output), rated_power)
        self.max_power = max(self.rated_power * (1. + percent_margin), 0.5)
        self.k_mass = k_mass

        self._mass = None
        self._power = None
        self._heat_output = None

    @property
    def mass(self):
        if self._mass is None:
            self._mass = self.k_mass * self.calc_mass()
            if np.isnan(self._mass):
                self._mass = 0.
        return self._mass  # kg

    @abstractmethod
    def calc_mass(self):
        pass  # kg

    @property
    def power(self):
        if self._power is None:
            self._power = self.calc_power()
        return self._power  # kW

    def calc_power(self):
        power = self.power_output / self.efficiency
        return power  # kW

    @property
    def heat_output(self):
        if self._heat_output is None:
            self._heat_output = self.calc_heat_output()
        return self._heat_output  # kW

    def calc_heat_output(self):
        heat_output = self.power - self.power_output
        return heat_output  # kW


class ChopperStage(PowerConditioningStage):
    """
    Converts DC into AC, is included in the inverter, DC/DC converter, and
    frequency converter models. Based on Weinberg converter topology.

    Sources:
    [1] NASA/CR-2011-217268 p.6

    Input Parameters
    ------------
    power_input (kW) : float
        Maximum output power load.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 Vdc.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 Vdc.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    efficiency : float
        Stage efficiency. Recommended input range: 0.968 to 0.984.
    stage_frequency (kHz) : float
        Stage frequency. Equal to 0 for DC stages.
    """

    def __init__(
        self,
        power_output,
        voltage_in=28.,
        voltage_out=28.,
        num_phases=1,
        available_modules=1,
        required_modules=1,
        efficiency=None,
        stage_frequency=40.,
        **kwargs
    ):
        if efficiency is None:
            if round(voltage_out, -1) <= 20.:
                efficiency = 0.9360
            elif round(voltage_out, -1) <= 30.:
                efficiency = 0.9600
            elif round(voltage_out, -1) <= 40.:
                efficiency = 0.9667
            elif round(voltage_out, -1) <= 50.:
                efficiency = 0.9700
            elif round(voltage_out, -1) <= 60.:
                efficiency = 0.9723
            elif round(voltage_out, -1) <= 70.:
                efficiency = 0.9736
            elif round(voltage_out, -1) <= 80.:
                efficiency = 0.9747
            elif round(voltage_out, -1) <= 90.:
                efficiency = 0.9753
            elif round(voltage_out, -1) <= 100.:
                efficiency = 0.9757
            else:
                efficiency = 0.9760

        super().__init__(
            power_output=power_output,
            voltage_in=voltage_in,
            voltage_out=voltage_out,
            num_phases=num_phases,
            available_modules=available_modules,
            required_modules=required_modules,
            efficiency=efficiency,
            stage_frequency=stage_frequency,
            **kwargs
        )

    def calc_mass(self):
        if self.num_phases == 1:
            mass_coefficient = 0.645
            power_level_factor = (self.max_power / self.required_modules)**(-0.065)
        else:
            mass_coefficient = 0.685
            power_level_factor = (self.max_power /
                                  self.required_modules)**(-0.07)

        efficiency_factor = np.exp(0.01 / (1 - self.efficiency)) / 1.5169
        redundancy_factor = self.available_modules / self.required_modules
        voltage_level_factor = (
            self.voltage_in / (self.voltage_in - 2))**7 * np.exp(self.voltage_in / 40000)
        frequency_factor = (20 / self.stage_frequency)**0.45 * \
            np.exp((self.max_power**0.1) * self.stage_frequency / 200)

        basic_mass = mass_coefficient * efficiency_factor * redundancy_factor * self.max_power * \
            power_level_factor * voltage_level_factor * frequency_factor

        return basic_mass  # kg


class ResonantChopperStage(PowerConditioningStage):
    """
    Converts DC into AC, is included in the inverter, DC/DC converter, and
    frequency converter models. Based on parallel resonant Mapham converter topology.

    Sources:
    [1] NASA-CR-189225 p.7-23

    Input Parameters
    ------------
    power_input (kW) : float
        Maximum output power load.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 Vdc.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 Vdc.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    efficiency : float
        Stage efficiency. Recommended input range: 0.95 to 0.97.
    stage_frequency (kHz) : float
        Stage frequency. Equal to 0 for DC stages.
    """

    def __init__(
        self,
        power_output,
        voltage_in=28.,
        voltage_out=28.,
        num_phases=1,
        available_modules=1,
        required_modules=1,
        efficiency=None,
        stage_frequency=40.,
        **kwargs
    ):
        if efficiency is None:
            if round(voltage_out, -1) <= 20.:
                efficiency = 0.9200
            elif round(voltage_out, -1) <= 30.:
                efficiency = 0.9440
            elif round(voltage_out, -1) <= 40.:
                efficiency = 0.9507
            elif round(voltage_out, -1) <= 50.:
                efficiency = 0.9540
            elif round(voltage_out, -1) <= 60.:
                efficiency = 0.9563
            elif round(voltage_out, -1) <= 70.:
                efficiency = 0.9576
            elif round(voltage_out, -1) <= 80.:
                efficiency = 0.9587
            elif round(voltage_out, -1) <= 90.:
                efficiency = 0.9593
            elif round(voltage_out, -1) <= 100.:
                efficiency = 0.9597
            else:
                efficiency = 0.96

        super().__init__(
            power_output=power_output,
            voltage_in=voltage_in,
            voltage_out=voltage_out,
            num_phases=num_phases,
            available_modules=available_modules,
            required_modules=required_modules,
            efficiency=efficiency,
            stage_frequency=stage_frequency,
            **kwargs
        )

    def calc_mass(self):
        if self.num_phases == 1:
            mass_coefficient = 0.39

        else:
            mass_coefficient = 0.4

        efficiency_factor = (np.exp(0.025 / (1 - self.efficiency))) / 1.86
        redundancy_factor = self.available_modules / self.required_modules
        power_level_factor = (self.max_power / self.required_modules) ** (-0.05)
        voltage_level_factor = (
            self.voltage_in / (self.voltage_in - 2))**7 * np.exp(self.voltage_in / 40000)
        frequency_factor = (20 / self.stage_frequency)**0.45 * \
            np.exp((self.max_power**0.1) * self.stage_frequency / 160)

        basic_mass = mass_coefficient * efficiency_factor * redundancy_factor * self.max_power * \
            power_level_factor * voltage_level_factor * frequency_factor

        return basic_mass  # kg


class InverterTransformerStage(PowerConditioningStage):
    """
    Used to step up or down the input voltage, and/or to provide isolation
    between the input and output. The inverter transformer stage is contained in
    the inverter, dc/dc converter, and frequency converter models. An inverter
    transformer follows or precedes a chopper section.

    Sources:
    [1] NASA/CR-2011-217268 p.18

    Input Parameters
    ------------
    power_input (kW) : float
        Maximum output power load.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 Vdc.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 Vdc.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    efficiency : float
        Stage efficiency. Recommended input range: 0.986 to 0.996.
    stage_frequency (kHz) : float
        Stage frequency. Equal to 0 for DC stages.
    """

    def __init__(
        self,
        power_output,
        voltage_in,
        voltage_out,
        num_phases=1,
        available_modules=1,
        required_modules=1,
        efficiency=0.992,
        stage_frequency=40.,
        **kwargs
    ):
        super().__init__(
            power_output=power_output,
            voltage_in=voltage_in,
            voltage_out=voltage_out,
            num_phases=num_phases,
            available_modules=available_modules,
            required_modules=required_modules,
            efficiency=efficiency,
            stage_frequency=stage_frequency,
            **kwargs
        )

    def calc_mass(self):
        if self.num_phases == 1:
            mass_coefficient = 1.27
            power_level_factor = (self.max_power /
                                  self.required_modules)**(-0.08)
        else:
            mass_coefficient = 2.75
            power_level_factor = (self.max_power /
                                  self.required_modules)**(-0.25)
        efficiency_factor = np.exp(
            0.0048 / (1 - self.efficiency)) / 1.8221
        redundancy_factor = self.available_modules / self.required_modules
        voltage_level_factor = np.exp(self.voltage_in / 200000) * np.exp(self.voltage_out / 200000)
        frequency_factor_1 = self.stage_frequency**(-0.47)
        frequency_factor_2 = (self.stage_frequency / 300)**1.4
        frequency_factor_3 = -(200 / self.max_power)**0.03 * \
            ((max(0., self.stage_frequency - 30)) / 300)**1.7

        basic_mass = mass_coefficient * efficiency_factor * redundancy_factor * self.max_power * \
            (power_level_factor * voltage_level_factor * frequency_factor_1 + frequency_factor_2 + frequency_factor_3)

        return basic_mass  # kg


class StandardTransformerStage(PowerConditioningStage):
    """
    Used in AC power transmission systems primarily at the user end to step down
    a high transmission voltage to a level suitable for secondary distribution.
    Standard AC transformers may also follow an alternator or inverter output in
    certain cases. The standard transformer stage is contained in the
    transformer and transformer/static rectifier models.

    Sources:
    [1] NASA/CR-2011-217268 p.26

    Input Parameters
    ------------
    power_input (kW) : float
        Maximum output power load.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 Vdc.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 Vdc.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    efficiency : float
        Stage efficiency. Recommended input range: 0.986 to 0.996.
    stage_frequency (kHz) : float
        Stage frequency. Equal to 0 for DC stages.
    """

    def __init__(
        self,
        power_output,
        voltage_in,
        voltage_out,
        num_phases=1,
        available_modules=1,
        required_modules=1,
        efficiency=0.98,
        stage_frequency=40.,
        **kwargs
    ):
        super().__init__(
            power_output=power_output,
            voltage_in=voltage_in,
            voltage_out=voltage_out,
            num_phases=num_phases,
            available_modules=available_modules,
            required_modules=required_modules,
            efficiency=efficiency,
            stage_frequency=stage_frequency,
            **kwargs
        )

    def calc_mass(self):
        if self.num_phases == 1:
            mass_coefficient = 1.15
            efficiency_factor = (
                    np.exp(0.0048 / (1 - self.efficiency)) / 1.8221)
            power_level_factor = (self.max_power /
                                  self.required_modules)**(-0.08)
        else:
            mass_coefficient = 2.5
            efficiency_factor = (
                    np.exp(0.003 / (1 - self.efficiency)) / 1.35)
            power_level_factor = (self.max_power /
                                  self.required_modules)**(-0.25)
        redundancy_factor = self.available_modules / self.required_modules
        voltage_level_factor = np.exp(
            self.voltage_in / 200000) * np.exp(self.voltage_out / 200000)
        frequency_factor_1 = self.stage_frequency**(-0.47)
        frequency_factor_2 = (self.stage_frequency / 300)**1.4
        frequency_factor_3 = -(200 / self.max_power)**0.03 * \
            ((max(0., self.stage_frequency - 30)) / 300)**1.7

        basic_mass = mass_coefficient * efficiency_factor * redundancy_factor * self.max_power * \
            power_level_factor * voltage_level_factor * frequency_factor_1 + \
            frequency_factor_2 + frequency_factor_3

        return basic_mass  # kg


class RectifierStage(PowerConditioningStage):
    """
    Converts AC into DC. Is contained in the rectifier, transformer/rectifier,
    dc/dc converter, and frequency converter models. Two basic operating types
    of rectifiers are available, diode and switching. The diode rectifier is a
    static device that simply converts AC into DC. The equations presented here
    are for diode rectifiers.

    Sources:
    [1] NASA/CR-2011-217268 p.29

    Input Parameters
    ------------
    power_input (kW) : float
        Maximum output power load.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 Vdc.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 Vdc.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    efficiency : float
        Stage efficiency. Recommended input range: 0.983 to 0.991.
    stage_frequency (kHz) : float
        Stage frequency. Equal to 0 for DC stages.
    """

    def __init__(
        self,
        power_output,
        voltage_in=28.,
        voltage_out=28.,
        num_phases=1,
        available_modules=3,
        required_modules=2,
        efficiency=None,
        stage_frequency=0.,
        **kwargs
    ):
        if efficiency is None:
            if round(voltage_out, -1) <= 20.:
                efficiency = 0.9670
            elif round(voltage_out, -1) <= 30.:
                efficiency = 0.9795
            elif round(voltage_out, -1) <= 40.:
                efficiency = 0.9820
            elif round(voltage_out, -1) <= 50.:
                efficiency = 0.9838
            elif round(voltage_out, -1) <= 60.:
                efficiency = 0.9850
            elif round(voltage_out, -1) <= 70.:
                efficiency = 0.9856
            elif round(voltage_out, -1) <= 80.:
                efficiency = 0.9862
            elif round(voltage_out, -1) <= 90.:
                efficiency = 0.9866
            elif round(voltage_out, -1) <= 100.:
                efficiency = 0.9868
            else:
                efficiency = 0.9870

        super().__init__(
            power_output=power_output,
            voltage_in=voltage_in,
            voltage_out=voltage_out,
            num_phases=num_phases,
            available_modules=available_modules,
            required_modules=required_modules,
            efficiency=efficiency,
            stage_frequency=stage_frequency,
            **kwargs
        )

    def calc_mass(self):
        if self.num_phases == 1:
            mass_coefficient = 0.1175
        else:
            mass_coefficient = 0.12
        efficiency_factor = (
                np.exp(0.005 / (1 - self.efficiency)) / 1.469)
        redundancy_factor = self.available_modules / self.required_modules
        voltage_level_factor = (self.voltage_in / (self.voltage_in - 2))**6

        basic_mass = mass_coefficient * efficiency_factor * redundancy_factor * self.max_power * \
            voltage_level_factor

        return basic_mass  # kg


class DCFilterStage(PowerConditioningStage):
    """
    Conditions the DC voltage to obtain the quality level required by the
    system. Two DC filters may be required for a component, one on the input and
    another on the output. Most components containing a chopper or rectifier
    will require DC filtering; therefore, DC filter stages are contained in the
    rectifier, DC/DC converter, and inverter models. The filter stage equations
    presented here are generalized and only intended to provide rough mass
    estimates to facilitate component comparisons. A single-stage filter design
    was assumed to precede the chopper and follow the rectifier.

    Sources:
    [1] NASA/CR-2011-217268 p.34

    Input Parameters
    ------------
    power_input (kW) : float
        Maximum output power load.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 Vdc.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 Vdc.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    efficiency : float
        Stage efficiency. Recommended input range: 0.997 to 0.999.
    stage_frequency (kHz) : float
        Stage frequency. Equal to 0 for DC stages.
    ripple_factor_percent : float
        Ripple factor percentage. Recommended input range: 0.1 to 5% (0.001 to
        0.05).
    """

    def __init__(
        self,
        power_output,
        voltage_in,
        voltage_out,
        num_phases=1,
        available_modules=1,
        required_modules=1,
        efficiency=0.998,
        stage_frequency=40.,
        ripple_factor_percent=0.004,
        **kwargs
    ):
        super().__init__(
            power_output=power_output,
            voltage_in=voltage_in,
            voltage_out=voltage_out,
            num_phases=num_phases,
            available_modules=available_modules,
            required_modules=required_modules,
            efficiency=efficiency,
            stage_frequency=stage_frequency,
            **kwargs
        )
        self.ripple_factor_percent = ripple_factor_percent

    def calc_mass(self):
        mass_coefficient = 22.05
        ripple_factor = 1 / ((self.ripple_factor_percent / 0.01)**0.5)
        efficiency_factor = (1 - 0.998) / (1 - self.efficiency)
        redundancy_factor = self.available_modules / self.required_modules
        voltage_level_factor = self.voltage_out**(-0.9) + 0.000015
        if self.num_phases == 1:
            frequency_factor = 40 / self.stage_frequency
        else:
            frequency_factor = 13.33 / self.stage_frequency

        basic_mass = mass_coefficient * ripple_factor * efficiency_factor * \
            redundancy_factor * self.max_power * voltage_level_factor * frequency_factor

        return basic_mass  # kg


class ACFilterStage(PowerConditioningStage):
    """
    Resonant converters can typically achieve less than 5% total harmonic
    distortion without filtering. This is adequate for most PMAD applications;
    however, a series harmonic trap is required to prevent external harmonics
    from being amplified within the converter. Following equations are
    approximate since there is very little concrete data. Equations are based on
    a series resonant circuit tuned to the inversion frequency of the converter.
    Filter configuration consists of a current transformer that is connected in
    parallel with a resistor, and a series connected inductor and capacitor
    combination.

    Sources:
    [1] NASA/CR-2011-217268 p.41

    Input Parameters
    ------------
    power_input (kW) : float
        Maximum output power load.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 Vdc.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 Vdc.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    efficiency : float
        Stage efficiency. Recommended input range: 0.997 to 0.999
    stage_frequency (kHz) : float
        Stage frequency. Equal to 0 for DC stages.
    """

    def __init__(
        self,
        power_output,
        voltage_in,
        voltage_out,
        num_phases=1,
        available_modules=1,
        required_modules=1,
        efficiency=0.995,
        stage_frequency=40.,
        **kwargs
    ):
        super().__init__(
            power_output=power_output,
            voltage_in=voltage_in,
            voltage_out=voltage_out,
            num_phases=num_phases,
            available_modules=available_modules,
            required_modules=required_modules,
            efficiency=efficiency,
            stage_frequency=stage_frequency,
            **kwargs
        )

    def calc_mass(self):
        if self.num_phases == 1:
            mass_coefficient = 0.1
        else:
            mass_coefficient = 0.105
        efficiency_factor = (1 - 0.998) / (1 - self.efficiency)
        redundancy_factor = self.available_modules / self.required_modules
        power_level_factor = (self.max_power /
                              self.required_modules)**(-0.03)
        frequency_factor = (self.stage_frequency / 20) ** (-0.6)

        basic_mass = mass_coefficient * efficiency_factor * redundancy_factor * self.max_power * \
            power_level_factor * frequency_factor

        return basic_mass  # kg


class DCRBIStage(PowerConditioningStage):
    """
    DC remote bus isolators (RBIs) are smart circuit protection devices that
    incorporate current sensors and are used to switch DC power and interrupt
    fault currents. They are located in DC switchgear units. This DC RBI model
    is based on a hybrid switch configuration.

    Sources:
    [1] NASA/CR-2011-217268 p.46

    Input Parameters
    ------------
    power_input (kW) : float
        Maximum output power load.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 Vdc.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 Vdc.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    efficiency : float
        Stage efficiency. Recommended input range: 0.998 to 0.999.
    stage_frequency (kHz) : float
        Stage frequency. Equal to 0 for DC stages.
    """

    def __init__(
        self,
        power_output,
        voltage_in,
        voltage_out,
        num_phases=1,
        available_modules=1,
        required_modules=1,
        efficiency=0.9985,
        stage_frequency=0.,
        **kwargs
    ):
        super().__init__(
            power_output=power_output,
            voltage_in=voltage_in,
            voltage_out=voltage_out,
            num_phases=num_phases,
            available_modules=available_modules,
            required_modules=required_modules,
            efficiency=efficiency,
            stage_frequency=stage_frequency,
            **kwargs
        )

    def calc_mass(self):
        mass_coefficient = 0.12
        efficiency_factor = np.exp(0.0008 / (1 - self.efficiency)) / 1.7
        redundancy_factor = self.available_modules / self.required_modules
        power_level_factor = (self.max_power /
                              self.required_modules)**(-0.15)
        voltage_level_factor = (self.voltage_out / 200)**0.13

        basic_mass = mass_coefficient * efficiency_factor * redundancy_factor * self.max_power * \
            power_level_factor * voltage_level_factor

        return basic_mass  # kg


class ACRBIStage(PowerConditioningStage):
    """
    AC RBIs are smart circuit protection switches with current sensors. They are
    used to switch major ac power feeds and interrupt faults. They are located
    in ac switchgear units.

    Sources:
    [1] NASA/CR-2011-217268 p.50

    Input Parameters
    ------------
    power_input (kW) : float
        Maximum output power load.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 Vdc.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 Vdc.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    efficiency : float
        Stage efficiency. Recommended input range: 0.998 to 0.999.
    stage_frequency (kHz) : float
        Stage frequency. Equal to 0 for DC stages.
    """

    def __init__(
        self,
        power_output,
        voltage_in,
        voltage_out,
        num_phases=1,
        available_modules=1,
        required_modules=1,
        efficiency=0.9985,
        stage_frequency=0.,
        **kwargs
    ):
        super().__init__(
            power_output=power_output,
            voltage_in=voltage_in,
            voltage_out=voltage_out,
            num_phases=num_phases,
            available_modules=available_modules,
            required_modules=required_modules,
            efficiency=efficiency,
            stage_frequency=stage_frequency,
            **kwargs
        )

    def calc_mass(self):
        if self.num_phases == 1:
            mass_coefficient = 0.1
            power_level_factor = (self.max_power / self.required_modules)**(-0.13)
        else:
            mass_coefficient = 0.135
            power_level_factor = (self.max_power / self.required_modules)**(-0.15)
        efficiency_factor = np.exp(0.0008 / (1 - self.efficiency)) / 1.7
        redundancy_factor = self.available_modules / self.required_modules
        voltage_level_factor = (self.voltage_out / 200)**0.05

        basic_mass = mass_coefficient * efficiency_factor * redundancy_factor * self.max_power * \
            power_level_factor * voltage_level_factor

        return basic_mass  # kg


class DCRPCStage(PowerConditioningStage):
    """
    DC remote power controllers (RPCs) are used to switch and monitor individual
    dc load circuits and provide circuit protection. These devices will be
    located in dc power distribution racks.

    Sources:
    [1] NASA/CR-2011-217268 p.55

    Input Parameters
    ------------
    power_input (kW) : float
        Maximum output power load.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 Vdc.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 Vdc.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    efficiency : float
        Stage efficiency. Recommended input range: 0.9965 to 0.9975.
    stage_frequency (kHz) : float
        Stage frequency. Equal to 0 for DC stages.
    """

    def __init__(
        self,
        power_output,
        voltage_in=28.,
        voltage_out=28.,
        num_phases=1,
        available_modules=1,
        required_modules=1,
        efficiency=0.997,
        stage_frequency=0.,
        **kwargs
    ):
        super().__init__(
            power_output=power_output,
            voltage_in=voltage_in,
            voltage_out=voltage_out,
            num_phases=num_phases,
            available_modules=available_modules,
            required_modules=required_modules,
            efficiency=efficiency,
            stage_frequency=stage_frequency,
            **kwargs
        )

    def calc_mass(self):
        mass_coefficient = 0.135
        efficiency_factor = np.exp(
            0.0006 / (1 - self.efficiency)) / 1.2214
        redundancy_factor = self.available_modules / self.required_modules
        power_level_factor = (self.max_power /
                              self.required_modules)**(-0.12)
        voltage_level_factor = (self.voltage_out / 120)**0.04

        basic_mass = mass_coefficient * efficiency_factor * redundancy_factor * self.max_power * \
            power_level_factor * voltage_level_factor

        return basic_mass  # kg


class ACRPCStage(PowerConditioningStage):
    """
    AC RPCs are used to switch and monitor individual ac load circuits and
    provide circuit protection. These devices will be located in ac power
    distribution racks.

    Sources:
    [1] NASA/CR-2011-217268 p.59

    Input Parameters
    ------------
    power_input (kW) : float
        Maximum output power load.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 Vdc.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 Vdc.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    efficiency : float
        Stage efficiency. Recommended input range: 0.9965 to 0.9975.
    stage_frequency (kHz) : float
        Stage frequency. Equal to 0 for DC stages.
    """

    def __init__(
        self,
        power_output,
        voltage_in,
        voltage_out,
        num_phases=1,
        available_modules=1,
        required_modules=1,
        efficiency=0.997,
        stage_frequency=0.,
        **kwargs
    ):
        super().__init__(
            power_output=power_output,
            voltage_in=voltage_in,
            voltage_out=voltage_out,
            num_phases=num_phases,
            available_modules=available_modules,
            required_modules=required_modules,
            efficiency=efficiency,
            stage_frequency=stage_frequency,
            **kwargs
        )

    def calc_mass(self):
        if self.num_phases == 1:
            mass_coefficient = 0.15
            power_level_factor = (self.max_power /
                                  self.required_modules)**(-0.14)
        else:
            mass_coefficient = 0.21
            power_level_factor = (self.max_power /
                                  self.required_modules)**(-0.22)
        efficiency_factor = np.exp(
            0.0007 / (1 - self.efficiency)) / 1.2628
        redundancy_factor = self.available_modules / self.required_modules
        voltage_level_factor = (self.voltage_out / 120)**0.03

        basic_mass = mass_coefficient * efficiency_factor * redundancy_factor * self.max_power * \
            power_level_factor * voltage_level_factor

        return basic_mass  # kg


class ConductorsConnectors:
    """
    Sizes the mass (within a power conditioning component) for the ipnut and
    output connectors, the conductors that transfer power from one stage to the
    next, the control and monitoring harnesses, and the power and control and
    monitoring connectors. 

    "Within a power conditioning component, conductors are required for internal
    power distribution and the transmission of control and monitoring commands
    and data. This section establishes a mass for the input and output power
    conductors, the conductors that transfer power from one stage to the next,
    the control and monitoring harnesses, and the power and control and
    monitoring connectors. This conductor mass doesn't include the wiring within
    a particular stage, for example the wiring in the chopper stage that
    connects its switches and tank hardware. This wiring is included as part of
    the stages ancillary hardware."

    Sources: 
    [1] NASA/CR-2011-217268 p.65

    Input Parameters
    ------------
    power_output (kW) : float
        Maximum output power load of component.
    voltage_in (V) : float
        Input voltage level. Recommended input range: 20 to 10,000 Vdc.
    voltage_out (V) : float
        Output voltage level. Recommended input range: 20 to 10,000 Vdc.
    num_phases_in : int
        Number of input phases.
        Recommended input range: 1 or 3.
    num_phases_out : int
        Number of output phases.
        Recommended input range: 1 or 3.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    component_efficiency : float
        Component efficiency.
    package_length (m) : float
        Packaged electronics length.
    package_width (m) : float
        Packaged electronics width.
    package_height (m) : float
        Packaged electronics height.
    power_conductor_mass_coefficient : float
        Power conductor mass coefficient.
    configuration : str
        Either 'finned' (finned heat exchanger box) or 'coldplate' (coldplate
        box).
    material : str
        Control and monitoring conductors material. Either 'cu' (copper) or 'fo'
        (fiber optic).
    rated_power (kW) : float
        Rated power of component. If None, will be set to max of power_output.
    percent_margin : float
        Amount by which the max power, which the element is sized to, exceeds rated power.
        percent_margin * max power output required = margin
    k_mass : float
        k-factor for scaling mass output. 1 is unscaled.
    """

    def __init__(
        self,
        power_output,
        voltage_in,
        voltage_out,
        num_phases_in,
        num_phases_out,
        available_modules,
        required_modules,
        component_efficiency,
        package_length,
        package_width,
        package_height,
        power_conductor_mass_coefficient=58.6,
        configuration='coldplate',
        material='copper',
        rated_power=None,
        percent_margin=0.,
        k_mass=1.,
    ):
        self.power_output = power_output
        if rated_power is None:
            self.rated_power = np.max(power_output)
        else:
            self.rated_power = max(rated_power, np.max(power_output))
        self.percent_margin = percent_margin
        self.max_power = self.rated_power * (1. + percent_margin)
        self.voltage_in = voltage_in
        self.voltage_out = voltage_out
        if num_phases_in == 1 or num_phases_in == 3:
            self.num_phases_in = num_phases_in
        else:
            raise RuntimeError(
                'Invalid number of input phases. Must be either 1-phase or 3-phase.')
        if num_phases_out == 1 or num_phases_out == 3:
            self.num_phases_out = num_phases_out
        else:
            raise RuntimeError(
                'Invalid number of output phases. Must be either 1-phase or 3-phase.')
        self.available_modules = available_modules
        self.required_modules = required_modules
        self.component_efficiency = component_efficiency
        self.package_length = package_length
        self.package_width = package_width
        self.package_height = package_height
        self.power_conductor_mass_coefficient = power_conductor_mass_coefficient
        if configuration.lower() == 'fh' or configuration.lower() == 'finned':
            self.configuration = 'fh'
        elif configuration.lower() == 'cp' or configuration.lower() == 'coldplate':
            self.configuration = 'cp'
        else:
            raise RuntimeError(
                "Invalid component enclosure type."
                "Must be either 'coldplate' (coldplate box) or 'finned' (finned heat exchanger box)."
            )
        if material.lower() == 'cu' or material.lower() == 'copper':
            self.material = 'cu'
        elif material.lower() == 'fo' or material.lower() == 'fiber optic':
            self.material = 'fo'
        else:
            raise RuntimeError(
                "Invalid conductor and connector material."
                "Must be either 'cu' (copper) or 'fo' (fiber optic)."
            )
        self.k_mass = k_mass

        self._mass = None

    @property
    def mass(self):
        if self._mass is None:
            self._mass = self.k_mass * self.calc_mass()
        return self._mass  # kg

    def calc_mass(self):
        power_conductor_mass_coefficient = self.power_conductor_mass_coefficient

        if self.voltage_in == self.voltage_out:
            voltage_factor = self.max_power / self.voltage_out
        else:
            power_conductor_mass_coefficient = power_conductor_mass_coefficient / 2.
            voltage_factor = self.max_power / self.component_efficiency / self.voltage_in \
                + self.max_power / self.voltage_out

        num_phases = min(self.num_phases_in, self.num_phases_out)
        if num_phases == 1:
            phases_coefficient = 1
            phases_factor = 1
        else:
            phases_coefficient = 1.5
            phases_factor = 3**0.5 / 2

        if self.configuration == 'fh':
            configuration_factor = 0.5 * \
                (self.package_length + self.package_width) + self.package_height
        else:
            configuration_factor = 0.5 * \
                (self.package_length + self.package_width) + \
                0.75 * self.package_height

        if self.material == 'cu':
            material_coefficient = 5.22
        else:
            material_coefficient = 2.61

        redundancy_factor = self.available_modules / self.required_modules
        power_conductor_mass = redundancy_factor * power_conductor_mass_coefficient * phases_factor * \
            configuration_factor * voltage_factor
        control_monitoring_cable_harness_mass = self.available_modules * \
            (material_coefficient * phases_coefficient * configuration_factor)
        power_control_monitoring_connector_mass = self.available_modules * \
            (phases_coefficient * 0.238 * (self.max_power / self.required_modules)**0.1 +
             0.2667 * (self.max_power / self.required_modules)**0.5)

        basic_mass = power_conductor_mass + control_monitoring_cable_harness_mass + \
            power_control_monitoring_connector_mass  # kg

        return basic_mass  # kg


class ControlMonitoringSubsystem:
    """
    "Each of the power conditioning components will have some type of control
    and monitoring subsystem. This subsystem was assumed to consist of a
    controller card, a data interface module, various voltage, current, and
    temperature sensors, and a housekeeping power supply."

    Sources:
    [1] NASA/CR-2011-217268 p.68

    Input Parameters
    ------------
    power_output (kW) : float or np.ndarray
        Output power load of component.
    num_phases : int
        Number of phases. Recommended input range: 1 or 3. 1 for DC.
    available_modules : int
        Available modules. Recommended input range: 1-5.
    required_modules : int
        Required modules. Recommended input range: 1-5.
    power_supply_specific_mass (kg/kW) : float
        Specific mass of control and monitoring subsystem power supply.
    power_supply_efficiency : float
        Efficiency of control and monitoring subsystem power supply.
    power_supply_margin : float
        Power rating margin of control and monitoring subsystem power supply.
    rated_power (kW) : float
        Rated power of component. If None, will be set to max of power_output.
    percent_margin : float
        Amount by which the max power, which the element is sized to, exceeds rated power.
        percent_margin * max power output required = margin
    k_mass : float
        k-factor for scaling mass output. 1 is unscaled.
    """

    def __init__(
        self,
        power_output,
        num_phases=1,
        available_modules=1,
        required_modules=1,
        power_usage_coefficient=None,
        control_data_module_mass=None,
        sensor_mass_coefficient=None,
        power_supply_specific_mass=70.,
        power_supply_efficiency=0.75,
        power_supply_margin=0.1,
        rated_power=None,
        percent_margin=0.,
        k_mass=1.,
    ):
        self.power_output = power_output
        if rated_power is None:
            self.rated_power = np.max(power_output)
        else:
            self.rated_power = max(rated_power, np.max(power_output))
        self.percent_margin = percent_margin
        self.max_power = self.rated_power * (1. + percent_margin)
        if num_phases == 1 or num_phases == 3:
            self.num_phases = num_phases
        else:
            raise RuntimeError(
                'Invalid number of phases. Must be either 1-phase or 3-phase.')
        self.available_modules = available_modules
        self.required_modules = required_modules
        self.power_usage_coefficient = power_usage_coefficient
        self.control_data_module_mass = control_data_module_mass
        self.sensor_mass_coefficient = sensor_mass_coefficient
        self.power_supply_specific_mass = power_supply_specific_mass
        self.power_supply_efficiency = power_supply_efficiency
        self.power_supply_margin = power_supply_margin
        self.k_mass = k_mass

        self._mass = None
        self._power = None
        self._heat_output = None

    @property
    def mass(self):
        if self._mass is None:
            self._mass = self.k_mass * self.calc_mass()
        return self._mass  # kg

    @property
    def power(self):
        if self._power is None:
            if isinstance(self.power_output, np.ndarray):
                self._power = self.calc_power() * np.ones(self.power_output.size)
            else:
                self._power = self.calc_power()
        return self._power  # kW

    @property
    def heat_output(self):
        if self._heat_output is None:
            self._heat_output = self.calc_heat()
        return self._heat_output  # kW

    def calc_mass(self):
        if self.num_phases == 1:
            if self.control_data_module_mass is None:
                self.control_data_module_mass = 1.2
            if self.sensor_mass_coefficient is None:
                self.sensor_mass_coefficient = 0.158
        else:
            if self.control_data_module_mass is None:
                self.control_data_module_mass = 1.6
            if self.sensor_mass_coefficient is None:
                self.sensor_mass_coefficient = 0.316

        power_supply_mass = self.power_supply_specific_mass * self.power_supply_efficiency * \
            (1.+self.power_supply_margin) * self.calc_power()
        basic_mass = self.available_modules * \
            (self.control_data_module_mass + self.sensor_mass_coefficient *
             (self.max_power / self.required_modules) ** 0.5) + power_supply_mass

        return basic_mass  # kg

    def calc_power(self):
        if self.power_usage_coefficient is None:
            if self.num_phases == 1:
                self.power_usage_coefficient = 43.3
            else:
                self.power_usage_coefficient = 57.4

        power_usage = (self.available_modules * self.power_usage_coefficient * (
                self.max_power / self.required_modules) ** 0.1) / 1000.

        return power_usage  # kW

    def calc_heat(self):
        heat_output = self.power

        return heat_output  # kW


class ComponentEnclosure:
    """
    Sizes the mass of the component enclosure box. This contains all the power
    conditioning stages within a power conditioning model. The enclosure box
    protects the internal components from the external environment and provides
    ease of handling.

    Sources: 
    [1] NASA/CR-2011-217268 p.70

    Input Parameters
    ------------
    power_output (kW) : float
        Maximum output power load of component.
    component_electronics_mass (kg) : float
        Component electronics mass (stages, control and monitoring subsystem, and conductors and connectors).
    electronics_mass (kg) float
        Mass of elemental electronics (stages and control and monitoring subsystem).
    required_modules : int
        Required modules. Recommended input range: 1-5.
    package_density (kg/m**3) : float
        Packaged electronics density for selected box type.
    electronics_density (g/cm**2) : float
        Density of component's elemental electronics.
    configuration : str
        Either 'finned' (finned heat exchanger box) or 'coldplate' (coldplate box).
    material : str
        Box material. Either 'cu' (copper) or 'fo' (fiber optic).
    internal_packaging_end_coefficient : float
        Mass coefficient for internal packaging and support boxes based on end area of electronics volume.
    internal_packaging_side_coefficient : float
        Mass coefficient for internal packaging and support boxes based on side area of electronics volume.
    rated_power (kW) : float
        Rated power of component. If None, will be set to max of power_output.
    percent_margin : float
        Amount by which the max power, which the element is sized to, exceeds rated power.
        percent_margin * max power output required = margin
    k_mass : float
        k-factor for scaling mass output. 1 is unscaled.
    """

    def __init__(
        self,
        power_output,
        component_electronics_mass,
        electronics_mass,
        required_modules,
        package_density=0.382*1.05,
        electronics_density=0.45,
        configuration='coldplate',
        material='cu',
        internal_packaging_end_coefficient=13.12,
        internal_packaging_side_coefficient=8.02,
        rated_power=None,
        percent_margin=0.,
        k_mass=1.,
    ):
        self.power_output = power_output
        if rated_power is None:
            self.rated_power = np.max(power_output)
        else:
            self.rated_power = max(rated_power, np.max(power_output))
        self.percent_margin = percent_margin
        self.max_power = self.rated_power * (1. + percent_margin)
        self.rated_power = np.max(power_output)
        self.required_modules = required_modules
        self.component_electronics_mass = component_electronics_mass
        self.electronics_mass = electronics_mass
        self.package_density = package_density
        if configuration.lower() == 'fh' or configuration.lower() == 'finned':
            self.configuration = 'fh'
        elif configuration.lower() == 'cp' or configuration.lower() == 'coldplate':
            self.configuration = 'cp'
        else:
            raise RuntimeError(
                "Invalid component enclosure type. "
                "Must be either 'coldplate' (coldplate box) or 'finned' (finned heat exchanger box)."
            )
        if material.lower() == 'al' or material.lower() == 'aluminum':
            self.material = 'al'
        elif material.lower() == 'cc' or material.lower() == 'carbon-carbon':
            self.material = 'cc'
        else:
            raise RuntimeError(
                "Invalid component enclosure material. Must be either 'al' (aluminum) or 'cc' (carbon-carbon)."
            )
        self.electronics_density = electronics_density
        self.internal_packaging_end_coefficient = internal_packaging_end_coefficient
        self.internal_packaging_side_coefficient = internal_packaging_side_coefficient
        self.k_mass = k_mass

        self._length_ar = None
        self._width_ar = None
        self._height_ar = None

        self._mass = None
        self._length = None
        self._width = None
        self._height = None
        self._volume = None

    @property
    def mass(self):
        if self._mass is None:
            self._mass = self.k_mass * self.calc_mass()
        return self._mass  # kg

    @property
    def length(self):
        if self._length is None:
            self.calc_dimensions()
        return self._length  # m

    @property
    def width(self):
        if self._width is None:
            self.calc_dimensions()
        return self._width  # m

    @property
    def height(self):
        if self._height is None:
            self.calc_dimensions()
        return self._height  # m

    @property
    def volume(self):
        if self._volume is None:
            self._volume = self.calc_volume()
        return self._volume  # m**3

    def calc_dimensions(self):
        component_volume = self.volume
        if self.configuration == 'cp':
            self._length_ar = 1.610
            self._width_ar = 1.043
            self._height_ar = 0.596
            self._length = 1.610 * component_volume**(1 / 3)
            self._width = 1.043 * component_volume**(1 / 3)
            self._height = 0.596 * component_volume**(1 / 3)
        else:
            self._length_ar = 1.351
            self._width_ar = 1.148
            self._height_ar = 0.646
            self._length = 1.351 * component_volume**(1 / 3)
            self._width = 1.148 * component_volume**(1 / 3)
            self._height = 0.646 * component_volume**(1 / 3)
        return self._length, self._width, self._height  # m, m, m

    def calc_mass(self):
        length = self.length
        width = self.width
        height = self.height

        if self.configuration == 'cp':
            connector_mounting_hardware_mass = 0.35 * (self.max_power / self.required_modules) ** 0.3
        else:
            connector_mounting_hardware_mass = 3.4 * (self.max_power / self.required_modules) ** 0.3

        if self.material == 'al':
            box_mass = 8.1 * (length * width + 2 * length * height + 2 * width * height)
        else:
            box_mass = 5.0 * (length * width + 2 * length * height + 2 * width * height)

        if self.configuration == 'cp':
            if self.material == 'al':
                baseplate_mass = 33.45 * length * width
            else:
                baseplate_mass = 20.44 * length * width
        else:
            if self.material == 'al':
                baseplate_mass = 44.6 * length * width
            else:
                baseplate_mass = 27.3 * length * width

        electronics_volume = 1.25 * self.electronics_mass / (self.electronics_density * 1000.)

        electronics_length = self._length_ar * electronics_volume**(1 / 3)
        electronics_width = self._width_ar * electronics_volume**(1 / 3)
        electronics_height = self._height_ar * electronics_volume**(1 / 3)

        internal_packaging_mass = 13.12 * (electronics_length * electronics_width) + \
            8.02 * (electronics_length * electronics_height + electronics_width * electronics_height)

        basic_mass = connector_mounting_hardware_mass + box_mass + baseplate_mass

        return basic_mass  # kg

    def calc_volume(self):
        enclosure_volume = self.component_electronics_mass / (self.package_density * 1000.)

        return enclosure_volume  # m**3


class ComponentRadiator:
    """
    "A radiator is needed to dissipate the waste heat a power conditioning component generates.
    The DDCU heat pipe (HP) radiator design was used to develop the radiator equations in these models."
    This component radiator model consists of a baseplate section for mounting to the PMAD component
    and a radiator section.

    Sources:
    [1] NASA/CR-2011-217268 p.75-76

    Input Parameters
    ------------
    heat_load (kW) : float or np.ndarray
        Heat load that must be dissipated by the radiator.
    material : str
        Baseplate and radiator material.
        Either 'al' (aluminum) or 'cc' (carbon-carbon).
    radiator_sides : int
        Number of radiator sides.
        Either 1 or 2.
    radiator_temperature_delta (K) : float
        Temperature delta from baseplate to radiator surface.
    radiator_temperature_sink (K) : float
        Temperature of radiator sink.
    radiator_temperature_baseplate (K) : float
        Temperature of radiator baseplate.
    baseplate_length (m) : float
        Length of radiator baseplate.
    baseplate_width (m) : float
        Width of radiator baseplate.
    rated_heat (kW) : float
        Rated heat load of the radiator. If None, will be set to max of heat_load.
    percent_margin : float
        Amount by which the max heat load, which the radiator is sized to, exceeds rated heat load.
        max_heat = rated_heat * (1 + percent_margin)
        percent_margin * max heat load to be dissipated = margin
    k_mass : float
        k-factor for scaling mass output. 1 is unscaled.
    """
    def __init__(
        self,
        heat_load,
        material='carbon-carbon',
        radiator_sides=2,
        radiator_temperature_delta=4.,
        radiator_temperature_sink=294.,
        radiator_temperature_baseplate=336.,
        baseplate_length=0.591,
        baseplate_width=0.590,
        rated_heat=None,
        percent_margin=0.,
        k_mass=1.,
    ):
        self.heat_load = heat_load
        if rated_heat is None:
            self.rated_heat = np.max(heat_load)
        else:
            self.rated_heat = max(rated_heat, np.max(heat_load))
        self.percent_margin = percent_margin
        self.max_heat = self.rated_heat * (1. + percent_margin)
        if material.lower() == 'al' or material.lower() == 'aluminum':
            self.material = 'al'
        elif material.lower() == 'cc' or material.lower() == 'carbon-carbon':
            self.material = 'cc'
        else:
            raise RuntimeError(
                "Invalid radiator material. Must be either 'al' (aluminum) or 'cc' (carbon-carbon)."
            )
        self.radiator_sides = radiator_sides
        self.radiator_temperature_delta = radiator_temperature_delta
        self.radiator_temperature_sink = radiator_temperature_sink
        self.radiator_temperature_baseplate = radiator_temperature_baseplate
        self.baseplate_length = baseplate_length
        self.baseplate_width = baseplate_width
        self.k_mass = k_mass

        self._mass = None
        self._area = None

    @property
    def mass(self):
        if self._mass is None:
            self._mass = self.k_mass * self.calc_mass()
        return self._mass  # kg

    @property
    def area(self):
        if self._area is None:
            self._area = self.calc_area()
        return self._area  # m**2

    def calc_area(self):
        radiator_area = (1.0823e10 / self.radiator_sides * self.max_heat) / \
                     ((self.radiator_temperature_baseplate - self.radiator_temperature_delta) ** 4 -
                      self.radiator_temperature_sink ** 4)
        return radiator_area  # m**2

    def calc_mass(self):
        if self.material == 'al':
            radiator_coeff = 22.26
        else:
            radiator_coeff = 13.6

        coldplate_mass = radiator_coeff * self.baseplate_length * self.baseplate_width
        radiator_mass = radiator_coeff * self.area

        self._mass = self.k_mass * (coldplate_mass + radiator_mass)

        return self._mass  # kg


if __name__ == "__main__":
    print_options = np.get_printoptions()
    np_precision = print_options['precision']

    chopper_stage = ChopperStage(
        power_output=1, voltage_in=120, voltage_out=120)
    mass = chopper_stage.calc_mass()
    mass = np.round(mass, np_precision)
    power_input = chopper_stage.calc_power()
    power_input = np.round(power_input, np_precision)
    heat = chopper_stage.calc_heat_output()
    heat = np.round(heat, np_precision)
    print(f'chopper_stage_mass = {mass} (kg)')
    print(f'chopper_stage_power_input = {power_input} (kW)')
    print(f'chopper_stage_heat = {heat} (kW)')

    chopper2_stage = ResonantChopperStage(
        power_output=1, voltage_in=120, voltage_out=120)
    mass = chopper2_stage.calc_mass()
    mass = np.round(mass, np_precision)
    power_input = chopper2_stage.calc_power()
    power_input = np.round(power_input, np_precision)
    heat = chopper2_stage.calc_heat_output()
    heat = np.round(heat, np_precision)
    print(f'chopper2_stage_mass = {mass} (kg)')
    print(f'chopper2_stage_power_input = {power_input} (kW)')
    print(f'chopper2_stage_heat = {heat} (kW)')

    inverter_transformer_stage = InverterTransformerStage(
        power_output=1, voltage_in=120, voltage_out=120)
    mass = inverter_transformer_stage.calc_mass()
    mass = np.round(mass, np_precision)
    power_input = inverter_transformer_stage.calc_power()
    power_input = np.round(power_input, np_precision)
    heat = inverter_transformer_stage.calc_heat_output()
    heat = np.round(heat, np_precision)
    print(f'inverter_transformer_stage_mass = {mass} (kg)')
    print(f'inverter_transformer_stage_power_input = {power_input} (kW)')
    print(f'inverter_transformer_stage_heat = {heat} (kW)')

    standard_transformer_stage = StandardTransformerStage(
        power_output=1, voltage_in=120, voltage_out=120)
    mass = standard_transformer_stage.calc_mass()
    mass = np.round(mass, np_precision)
    power_input = standard_transformer_stage.calc_power()
    power_input = np.round(power_input, np_precision)
    heat = standard_transformer_stage.calc_heat_output()
    heat = np.round(heat, np_precision)
    print(f'standard_transformer_stage_mass = {mass} (kg)')
    print(f'standard_transformer_stage_power_input = {power_input} (kW)')
    print(f'standard_transformer_stage_heat = {heat} (kW)')

    rectifier_stage = RectifierStage(
        power_output=1, voltage_in=120, voltage_out=120)
    mass = rectifier_stage.calc_mass()
    mass = np.round(mass, np_precision)
    power_input = rectifier_stage.calc_power()
    power_input = np.round(power_input, np_precision)
    heat = rectifier_stage.calc_heat_output()
    heat = np.round(heat, np_precision)
    print(f'rectifier_stage_mass = {mass} (kg)')
    print(f'rectifier_stage_power_input = {power_input} (kW)')
    print(f'rectifier_stage_heat = {heat} (kW)')

    dc_filter_stage = DCFilterStage(
        power_output=1, voltage_in=120, voltage_out=120)
    mass = dc_filter_stage.calc_mass()
    mass = np.round(mass, np_precision)
    power_input = dc_filter_stage.calc_power()
    power_input = np.round(power_input, np_precision)
    heat = dc_filter_stage.calc_heat_output()
    heat = np.round(heat, np_precision)
    print(f'dc_filter_stage_mass = {mass} (kg)')
    print(f'dc_filter_stage_power_input = {power_input} (kW)')
    print(f'dc_filter_stage_heat = {heat} (kW)')

    ac_filter_stage = ACFilterStage(
        power_output=1, voltage_in=120, voltage_out=120)
    mass = ac_filter_stage.calc_mass()
    mass = np.round(mass, np_precision)
    power_input = ac_filter_stage.calc_power()
    power_input = np.round(power_input, np_precision)
    heat = ac_filter_stage.calc_heat_output()
    heat = np.round(heat, np_precision)
    print(f'ac_filter_stage_mass = {mass} (kg)')
    print(f'ac_filter_stage_power_input = {power_input} (kW)')
    print(f'ac_filter_stage_heat = {heat} (kW)')

    dcrbi_stage = DCRBIStage(power_output=1, voltage_in=120, voltage_out=120)
    mass = dcrbi_stage.calc_mass()
    mass = np.round(mass, np_precision)
    power_input = dcrbi_stage.calc_power()
    power_input = np.round(power_input, np_precision)
    heat = dcrbi_stage.calc_heat_output()
    heat = np.round(heat, np_precision)
    print(f'dcrbi_stage_mass = {mass} (kg)')
    print(f'dcrbi_stage_power_input = {power_input} (kW)')
    print(f'dcrbi_stage_heat = {heat} (kW)')

    acrbi_stage = ACRBIStage(power_output=1, voltage_in=120, voltage_out=120)
    mass = acrbi_stage.calc_mass()
    mass = np.round(mass, np_precision)
    power_input = acrbi_stage.calc_power()
    power_input = np.round(power_input, np_precision)
    heat = acrbi_stage.calc_heat_output()
    heat = np.round(heat, np_precision)
    print(f'acrbi_stage_mass = {mass} (kg)')
    print(f'acrbi_stage_power_input = {power_input} (kW)')
    print(f'acrbi_stage_heat = {heat} (kW)')

    dcrpc_stage = DCRPCStage(power_output=1, voltage_in=120, voltage_out=120)
    mass = dcrpc_stage.calc_mass()
    mass = np.round(mass, np_precision)
    power_input = dcrpc_stage.calc_power()
    power_input = np.round(power_input, np_precision)
    heat = dcrpc_stage.calc_heat_output()
    heat = np.round(heat, np_precision)
    print(f'dcrpc_stage_mass = {mass} (kg)')
    print(f'dcrpc_stage_power_input = {power_input} (kW)')
    print(f'dcrpc_stage_heat = {heat} (kW)')

    acrpc_stage = ACRPCStage(power_output=1, voltage_in=120, voltage_out=120)
    mass = acrpc_stage.calc_mass()
    mass = np.round(mass, np_precision)
    power_input = acrpc_stage.calc_power()
    power_input = np.round(power_input, np_precision)
    heat = acrpc_stage.calc_heat_output()
    heat = np.round(heat, np_precision)
    print(f'acrpc_stage_mass = {mass} (kg)')
    print(f'acrpc_stage_power_input = {power_input} (kW)')
    print(f'acrpc_stage_heat = {heat} (kW)')

    conductors_connectors = ConductorsConnectors(
        power_output=1,
        voltage_in=120,
        voltage_out=120,
        num_phases_in=1,
        num_phases_out=1,
        available_modules=1,
        required_modules=1,
        component_efficiency=0.99,
        package_length=1,
        package_width=1,
        package_height=1,
        configuration='coldplate',
        material='cu',
    )
    mass = conductors_connectors.calc_mass()
    mass = np.round(mass, np_precision)
    print(f'conductors_connectors_mass = {mass} (kg)')

    controller_monitoring_subsystem = ControlMonitoringSubsystem(
        power_output=1., num_phases=1, available_modules=1, required_modules=1)
    mass = controller_monitoring_subsystem.calc_mass()
    mass = np.round(mass, np_precision)
    power_draw = controller_monitoring_subsystem.calc_power()
    power_draw = np.round(power_draw, np_precision)
    heat = controller_monitoring_subsystem.calc_heat()
    heat = np.round(heat, np_precision)
    print(f'controller_monitoring_subsystem_mass = {mass} (kg)')
    print(f'controller_monitoring_subsystem_power = {power_draw} (kW)')
    print(f'controller_monitoring_subsystem_heat = {heat} (kW)')

    component_enclosure = ComponentEnclosure(
        power_output=1.,
        required_modules=1,
        component_electronics_mass=5.,
        electronics_mass=5.,
        package_density=0.382,
        configuration='coldplate',
        material='cc',
    )
    mass = component_enclosure.calc_mass()
    mass = np.round(mass, np_precision)
    volume = component_enclosure.calc_volume()
    volume = np.round(volume, np_precision)
    print(f'component_enclosure_mass = {mass} (kg)')
    print(f'component_enclosure_volume = {volume} (m**3)')
