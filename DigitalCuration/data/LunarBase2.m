% Gather user inputs
num_astronauts = input('Enter the number of astronauts: ');
mission_duration = input('Enter the mission duration (in days): ');
mission_duration = mission_duration*24;


% Define initial conditions and constants
initial_power = 1000; % Initial power supply in Watts
current_power = 1000; % Initial power supply in Watts
initial_oxygen = 21.2; % Initial oxygen level in liters
initial_water = 200; % Initial water level in liters
power_threshold_for_scrubbing = 800; % Example value, adjust as needed
vehicle_route_radius = 100000; % 100 km
%Pressure
habitat_pressure = 101.3; % Pressure inside the habitat in kPa
min_pressure = 98.5; % Minimum acceptable pressure in kPa
max_pressure = 102.5; % Maximum acceptable pressure in kPa
pressure_maintenance_power = 100; % Power needed to adjust pressure (example value)
fluctuation_range = 0.5; % Example: ±0.5 kPa fluctuation is considered normal
CO2_levels = zeros(1, mission_duration);
power_consumption = zeros(1, mission_duration);

% Constants for CO2 Management
max_CO2 = 0.4; % Maximum safe CO2 level in kPa
initial_CO2 = 0.2; % Initial CO2 level in kPa
CO2_production_sleep = 0.005; % Reduced CO2 production rate during sleep (example value)
CO2_production_normal = 0.01; % Normal CO2 production rate (example value)
CO2_production_exercise = 0.02; % Increased CO2 production rate during exercise (example value)
max_CO2_scrubbing_capacity = 0.05; % Maximum amount of CO2 that can be scrubbed per hour in kPa
power_consumption_per_scrubbing = 50; % Power consumed for CO2 scrubbing in Watts
num_hours_sleep = 8; % Number of hours the astronauts sleep
num_hours_exercise = 4; % Number of hours of exercise
% Initialize CO2 history
co2_history = zeros(1, mission_duration);
co2_history(1) = initial_CO2;
% Constants for Activity Schedule
max_variation = 2; % Maximum hours of variation in activities
% Initialize variables for random activity times
random_sleep_start = 0;
random_sleep_end = 0;
random_exercise_start = 0;
random_exercise_end = 0;
% Constants for Activity Durations and Variability
base_duration_sleep = 8; % Base duration for sleep in hours
base_duration_nominal = 14.5; % Base duration for nominal activities
base_duration_exercise = 1; % Total duration for exercise and recovery
variation_range = 1; % Max variation in hours
% CO2 production rates converted from g/min to kPa/h
% Constants
molar_mass_CO2 = 44.01;  % g/mol
R = 8.314;  % J/(mol·K)
temperature_kelvin = 295;  % Kelvin
volume_m3 = 100;  % m³
% Since the output needs to be in kPa, we convert the gas constant from J/(mol·K) to kPa·m³/(mol·K)
R_kPa = R / 1000;
% Calculate the conversion factor from g/min to kPa
conversion_factor_gmin_to_kPa = (1 / molar_mass_CO2) * R_kPa * temperature_kelvin / volume_m3;
CO2_output_sleep = 0.44 * 60 * conversion_factor_gmin_to_kPa; % CO2 output for sleep in kPa/h
CO2_output_nominal = 0.69 * 60 * conversion_factor_gmin_to_kPa; % CO2 output for nominal activity in kPa/h
CO2_output_exercise_peak = 5.22 * 60 * conversion_factor_gmin_to_kPa; % CO2 output for peak exercise in kPa/h
normal_CO2_level = 0.2; % Normal CO2 level in kPa
exercise_CO2_level = 0.4; % CO2 level during exercise in kPa
max_CO2_during_power_loss = 1; % Maximum CO2 level during power loss in kPa
reduced_scrubbing_efficiency=0.01;
target_CO2_level = normal_CO2_level;

