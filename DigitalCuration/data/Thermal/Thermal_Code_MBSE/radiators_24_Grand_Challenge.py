"""Collection of radiator subelement models"""
from __future__ import print_function
from __future__ import division

import numpy as np
import matplotlib.pylab as plt

# class BasicRadiator:
#     """
#     Basic radiator subelement. Sizes a radiator using mass estimation
#     relationships. Can be paired with a heat transport subelement, such as a
#     fluid loop.
#
#     Sources:
#     [1] Ch. 16 of Human Spaceflight Mission Analysis and Design
#
#     Input Parameters
#     ------------
#     heat_load (W) : float
#         Heat that the radiator must dissipate.
#     application : str
#         Assigns preliminary sizing values for approximate heat flux rejection; one of:
#         near_earth_stationary, near_earth_tracking, moon_orbit, moon_surface_poles,
#         mars_surface, mars_transit
#     radiator_type : str
#         Type of radiator; one of: fixed, deployable. Fixed or mounted radiators
#         are only used when the radiator area is expected to be less than
#         the element's surface area (accounting for other subsystems taking up
#         space on the element's outer surface), i.e. Dragon, Orion, ATV.
#     radiator_sides : int
#         Number of sides that radiate heat (either 1 or 2). Fixed or mounted
#         radiators are typically 1-sided.
#     radiator_temperature (K) : float
#         Average radiator surface temperature, near the lowest required coolant
#         temperature or set-point of the external thermal control system. Must be
#         above 270 K.
#     """
#
#     def __init__(self, heat_load, application, radiator_type, radiator_sides, radiator_temperature):
#         self.heat_load = heat_load
#         self.application = application
#         self.radiator_type = radiator_type
#         self.radiator_sides = radiator_sides
#         self.radiator_temperature = radiator_temperature
#
#     def calc_area(self):
#         # Based on Table 16-4 of [1]
#         match self.application:
#             case 'near_earth_stationary':
#                 heat_flux_rejection = 50 + (self.radiator_temperature - 270) * (131 - 50) / (290 - 270)  # W/m**2
#             case 'near_earth_tracking':
#                 heat_flux_rejection = 104 + (self.radiator_temperature - 270) * (185 - 104) / (290 - 270)  # W/m**2
#             case 'moon_orbit':
#                 heat_flux_rejection = 171 + (self.radiator_temperature - 270) * (251 - 171) / (290 - 270)  # W/m**2
#             case 'moon_surface_poles':
#                 heat_flux_rejection = 171 + (self.radiator_temperature - 270) * (251 - 171) / (290 - 270)  # W/m**2
#             case 'mars_surface':
#                 heat_flux_rejection = 81 + (self.radiator_temperature - 270) * (162 - 81) / (290 - 270)  # W/m**2
#             case 'mars_transit':
#                 heat_flux_rejection = 171 + (self.radiator_temperature - 270) * (251 - 171) / (290 - 270)  # W/m**2
#             case _:
#                 raise ValueError(f'{self.application} is an invalid input')
#
#         radiator_area = self.heat_load / heat_flux_rejection  # m**2
#
#         return radiator_area
#
#     def calc_mass(self):
#         # Based on Table 16-7 of [1]
#         match self.radiator_type:
#             case 'fixed':
#                 basic_mass = self.calc_area() * 5.3 * 2 / self.radiator_sides
#             case 'deployable':
#                 basic_mass = self.calc_area() * 8.5 * 2 / self.radiator_sides
#             case _:
#                 raise ValueError(f'{self.radiator_type} is an invalid input')
#
#         return basic_mass
#
#     def calc_volume(self):
#         # Based on Table 16-7 of [1]
#         match self.radiator_type:
#             case 'fixed':
#                 basic_volume = self.calc_area() * 0.02 * 2 / self.radiator_sides
#             case 'deployable':
#                 basic_volume = self.calc_area() * 0.06 * 2 / self.radiator_sides
#             case _:
#                 raise ValueError(f'{self.radiator_type} is an invalid input')
#
#         return basic_volume
#
#
# class SpacecraftRadiator:
#     """
#     Radiator subelement for a spacecraft. Sizes radiator as a function of the
#     required heat load and radiator area. Can be paired with a fluid loop
#     subelement. Thermal environment inputs correspond to the sizing case.
#
#     Sources:
#     [1] Thermal Performance Evaluation of Space Radiator for Single-Phase Mechanically Pumped Fluid Loop
#     [2] Ch. 21 of Space Mission Engineering: The New SMAD.
#     [3] Ch. 9 of Space Vehicle Design, 2nd ed.
#     [4] http://imartinez.etsiae.upm.es/~isidoro/tc3/Radiation%20View%20factors.pdf
#
#     Input Parameters
#     ------------
#     heat_load (W) : float
#         Heat that the radiator must dissipate.
#     radiator_sides : int
#         Number of sides that radiate heat (either 1 or 2). Fixed or mounted
#         radiators are typically 1-sided.
#     radiator_view_factor : str
#         Type of view factor calculation; based on [4]; one of: circular, planar,
#         deep_space
#     radiator_temperature (K) : float
#         Average radiator surface temperature, near the lowest required coolant
#         temperature or set-point of the external thermal control system. Must be
#         above orbiting body temperature.
#     radiator_density (kg/m**2) : float
#         The areal density of the radiator per radiator area NOT total surface
#         area. Common values [1]:
#         ISS - 13.2 kg/m**2
#         Space Shuttle - 5.3 kg/m**2
#         Orion - 10.3 kg/m**2
#         Dream Chaser - 9.2 kg/m**2
#     radiator_emissivity : float
#         The emissivity of the radiator
#     radiator_absorptivity : float
#         Thermal absorbtivity of the radiator.
#     radiator_fin_efficiency : float
#         The efficiency of the radiator fins. Related to radiator density.
#         Typically between 0.8 and 0.9 [1].
#     operational_distance (AU) : float
#         Assumed operational distance of the spacecraft from the sun.
#     body_temperature (K) : float
#         Temperature of the orbited body.
#     body_radius (km) : float
#         Radius of the orbited body.
#     body_albedo : float
#         Percentage of orbited body reflected radiation.
#     body_orbit_altitude (km) : float
#         Assumed orbit altitude of the spacecraft.
#     radiator_body_angle (rad) : float
#         Angle between the radiator and the body; 0 when facing the body, pi/2
#         when perpendicular to body.
#     """
#
#     def __init__(
#         self,
#         heat_load,
#         radiator_sides,
#         radiator_view_factor,
#         radiator_temperature,
#         radiator_density,
#         radiator_emissivity,
#         radiator_absorptivity,
#         radiator_fin_efficiency,
#         operational_distance,
#         body_temperature,
#         body_radius,
#         body_albedo,
#         body_orbit_altitude,
#         radiator_body_angle=0,
#     ):
#         self.heat_load = heat_load
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
#
#     def calc_view_factor(self):
#         # View factor calculation based on [4]
#         match self.radiator_view_factor:
#             case 'circular':
#                 sub_angle = np.arcsin(self.body_radius / (self.body_radius + self.body_orbit_altitude))  # the subtended angle of the body
#                 view_factor = 2 * np.pi * (1 - np.cos(sub_angle)) / (4 * np.pi)
#             case 'planar':
#                 H_r = (self.body_orbit_altitude + self.body_radius) / self.body_radius
#                 beta = self.radiator_body_angle  # radians
#
#                 if abs(beta) <= np.arccos(1 / H_r):
#                     view_factor_1 = np.cos(beta) / H_r**2
#                     view_factor_2 = 0
#                 elif abs(beta) > np.arccos(1 / H_r):
#                     c1 = (H_r**2 - 1) ** 0.5
#
#                     def F(beta):
#                         c2 = -c1 / np.tan(beta)
#                         f = 1 / (np.pi * H_r**2) * (np.cos(beta) * np.arccos(c2) - c1 * np.sin(beta) * (1 - c2**2) ** 0.5) + \
#                             1 / np.pi * np.arctan2(np.sin(beta) * (1 - c2**2) ** 0.5, c1)
#                         return f
#
#                     view_factor_1 = F(beta)
#                     view_factor_2 = F(np.pi - beta)
#
#                 if self.radiator_sides == 2:
#                     view_factor = (view_factor_1 + view_factor_2) / 2
#                 else:
#                     view_factor = view_factor_1
#
#
#             case 'deep_space':
#                 view_factor = 0
#
#         return view_factor
#
#     def calc_area(self):
#         sb = 5.67037e-8  # W * m**-2 * K**-4, Stefan Boltzmann constant
#         space_temperature = 2.7  # K
#
#         # Modified version of Eq. 16-4 from [1]
#         net_flux = (
#             (1 - self.calc_view_factor()) * sb * self.radiator_emissivity * self.radiator_fin_efficiency * (self.radiator_temperature**4 - space_temperature**4) + \
#                 self.calc_view_factor() * sb * self.radiator_emissivity * self.radiator_fin_efficiency * (self.radiator_temperature**4 - self.body_temperature**4) - \
#                 self.calc_heat_flux())
#         radiator_area = self.heat_load / net_flux
#
#         return radiator_area
#
#     def calc_mass(self):
#         basic_mass = self.calc_area() * self.radiator_density
#
#         return basic_mass
#
#     def calc_heat_flux(self):
#         """Accounts for additional heat gain from solar radiation and albedo on the radiator"""
#         view_factor = self.calc_view_factor()
#
#         # Fig. 21-24 of [2]
#         solar_flux = 1368 * (1 / self.operational_distance**2)  # W/m**2
#
#         # Radiation equations from Sec. 9.5.2 of [3]
#         Qbref = self.body_albedo * self.radiator_absorptivity * view_factor * solar_flux  # orbited body reflected heat (albedo)
#         Q_ss = 0  # radiator is perpendicular to the sun
#
#         return Q_ss + Qbref


