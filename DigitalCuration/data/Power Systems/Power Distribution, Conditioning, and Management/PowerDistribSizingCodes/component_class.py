from stages import *
from abc import ABC, abstractmethod


class PowerConditioningComponent(ABC):
    """
    This is defined as a class for specific power conditioning components defined in
    'Power Management and Distribution (PMAD) Model Development Final Report' to inherit from.
    Consolidates common methods for declaring enclosure options, defining resource models, calculating and performing
    heat calculations.

    power_output (kW) : float or np.ndarray
        Output power level.
        If is float, will assume power_input is max power and power() method will return max input power required.
        If np.ndarray, will size mass to max value and power() method will return ndarray of input power required.
    rated_power (kW) : float
        Rated power. Max power output that the stage can handle. If None, will be set to max of power_output
    percent_margin : float
        Amount by which rated power output of components should exceed max power output required.
        percent_margin * max power output required = margin
    voltage_in (V) : float
        Input voltage level.
        Recommended input range: 20 to 10,000 V.
    voltage_out (V) : float
        Output voltage level.
        Recommended input range: 20 to 10,000 V.
    num_phases_in : int
        Number of input phases.
        Recommended input range: 1 or 3.
    num_phases_out : int
        Number of output phases.
        Recommended input range: 1 or 3.
    frequency_in (kHz) : float
        Input frequency.
        Recommended input range: 60 Hz to 5 kHz
    frequency_out (kHz) : float
        Output frequency.
        Recommended input range: 60 Hz to 5 kHz
    available_modules : int
        Available modules of constituent stages. Must be >= required modules.
        Available modules / required modules gives redundancy.
        Recommended input range: 1-5.
    required_modules : int
        Required modules of constituent stages.
        Recommended input range: 1-5.
    conductor_material : str
        Conductor and connector material. Includes control and monitoring conductors, power conductors,
        control and monitoring cable harness, and control and monitoring connectors.
        'copper' or 'fiber optic'
    power_conductor_mass_coefficient : float
        Mass coefficient to allow for custom power conductor mass
    enclosure_baseplate_type: str
        Enclosure baseplate type. The coldplate design is representative of a typical satellite box. The finned
        configuration accounts for hardware to support the orbital replacement unit (ORU) removal and replacement
        requirements of the ISS finned heat exchanger design.
        Either 'finned' (finned heat exchanger) or 'coldplate' (coldplate).
    enclosure_material : str
        Material used for enclosure box and hardware mass calculations.
        Carbon-carbon as several advantages over aluminum including being significantly lighter, but Aluminum is much
        less expensive than carbon-carbon.
        Either 'al' (aluminum) or 'cc' (carbon-carbon).
    electronics_density (g/cm**3) : float
        Electronics density.
    include_enclosure : bool
        True if enclosure should be included in component. False if not.
    k_mass_stages : float
        k-factor for scaling masses of each stage. 1 is unscaled.
    k_mass_conductors : float
        k-factor for scaling mass of conductors and connectors. 1 is unscaled.
    k_mass_cms : float
        k-factor for scaling mass of control and monitoring subsystem. 1 is unscaled.
    k_mass_enclosure : float
        k-factor for scaling mass of enclosure. 1 is unscaled.
    k_mass_radiators : float
        k-factor for scaling mass of radiators. 1 is unscaled.
    k_mass_simple : float
        k_factor for applying simple scale factor for overall mass and masses in mass breakdown. Does not apply scale
        factor to individual element objects.

    Sources:
    [1] NASA/CR-2011-217268
    [2] NASA-CR-189225
    """

    def __init__(
            self,
            power_output,
            voltage_in=28.,
            voltage_out=28.,
            num_phases_in=1,
            num_phases_out=1,
            frequency_in=0.,
            frequency_out=0.,
            available_modules=1,
            required_modules=1,
            rated_power=None,
            percent_margin=0.,
            conductor_material='copper',
            power_conductor_mass_coefficient=58.6,
            enclosure_baseplate_type='coldplate',
            enclosure_material='carbon-carbon',
            packaged_electronics_density=None,
            electronics_density=0.45,
            include_enclosure=True,
            cms_power_usage_coefficient=None,
            cms_control_data_module_mass=None,
            cms_sensor_mass_coefficient=None,
            cms_power_supply_specific_mass=70.,
            cms_power_supply_efficiency=0.75,
            cms_power_supply_margin=0.1,
            include_radiator=False,
            radiator_material_coff=13.6,
            radiator_sides=2,
            radiator_temperature_delta=None,
            radiator_temperature_sink=294.,
            radiator_temperature_baseplate=336.,
            auto_baseplate_dimensions=True,
            baseplate_length=0.591,
            baseplate_width=0.590,
            k_mass_stages=1.,
            k_mass_conductors=1.,
            k_mass_cms=1.,
            k_mass_enclosure=1.,
            k_mass_radiators=1.,
            k_mass_simple=1.,
            **kwargs
    ):

        # General PMAD Component Inputs
        self.power_output = power_output
        if rated_power is None:
            self.rated_power = np.max(power_output)
        else:
            self.rated_power = max(rated_power, np.max(power_output))
        self.percent_margin = percent_margin
        self.max_power = max(self.rated_power * (1. + percent_margin), 0.5)
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
        self.frequency_in = frequency_in
        self.frequency_out = frequency_out
        self.available_modules = available_modules
        self.required_modules = required_modules

        # Conductor and Connector Inputs
        self.conductor_material = conductor_material
        self.power_conductor_mass_coefficient = power_conductor_mass_coefficient
        self._conductors_connectors = None

        self.electronics_length = None
        self.electronics_width = None
        self.electronics_height = None

        # Control and Monitoring System
        self._control_monitoring_subsystem = None
        self.cms_power_usage_coefficient = cms_power_usage_coefficient
        self.cms_control_data_module_mass = cms_control_data_module_mass
        self.cms_sensor_mass_coefficient = cms_sensor_mass_coefficient
        self.cms_power_supply_specific_mass = cms_power_supply_specific_mass
        self.cms_power_supply_efficiency = cms_power_supply_efficiency
        self.cms_power_supply_margin = cms_power_supply_margin

        # Component Enclosure Inputs
        self.include_enclosure = include_enclosure
        if include_enclosure:
            self._enclosure = None
        if enclosure_baseplate_type.lower() == 'fh' or enclosure_baseplate_type.lower() == 'finned':
            self.enclosure_baseplate_type = 'fh'
        elif enclosure_baseplate_type.lower() == 'cp' or enclosure_baseplate_type.lower() == 'coldplate':
            self.enclosure_baseplate_type = 'cp'
        else:
            raise RuntimeError(
                "Invalid component enclosure type. "
                "Must be either 'coldplate' (coldplate box) or 'finned' (finned heat exchanger box)."
            )
        self.enclosure_material = enclosure_material
        if packaged_electronics_density is None:
            if self.enclosure_baseplate_type == 'cp':
                self.packaged_electronics_density = 0.382 * 1.05
            else:
                self.packaged_electronics_density = 0.197 * 1.05
        else:
            self.packaged_electronics_density = packaged_electronics_density
        self.electronics_density = electronics_density

        # Built-in Radiator Inputs
        self.include_radiator = include_radiator
        if include_radiator:
            self._radiator = None
        self.radiator_material_coeff = radiator_material_coff
        self.radiator_sides = radiator_sides
        if radiator_temperature_delta is None:
            if self.enclosure_baseplate_type == 'fh':
                self.radiator_temperature_delta = 11.
            else:
                self.radiator_temperature_delta = 4.
        else:
            self.radiator_temperature_delta = radiator_temperature_delta
        self.radiator_temperature_sink = radiator_temperature_sink
        self.radiator_temperature_baseplate = radiator_temperature_baseplate
        self.auto_baseplate_dimensions = auto_baseplate_dimensions
        if not auto_baseplate_dimensions:
            self.baseplate_length = baseplate_length
            self.baseplate_width = baseplate_width

        self.k_mass_stages = k_mass_stages
        self.k_mass_conductors = k_mass_conductors
        self.k_mass_cms = k_mass_cms
        self.k_mass_enclosure = k_mass_enclosure
        self.k_mass_radiators = k_mass_radiators
        self.k_mass_simple = k_mass_simple

        # Additional Inputs
        self.__dict__.update(kwargs)

        self._stages = dict()
        self._stages_efficiency = None
        self._stages_mass = None

        self._ancillary_hardware_mass = None

        self._mass = None

        self._length = None
        self._width = None
        self._height = None
        self._volume = None
        self._power_input = None
        self._heat_output = None

        self._efficiency = None
        self._specific_mass = None
        self._mass_breakdown = None

    @property
    def stages(self):
        if not self._stages:
            self.initialize_stages()
        return self._stages

    @property
    def stages_efficiency(self):
        if self._stages_efficiency is None:
            self.initialize_stages()
        return self._stages_efficiency

    @property
    def stages_mass(self):
        if self._stages_mass is None:
            self.initialize_stages()
        return self._stages_mass  # kg

    @abstractmethod
    def initialize_stages(self):
        pass

    @property
    def efficiency(self):
        if self._efficiency is None:
            self.calc_efficiency()
        return self._efficiency

    def calc_efficiency(self):
        self._efficiency = np.max(self.power_output) / np.max(self.power_input)
        return self._efficiency

    @property
    def mass(self):
        if self._mass is None:
            self.calc_mass()
        return self._mass  # kg

    def calc_mass(self):
        self._mass = self.k_mass_simple * (self.stages_mass + self.ancillary_hardware_mass)
        return self._mass  # kg

    @property
    def specific_mass(self):
        if self._specific_mass is None:
            self._specific_mass = self.mass / self.power_output
        return self._specific_mass  # kg / kW

    @property
    def length(self):
        if self._length is None:
            self._length = self.enclosure.length
        return self._length

    @property
    def width(self):
        if self._width is None:
            self._width = self.enclosure.width
        return self._width  # m

    @property
    def height(self):
        if self._height is None:
            self._height = self.enclosure.height
        return self._height  # m

    @property
    def volume(self):
        if self._volume is None:
            self._volume = self.enclosure.volume
        return self._volume  # m**3

    @property
    def power_input(self):
        if self._power_input is None:
            self.calc_power_input()
        return self._power_input  # kW

    def calc_power_input(self):
        self._power_input = self.power_output / self.stages_efficiency + self.control_monitoring_subsystem.power
        return self._power_input  # kW

    @property
    def heat_output(self):
        if self._heat_output is None:
            self.calc_heat_output()
        return self._heat_output  # kW

    def calc_heat_output(self):
        if self.include_radiator:
            self._heat_output = 0.
        else:
            self._heat_output = self.power_input - self.power_output
        return self._heat_output  # kW

    @property
    def mass_breakdown(self):
        if self._mass_breakdown is None:
            self._mass_breakdown = {}
            for stage in self.stages:
                self._mass_breakdown[stage] = self.k_mass_simple * self.stages[stage].mass
            self._mass_breakdown['conductors_connectors'] = self.k_mass_simple * self.conductors_connectors.mass
            self._mass_breakdown['control_monitoring_subsystem'] = self.k_mass_simple * \
                self.control_monitoring_subsystem.mass
            if self.include_enclosure:
                self._mass_breakdown['enclosure'] = self.k_mass_simple * self.enclosure.mass
            if self.include_radiator:
                self._mass_breakdown['radiator'] = self.k_mass_simple * self.radiator.mass
            self._mass_breakdown['total'] = self.mass
        return self._mass_breakdown  # kW

    @property
    def ancillary_hardware_mass(self):
        if self._ancillary_hardware_mass is None:
            ancillary_hardware_mass = 0.
            ancillary_hardware_mass += self.control_monitoring_subsystem.mass
            ancillary_hardware_mass += self.conductors_connectors.mass

            if self.include_enclosure:
                ancillary_hardware_mass += self.enclosure.mass

            if self.include_radiator:
                ancillary_hardware_mass += self.radiator.mass

            self._ancillary_hardware_mass = ancillary_hardware_mass
        return self._ancillary_hardware_mass  # kW

    @property
    def control_monitoring_subsystem(self):
        if self._control_monitoring_subsystem is None:
            self._control_monitoring_subsystem = ControlMonitoringSubsystem(
                power_output=self.power_output,
                rated_power=self.rated_power,
                percent_margin=self.percent_margin,
                num_phases=min(self.num_phases_in, self.num_phases_out),
                available_modules=self.available_modules,
                required_modules=self.required_modules,
                power_usage_coefficient=self.cms_power_usage_coefficient,
                control_data_module_mass=self.cms_control_data_module_mass,
                sensor_mass_coefficient=self.cms_sensor_mass_coefficient,
                power_supply_specific_mass=self.cms_power_supply_specific_mass,
                power_supply_efficiency=self.cms_power_supply_efficiency,
                power_supply_margin=self.cms_power_supply_margin,
                k_mass=self.k_mass_cms
            )
        return self._control_monitoring_subsystem

    @property
    def conductors_connectors(self):
        if self._conductors_connectors is None:
            electronics_mass = self.stages_mass + self.control_monitoring_subsystem.mass
            electronics_volume = 1.25 * electronics_mass / (self.electronics_density * 1000.)
            if self.enclosure_baseplate_type == 'fh':
                electronics_length_ar = 1.351
                electronics_width_ar = 1.148
                electronics_height_ar = 0.646
            else:
                electronics_length_ar = 1.610
                electronics_width_ar = 1.043
                electronics_height_ar = 0.596

            self.electronics_length = electronics_length_ar * (electronics_volume ** 0.3333)
            self.electronics_width = electronics_width_ar * (electronics_volume ** 0.3333)
            self.electronics_height = electronics_height_ar * (electronics_volume ** 0.3333)

            self._conductors_connectors = ConductorsConnectors(
                power_output=self.power_output,
                rated_power=self.rated_power,
                percent_margin=self.percent_margin,
                voltage_in=self.voltage_in,
                voltage_out=self.voltage_out,
                num_phases_in=self.num_phases_in,
                num_phases_out=self.num_phases_out,
                available_modules=self.available_modules,
                required_modules=self.required_modules,
                component_efficiency=self.efficiency,
                package_length=self.electronics_length,
                package_width=self.electronics_width,
                package_height=self.electronics_height,
                power_conductor_mass_coefficient=self.power_conductor_mass_coefficient,
                configuration=self.enclosure_baseplate_type,
                material=self.conductor_material,
                k_mass=self.k_mass_conductors
            )
        return self._conductors_connectors

    @property
    def enclosure(self):
        component_electronics_mass = self.stages_mass + self.control_monitoring_subsystem.mass + \
                                     self.conductors_connectors.mass
        electronics_mass = self.stages_mass + self.control_monitoring_subsystem.mass
        self._enclosure = ComponentEnclosure(
            power_output=self.power_output,
            required_modules=self.required_modules,
            component_electronics_mass=component_electronics_mass,
            electronics_mass=electronics_mass,
            package_density=self.packaged_electronics_density,
            electronics_density=self.electronics_density,
            configuration=self.enclosure_baseplate_type,
            material=self.enclosure_material,
            percent_margin=self.percent_margin,
            k_mass=self.k_mass_enclosure
        )
        return self._enclosure

    @property
    def radiator(self):
        if self._radiator is None:
            if self.auto_baseplate_dimensions:
                self.baseplate_length = self.enclosure.length
                self.baseplate_width = self.enclosure.width
            self._radiator = ComponentRadiator(
                heat_load=self.power_input - self.power_output,
                material=self.enclosure_material,
                radiator_sides=self.radiator_sides,
                radiator_temperature_delta=self.radiator_temperature_delta,
                radiator_temperature_sink=self.radiator_temperature_sink,
                radiator_temperature_baseplate=self.radiator_temperature_baseplate,
                baseplate_length=self.baseplate_length,
                baseplate_width=self.baseplate_width,
                k_mass=self.k_mass_radiators
            )
        return self._radiator