% Constants for Power Generation
photovoltaic_max_output = 50; % kW
fission_surface_power = 40; % kW
fuel_cell_output = 0.5; % kW
vertical_solar_array_output = 10; % kW
gateway_power = 60; % kW
% Constants for Power Utilization
ISRU_power_need = 60; % kW
habitation_power_need = 20; % kW when crewed
transportation_power_need = 0.5; % kW
% Constants for Lunar Cycle
lunar_day_length = 14 * 24; % hours
lunar_night_length = 14 * 24; % hours
lunar_cycle_length = lunar_day_length + lunar_night_length; % hours

% Constants for Oxygen Consumption and Heat Generation (per minute)
oxygen_consumption_sleep = 0.44 / 60; % g/min
oxygen_consumption_nominal = 0.69 / 60; % g/min
oxygen_consumption_exercise_peak = 5.22 / 60; % g/min
% Constants for Heat Generation (kJ/min)
heat_generation_sleep = 5512 / 24 / 60; % kJ/min
heat_generation_nominal = 6283 / 24 / 60; % kJ/min
heat_generation_exercise_peak = 11795 / 24 / 60; % kJ/min
% Constants for p[O2] Limits (kPa)
min_pO2_nominal_no_impairment = 20.7; % Minimum p[O2] for no impairment
max_pO2_nominal_no_impairment = 30.6; % Maximum p[O2] for no impairment
low_power_reduction_factor = 0.5; % Reduction factor for O2 generation during low power 
initial_oxygen_kpa = 30; % Initial oxygen level in kPa
% Define the efficiency of the oxygen generator (e.g., 0.5 for 50% efficiency)
efficiency = 0.7;

% Define the power consumed by the oxygen generator in watts
oxygen_generator_power = 1000; % Replace with the actual power consumption

% Constants for oxygen generation
molar_mass_oxygen = 32; % g/mol
faraday_constant = 96485; % C/mol
cell_voltage = 0.5; % V (Replace with the actual cell voltage)

% Calculate the oxygen generation rate in g/min
oxygen_generation_rate = 60 * (oxygen_generator_power * efficiency) / (molar_mass_oxygen * faraday_constant * cell_voltage);


% Define additional space requirements for different areas in square meters
additional_space_for_ecls = 100; % Additional space for ECLS
additional_space_for_exercise = 200; % Additional space for exercise
additional_space_for_research = 300; % Additional space for research space
additional_space_for_common_areas = 400; % Additional space for common areas

% Initialize variables
current_oxygen_kpa = initial_oxygen_kpa;

% Initialize oxygen consumption rates based on activity (g/min)
oxygen_consumption_rate_sleep = 0.44 / 60; % g/min
oxygen_consumption_rate_nominal = 0.69 / 60; % g/min
oxygen_consumption_rate_exercise_peak = 5.22 / 60; % g/min

habitat_temperature = 295; % Temperature inside the habitat in Kelvin
habitat_humidity = 40; % Relative Humidity inside the habitat in percentage
% Initialize food and waste stocks
food_storage_capacity = 1000; % Food storage capacity in kg
food_stock = food_storage_capacity; % Initial food stock
waste_storage_capacity = 500; % Waste storage capacity in kg
waste_stock = 0; % Initial waste stock
% Initialize astronaut health
initial_astronaut_health = 100; % Initial astronaut health (example)
astronaut_health = initial_astronaut_health; % Initialize astronaut health
% Initialize health degradation rate
health_degradation_rate = 0.1; % Example health degradation rate
% Initialize vehicle positions
num_vehicles = 3; % You can change this number according to your needs
vehicle_route_length = 200; % You can change this value according to your simulation requirements
vehicle_positions = zeros(num_vehicles, 2); % Initialize with zeros

base_size = 100; % You can change this value according to your lunar base size

% Initialize vehicle payloads
vehicle_payloads = zeros(num_vehicles, 1);

% Initialize vehicle statuses (e.g., operational, in maintenance)
vehicle_statuses = cell(num_vehicles, 1);

% Define acceptable limits
max_oxygen = 50.6; % Maximum safe oxygen level in liters
max_co2 = 70; % Maximum safe CO2 level in liters
min_power = 800; % Minimum power requirement in Watts
min_water = 150; % Minimum water requirement in liters