# class SurfaceRadiator:
#     """
#     Radiator subelement for a surface system. Sizes radiator as a function of
#     the required heat load and radiator area. Can be paired with a fluid loop
#     subelement.
#
#     Sources:
#     [1] Human Spaceflight Mission Analysis and Design, p. 521
#     [2] Thermal Performance Evaluation of Space Radiator for Single-Phase Mechanically Pumped Fluid Loop
#     [3] Oren, J. A., Howell, H. R., 'Space Station Heat Rejection Subsystem Radiator Assembly Design and Development,' Journal of Aerospace, Vol. 104, No. 1, 1995.
#     [4] Iwata, N., Nakanoya, S., Nakamura, N., Takeda, N., Tsutsui, F., 'Thermal Performance Evaluation of Space Radiator for Single-Phase Mechanically Pumped Fluid Loop,' Journal of Spacecraft and Rockets, Vol. 59, No. 1, 2022. https://doi.org/10.2514/1.A35030
#
#     Input Parameters
#     ------------
#     heat_load (W) : float
#         Heat that the radiator must dissipate
#     view_factors : [list,list|None]
#         Provides list of view factors for each side
#     surface_temps (K) : [list,list|None]
#         Provides temperatures of visible surfaces corresponding with the view
#         factors for each side
#     incident_rad (W/m**2) : list
#         Radiation incident on the radiator surface, with form ['first
#         side','None' | 'second side']
#     double_sided : bool
#         Controls whether the radiator radiates heat from one or both sides
#     radiator_temperature (K) : float
#         Average of the radiator input and output temperatures
#     radiator_emissivity : float
#         End-of-life emissivity of the radiator coating
#     radiator_absorptivity : float
#         End-of-life absorptivity of the radiator coating
#
#     Assumptions
#     ------------
#     radiator_fin_efficiency : float
#         Efficiency of the radiator fins [1-2]
#     radiator_density (kg/m**2) : float
#         The areal density of the radiator per radiator area NOT total surface
#         area.
#     """
#
#     def __init__(
#         self,
#         heat_load,
#         area,
#         view_factors: list,
#         surface_temps: list,
#         incident_rad: list,
#         double_sided: bool,
#         radiator_temperature,
#         radiator_emissivity,
#         radiator_absorptivity,
#         radiator_fin_efficiency=0.9,
#         radiator_density=7.75,
#     ):
#         # Inputs
#         self.heat_load = heat_load
#         self.view_factors = view_factors
#         self.surface_temps = surface_temps
#         self.incident_rad = incident_rad
#         self.double_sided = double_sided
#         self.radiator_temperature = radiator_temperature
#         self.radiator_emissivity = radiator_emissivity
#         self.radiator_absorptivity = radiator_absorptivity
#         self.area = area
#
#         # Assumptions
#         self.radiator_fin_efficiency = radiator_fin_efficiency
#         self.radiator_density = radiator_density
#
#     def calc_area(self):
#         if not self.double_sided and type(self.view_factors[0]) != list:
#             self.view_factors = [self.view_factors]
#             self.surface_temps = [self.surface_temps]
#
#         if self.double_sided and (len(self.surface_temps) != 2 or len(self.view_factors) != 2 or len(self.incident_rad) != 2):
#             raise Exception('View factors, surface temperatures, and incident radiation must be included for both sides if double sided')
#         if len(self.surface_temps[0]) != len(self.view_factors[0]) or (self.double_sided and len(self.surface_temps[1]) != len(self.view_factors[1])):
#             raise Exception('Radiator "surface_temps" and "view_factors" must have the same length')
#         if sum(self.view_factors[0]) != 1 or (self.double_sided and sum(self.view_factors[1]) != 1):
#             raise Exception('View factors must add to 1 for each side')
#
#         sb = 5.67e-8  # W/m**2-K**4, Stefan-Boltzmann constant
#         q_out = 0
#         q_in = 0
#         for side in [0, 1] if self.double_sided else [0]:
#             for surface_temp in range(len(self.surface_temps[side])):
#                 q_out += (
#                     sb
#                     * self.radiator_emissivity
#                     * self.view_factors[side][surface_temp]
#                     * self.radiator_fin_efficiency
#                     * (self.radiator_temperature**4 - self.surface_temps[side][surface_temp] ** 4)
#                 )
#             q_in += self.radiator_absorptivity * self.incident_rad[side]
#
#         q_net = q_out - q_in
#         if q_net < 0:
#             raise ValueError('The radiator is dissipating negative heat')
#
#         radiator_area = self.heat_load / q_net
#
#         return radiator_area
#
#     def calc_mass(self):
#         radiator_area = self.area
#         radiator_mass = self.radiator_density * radiator_area
#
#         return radiator_mass

