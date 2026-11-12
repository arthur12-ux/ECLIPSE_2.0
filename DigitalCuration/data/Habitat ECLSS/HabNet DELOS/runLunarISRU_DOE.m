clear all
close all
clc
%% set mission parameters
numberOfCrewDOE = [2, 4];
missionDurationInHoursDOE = [30, 60, 90, 180].*24;% 7, 30 , 60, 90, 180 days; DELETE 7 DAYS
isruAddedWaterRateDOE = [0.1, .5, 1.5, 3];      % Liters/hour which is equal to kg/hr
initialWaterLevelPerDayDOE = [10, 30, 50]; %(Based on mission planner's assumption) ISS is 32.85 L/day) 1500 L for 30 day, so that scaled is ~50L/day (Commensurate with ISS), also assumed that initialWaterLevel is = to potable water tank size
waterPayloadMassDOE = [50, 100, 200, 400]; % in days  Note, Increase payload up to 300

% numberOfCrewDOE = [2];
% missionDurationInHoursDOE = [7].*24;% 7, 30 , 60, 90, 180 days; DELETE 7 DAYS
% isruAddedWaterRateDOE = [0.05, 1, 3];      % Liters/hour which is equal to kg/hr
% initialWaterLevelPerDayDOE = [50]; %(Based on mission planner's assumption) ISS is 32.85 L/day) 1500 L for 30 day, so that scaled is ~50L/day (Commensurate with ISS), also assumed that initialWaterLevel is = to potable water tank size
% waterPayloadMassDOE = [50, 100];

dFF = fullfact([length(numberOfCrewDOE), length(missionDurationInHoursDOE), length(isruAddedWaterRateDOE), length(initialWaterLevelPerDayDOE), length(waterPayloadMassDOE)]);
dFF(:,1) = numberOfCrewDOE(dFF(:,1));
dFF(:,2) = missionDurationInHoursDOE(dFF(:,2));
dFF(:,3) = isruAddedWaterRateDOE(dFF(:,3));
dFF(:,4) = initialWaterLevelPerDayDOE(dFF(:,4));
dFF(:,5) = waterPayloadMassDOE(dFF(:,5));

runLength = length(dFF); % TODO change
if runLength==5
    runLength=1;
end
titles = ["#Astronauts", "missionHours", "waterRate", "waterLevelPerDay", "payloadMass",...
    "tankVolume", "HabitableVolume", "ArchClass", "DeliveryIntervalDays", ...
    "waterDepletionHours", "remainingWater", "powerDepletionHours", "BatterySize", "SolarPArea", "isruPower", "isruProdMassTot", "earthLanders" ];
DOE_Results = titles;
% [inputMetrics, outputMetrics] = LunarDOE(dFF(1,:), 1);
% [inputMetrics, outputMetrics] = LunarDOE(dFF(2,:), 2);
% [inputMetrics, outputMetrics] = LunarDOE(dFF(3,:), 3);
% Note: Commented out waitbar in LunarDOE.m
%% Todo: Forloop on DOE_i
for DOE_i = 1:runLength
    inputArray = dFF(DOE_i,:);
    tic
    try
        % run LunarDOE --- function call is : function [inputMetrics, outputMetrics] = LunarDOE(inputArray, i)
        [inputMetrics, outputMetrics] = LunarISRU_DOE(inputArray, DOE_i);
    catch
        fprintf(['LunarDOE failed on iteration: ', num2str(DOE_i), ' with inputs: ', num2str(inputArray)]);
        % make all outputs -1 for this iteration
        combinedInOutputs = cat(2, inputArray, (ones(1, 12)*-1));
        DOE_Results = cat(1, DOE_Results, combinedInOutputs);
        continue;  % Jump to next iteration of: for i
    end
    toc
    close all
    combinedOutputs = cat(2, inputMetrics, outputMetrics);
    combinedInOutputs = cat(2, inputArray, combinedOutputs);
    DOE_Results = cat(1, DOE_Results, combinedInOutputs);
end
DOE_Results;
%% Write to CSV
writematrix(DOE_Results,'DOE_Results2.csv')
close all
 %% Tick Waitbar  TODO
%         if mod(i,100) == 0
%             waitbar(i/simtime,h,['Current tick: ',num2str(i),' | Time Elapsed: ',num2str(round(toc)),'sec']);
%         end


% % set random crew schedule to be true or false. Note: False in LunarDOE
% randomSchedule = false; 
% % set to use methane pyrolysis or not. Note: False in LunarDOE
% methanePyrolysis = false;



%% run resilience calculations
% resilienceData = habnetResilienceCalculation(missionData);


%     disp(["INPUT: The number of astronauts is: ", dFF_vals(1)]);
%     disp(["INPUT: The mission duration in days is: ", ceil(missionDurationInHours/24)]);
%     disp(["INPUT: The ISRU water resupply rate in [kg/hr] is: ", dFF_vals(3)]);
%     disp(["INPUT: The initial water level per day of a mission [L/day] is: ", dFF_vals(4)]);
%     disp(["INPUT: The mass of a water payload delivered to the habitat is: ", payloadMass]);
%     inputs = dFF_array;
    %% Print Input Additional Metrics:
%     disp(["OUTPUT: The initial water level (and water tank volume) in [L] is: ", initialWaterLevel]);
%     disp(["OUTPUT: The habitable volume [m^3] selected based on mission duration: ", totHabVolume]);
%     disp(["OUTPUT: The architecture class based on habitable volume is: ", architecture]);
%     disp(["OUTPUT: The delivery interval in days for water resupply is: ", num2str(deliveryInterval)]);
%     inputMetrics = [initialWaterLevel, initialWaterLevel, architecture, deliveryInterval];
    %% Print Final Output Metrics:
%     disp(["OUTPUT: The time until depletion for water in hours: ", depletionMetrics(1)]);
%     disp(["OUTPUT: The final amount of water at end of mission in L: ", data.potablewaterstorelevel(simtimeDepletionIndex)]);
%     disp(["OUTPUT: The time until depletion for power in hours: ", depletionMetrics(2)]); % usually NaN
%     disp(["OUTPUT: The Battery Size in Whr was: ", batteryCapacity]);
%     disp(["OUTPUT: The Solar Panel Size in kWhr was: ", solarPanelSize]);
%     disp(["OUTPUT: The ISRU power Reqired was: ", isruPwrReq]);
%     disp(["OUTPUT: The ISRU production mass (Battery+SolarPanels+isruProd+Hoppers mass) [kg] is: ", isruProdMass]);
%     disp(["OUTPUT: The mass of earth delivered water landers (landed mass) in kg is: ", num2str(massAllEarthLanders)]);