% Define constants
lunar_day_length = 14 * 24; % Length of a lunar day in hours (14 Earth days)
lunar_night_length = 14 * 24; % Length of a lunar night in hours (14 Earth days)
lunar_cycle_length = lunar_day_length + lunar_night_length; % Total length of lunar day/night cycle

% Constants
safety_factor = 1.2; % For example, a 20% safety margin
life_support_power = 500; % Example power usage for life support systems in Watts
other_systems_power = 200; % Power for other systems in Watts

% Define power requirements
power_for_life_support = 500; % Power usage for life support systems in Watts

% Calculate power usage based on pressure requirements
power_for_pressure = 0; % Initialize power for pressure
if habitat_pressure < min_pressure
    % Additional power needed to increase pressure
    power_for_pressure = (min_pressure - habitat_pressure) * 10; % Example power calculation (adjust as needed)
end

% Calculate minimum required power
min_required_power = (life_support_power + other_systems_power+power_for_pressure) * safety_factor;

% Adjust initial power to be above the minimum required power
initial_power = min_required_power; % Adjust as per actual system requirements

% Assume power generation rate is now dependent on the minimum required power
power_generation_rate = min_required_power; % Adjust as per actual system requirements

% Additional code for cost and payload impact
% This is a simplified example. Actual calculations would be more complex.
cost_per_watt = 10; % Example cost per Watt of power generation capability
payload_weight_per_watt = 0.05; % Example weight in kg per Watt for payload calculations

% Calculate cost and payload impact
total_system_cost = initial_power * cost_per_watt;
total_payload_weight = initial_power * payload_weight_per_watt;

% Display cost and payload impact
fprintf('Total system cost: $%.2f\n', total_system_cost);
fprintf('Total payload weight impact: %.2f kg\n', total_payload_weight);

water_reclamation_rate = 0.98; % Example rate of water reclamation in liters per hour