def Earthshine(S,A,Rem,T):
    """
       Calculates total heatflux on habitat due to Earthshine

       Sources:
       TBD

       Input Parameters
       ------------
        S (W/m^2) : float
            Solar radiation intensity
        A (N/A)   : float
            Albedo of the Earth
        Rem (km)   : float
            Distance between the earth and the moon
        T (k)     : float
            Blackbody radiation temperature of earth

        Additional Parameters
        -------------
        Re (km)  : float
            Radius of the earth
        alp (N/A) : float
            TBD
        sig (m^2 kg / (s^2 K)): float
            Stephan Boltzman Constant

        Output
        ------
        Q (W/m^2)  : float
            Heat flux due to earthshine
    """
    Re = 6371
    alp = 1
    sig = 5.67e-8
    Q = (Re/Rem)**2*(S*A*alp + sig*T)
    print(Q)
    return(Q)

def Lunar_planetshine(Lunar_Latitude,Lunar_Longitude,state):
    """
           Calculates total heatflux on habitat due to Lunar planetshine

           Sources:
           TBD

           Input Parameters
           ------------
            Lunar_Latitude (Deg) : float
                Latitude of the lunar base (Assumes negatives mean south of equator)
            Lunar Longtiude (Deg): float
                Longtiude of the lunar base (Assumes negatives mean west of prime meridian)
            state : string
                Indicates whether hot or cold condition will be used

            Additional Parameters
            -------------
            subsolar_longitude (Deg)
                Longitude of the subsolar point (point where the sun is directly overhead) (Note: there is no
                subsolar latitude as it is assumed to be 0)
            sig (m^2 kg / (s^2 K)): float
                Stephan Boltzman Constant
            a (N/A): float
                Lunar albedo
            S (w/m^2): float
                Solar flux
            e (N/A): float
                Lunar surface emissivity
            Tdark (K): float
                Temperature of the lunar surface without any sunlight hitting it
    """
    subsolar_longitude = np.linspace(-180,180,num=360)
    Qtot = np.zeros(360)
    sig = 5.67e-8
    if state=='cold':
        a = 0.07
        S = 1310
        e = 0.95
        Tdark = 80
    if state == 'hot':
        a = 0.2
        S = 1426
        e = 0.98
        Tdark = 120
    for i in range(360):
        if np.abs(Lunar_Longitude-subsolar_longitude[i-1])<=90:
            Qtot[i] = (np.cos(np.deg2rad(Lunar_Longitude)-np.deg2rad(subsolar_longitude[i-1]))*np.cos(np.deg2rad(Lunar_Latitude)))*((1-a)*S-sig*e*Tdark**4)+sig*e*Tdark**4
        else:
            Qtot[i] = sig*e*Tdark**4

    plt.plot(subsolar_longitude,Qtot)
    plt.xlabel("Time (hrs)")
    plt.ylabel("Heat Flux (w/m^2)")
    plt.title("Heat flux for relfected lunar sunlight at Latitude -85 deg")
    plt.show()
    return(np.max(Qtot))