% Simulation loop
for t = 1:mission_duration
        
    % Determine position in lunar cycle (day or night)
    cycle_position = mod(t+7, lunar_cycle_length);
        
    % Determine position in lunar cycle (day or night)
    cycle_position = mod(t + lunar_day_length/2, lunar_cycle_length);
    
    % Calculate the illumination factor as a sinusoidal function
    illumination_factor = 0.5 * (1 + sin(2 * pi * cycle_position / lunar_cycle_length));
    
    % Adjust power generation based on the illumination factor
    solar_power_photovoltaic = photovoltaic_max_output * illumination_factor;
    
    % Constant power from vertical solar arrays
    solar_power_vertical = vertical_solar_array_output;
    
    % Total Solar Power Generation
    total_solar_power = solar_power_photovoltaic + solar_power_vertical + gateway_power;
    % Total Power Generation
    total_power_generation = total_solar_power + fission_surface_power; % Adding fission power
    % Update current power
    current_power = current_power + total_power_generation - (ISRU_power_need + habitation_power_need + transportation_power_need);


     % Simulate normal pressure fluctuations
    normal_fluctuation = (rand() - 0.5) * 2 * fluctuation_range; % Generates random fluctuation within the range
    habitat_pressure = habitat_pressure + normal_fluctuation;

    % Check for power critical level
    if current_power < min_power
        % Reduce pressure maintenance to save power
        if habitat_pressure > min_pressure
            habitat_pressure = habitat_pressure - 0.5; % Example depressurization rate
            % Reduce power consumption for pressure maintenance
            current_power = current_power + pressure_maintenance_power / 2;
        end
        disp(['Power Saving Mode Activated at hour ', num2str(t)]);
    else
        % Normal operation: maintain pressure
        if habitat_pressure < min_pressure || habitat_pressure > max_pressure
            current_power = current_power - pressure_maintenance_power;
            % Adjust habitat pressure back to 1 atm
            habitat_pressure = adjust_pressure(habitat_pressure, min_pressure, max_pressure);
        end
    end

    % Store pressure history
    pressure_history(t) = habitat_pressure;
    
    hour_of_day = mod(t-1, 24) + 1; % Calculate hour of the day (1-24)

    % Randomize the activity schedule at the start of each day
    if hour_of_day == 1
        % Randomize durations within specified range
        duration_sleep = base_duration_sleep + randi([-variation_range, variation_range], 1);
        random_sleep_start = randi([1, max(1, 24 - duration_sleep)], 1); 
        random_sleep_end = random_sleep_start + duration_sleep;

        duration_exercise = base_duration_exercise + randi([-variation_range, variation_range], 1);
        random_exercise_start = randi([random_sleep_end, max(random_sleep_end, 24 - duration_exercise)], 1);
        random_exercise_end = random_exercise_start + duration_exercise;
    end

    % Calculate CO2 production rate based on activity
    % Adjust CO2 production rates to maintain the desired levels
    if hour_of_day >= random_sleep_start && hour_of_day < random_sleep_end
        CO2_production_rate = CO2_output_sleep * conversion_factor_gmin_to_kPa;
    elseif hour_of_day >= random_exercise_start && hour_of_day < random_exercise_end
        CO2_production_rate = CO2_output_exercise_peak * conversion_factor_gmin_to_kPa;
        % Set the target CO2 level to the exercise level
        target_CO2_level = exercise_CO2_level;
    else
        CO2_production_rate = CO2_output_nominal * conversion_factor_gmin_to_kPa;
        % Set the target CO2 level back to normal
        target_CO2_level = normal_CO2_level;
    end

    % Update CO2 levels
    if t == 1
        current_co2 = initial_CO2 + CO2_production_rate * num_astronauts;
    else
        current_co2 = co2_history(t-1) + CO2_production_rate * num_astronauts;
    end

    % Adjust CO2 scrubbing based on power availability
    if current_power < power_threshold_for_scrubbing
        effective_scrubbing_capacity = max_CO2_scrubbing_capacity * reduced_scrubbing_efficiency;
        target_CO2_level = max_CO2_during_power_loss; % Increase target CO2 level during power loss
    else
        effective_scrubbing_capacity = max_CO2_scrubbing_capacity;
    end

    % Apply CO2 scrubbing
    if current_co2 > target_CO2_level
        amount_to_scrub = min(current_co2 - target_CO2_level, effective_scrubbing_capacity);
        current_co2 = current_co2 - amount_to_scrub; % Directly reduce the CO2
        current_power = current_power - power_consumption_per_scrubbing;
    end

    % Store the updated CO2 level
    co2_history(t) = current_co2;

    % Calculate oxygen consumption rate based on activity (g/min)
    if hour_of_day >= random_sleep_start && hour_of_day < random_sleep_end
        oxygen_consumption_rate = oxygen_consumption_rate_sleep;
    elseif hour_of_day >= random_exercise_start && hour_of_day < random_exercise_end
        oxygen_consumption_rate = oxygen_consumption_rate_exercise_peak;
    else
        oxygen_consumption_rate = oxygen_consumption_rate_nominal;
    end

    % Calculate oxygen change due to generation, consumption, and activity (g)
    if current_power >= oxygen_generator_power
        oxygen_change_g = (oxygen_generation_rate - oxygen_consumption_rate * num_astronauts) * (current_power - oxygen_generator_power) / initial_power;
    else
        % If power is below the oxygen generator's power requirement, no oxygen is generated
        oxygen_change_g = -oxygen_consumption_rate * num_astronauts * current_power / initial_power;
    end
    
    % Convert oxygen change from grams to kPa
    oxygen_change_kpa = oxygen_change_g / (8.314 * 295.15) * 1000;
    
    % Update current oxygen level in kPa
    current_oxygen_kpa = current_oxygen_kpa + oxygen_change_kpa;

    % Ensure oxygen levels do not exceed the maximum safe level
    if current_oxygen_kpa > max_pO2_nominal_no_impairment
        current_oxygen_kpa = max_pO2_nominal_no_impairment;
    end


    reclaimed_water = water_reclamation_rate * t; % Water reclaimed over time
    current_water = initial_water - 1 * t * num_astronauts + reclaimed_water; % Water level updated with reclamation

    % Check for critical values
    if current_co2 > max_co2
        % Handle CO2 critical level
        disp(['Critical CO2 Level at hour ', num2str(t)]);
    end
    if current_power < min_power
        % Handle power critical level
        disp(['Critical Power Level at hour ', num2str(t)]);
    end
    if current_water < min_water
        % Handle water critical level
        disp(['Critical Water Level at hour ', num2str(t)]);
    end

    % Store results in history arrays
    power_history(t) = current_power;
    oxygen_history(t) = current_oxygen_kpa;
    water_history(t) = current_water;
    
    % Update food and waste levels
    food_consumption = num_astronauts * 0.02; % Food consumption rate (example)
    food_stock = food_stock - food_consumption;
    waste_production = num_astronauts * 0.03; % Waste production rate (example)
    waste_stock = waste_stock + waste_production;
    
    % Check food and waste levels
    if food_stock < 0
        % Handle food shortage
        disp(['Food Shortage at hour ', num2str(t)]);
        % Implement emergency procedures here (e.g., request resupply)
    end
    if waste_stock > waste_storage_capacity
        % Handle waste overflow
        disp(['Waste Overflow at hour ', num2str(t)]);
        % Implement waste disposal procedures here (e.g., jettison waste)
    end
    
    % Astronaut health degradation
    astronaut_health = astronaut_health - health_degradation_rate;
    
    % Store health history
    health_history(t) = astronaut_health;
    solar_power_history(t)=total_solar_power;

end
%     total_energy_required = sum(power_consumption);
%     total_solar_energy = trapz(time, (solar_power_photovoltaic + solar_power_vertical + gateway_power));
%     solar_cell_efficiency = 0.20;
%     required_solar_cell_area = total_energy_required / (total_solar_energy * solar_cell_efficiency);

% Simulation loop for surface vehicles
for t = 1:mission_duration
    % Update vehicle positions
    for i = 1:num_vehicles
        % Simulate vehicle movement (for example, moving in a straight line)
        vehicle_positions(i, 1) = vehicle_positions(i, 1) + randn(1); % Random horizontal movement
        vehicle_positions(i, 2) = vehicle_positions(i, 2) + randn(1); % Random vertical movement
        
        % Check if the vehicle has reached the end of its route
        if vehicle_positions(i, 1) > base_size + vehicle_route_length
            % Vehicle has completed its route, reset its position
            vehicle_positions(i, 1) = base_size;
        end
        
        % Check for resource extraction
        if rand() < 0.1 % 10% chance of resource extraction per hour
            % Simulate resource extraction and update payload
            extracted_payload = randi([1, 10]); % Random payload between 1 to 10 kg
            vehicle_payloads(i) = vehicle_payloads(i) + extracted_payload;
        end
        
        % Check for maintenance needs
        if rand() < 0.05 % 5% chance of maintenance need per hour
            % Simulate maintenance need and update status
            vehicle_statuses{i} = 'Maintenance Required';
        else
            % Vehicle is operational
            vehicle_statuses{i} = 'Operational';
        end
    end
end

% Plotting results with critical level visualization
time = 1:mission_duration;
subplot(4,1,1)
plot(time/24, power_history, 'b');
hold on;
plot(time(power_history < min_power)/24, power_history(power_history < min_power), 'r*');
title('Power Generation Over Time');
ylabel('Power (Watts)');

% Plotting oxygen levels in kPa
subplot(4, 1, 2)
plot(time/24, oxygen_history, 'b'); % Plot oxygen levels in kPa
hold on;
plot(time(oxygen_history> max_pO2_nominal_no_impairment | oxygen_history < 0)/24, oxygen_history(oxygen_history > max_pO2_nominal_no_impairment | oxygen_history < 0), 'r*');
hold on;
oxygen_threshold = 20.6; % Set the threshold value
plot(time(oxygen_history < oxygen_threshold)/24, oxygen_history(oxygen_history < oxygen_threshold), 'r*');
title('Oxygen Levels Over Time');
ylabel('Oxygen (kPa)');