def surface_temperature(Lun_Lat,state):
    """
               Calculates total temperature of the lunar surface due to Lunar planetshine and reflection sunlight based on latitude

               Sources:
               TBD

               Input Parameters
               ------------
                Lunar_Lat (Deg) : float
                    Latitude of the lunar base (Assumes negatives mean south of equator)
                state : string
                    Indicates whether hot or cold condition will be used

                Additional Parameters
                -------------
                sig (m^2 kg / (s^2 K)): float
                    Stephan Boltzman Constant
                a (N/A): float
                    Lunar albedo
                S (w/m^2): float
                    Solar flux
                e (N/A): float
                    Lunar surface emissivity
                Tdark (K): float
                    Temperature of the lunar surface without any sunlight hitting it
                th_a (Deg): float
                    Solar elevation angle
                th_z (Deg): float
                    Solar zenith angle

    """
    hr = np.linspace(0.1,708,num=708)
    sig = 5.67e-8
    ph = np.deg2rad(0)
    if state == 'cold':
        a = 0.93
        S = 1310
        e = 0.95
        Tdark = 80
    if state == 'hot':
        a = 0.8
        S = 1426
        e = 0.98
        Tdark = 120
    th_s = 360/(708/hr)
    th_a = np.arcsin(np.sin(ph)*np.sin(np.deg2rad(Lun_Lat))+np.cos(ph)*np.cos(np.deg2rad(th_s))*np.cos(np.deg2rad(Lun_Lat)))
    th_a = np.rad2deg(th_a)
    th_z = 90 - th_a
    Tm = np.zeros(708)
    for i in range(708):
        if th_s[i] < 82 or th_s[i] > 278:
            Tm[i] = ((a*S*np.cos(np.deg2rad(th_z[i])))/(e*sig))**0.25
        else:
            Tm[i] = Tdark
    plt.plot(hr,Tm)
    plt.xlabel("Time (hrs)")
    plt.ylabel("Temperature (K)")
    plt.title("Temperature for a Lunar Day at Latitude -85 deg")
    plt.show()
    return(np.max(Tm))

def Radiator_sizing_new(num_panels,n,e,th,alpha,Trad,Q,Earthshine_prop,Surf_temp_prop,Lunshine_prop):
    """
                   Calculates total temperature of the lunar surface due to Lunar planetshine and reflection sunlight based on latitude

                   Sources:
                   TBD

                   Input Parameters
                   ------------
                    num_panels (N/A) : int
                        Number of radiator panels
                    n (N/A): float
                        Radiator efficency
                    e (N/A): float
                        Emissivity of radiator
                    th (Deg): float
                        Angle which radiator panels are elevated from horizontal
                    alpha (N/A): float
                        Absortivitiy of radiator
                    Trad (K): float
                        Temperature of the radiator
                    Earthshine_prop (N/A): float
                        Array of values used to get heatflux value in earthshine script
                    Surf_temp_prop (N/A): float
                        Array of values used to get max temperature value in Lunar surface planetshine script
                    Lunshine_prop (N/A): float
                        Array of values used to get heatflux due to lunar planetshine

                    Additional Parameters
                    -------------
                    sig (m^2 kg / (s^2 K)): float
                        Stephan Boltzman Constant
                    qout (W): float
                        Heat flux escaping radiators
                    Ti (K): float
                        Temperature of space enviornment
                    earthshine (W/m^2): float
                        Earthshine heat flux
                    Ts (K): float
                        Temperature of lunar surface
                    Lunshine (W/m^2): float
                        Lunar planetshine heat flux
                    qin (W/m^2): float
                        Heat flux incoming to lunar habitat
                    Areq (m^2): float
                        Area of radiator required to dissipate heat
                    Arad (m^2) : float
                        Total area of radiators required (10% mass margin applied)

                    Output
                    ---------------
                    Lrad (m): float
                        Total length of all radiator panels
                    Wrad (m): float
                        Width of radiator panels
    """
    sig = 5.67e-8
    earthshine = Earthshine(S=Earthshine_prop[0],A=Earthshine_prop[1],Rem=Earthshine_prop[2],T=Earthshine_prop[3])
    Ts = surface_temperature(Lun_Lat=Surf_temp_prop[0],state=Surf_temp_prop[1])
    Lunshine = Lunar_planetshine(Lunar_Latitude=Lunshine_prop[0],Lunar_Longitude=Lunshine_prop[1],state=Lunshine_prop[2])
    qout=0
    for i in range(num_panels*2):
        if i%2 ==0:
            Ti = 2.7
            qout = qout + n*sig*e*np.cos(np.deg2rad(th))*(Trad**4-Ti**4)
        else:
            qout = qout + n * sig * e * np.cos(np.deg2rad(th))* (Trad ** 4 - Ts ** 4)
    qin = 1421*np.sin(np.deg2rad(th)) + Lunshine + earthshine
    qnet = qout - qin*alpha
    if qnet<0:
        raise Exception('Radiator is gaining more heat than losing')

    Areq = Q/qnet
    Arad = 1.1*Areq
    Lrad = np.sqrt(Arad/num_panels)
    Wrad = Arad/Lrad

    return [Lrad,Wrad]