% Plotting CO2 levels in kPa
subplot(4,1,3)
plot(time/24, co2_history, 'b');
hold on;
plot(time(co2_history > max_CO2)/24, co2_history(co2_history > max_CO2), 'r*');
title('CO2 Levels Over Time');
ylabel('CO2 (kPa)');

% Plotting pressure over time
subplot(4,1,4)
plot(time/24, pressure_history, 'b');
hold on;
% Logical index for time points where pressure is outside of the safe range
outside_pressure_range = (pressure_history < min_pressure) | (pressure_history > max_pressure);
% Corrected plot command
plot(time(outside_pressure_range)/24, pressure_history(outside_pressure_range), 'r*', 'MarkerSize', 8);
title('Habitat Pressure Over Time');
ylabel('Pressure (kPa)');
xlabel('Time (Days)');
legend('Normal', 'Critical');
grid on;



% Add legends and grid
for i = 1:4
    subplot(4,1,i);
    legend('Normal', 'Critical');
    grid on;
end

min_personal_space_per_astronaut = 10; % Minimum personal space per astronaut in square meters

% Calculate the total area required for personal space based on the number of astronauts
total_personal_space = num_astronauts * min_personal_space_per_astronaut;

% Calculate the size of the base, including ECLS, exercise, research space, and common areas
base_size = total_personal_space + additional_space_for_ecls + additional_space_for_exercise + additional_space_for_research + additional_space_for_common_areas;

% Load the lunar image
lunar_image = imread('lunar_image.jpg'); % Replace 'lunar_image.jpg' with the actual file path of your lunar image
lunar_image_size_km = 121.293401697; % Size of the lunar image in kilometers

% Create a figure
figure;

% Hold the current axis
hold on;

% Plotting a green circle representing the distance covered (100 km)
green_circle_radius_km = 50; % 100 km
% Calculate the center of the green circle (assuming it's at the lunar base)
center_x_km = 0; % Replace with the actual x-coordinate of the lunar base
center_y_km = 0; % Replace with the actual y-coordinate of the lunar base

% Display the lunar image
imshow(lunar_image, 'XData', [-lunar_image_size_km/2, lunar_image_size_km/2], 'YData', [-lunar_image_size_km/2, lunar_image_size_km/2]);

% Plot the green circle directly on the lunar image
rectangle('Position', [center_x_km - green_circle_radius_km, center_y_km - green_circle_radius_km, 2 * green_circle_radius_km, 2 * green_circle_radius_km], 'Curvature', [1, 1], 'EdgeColor', 'g', 'LineWidth', 2);

% Set plot limits and labels
axis equal;
xlim([-lunar_image_size_km/2, lunar_image_size_km/2]);
ylim([-lunar_image_size_km/2, lunar_image_size_km/2]);
xlabel('Distance (km)');
ylabel('Distance (km)');
title('Lunar Base Location with Green Circle on Lunar Image');
grid on;

% Release the hold on the axis
hold off;

% Create a figure
figure;

% Plotting the base
rectangle('Position', [0, 0, base_size, base_size], 'FaceColor', [0.8, 0.8, 0.8], 'EdgeColor', 'b');
text(base_size/2, base_size/2, 'Lunar Base', 'HorizontalAlignment', 'center');

grid on;

% Function for time-dependent power generation
function power_generated = calculate_power_generation(t, lunar_day_length, lunar_cycle_length, base_generation_rate, min_required_power)
    if mod(t, lunar_cycle_length) <= lunar_day_length
        % Lunar day: Power generation should meet or exceed min_required_power
        power_generated = max(base_generation_rate, min_required_power);
    else
        % Lunar night: Reduced or no power generation
        power_generated = 0; % Assuming no power generation during lunar night
    end
end

% Function to adjust pressure
function adjusted_pressure = adjust_pressure(current_pressure, min_pressure, max_pressure)
    % Logic to adjust pressure
    % Example: If pressure is too low, increase it, and vice versa
    if current_pressure < min_pressure
        adjusted_pressure = current_pressure + (min_pressure - current_pressure);
    elseif current_pressure > max_pressure
        adjusted_pressure = current_pressure - (current_pressure - max_pressure);
    else
        adjusted_pressure = current_pressure;
    end
end