def Radiator_plot(num_panels,n,e,th,alpha,Trad,Q,Earthshine_prop,Surf_temp_prop,Lunshine_prop):
    """
                       Calculates total temperature of the lunar surface due to Lunar planetshine and reflection sunlight based on latitude

                       Sources:
                       TBD

                       Input Parameters
                       ------------
                        num_panels (N/A) : int
                            Number of radiator panels
                        n (N/A): float
                            Radiator efficency
                        e (N/A): float
                            Emissivity of radiator
                        th (Deg): float
                            Angle which radiator panels are elevated from horizontal
                        alpha (N/A): float
                            Absortivitiy of radiator
                        Trad (K): float
                            Temperature of the radiator
                        Earthshine_prop (N/A): float
                            Array of values used to get heatflux value in earthshine script
                        Surf_temp_prop (N/A): float
                            Array of values used to get max temperature value in Lunar surface planetshine script
                        Lunshine_prop (N/A): float
                            Array of values used to get heatflux due to lunar planetshine

                        Output
                        ---------------
                        Lrad (m): float
                            Total length of all radiator panels
                        Wrad (m): float
                            Width of radiator panels
        """
    sig = 5.67e-8
    earthshine = Earthshine(S=Earthshine_prop[0], A=Earthshine_prop[1], Rem=Earthshine_prop[2], T=Earthshine_prop[3])
    Ts = surface_temperature(Lun_Lat=Surf_temp_prop[0], state=Surf_temp_prop[1])
    Lunshine = Lunar_planetshine(Lunar_Latitude=Lunshine_prop[0], Lunar_Longitude=Lunshine_prop[1],
                                 state=Lunshine_prop[2])
    qout = np.zeros(len(th))
    for j in range(len(th)):
        for i in range(num_panels * 2):
            if i % 2 == 0:
                Ti = 2.7
                qout[j] = qout[j] + n * sig * e * np.cos(np.deg2rad(th[j])) * (Trad ** 4 - Ti ** 4)
            else:
                qout[j] = qout[j] + n * sig * e * np.cos(np.deg2rad(th[j])) * (Trad ** 4 - Ts ** 4)

    plt.plot(th,qout)
    plt.xlabel("Angle of Radiator (deg)")
    plt.ylabel("Output Heat Flux (W/m^2)")
    plt.title("Output Heat for radiator panel vs angle")
    plt.show()

if __name__ == '__main__':
    model = 'SurfaceRadiator'  # BasicRadiator, SpacecraftRadiator, SurfaceRadiator
    print_options = np.get_printoptions()
    np_precision = print_options['precision']
    Rad_prop = Radiator_sizing_new(num_panels=num_panel,n=0.9,e=emis,th=theta,alpha=alpha_s,Trad=Trad_s,Q=Q_s,Earthshine_prop=[1400,0.3,385000,255],Surf_temp_prop=[Lat_s,'hot'],Lunshine_prop=[Lat_s,0,'hot'])
    Rad_area = Rad_prop[0]*Rad_prop[1]
    Radiator_plot(num_panels=num_panel,n=0.9,e=emis,th=np.linspace(0,90,100),alpha=alpha_s,Trad=Trad_S,Q=Q_s,Earthshine_prop=[1400,0.3,385000,255],Surf_temp_prop=[Lat_s,'hot'],Lunshine_prop=[Lat_s,0,'hot'])

    # match model:
    #     case 'BasicRadiator':
    #         radiator = BasicRadiator(
    #             heat_load=17100,  # W
    #             application='moon_surface_poles',
    #             radiator_type='fixed',
    #             radiator_sides=1,
    #             radiator_temperature=330,  # K
    #         )
    #
    #         mass = radiator.calc_mass()
    #         mass = np.round(mass, np_precision)
    #         area = radiator.calc_area()
    #         area = np.round(area, np_precision)
    #         volume = radiator.calc_volume()
    #         volume = np.round(volume, np_precision)
    #
    #         print(f'mass = {mass} (kg)')
    #         print(f'area = {area} (m**2)')
    #         print(f'volume = {volume} (m**3)')
    #
    #     case 'SpacecraftRadiator':
    #         radiator = SpacecraftRadiator(
    #             heat_load=3000,  # W
    #             radiator_sides=1,
    #             radiator_view_factor='planar',
    #             radiator_temperature=300,  # K
    #             radiator_density=4.5,
    #             radiator_emissivity=0.9,
    #             radiator_absorptivity=0.1,
    #             radiator_fin_efficiency=0.9,
    #             operational_distance=1,
    #             body_temperature=290,
    #             body_radius=6378,
    #             body_albedo=0.3,
    #             body_orbit_altitude=6378/2,
    #             radiator_body_angle=0,
    #         )
    #
    #         view_factor = radiator.calc_view_factor()
    #         view_factor = np.round(view_factor, np_precision)
    #         mass = radiator.calc_mass()
    #         mass = np.round(mass, np_precision)
    #         area = radiator.calc_area()
    #         area = np.round(area, np_precision)
    #         heat_flux = radiator.calc_heat_flux()
    #         heat_flux = np.round(heat_flux, np_precision)
    #
    #         print(f'view_factor = {view_factor}')
    #         print(f'mass = {mass} (kg)')
    #         print(f'area = {area} (m**2)')
    #         print(f'heat_flux = {heat_flux} (m**2)')
    #
    #     case 'SurfaceRadiator':
    # radiator = SurfaceRadiator(
    #             heat_load=3e4,
    #             view_factors=[[0.7, 0.3], [1]],
    #             surface_temps=[[290, 2.7], [2.7]],
    #             incident_rad=[0, 137],
    #             double_sided=True,
    #             radiator_temperature=330,
    #             radiator_emissivity=0.9,
    #             radiator_absorptivity=0.1,
    #             area=Rad_area,
    #         )

    mass = Rad_area*7.75
    mass = np.round(mass, np_precision)
    area = np.round(Rad_area, np_precision)
    print('mass (kg)')
    print(mass)
    print('area (m**2)')
    print(area)
    print('Radiator Length (m)')
    print(Rad_prop[0])
    print('Radiator Width')
    print(Rad_prop[1])
