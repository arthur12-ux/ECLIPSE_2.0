function [inputMetrics, outputMetrics] = LunarISRU_DOE(inputArray, i)
    


    %%  Habitation Development Unit / Human Exploration Research Analog Default Simulation Case
    %   By: Sydney Do (sydneydo@mit.edu)
    %   Date Created: 2/7/2015
    %   Last Updated: 4/18/2015
    %
    %   Simulation Notes: Code to model baseline architecture for the ICES2015
    %   paper entitled: Benefits of In-Situ Manufacturing for Mars
    %   Explorationhttps://ttu-ir.tdl.org/bitstream/handle/2346/64526/ICES_2015_submission_287.pdf?sequence=1&isAllowed=y
    %   This simulation models four crew inhabitating the HDU for 26 months
    %   (one Martian synodic period). The desired output is the rate of
    %   resupply required over time, as well as the survival time of the crew
    %   when a failure of a particular system occurs
    %
    %   UPDATE 4/18/2015 Added pressure balancer code and restructured time
    %   loop to accomodate this code
    %
    %   UPDATE 2/23/2015 - Turned off fan between suitlock and lab to prevent
    %   air exchange - Modified code so that Suitlock PCA and CCAA were only
    %   operated when no crew were on EVA
    %
    %   UPDATE 2/21/2015 - Code added to invoke a failure at a desired time
    %   within the simulation time horizon
    %
    %   UPDATE 12/21/2014 - Corrected plant model code (ShelfImpl3.m - updated
    %   12/20/2014) incorporated - Updated plant growth profile incorporated
    %   (calculated 12/21/2014 - see Modified Energy Cascade Low CO2
    %   Correction.docx for details)
    %
    %   
    %%  Simulation Notes
    %   Time Horizon: 26 months (time between resupply) (approx. 19000 hours)
    %   calculated from 2*365*24 + 2*31*24 (ie. 2 years + 2 months) Crew Size:
    %   4 persons
    %   
    %   Minimum-Pressure Atmosphere: 52.4kPa, 32% O2 (Corresponds to EAWG
    %   Recommendation for Mars Habitats)
    %
    %% CODE
%     clear all
%     close all
%     clc
    % close all

    tic

    %% CODE DOE Run
%     numberOfCrewDOE = [2, 4];
%     missionDurationInHoursDOE = [30, 60, 90, 180].*24;% 7, 30 , 60, 90, 180 days; DELETE 7 DAYS
%     isruAddedWaterRateDOE = [0.05, 1, 3, 5];      % Liters/hour which is equal to kg/hr
%     initialWaterLevelPerDayDOE = [10, 30, 50]; %(Based on mission planner's assumption) ISS is 32.85 L/day) 1500 L for 30 day, so that scaled is ~50L/day (Commensurate with ISS), also assumed that initialWaterLevel is = to potable water tank size
%     waterPayloadMassDOE = [50, 100]; % in days
%     dFF = fullfact([length(numberOfCrewDOE), length(missionDurationInHoursDOE), length(isruAddedWaterRateDOE), length(initialWaterLevelPerDayDOE), length(waterPayloadMassDOE)]);
%     dFF(:,1) = numberOfCrewDOE(dFF(:,1));
%     dFF(:,2) = missionDurationInHoursDOE(dFF(:,2));
%     dFF(:,3) = isruAddedWaterRateDOE(dFF(:,3));
%     dFF(:,4) = initialWaterLevelPerDayDOE(dFF(:,4));
%     dFF(:,5) = waterPayloadMassDOE(dFF(:,5));
    dFF_vals = inputArray
%     DOE_i = 1;
    % dFF_vals = dFF(DOE_i,:); % 2.0000  168.0000    0.0500         0
%     dFF_vals = [2.0000,   24*30,    1,         10,      100];
    initialWaterLevel = dFF_vals(2)*dFF_vals(4)/24; % Also tank water level


    FSHVolume = 140000; % cm^3
    Tot_Habitable_VolumeFSH = FSHVolume; % m^3
    HMPVolume = 25000; % cm^3
    Tot_Habitable_VolumeFSH_HMP = FSHVolume+HMPVolume; % m^3
    habVolume = 56000; % cm^3
    loftVolume = 60000; % cm^3
    Tot_Habitable_Volume12 = habVolume*3+loftVolume; % m^3
    % architecture = 0; % to be used for switch case statements down below (quite convoluted)
    switch(dFF_vals(2)/24)
       case {7, 30, 60} 
          totHabVolume=FSHVolume;
          architecture = 1;
       case {90} 
          totHabVolume=FSHVolume+HMPVolume;
          architecture = 2;
       otherwise 
          totHabVolume=habVolume*3+loftVolume;
          architecture = 3;
    end

    %% Key Mission Parameters
    missionDurationInHours = dFF_vals(2);% 60 days;
    % missionDurationInHours = missionDuration;
    r = dFF_vals(3); % isruAddedWaterRate. Note: Current loss levels are .1625 L/hr or kg/hr vs ~1.4 kg/hr loss on ISS which is 8x more efficient
%     r = 0.5; % COMMENT OUT TO RUN PROPERLY % Delete!!!  Delete!!!  Delete!!! Delete!!! Delete!!! Delete!!! Delete!!! Delete!!! Delete!!! Delete!!! Delete!!! Delete!!! Delete!!! Delete!!! Delete!!! Delete!!!
    isruPwrReq = r*10784; % isruAddedWaterRate* 10784 [Watts/(kg/hr)] conversion (from regressions on isru technology)
    isruMass = 321.88*r+3.8745; % From regressions See excel spreadsheet: ISRU_lit_rate_Masses2.xls
    isruPwrUsedTot = isruPwrReq*missionDurationInHours; % isruAddedWaterRate*  Watts/rate (from regressions on isru technology)
    % upperPowerGenTot = Tot_Habitable_Volume*(50000/228000)+isruPwrReq; % FOR NUCLEAR OPTION upperPowerGenTot = Tot_Habitable_Volume*(50000/228m^3)+isruPwrReq
    upperPowerGenTot = 1; % FOR SOLAR OPTION upperPowerGenTot = Tot_Habitable_Volume*(50000/228m^3)+isruPwrReq; dOES NOTHING
    BasePowerUseOneYr4crewHab = 1e5*(0.0363*r^2+0.1447*r+0.5324);%*(0.1+totHabVolume/Tot_Habitable_Volume12); % kW or kWhr (based on power use for senario 12.1 in current demoDay setup.   NOTE: Add higher intercept point for higher base power draws
    batteryCapacity = (isruPwrReq+BasePowerUseOneYr4crewHab)*1; % ?_????=(?_????+?_????)?1[??]      Similar to Apollo's 9600 Whr to Blue Origin's HLS at 20kWhr (presumed)
    batteryMass = batteryCapacity/180; % 180 [Whr/kg] from: https://www.nasa.gov/sites/default/files/atoms/files/darcy_-_nasa_batt_workshop_2015.pdf
    solarPanelSize = (BasePowerUseOneYr4crewHab+isruPwrReq)*1/(1334*0.97); % m^2, calulation is from powerNeeded/solarIntensityMaxMoon (note these are not variables)
    solarISRUMass = (isruPwrReq)/200; % 200 [W/kg] SMAD

    %% Hopper Mass
    % From the MS thesis: https://dspace.mit.edu/handle/1721.1/65292
    % assuming 10 hops per hopper before replacement, distance of 2.5km hops and
    % a height of 10km. Note: for a more accurate mass, reccomend making model
    % using equations from said source. (Would be at least 3 week modeling
    % effort)
    payloadMass = dFF_vals(5); % [kg]
    deliveryInterval = payloadMass/r; % assumes 100kg mass of payload
    hopperReplacementInterval = 10*deliveryInterval;
    % massPayload = deliveryInterval*r % Gives a mass of water to be delivered
    % Mutltiplied by 2 for ascent and descent, and is the equation for escape velocity for a circular orbit v^2=mu*(1/a) (one with hop height added to moon's radius for aphelion)
    hopHeight = 1; % [km] Note the depth of shakleton crater is 4.2km
    moonRadius = 1737.1; % [km]
    moonMass = 7.346e22; % [kg]
    G = 6.67430e-11; % [N*m^2/kg^2]
    dV_hopHeight = (G*moonMass/(moonRadius))^0.5-(G*moonMass/(moonRadius+hopHeight))^0.5; % v_equator&Hop-v_circularEquator  [km/s]
    dV_HoverDist = 3.5; % for 2.5 km hop.  or 4.2 [km/s] for a 4.5 km hop
    dV = dV_hopHeight+dV_HoverDist;
    propMassPERinitMassRatio = 2*.119; %.112; % for mass0 of 150kg, if mass0=50kg then should be .135. From Figure III-4 (multiplied by 2 as num hops for this figure is 1 not 10, thus more delta v per tank of prop)
    massLander0 = payloadMass*(10.1/7)+50; % Ratio from Figure A-16 on MS thesis
%     massLander0Prop = massLander0*propMassPERinitMassRatio;
    massLander0Structure = massLander0-massLander0*propMassPERinitMassRatio;
    massHopper = massLander0Structure + massLander0Prop*(dV/dV_HoverDist); % The reason to increase the propellant mass is that Figure A-16 has a hop height of 10 m, not >1km for crater rim heights
    massAllHoppers = massHopper*round(missionDurationInHours/hopperReplacementInterval); % could also do ceil()
    % From MS thesis Figure A-16

    %% Assume average of drymass/payload for perigrine and Nova-C Landers from CLPS for 100 kg payload
    ratioDryMass2PayLoad = (1283/256+1500/100)/2; % https://en.wikipedia.org/wiki/Commercial_Lunar_Payload_Services,     https://spaceflightnow.com/2019/10/02/intuitive-machines-selects-spacex-to-launch-commercial-lunar-lander/
    landedMass = payloadMass*ratioDryMass2PayLoad; % use payload of 100 kg per lander (as according to their designed PL)
    massAllEarthLanders = landedMass*ceil(missionDurationInHours/deliveryInterval);


    isruProdMass = isruMass+batteryMass+solarISRUMass+massAllHoppers;
    numberOfEVAdaysPerWeek = 5;
    numberOfCrew = dFF_vals(1);
    missionDurationInWeeks = ceil(missionDurationInHours/24/7);

    TotalAtmPressureTargeted = 55;      % EAWG recommended atmosphere for Mars surface habitats 70.3;        % targeted total atmospheric pressure, in kPa
    O2FractionHypoxicLimit = 0.305;     % lower bound for a 55kPa atm based on EAWG Fig 4.1.1 and Advanced Life Support Requirements Document Fig 4-3
    TargetO2MolarFraction = 0.32; 
    o2fireRiskMolarFraction = 0.6;      % overwrite default value of 0.3 since target O2 fraction is 0.32. We set to 0.6 as this corresponds roughly to the hyperoxia limit for a 55kPA atmosphere (REF: Fig 6.2-2 HIDH)
    idealGasConstant = 8.314;           % J/K/mol

    %% Calculation of ISRU Mass required
    % Calculate Battery mass

    % Based on rate calculate mass from rubberized interpolation or isru type

    %% Calculation of Earth Delivered ISRU mass
    % based on simple delta V budget and CLPS lander porportions.

    % TotalPPO2Targeted = TargetO2MolarFraction*TotalAtmPressureTargeted;               % targeted O2 partial pressure, in kPa (converted from 26.5% O2)

    %% Invoke One-At-A-Time Failure at Given Tick
    FailureTick = 1;

    ErrorList = {'FSHPCA', 'HMPPCA', 'LabPCA','LoftPCA','PCMPCA','SuitlockPCA','PLMPPRV',...
        'LabCCAA','LoftCCAA','PCMCCAA','SuitlockCCAA','mainvccr','ogs',...
        'crs.CompressorError','crs.ReactorError','crs.SeparatorError',...
        'waterRS.WPAerror','waterRS.UPAerror','Lab2PCMFan','PLM2PCMFan',...
        'Loft2PCMFan','Lab2AirlockFan'};

    SystemToFail = {};%1:5;%[1,12,5,14];%1,6,17,11ogs,12-14crs  No Errors

    % Determine failure command based on type of technology

    FailCommand = cell(1,length(SystemToFail));
    failcount = 0;
    for j = 1:length(SystemToFail)
        if SystemToFail(j) == 12 || SystemToFail(j) == 13 || ...
                SystemToFail(j) == 14 || SystemToFail(j) == 15 || ...
                SystemToFail(j) == 16
            FailCommand{j} = [ErrorList{SystemToFail(j)},'=1;'];
        else
            FailCommand{j} = [ErrorList{SystemToFail(j)},'.Error=1;'];
        end
    end

    %% ISRU Production Rates
    shareISRUtoCrops = 0.1;
    isruAddedWater = r*(1-shareISRUtoCrops);      % Liters/hour
    isruAddedCropWater = r*shareISRUtoCrops;  % Liter/hour
    isruAddedO2 = 0;            % moles/hour
    isruAddedN2 = 0;          % moles/hour

    %% EMU
    EMUco2RemovalTechnology = 'RCA';  % options are RCA or METOX
    EMUurineManagementTechnology = 'UCTA';  % options are MAG or UCTA

    %% Initialize Stores
    % Potable Water Store within Life Support Units (note water store capacity
    % measured in liters)

    % initialWaterLevel = 2960; %1500
    PotableWaterStore = StoreImpl('Potable H2O','Material',initialWaterLevel,initialWaterLevel);      % Assume 1500L of water initially - note that ATV transports 840L of water while HTV carries 600L in 14 CWC-Is
    % PotableWaterStore = StoreImpl('Potable H2O','Material',56.7,56.7);      %
    % WPA Product Water tank has a capacity of 56.7L (ref: SAE 2008-01-2007).
    % Note that on ISS, the WPA Product Water Tank feeds the Potable Water
    % Dispenser, the OGA, and the WHC flush and hygiene hose.

    % O2 Store within Life Support Units (note O2 capacity measured in moles)
    initialO2TankCapacityInKg = 670; %3*91; %120; %100.2;  % Corresponds to three O2 tanks currently located on exterior of Quest airlock (REF: ISS ECLSS Status 2010-11)
    o2MolarMass = 2*15.999; % g/mol
    initialO2StoreMoles = initialO2TankCapacityInKg*1E3/o2MolarMass;
    O2Store = StoreImpl('O2 Store','Material',initialO2StoreMoles,initialO2StoreMoles);

    % Dirty water corresponds to Humidity Condensate and Urine 
    DirtyWaterStore = StoreImpl('Dirty H2O','Material',18/2.2*1.1,0);        % Corresponds to the UPA waste water tank - 18lb capacity (we increase volume by 10% to avoid loss of dirty water when running UPA in batch mode)

    % Grey water corresponds to wash water - it is included for the purposes of
    % modeling a biological water processor
    GreyWaterStore = StoreImpl('Grey H2O','Material',100/2.2,0);
    % Note that WPA waste water tank has a 100lb capacity, but is nominally
    % operated at 65lb capacity
    % Lab Condensate tank has a working capacity of 45.5L

    % Gas Stores

    H2Store = StoreImpl('H2 Store','Material',10000,0);     % H2 store for output of OGS - note that currently on the ISS, there is no H2 store, it is sent directly to the Sabatier reactor 
    CO2Store = StoreImpl('CO2 Store','Material',1000,0);    % CO2 store for VCCR - refer to accumulator attached to CDRA

    MethaneStore = StoreImpl('CH4 Store','Environmental');    % CH4 store for output of CRS (Sabatier) - note CH4 is currently vented directly to space on ISS
    % Look at option of including a pyrolyzer?

    % N2 Store
    % Corresponds to 2x high pressure N2 tanks currently mounted on exterior of Quest airlock on ISS (each holds 91kg of N2)
    % This is subject to change based on requirements
    numberOfN2Tanks = 2;% Corresponds to the number of N2 tanks on ISS
    initialN2TankCapacityInKg = 38; %numberOfN2Tanks*91;
    n2MolarMass = 2*14.007; %g/mol;
    initialN2StoreMoles = initialN2TankCapacityInKg*1E3/n2MolarMass;
    % initialN2StoreMoles = 1260;
    N2Store = StoreImpl('N2 Store','Material',initialN2StoreMoles,initialN2StoreMoles);     

    % Power Stores
    MainPowerStore = StoreImpl('Power','Material',batteryCapacity, batteryCapacity); % this is the size of your habitat battery

    % Waste Stores
    DryWasteStore = StoreImpl('Dry Waste','Material',1000000,0);    % Currently waste is discarded via logistics resupply vehicles on ISS

    %% Food Stores
    % carry along 120days worth of calories - initial simulations show an
    % average crew metabolic rate of 3040.1 Calories/day
    % Note that 120 days is equivalent to the longest growth cycle of all the
    % plants grown
    CarriedFood = Wheat;
    AvgCaloriesPerCrewPerson = 3040.1;
    StockedDaysOfFood = ceil(missionDurationInHours/24)+14; % Days worth of food to carry - we initially assume that all food is carried along + 14 days buffer
    CarriedCalories = numberOfCrew*AvgCaloriesPerCrewPerson*StockedDaysOfFood;    % one synodic period's worth of calories
    CarriedTotalMass = CarriedCalories/CarriedFood.CaloriesPerKilogram; % Note that calories per kilogram is on a wet mass basis

    initialfood = FoodMatter(Wheat,CarriedTotalMass,CarriedFood.EdibleFreshBasisWaterContent*CarriedTotalMass); % xmlFoodStoreLevel is declared within the createFoodStore method within SimulationInitializer.java

    CarriedFoodStore = FoodStoreImpl(CarriedTotalMass,initialfood);

    LocallyGrownFoodStore = FoodStoreImpl(1);

    %% Initialize SimEnvironments
    % Convert daily leakage rate to hourly leakage rate
    dailyLeakagePercentage = 0.14;      % Based on BVAD Table 4.1.1 for percentage of total gas mass lost per day  (between 0.05 and 0.14)
    % Let H = hourLeakagePercentage and initial total moles of gas = n_init
    % Therefore we want:
    % n_init*(1-dailyLeakagePercentage/100) = n_init*(1-H/100)^24
    % Solving for H yields:
    % H = 100*(1-(1-dailyLeakagePercentage/100)^(1/24))

    % Using the above derived equation:
    hourlyLeakagePercentage = 100*(1-(1-dailyLeakagePercentage/100)^(1/24));
    %       1000 Literes = 1 m^3
    %       function obj = SimEnvironmentImpl(name,pressure,Volume,o2Percentage,co2Percentage,nitrogenPercentage,waterPercentage,...
    %               otherPercentage,leakPercentage,potablewaterstore,greywaterstore,dirtywaterstore,drywastestore,foodstore,maxO2fraction)

    % All ECLSS technologies are located in FSH for Arch 1 and 2, while HMP is
    % like the Lab
    FSH = SimEnvironmentImpl('Foundational Surface Habitat',             55,FSHVolume, 0.32,0.003,0.676,0,0.001,hourlyLeakagePercentage,PotableWaterStore,GreyWaterStore,DirtyWaterStore,DryWasteStore,[LocallyGrownFoodStore,CarriedFoodStore],o2fireRiskMolarFraction);     %Note volume input is in Liters. Volume reference - CxP Scenario 12.1
    HMP = SimEnvironmentImpl('Habitable Mobility Platform',              55,HMPVolume, 0.32,0.003,0.676,0,0.001,hourlyLeakagePercentage,PotableWaterStore,GreyWaterStore,DirtyWaterStore,DryWasteStore,[LocallyGrownFoodStore,CarriedFoodStore],o2fireRiskMolarFraction);     %Note volume input is in Liters. Volume reference - CxP Scenario 12.1 
    Lab = SimEnvironmentImpl('Laboratory - Pressurized Excursion Module',55,habVolume, 0.32,0.003,0.676,0,0.001,hourlyLeakagePercentage,PotableWaterStore,GreyWaterStore,DirtyWaterStore,DryWasteStore,[LocallyGrownFoodStore,CarriedFoodStore],o2fireRiskMolarFraction);     %Note volume input is in Liters. Volume reference - CxP Scenario 12.1
    Loft = SimEnvironmentImpl('Loft',                                    55,loftVolume,0.32,0.003,0.676,0,0.001,hourlyLeakagePercentage,PotableWaterStore,GreyWaterStore,DirtyWaterStore,DryWasteStore,[LocallyGrownFoodStore,CarriedFoodStore],o2fireRiskMolarFraction);        % Volume reference - X-Hab Solicitation 2010
    PCM = SimEnvironmentImpl('Pressurized Core Module',                  55,habVolume, 0.32,0.003,0.676,0,0.001,hourlyLeakagePercentage,PotableWaterStore,GreyWaterStore,DirtyWaterStore,DryWasteStore,[LocallyGrownFoodStore,CarriedFoodStore],o2fireRiskMolarFraction);   % All ECLSS technologies are located here
    PLM = SimEnvironmentImpl('Pressurized Logistics Module',             55,habVolume, 0.32,0.003,0.676,0,0.001,hourlyLeakagePercentage,PotableWaterStore,GreyWaterStore,DirtyWaterStore,DryWasteStore,[LocallyGrownFoodStore,CarriedFoodStore],o2fireRiskMolarFraction);   % All ECLSS technologies are located here
    %% Airlock Environment
    % This environment is modeled to represent airlock depressurization losses
    % and O2 consumed during EVA prebreathe

    % Include airlock PCA (to recharge airlock)
    % Remember to vent airlock for only first tick of EVA
    % Remove this amount of air from the hab everytime an EVA occurs

    airlockFreegasVolume = 7.4*1E3; %Obtained from "A Dual Chamber Hybrid Inflatable Suitlock for Planetary Surfaces or Deep Space" %3.7*1E3;     % L (converted from 3.7m^3) REF: BVAD Section 5.2.1 - this is equivalent to shuttle airlock - total volume is 4.25m^3 (pg 230 - The New Field of Space Architecture)
     %%%%%% TODO CHANGE %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    Suitlock = SimEnvironmentImpl('Suitlock',55,airlockFreegasVolume,0.32,0.003,0.676,0,0.001);      % We assume that the suitlock does not leak
     %%%%%% TODO CHANGE %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    suitlockAirLossVolume = 0.97*0.72*0.0254; % Assumed suitlock loss volume based on suitlock plate dimensions (assuming a 1 inch air gap). REF: Lunar Habitat Airlock/Suitlock (also refer to Space Architecture Book)
    suitlockCycleLoss = Suitlock.pressure*suitlockAirLossVolume/(idealGasConstant*(273.15+Suitlock.temperature));    % REF: ISS Airlock depress pump is operated down to 13.8kPa, so the rest of the air is vented overboard - REF: "Trending of Overboard Leakage of ISS Cabin Atmosphere" (AIAA 2011-5149)

    %% Set up EVA environment
    % Size EVA for two people - include airlock losses when EVA is executed
    % Currently, CrewPersonImpl is only configured to exchange air with
    % the environment that their activity is in
    % EVAs last for eight hours continuously
    % EVA essentially consumes gases from the O2 storage tank - since these
    % recharge the PLSS tanks

    %% EVA Consumable Consumption
    % EVAs occur over eight ticks
    numberOfEVAcrew = 2;
    O2molarMass = 2*15.999;          % g/mol
    EMUpressure = 29.6; % in kPa - equates to 4.3psi - same as Shuttle EMU and is quoted in EAWG Section 5.1 for dexterous tasks
    EMUvolume = 2*28.3168*numberOfEVAcrew; % Generally between 1.5 and 2 cubic feet [L] - EMU Handbook Section 1.5.5      % in Liters, for two crew members
    EMUtotalMoles = EMUpressure*EMUvolume/(idealGasConstant*(273.15+23));   % Total moles within both EMUs
    % EMUleakmoles = 0.005*1E3/O2molarMass;       % From BVAD Section 5.2.2 - EMU leakage is 0.005kg/h (which is higher than the value quoted within Figure 1.8 of the Hamilton Sundstand EMU Handbook (36.2cubic cm/min)
    Vleakrate = 36.2*1E-3*60;   % (L/hr) Maximum volumetric leakage rate of the PGA is calculated as 36.2 cubic cm/min (Figure 1.8) [2] [L/hr]
    EMUleakmoles = EMUpressure*Vleakrate/(idealGasConstant*(273.15+23));      % Maximum mass leakage rate of the PGA [kg/s]
    EMUleakPercentage = EMUleakmoles*numberOfEVAcrew/EMUtotalMoles;

    % EMUco2RemovalTechnology = 'METOX';  % other option is RCA
    % EMUurineManagementTechnology = 'UCTA';  % other option is MAG

%     load EVAPLSSoutput
    emuCO2levelMETOX = 0.0044; emuCO2levelRCA = 0.0066;
    emuO2levelMETOX = 0.6630; emuO2levelRCA = 0.6608;
    emuVaporlevelcommon = 0.0135; plssCO2removedlevelMETOX = 7.7814;
    plssCO2removedlevelRCA = 7.7528; plssfeedwatertanklevelMETOX = 0.9259;
    plssfeedwatertanklevelRCA = 2.8528; plssO2TanklevelMETOX = 8.0113;
    plssO2TanklevelRCA = 8.0442;
    % Define end of EVA EMU gaseous parameters
    if strcmpi(EMUco2RemovalTechnology,'METOX')
        finalEMUo2level = emuO2levelMETOX*numberOfEVAcrew;
        finalEMUco2level = emuCO2levelMETOX*numberOfEVAcrew;
        finalFeedwaterTanklevel = plssfeedwatertanklevelMETOX*numberOfEVAcrew;    % also corresponds to total humidity level consumed, this captures any thermal control leakage
        plssO2TankLevel = plssO2TanklevelMETOX*numberOfEVAcrew;        % set corresponding StoreImpl.currentLevel to this value
        totalCO2removed = plssCO2removedlevelMETOX*numberOfEVAcrew;
        METOXregeneratorLoad = StoreImpl('METOX adsorbed CO2','Environmental');
        metoxCO2regenRate = totalCO2removed/10;         % 10 hours to completely regenerate a METOX canister
    elseif strcmpi(EMUco2RemovalTechnology,'RCA')
        finalEMUo2level = emuO2levelRCA*numberOfEVAcrew;
        finalEMUco2level = emuCO2levelRCA*numberOfEVAcrew;
        finalFeedwaterTanklevel = plssfeedwatertanklevelRCA*numberOfEVAcrew;
        plssO2TankLevel = plssO2TanklevelRCA*numberOfEVAcrew;        % set corresponding StoreImpl.currentLevel to this value
        totalCO2removed = plssCO2removedlevelRCA*numberOfEVAcrew;
    end
    finalEMUvaporlevel = emuVaporlevelcommon*numberOfEVAcrew;


    % Thermal control = {sublimator,radiator,cryogenic} = water usage = [0.57kg/hr,0.19kg/h,0]      REF:
    % BVAD Section 5.2.2
    % Note: Cryogenic cooling refers to cryogenic storage of O2
    % O2 use: metabolic + leakage - 0.076kg/h, Note: O2 leakage alone is
    % 0.005kg/h - REF BVAD Section 5.2.2 (compare this with EMU data)
    % EVAco2removal = [METOX, Amine Swingbed]
    % Amine Swingbed O2 loss rate is 0.15kg/h

    EMUfeedwaterCapacity = 10*0.453592;  % (L), converted from 10 pounds of water, assuming a water density of 1000kg/m^3 = 1kg/L, REF - Section 2.1.4 EMU Handbook
    EMUfeedwaterReservoir = StoreImpl('PLSS Feedwater Reservoir','Material',EMUfeedwaterCapacity*numberOfEVAcrew,0);

    % Two options for liquid metabolic waste - either throw it away (as in the
    % EMU MAG), or collect urine and feed it back into the UPA - as in Apollo
    % EMU - find a reference for this!)
    if strcmpi(EMUurineManagementTechnology,'UCTA')
        EVAenvironment = SimEnvironmentImpl('EVA Environment',EMUpressure,EMUvolume,1,0,0,0,0,EMUleakPercentage,PotableWaterStore,EMUfeedwaterReservoir,DirtyWaterStore,DryWasteStore,[LocallyGrownFoodStore,CarriedFoodStore]);
    elseif strcmpi(EMUurineManagementTechnology,'MAG')
        EMUmetabolicWaste = StoreImpl('EVA MAG','Environmental');       % This is to replace the dirty water store if water is collected within the MAG
        EVAenvironment = SimEnvironmentImpl('EVA Environment',EMUpressure,EMUvolume,1,0,0,0,0,EMUleakPercentage,PotableWaterStore,EMUfeedwaterReservoir,EMUmetabolicWaste,DryWasteStore,[LocallyGrownFoodStore,CarriedFoodStore]);
    end

    EMUo2TankCapacity = 1.217*453.592/O2molarMass;      % moles, Converted from 1.217lbs - REF: Section 2.1.3 EMU Handbook
    EMUo2Tanks = StoreImpl('EMU O2 Bottles','Material',EMUo2TankCapacity*numberOfEVAcrew,0);



    % Note: EMU Food bar is no longer flown (REF:
    % http://spaceflight.nasa.gov/shuttle/reference/faq/eva.html)

    %% EMU Prebreathe per CrewPerson
    % This is the same as that employed for the space shuttle (going from a
    % 70.3kPa 26.5% O2 atmosphere to a 29.6kPa 100% O2 atmosphere
    % - Prebreathe lasts for 40 minutes and is performed in suit (REF: Table
    % 3.1-1 EAWG Report)
    % On ISS, an in-suit prebreath lasts 240 minutes (REF: Table 3.1-1 EAWG
    % Report) and consumes 4.53kg per EVA (REF: Methodology and Assumptions
    % of Contingency Shuttle Crew Support (CSCS) Calculations Using ISS ECLSS -
    % SAE 2006-01-2061)

    % Modified value according to more updated data:
    % A typical suit purge on the ISS will achieve ? 95% O2 after 8 minutes and requires about 0.65 lb of O2."
    % REF: Fifteen-minute EVA Prebreathe Protocol Using NASA's Exploration
    % Atmosphere - AIAA2013-3525 - 0.65lb O2 used per EMU (includes inflation)
    prebreatheO2 = 0.65*453.592/O2molarMass*numberOfEVAcrew;   % moles of O2... supplied from O2 tanks

    %% Initialize Pressure Balancer
    % Adjacency Matrix to represent connectivity between modules
    Modules1 = [FSH,Suitlock];
    AdjacencyMatrix1 = zeros(length(Modules1));
    AdjacencyMatrix1(1,2) = 1;
    AdjacencyMatrix1(2,1) = 1;
    PressureFlow1 = PressureDistribute(Modules1,AdjacencyMatrix1);

    Modules2 = [FSH,Suitlock,HMP];
    AdjacencyMatrix2 = zeros(length(Modules2));
    AdjacencyMatrix2(1,[2,3]) = 1;
    AdjacencyMatrix2([2,3], 1) = 1;
    PressureFlow2 = PressureDistribute(Modules2,AdjacencyMatrix2);

    Modules3 = [PCM,Lab,Loft,Suitlock,PLM];
    AdjacencyMatrix3 = zeros(length(Modules3));
    AdjacencyMatrix3(1,[2,3,5]) = 1;
    AdjacencyMatrix3(2,1) = 1;
    AdjacencyMatrix3(3,[1,4]) = 1;
    AdjacencyMatrix3(4,3) = 1;
    AdjacencyMatrix3(5,1) = 1;
    PressureFlow3 = PressureDistribute(Modules3,AdjacencyMatrix3);

    %% Initialize Key Activity Parameters

    % Baseline Activities and Location Mappings
    lengthOfExercise = 2;                       % Number of hours spent on exercise activity

    % Generate distribution of habitation options from which IVA activities
    % will take place
    HabDistribution1= [FSH];
    HabDistribution2= [FSH, HMP];
    HabDistribution3= [repmat(Lab,1,2),repmat(Loft,1,2),PCM,PLM];
    switch(architecture)
        case 1
            IVAhour = ActivityImpl('IVA',2,1,HabDistribution1);          % One hour of IVA time (corresponds to generic IVA activity)
            Sleep = ActivityImpl('Sleep',1,8,FSH);          % Sleep period
            Exercise = ActivityImpl('Exercise',5,lengthOfExercise,FSH);    % Exercise period
        case 2
            IVAhour = ActivityImpl('IVA',2,1,HabDistribution2);          % One hour of IVA time (corresponds to generic IVA activity)
            Sleep = ActivityImpl('Sleep',1,8,FSH);          % Sleep period
            Exercise = ActivityImpl('Exercise',5,lengthOfExercise,FSH);    % Exercise period
        case 3
            IVAhour = ActivityImpl('IVA',2,1,HabDistribution3);          % One hour of IVA time (corresponds to generic IVA activity)
            Sleep = ActivityImpl('Sleep',1,8,Loft);          % Sleep period
            Exercise = ActivityImpl('Exercise',5,lengthOfExercise,PCM);    % Exercise period
    end
    EVA = ActivityImpl('EVA',4,8,EVAenvironment);              % EVA - fixed length of 8 hours

    % Vector of baseline activities:
    ActivityList = [IVAhour,Sleep,Exercise,EVA];

    % Auto-Generate Crew Schedule
    [crewSchedule, missionEVAschedule,crewEVAScheduleLogical] = CrewScheduler(numberOfEVAdaysPerWeek,numberOfCrew,missionDurationInWeeks,ActivityList, false);
    %                                             CrewScheduler(numberOfEVAdaysPerWeek,numberOfCrew,missionDurationInWeeks,activityList,randomSchedule)
    %% Initialize CrewPersons
    astro1 = CrewPersonImpl2('Male 1',35,75,'Male',[crewSchedule{1,:}]);%,O2FractionHypoxicLimit);
    astro2 = CrewPersonImpl2('Female 1',35,55,'Female',[crewSchedule{2,:}]);
    if numberOfCrew~=4
        crew = struct('astro1',astro1, 'astro2', astro2);
    else
        astro3 = CrewPersonImpl2('Male 2',35,75,'Male',[crewSchedule{3,:}]);
        astro4 = CrewPersonImpl2('Female 2',35,55,'Female',[crewSchedule{4,:}]);
        crew = struct('astro1',astro1, 'astro2', astro2, 'astro3', astro3, 'astro4', astro4);
    end
    %% Clear crewSchedule to save ~2MB memory
    clear crewSchedule

    %% Biomass Stores
    BiomassStore = BiomassStoreImpl(100000);
    % Set more crop type for FoodMatter somewhere later on

    %% Initialize ISRU power req
    isruPower = isruPowerUseImpl(isruPwrReq, MainPowerStore); 
    %% Initialize default payload 
    missionPayload = ISSPayloadImpl(PotableWaterStore, GreyWaterStore, MainPowerStore); 
    %% Initialize crop shelves

    CropWaterStore = StoreImpl('Grey Crop H2O','Material',800,800);   % Initialize a 9200L water buffer (Changed to be 800 L instead)

    LettuceGrowthArea = 8*8*0.102^2;        % Growth area for atrium within HDU (REF: Plant Atrium System for Food Production in NASA's DSH Tests)
    if architecture==3
        LettuceShelf = ShelfImpl3(Lettuce,LettuceGrowthArea,Loft,CropWaterStore,CropWaterStore,MainPowerStore,BiomassStore);    % Grow this shelf all together (since total area is <1m^2)
    else
        LettuceShelf = ShelfImpl3(Lettuce,LettuceGrowthArea,FSH,CropWaterStore,CropWaterStore,MainPowerStore,BiomassStore);    % Grow this shelf all together (since total area is <1m^2)
    end
    %% Initialize FoodProcessor
    FoodProcessor = FoodProcessorImpl;
    FoodProcessor.BiomassConsumerDefinition = ResourceUseDefinitionImpl(BiomassStore,1000,1000);
    FoodProcessor.PowerConsumerDefinition = ResourceUseDefinitionImpl(MainPowerStore,1000,1000);
    FoodProcessor.FoodProducerDefinition = ResourceUseDefinitionImpl(LocallyGrownFoodStore,1000,1000);
    FoodProcessor.WaterProducerDefinition = ResourceUseDefinitionImpl(CropWaterStore,1000,1000);        % FoodProcessor now outputs back to crop water store
    FoodProcessor.DryWasteProducerDefinition = ResourceUseDefinitionImpl(DryWasteStore,1000,1000);


    %% Initialize all subsytems: Note will be differentiated by architecture type
    %% Initialize (Intermodule Ventilation) Fans

    % NB. Under normal power consumption conditions, the ISS IMV fan moves 
    % approx. 6791 moles of air every hour
    % As a result, we modify the max and desired molar flow rates to meet this
    % number
    % Desired is rounded up to 6800moles/hr, and the max corresponds to the max
    % volumetric flow rate of 4106L/min indicated within Section 2, Chapter
    % 3.2.6 of "Living Together In Space"
    % 4106L/min*60min/hr*70.3kPa/(8.314J/K/mol*296.15K) = 7034mol/hr (we round
    % this up to 7035mol/hr)

    % Architecture 1
    % IMV FSH and Airlock
    FSH2AirlockFan = ISSFanImpl2(FSH,Suitlock,MainPowerStore);
    % Architecture 2
    % IMV FSH and HMP (also uses fan for previous architecture)
    FSH2HMPFan = ISSFanImpl2(FSH,HMP,MainPowerStore);

    % IMV between Lab (PEM) and PCM
    Lab2PCMFan = ISSFanImpl2(Lab,PCM,MainPowerStore);

    % IMV between PLM and PCM
    PLM2PCMFan = ISSFanImpl2(PLM,PCM,MainPowerStore);

    % IMV between Loft and PCM
    Loft2PCMFan = ISSFanImpl2(Loft,PCM,MainPowerStore);

    % IMV between Lab (PEM) and Airlock
    Lab2AirlockFan = ISSFanImpl2(Lab,Suitlock,MainPowerStore);

    %% Initialize Injectors (Models ISS Pressure Control Assemblies)
    % See accompanying word doc for rationale behind PCA locations

    % Architecture 1
    % FSH PCA
    FSHPCA = ISSinjectorImpl(TotalAtmPressureTargeted,TargetO2MolarFraction,O2Store,N2Store,FSH);
    FSHPCA.UpperPPO2PercentageLimit = o2fireRiskMolarFraction;

    % Architecture 2
    % HMP PCA
    HMPPCA = ISSinjectorImpl(TotalAtmPressureTargeted,TargetO2MolarFraction,O2Store,N2Store,HMP);
    HMPPCA.UpperPPO2PercentageLimit = o2fireRiskMolarFraction;

    % Architecture 3
    % Lab (PEM) PCA
    LabPCA = ISSinjectorImpl(TotalAtmPressureTargeted,TargetO2MolarFraction,O2Store,N2Store,Lab);
    LabPCA.UpperPPO2PercentageLimit = o2fireRiskMolarFraction;

    % Loft PCA 
    LoftPCA = ISSinjectorImpl(TotalAtmPressureTargeted,TargetO2MolarFraction,O2Store,N2Store,Loft);
    LoftPCA.UpperPPO2PercentageLimit = o2fireRiskMolarFraction;

    % PCM PCA
    PCMPCA = ISSinjectorImpl(TotalAtmPressureTargeted,TargetO2MolarFraction,O2Store,N2Store,PCM);
    PCMPCA.UpperPPO2PercentageLimit = o2fireRiskMolarFraction;

    % Suitlock PCA
    SuitlockPCA = ISSinjectorImpl(TotalAtmPressureTargeted,TargetO2MolarFraction,O2Store,N2Store,Suitlock);
    SuitlockPCA.UpperPPO2PercentageLimit = o2fireRiskMolarFraction;

    % PLM PPRV
    PLMPPRV = ISSinjectorImpl(TotalAtmPressureTargeted,TargetO2MolarFraction,O2Store,N2Store,PLM,'PPRV');
    PLMPPRV.UpperPPO2PercentageLimit = o2fireRiskMolarFraction;

    %% Initialize Temperature and Humidity Control (THC) Technologies
    % Insert CCAA within Lab, Loft, PCM, and Suitlock
    % Placement of CCAAs is based on modules with a large period of continuous
    % human presence (i.e. large sources of humidity condensate)

    % FSH CCAA
    FSHCCAA = ISSDehumidifierImpl(FSH,GreyWaterStore,MainPowerStore);

    % Lab (PEM) CCAA
    LabCCAA = ISSDehumidifierImpl(Lab,GreyWaterStore,MainPowerStore);

    % Loft CCAA
    LoftCCAA = ISSDehumidifierImpl(Loft,GreyWaterStore,MainPowerStore);

    % PCM CCAA
    PCMCCAA = ISSDehumidifierImpl(PCM,GreyWaterStore,MainPowerStore);

    % Suitlock
    SuitlockCCAA = ISSDehumidifierImpl(Suitlock,GreyWaterStore,MainPowerStore);

    %% Initialize Power Production Systems
    % We assume basically unlimited power here
    % Initialize General Power Producer
    powerPS = PowerPSImpl('Solar',upperPowerGenTot, solarPanelSize);
    powerPS.PowerProducerDefinition = ResourceUseDefinitionImpl(MainPowerStore);%,50000,50000);   % use 50000 Whr/hr for nuclear flow rate max

    %% Initialize Air Processing Technologies

    % Initialize Main VCCR (Linear) AND OGS AND Power

    cropsTargetCO2 = 1200;      % Ideal CO2 PPM level for lettuce crops
    if architecture==3
        mainvccr = ISSVCCRLinearImpl(PCM,PCM,CO2Store,MainPowerStore,cropsTargetCO2);       % When there is a 5th element within the constructor for ISSVCCRLinearImpl, the CDRA is set to a reduced mode, where it only operates to reach a target CO2 level
        ogs = ISSOGA(TotalAtmPressureTargeted,TargetO2MolarFraction,PCM,PotableWaterStore,MainPowerStore,H2Store);
        powerPS.LightConsumerDefinition = Lab;
    else
        mainvccr = ISSVCCRLinearImpl(FSH,FSH,CO2Store,MainPowerStore,cropsTargetCO2);       % When there is a 5th element within the constructor for ISSVCCRLinearImpl, the CDRA is set to a reduced mode, where it only operates to reach a target CO2 level
        ogs = ISSOGA(TotalAtmPressureTargeted,TargetO2MolarFraction,FSH,PotableWaterStore,MainPowerStore,H2Store);
        powerPS.LightConsumerDefinition = FSH;
    end

    % Initialize CRS (Sabatier Reactor)
    crs = ISSCRSImpl(H2Store,CO2Store,GreyWaterStore,MethaneStore,MainPowerStore);

    %% Initialize Water Processing Technologies
    % Initialize WaterRS (Linear)
    waterRS = ISSWaterRSLinearImpl(DirtyWaterStore,GreyWaterStore,GreyWaterStore,DryWasteStore,PotableWaterStore,MainPowerStore);



    %% Initalization before Time Loop

    simtime = missionDurationInHours;
    % t = 1:simtime;
    data = struct();
    data.o2storelevel = zeros(1,simtime);
    data.co2storelevel = zeros(1,simtime);
    data.n2storelevel = zeros(1,simtime);
    data.h2storelevel = zeros(1,simtime);
    data.ch4storelevel = zeros(1,simtime);

    data.potablewaterstorelevel = zeros(1,simtime);
    data.dirtywaterstorelevel = zeros(1,simtime);
    data.greywaterstorelevel = zeros(1,simtime);
    data.drywastestorelevel = zeros(1,simtime);
    data.carriedfoodstorelevel = zeros(1,simtime);
    data.grownfoodstorelevel = zeros(1,simtime);
    data.dryfoodlevel = zeros(1,simtime);
    data.caloriccontent = zeros(1,simtime);
    data.biomassstorelevel = zeros(1,simtime);
    data.cropwaterstorelevel = zeros(1,simtime);
    data.powerlevel = zeros(1,simtime);
    data.metoxregenstore = zeros(1,simtime);
    data.dumpedEVAdirtywater = zeros(1,simtime);
    data.plssfeedwatertanklevel = zeros(1,simtime);
    data.plsso2tanklevel = zeros(1,simtime);
    data.reservoirFillLevel = zeros(1,simtime);

    data.SuitlockPressure = zeros(1,simtime);
    data.SuitlockO2level = zeros(1,simtime);
    data.SuitlockCO2level = zeros(1,simtime);
    data.SuitlockN2level = zeros(1,simtime);
    data.SuitlockVaporlevel = zeros(1,simtime);
    data.SuitlockOtherlevel = zeros(1,simtime);
    data.SuitlockTotalMoles = zeros(1,simtime);

    data.PowerProduced = zeros(1,simtime);

    data.ogsoutput = zeros(1,simtime);

    % Architecture 1
    data.FSHPCAaction = zeros(4,simtime+1);
    % Architecture 2
    data.HMPPCAaction = zeros(4,simtime+1);
    % Architecture 3
    data.LabPCAaction = zeros(4,simtime+1);
    data.LoftPCAaction = zeros(4,simtime+1);
    data.PCMPCAaction = zeros(4,simtime+1);
    data.SuitlockPCAaction = zeros(4,simtime+1);
    data.PLMPPRVaction = zeros(4,simtime+1);

    data.FSHCCAA = zeros(1,simtime);
    data.LabCCAAoutput = zeros(1,simtime);
    data.LoftCCAAoutput = zeros(1,simtime);
    data.PCMCCAAoutput = zeros(1,simtime);
    data.SuitlockCCAAoutput = zeros(1,simtime);


    data.crsH2OProduced = zeros(1,simtime);
    data.crsCompressorOperation = zeros(2,simtime);
    data.co2accumulatorlevel = zeros(1,simtime);
    data.co2removed = zeros(1,simtime);

    data.suitlockGasVented = zeros(1,simtime);

    data.hoursOnEVA = zeros(1,simtime);     % Flag to indicate whether or not the Airlock should be depressurized
    data.currentEVAcrew = zeros(1,4);    % Current crewpersons on EVA

%     h = waitbar(0,'Please wait...');

    timeUntilDepletion = struct('o2storelevel',zeros(1,simtime),...
        'n2storelevel',zeros(1,simtime),'h2storelevel',...
        zeros(1,simtime),'ch4storelevel',zeros(1,simtime),...
        'potablewaterstorelevel',zeros(1,simtime),'dirtywaterstorelevel',...
        zeros(1,simtime),'greywaterstorelevel',zeros(1,simtime),...
        'carriedfoodstorelevel',zeros(1,simtime),'powerlevel',zeros(1,simtime),...
        'SuitlockPressure',zeros(1,simtime),'SuitlockO2level',zeros(1,simtime));

    toc

    %% Time Loop

    tic

    timestamp = datestr(clock);
    timestamp(timestamp==':') = '-';
    % Start recording command window
    % diary(['HabNet Log ',timestamp,'.txt'])
    disp(['Simulation Run Started: ',datestr(clock), ' On iteration: ', num2str(i)]);
%     disp('Baseline Simulation Run - With Lettuce & All ISRU')

    for i = 1:simtime
    %     disp(['simtime step i: ', num2str(i)])
        if checkCrewFoodAlive(numberOfCrew, crew,LettuceShelf)

    %             sum([WhitePotatoShelves.Shelves.hasDied]) >= 1 ||...
    %             sum([PeanutShelves.Shelves.hasDied]) >= 1 || ...
    %             sum([SoybeanShelves.Shelves.hasDied]) >= 1 || ...
    %             sum([SweetPotatoShelves.Shelves.hasDied]) >= 1 || ...
    %             sum([WheatShelves.Shelves.hasDied]) >= 1

            % Remove all trailing zeros from recorded data vectors
            data.o2storelevel = data.o2storelevel(1:(i-1));
            data.co2storelevel = data.co2storelevel(1:(i-1));
            data.n2storelevel = data.n2storelevel(1:(i-1));
            data.h2storelevel = data.h2storelevel(1:(i-1));
            data.ch4storelevel = data.ch4storelevel(1:(i-1));
            data.potablewaterstorelevel = data.potablewaterstorelevel(1:(i-1));
            data.dirtywaterstorelevel = data.dirtywaterstorelevel(1:(i-1));
            data.greywaterstorelevel = data.greywaterstorelevel(1:(i-1));
            data.drywastestorelevel = data.drywastestorelevel(1:(i-1));
            data.carriedfoodstorelevel = data.carriedfoodstorelevel(1:(i-1));
            data.cropwaterstorelevel = data.cropwaterstorelevel(1:(i-1));
            data.powerlevel = data.powerlevel(1:(i-1));
            if strcmpi(EMUco2RemovalTechnology,'METOX')
                data.metoxregenstore = data.metoxregenstore(1:(i-1));
            end

            if strcmpi(EMUurineManagementTechnology,'MAG')
                data.dumpedEVAdirtywater = data.dumpedEVAdirtywater(1:(i-1));
            end
            data.plssfeedwatertanklevel = data.plssfeedwatertanklevel(1:(i-1));
            data.plsso2tanklevel = data.plsso2tanklevel(1:(i-1));

            data.hoursOnEVA = data.hoursOnEVA(1:(i-1));


            % Record Airlock Atmosphere
            data.SuitlockPressure = data.SuitlockPressure(1:(i-1));
            data.SuitlockO2level = data.SuitlockO2level(1:(i-1));
            data.SuitlockCO2level = data.SuitlockCO2level(1:(i-1));
            data.SuitlockN2level = data.SuitlockN2level(1:(i-1));
            data.SuitlockVaporlevel = data.SuitlockVaporlevel(1:(i-1));
            data.SuitlockOtherlevel = data.SuitlockOtherlevel(1:(i-1));
            data.SuitlockTotalMoles = data.SuitlockTotalMoles(1:(i-1));  

            % OGS Production and Consumption
            data.ogsoutput = data.ogsoutput(1:(i-1));

            % Power Production and Consumption
            data.PowerProduced = data.PowerProduced(:,1:(i-1));

            % Common Cabin Air Assemblies
            data.FSHCCAAoutput = data.FSHCCAAoutput(1:(i-1));
            data.LabCCAAoutput = data.LabCCAAoutput(1:(i-1));
            data.LoftCCAAoutput = data.LoftCCAAoutput(1:(i-1));
            data.PCMCCAAoutput = data.PCMCCAAoutput(1:(i-1));
            data.SuitlockCCAAoutput = data.SuitlockCCAAoutput(1:(i-1));

            % Common Cabin Air Assemblies THEN Pressure Control Assemblies per
            % Architecture
            switch(architecture)
                case 1 
                    data.FSHCCAAoutput = data.FSHCCAAoutput(1:(i-1));
                    data.SuitlockCCAAoutput = data.SuitlockCCAAoutput(1:(i-1));
                    data.FSHPCAaction = data.FSHPCAaction(:,1:(i-1));
                    data.SuitlockPCAaction = data.SuitlockPCAaction(:,1:(i-1)); % suitlock still needs ticking
                case 2 
                    data.FSHCCAAoutput = data.FSHCCAAoutput(1:(i-1));
                    data.SuitlockCCAAoutput = data.SuitlockCCAAoutput(1:(i-1));
                    data.FSHPCAaction = data.FSHPCAaction(:,1:(i-1));
                    data.HMPPCAaction = data.HMPPCAaction(:,1:(i-1));
                    data.SuitlockPCAaction = data.SuitlockPCAaction(:,1:(i-1));
                case 3 
                    data.LabCCAAoutput = data.LabCCAAoutput(1:(i-1));
                    data.LoftCCAAoutput = data.LoftCCAAoutput(1:(i-1));
                    data.PCMCCAAoutput = data.PCMCCAAoutput(1:(i-1));
                    data.SuitlockCCAAoutput = data.SuitlockCCAAoutput(1:(i-1));

                    data.LabPCAaction = data.LabPCAaction(:,1:(i-1));
                    data.LoftPCAaction = data.LoftPCAaction(:,1:(i-1));
                    data.PCMPCAaction = data.PCMPCAaction(:,1:(i-1));
                    data.SuitlockPCAaction = data.SuitlockPCAaction(:,1:(i-1));
                    data.PLMPPRVaction = data.PLMPPRVaction(:,1:(i-1));
            end



            % Run Waste Processing ECLSS Hardware
            data.co2removed = data.co2removed(1:(i-1));
            data.crsH2OProduced = data.crsH2OProduced(1:(i-1));
            data.co2accumulatorlevel = data.co2accumulatorlevel(1:(i-1));

            data.suitlockGasVented = data.suitlockGasVented(1:(i-1));

            t = 1:(length(data.o2storelevel));

            toc

            % Record and save command window display
            disp(['Simulation Run Ended: ',datestr(clock)]);
            diary off

            close(h)
            return
        end

        %% Invoke Fail
        if i == FailureTick
            for ii = 1:length(FailCommand)
                eval(FailCommand{ii});
                disp(['Failure invoked in ',ErrorList{SystemToFail(ii)},' at tick ',num2str(i)])
            end
        end

        %% Record Data
        % Resource Stores
        data.o2storelevel(i) = O2Store.currentLevel;
        data.co2storelevel(i) = CO2Store.currentLevel;
        data.n2storelevel(i) = N2Store.currentLevel;
        data.h2storelevel(i) = H2Store.currentLevel;
        data.ch4storelevel(i) = MethaneStore.currentLevel;
        data.potablewaterstorelevel(i) = PotableWaterStore.currentLevel;
        data.dirtywaterstorelevel(i) = DirtyWaterStore.currentLevel;
        data.greywaterstorelevel(i) = GreyWaterStore.currentLevel;
        data.drywastestorelevel(i) = DryWasteStore.currentLevel;
        data.biomassstorelevel(i) = BiomassStore.currentLevel;
        data.powerlevel(i) = MainPowerStore.currentLevel;
        if strcmpi(EMUco2RemovalTechnology,'METOX')
            data.metoxregenstore(i) = METOXregeneratorLoad.currentLevel;
        end

        if strcmpi(EMUurineManagementTechnology,'MAG')
            data.dumpedEVAdirtywater(i) = EMUmetabolicWaste.currentLevel;
        end

        % Record PLSS Tanks
        data.plssfeedwatertanklevel(i) = EMUfeedwaterReservoir.currentLevel;
        data.plsso2tanklevel(i) = EMUo2Tanks.currentLevel;

        % Record Suitlock Atmosphere
        data.SuitlockPressure(i) = Suitlock.pressure;
        data.SuitlockO2level(i) = Suitlock.O2Store.currentLevel;
        data.SuitlockCO2level(i) = Suitlock.CO2Store.currentLevel;
        data.SuitlockN2level(i) = Suitlock.NitrogenStore.currentLevel;
        data.SuitlockVaporlevel(i) = Suitlock.VaporStore.currentLevel;
        data.SuitlockOtherlevel(i) = Suitlock.OtherStore.currentLevel;
        data.SuitlockTotalMoles(i) = Suitlock.totalMoles;


        %% Tick Modules
        % Leak Modules
        % Run Fans
        % Equalize Pressures Across Modules (always put this line directly
        % after fan ticks)
        switch(architecture)
            case 1 
                FSH.tick;
                Suitlock.tick;

                FSH2AirlockFan.tick;

                PressureFlow1.tick;
            case 2 
                FSH.tick;
                HMP.tick;
                Suitlock.tick;

                FSH2AirlockFan.tick;
                FSH2HMPFan.tick;

                PressureFlow2.tick;
            case 3 
                Lab.tick;
                Loft.tick;
                PCM.tick;
                PLM.tick;

                Suitlock.tick;

                Lab2PCMFan.tick;
                PLM2PCMFan.tick;
                Loft2PCMFan.tick;
                Lab2AirlockFan.tick;

                PressureFlow3.tick;
        end

        % Run Power Supply
        data.PowerProduced(i) = powerPS.tick; 


        % Run ISRU Power Beamed
        isruPower.tick;

        % Run mission payload
        missionPayload.tick;

        % Run ECLSS Hardware       
        data.ogsoutput(i) = ogs.tick;

        % Tick ORA
    %     inflatableO2extracted(i) = inflatableORA.tick;
        % Pressure Control Assemblies THEN Common Cabin Air Assemblies
        % Needs to be per architecture (PCA and CCAA)
        switch(architecture)
            case 1 
                data.FSHPCAaction(:,i+1) = FSHPCA.tick(data.FSHPCAaction(:,i));
                data.SuitlockPCAaction(:,i+1) = SuitlockPCA.tick(data.SuitlockPCAaction(:,i));

                data.FSHCCAAoutput(i) = FSHCCAA.tick;
                data.SuitlockCCAAoutput(i) = SuitlockCCAA.tick;
            case 2 
                data.FSHPCAaction(:,i+1) = FSHPCA.tick(data.FSHPCAaction(:,i));
                data.HMPPCAaction(:,i+1) = HMPPCA.tick(data.HMPPCAaction(:,i));
                data.SuitlockPCAaction(:,i+1) = SuitlockPCA.tick(data.SuitlockPCAaction(:,i));

                data.FSHCCAAoutput(i) = FSHCCAA.tick;
                data.SuitlockCCAAoutput(i) = SuitlockCCAA.tick;
            case 3 
                data.LabPCAaction(:,i+1) = LabPCA.tick(data.LabPCAaction(:,i));
                data.LoftPCAaction(:,i+1) = LoftPCA.tick(data.LoftPCAaction(:,i));
                data.PCMPCAaction(:,i+1) = PCMPCA.tick(data.PCMPCAaction(:,i));
                data.SuitlockPCAaction(:,i+1) = SuitlockPCA.tick(data.SuitlockPCAaction(:,i));
                data.PLMPPRVaction(:,i+1) = PLMPPRV.tick(data.PLMPPRVaction(:,i));

                data.LabCCAAoutput(i) = LabCCAA.tick;
                data.LoftCCAAoutput(i) = LoftCCAA.tick;
                data.PCMCCAAoutput(i) = PCMCCAA.tick;
                data.SuitlockCCAAoutput(i) = SuitlockCCAA.tick;
        end

        % Run Waste Processing ECLSS Hardware
        data.co2removed(i) = mainvccr.tick;
        data.crsH2OProduced(i) = crs.tick;
        data.crsCompressorOperation(:,i) = crs.CompressorOperation;
        data.co2accumulatorlevel(i) = crs.CO2Accumulator.currentLevel;
        waterRS.tick;

        %% Food Production System
        data.cropwaterstorelevel(i) = CropWaterStore.currentLevel;

        if CropWaterStore.currentLevel <= 0
            disp(['Crop Water Store is empty at tick: ',num2str(i)])
            break
        end



        LettuceShelf.tick;

        FoodProcessor.tick;
        data.carriedfoodstorelevel(i) = CarriedFoodStore.currentLevel;
        data.grownfoodstorelevel(i) = LocallyGrownFoodStore.currentLevel;
        if LocallyGrownFoodStore.currentLevel > 0       
            data.dryfoodlevel(i) = sum(cell2mat({LocallyGrownFoodStore.foodItems.Mass})-cell2mat({LocallyGrownFoodStore.foodItems.WaterContent}));
            data.caloriccontent(i) = sum([LocallyGrownFoodStore.foodItems.CaloricContent]);
        end   

        %% Tick Crew, and check if on EVA
        if length(fieldnames(crew))~=4
            astro1.tick;
            astro2.tick;
            CrewEVAstatus = [strcmpi(astro1.CurrentActivity.Name,'EVA'),...
            strcmpi(astro2.CurrentActivity.Name,'EVA')];
        else
            astro1.tick;
            astro2.tick;  
            astro3.tick;
            astro4.tick;
            CrewEVAstatus = [strcmpi(astro1.CurrentActivity.Name,'EVA'),...
            strcmpi(astro2.CurrentActivity.Name,'EVA'),...
            strcmpi(astro3.CurrentActivity.Name,'EVA'),...
            strcmpi(astro4.CurrentActivity.Name,'EVA')];
        end
        %% Run ISRU
        if mod(i,floor(deliveryInterval))==0
            PotableWaterStore.add(isruAddedWater*deliveryInterval);
            CropWaterStore.add(isruAddedCropWater*deliveryInterval);
        end

        
        O2Store.add(isruAddedO2);
        N2Store.add(isruAddedN2);

        %% EVA

        % Regenerate METOX canisters if required
        % Add CO2 removed from METOX canister to Airlock
        if strcmpi(EMUco2RemovalTechnology,'METOX')
            Suitlock.CO2Store.add(METOXregeneratorLoad.take(metoxCO2regenRate));
        end

        % if any astro has a current activity that is EVA
        if sum(CrewEVAstatus) > 0
            % identify first crewmember
            data.hoursOnEVA(i) = data.hoursOnEVA(i-1)+1;
            if data.hoursOnEVA(i) == 1
                % Store EVA status
                data.currentEVAcrew = CrewEVAstatus;

                % Error
                if O2Store.currentLevel < prebreatheO2
                    disp(['Insufficient O2 for crew EVA prebreathe or EMU suit fill at tick: ',num2str(i)])
                    disp('Current EVA has been skipped')
                    % Advance activities for all astronauts
                    astro1.skipActivity;
                    astro2.skipActivity;
                    if length(fieldnames(crew))==4
                        astro3.skipActivity;
                        astro4.skipActivity;
                    end
                    continue
                end

                % perform airlock ops
                % purge and fill EVA suits with O2 from O2Store 
                EVAsuitfill = EVAenvironment.O2Store.add(O2Store.take(prebreatheO2));              % Fill two EMUs with 100% O2
                data.reservoirFillLevel(i) = EMUfeedwaterReservoir.fill(PotableWaterStore);                                      % fill feedwater tanks
                EMUo2Tanks.fill(O2Store);                                                           % fill PLSS O2 tanks

                % Vent lost airlock gases
                suitlockCycleLoss = Suitlock.pressure*suitlockAirLossVolume/(idealGasConstant*(273.15+Suitlock.temperature));    % Suitlock losses are a function of pressure
                data.suitlockGasVented(i) = Suitlock.vent(suitlockCycleLoss);

            elseif data.hoursOnEVA(i) == 8      % end of EVA
                % Empty EMU and add residual gases within EMU to Airlock
                EVAenvironment.O2Store.currentLevel = 0;
                EVAenvironment.CO2Store.currentLevel = 0;
                EVAenvironment.VaporStore.currentLevel = 0;

                Suitlock.O2Store.add(finalEMUo2level);
                Suitlock.CO2Store.add(finalEMUco2level);
                Suitlock.VaporStore.add(finalEMUvaporlevel);

                % Define PLSS Store levels
                EMUfeedwaterReservoir.currentLevel = finalFeedwaterTanklevel;
                EMUo2Tanks.currentLevel = plssO2TankLevel;       

                % For METOX case, add PLSS removed CO2 back to Airlock 
                % (equivalent to METOX oven baking) 
                if strcmpi(EMUco2RemovalTechnology,'METOX')
                    METOXregeneratorLoad.add(totalCO2removed);
                end

                % For humidity condensate: for RCA, the loss is captured in 
                % finalEMUvaporlevel, while for the METOX, all humidity
                % condensate is sitting within the feedwater tank
            end
        end
        % If the crew is no longer on EVA, reset hoursOnEVA
        if ~isequal(CrewEVAstatus,data.currentEVAcrew)
            % if identified crewmember's current activity is not EVA
            data.hoursOnEVA(i) = 0;

            % Run Suitlock PCA
    %         SuitlockPCAaction(:,i+1) = SuitlockPCA.tick(SuitlockPCAaction(:,i));

            % Run Suitlock CCAA
    %         SuitlockCCAAoutput(i) = SuitlockCCAA.tick;
        end

        %% Tick Waitbar
%         if mod(i,100) == 0
%             waitbar(i/simtime,h,['Current tick: ',num2str(i),' | Time Elapsed: ',num2str(round(toc)),'sec']);
%         end

    %     value(i) = hoursOnEVA;
    end
    toc

    beep

%     close(h)

    diary off

    % save('HDUBaseline')

    %% Random plot commands used in code validation exercise
%     figure, plot(1:length(data.powerlevel),data.powerlevel),title('Battery Storage level [Whr] *10^4'), grid on
%     figure, plot(1:length(data.potablewaterstorelevel),data.potablewaterstorelevel), title('Potable Water store level [L]'), grid on
%     figure, plot(1:length(data.dirtywaterstorelevel),data.dirtywaterstorelevel), title('Dirty Water store level [L]'), grid on
%     figure, plot(1:length(data.greywaterstorelevel),data.greywaterstorelevel), title('Grey Water store level [L]'), grid on
%     figure, plot(1:length(data.o2storelevel),data.o2storelevel), title('O2 store level [L]'), grid on
%     figure, plot(1:length(data.co2storelevel),data.co2storelevel), title('CO2 store level [L]'), grid on
%     figure, plot(1:length(data.h2storelevel),data.h2storelevel), title('H2 store level [L]'), grid on
%     figure, plot(1:length(data.n2storelevel),data.n2storelevel), title('N2 store level [L]'), grid on
%     figure, plot(1:length(data.ch4storelevel),data.ch4storelevel), title('CH4 store level [L]'), grid on
%     figure, plot(1:length(data.drywastestorelevel),data.drywastestorelevel), title('dry waste store level [L]'), grid on
%     figure, plot(1:length(data.cropwaterstorelevel),data.cropwaterstorelevel), title('crop water store level [L]'), grid on
%     figure, plot(1:length(data.carriedfoodstorelevel),data.carriedfoodstorelevel), title('carried food store level [L]'), grid on
%     data.drywastestorelevel = data.drywastestorelevel(1:(i-1));
%     data.carriedfoodstorelevel = data.carriedfoodstorelevel(1:(i-1));
%     data.cropwaterstorelevel = data.cropwaterstorelevel(1:(i-1));
%     % figure, plot(1:length(data.plssfeedwatertanklevel),data.plssfeedwatertanklevel), title('plss feedwater tank level [L]'), grid on
%     totalWaterStoreLevel = data.potablewaterstorelevel+data.dirtywaterstorelevel+data.greywaterstorelevel+data.plssfeedwatertanklevel;
%     figure, plot(1:length(totalWaterStoreLevel),totalWaterStoreLevel), title('Total Water store level [L]'), grid on
    % figure, plot(1:length(data.PowerProduced),data.PowerProduced), grid on

    % figure, plot(1:length(co2storelevel),co2storelevel, title('MATLAB CO_2 Store')), grid on
    % figure, plot(1:(i-1),CO2Storelevel(1:(i-1)),'LineWidth',2), title('MATLAB CO_2 Store'), grid on
    % figure, plot(1:length(intensity),intensity)
    % data.powerlevel;
    powerdiff = zeros(1, length(data.powerlevel));
    simtimeDepletionIndex = simtime-3;
    timeUntilDepletion = EnvironmentalAnalyzer(data,timeUntilDepletion,simtimeDepletionIndex);
    depletionMetrics = [timeUntilDepletion.potablewaterstorelevel(simtimeDepletionIndex), timeUntilDepletion.powerlevel(simtimeDepletionIndex)];
    for i = 1:length(depletionMetrics) % if NaN convert to Inf so RSM can fit properly
        if isnan(depletionMetrics(i))
            depletionMetrics(i) = inf;
        end
    end

    %% Print Input Parameters:
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
    inputMetrics = [initialWaterLevel, totHabVolume, architecture, deliveryInterval];
    %% Print Final Output Metrics:
%     disp(["OUTPUT: The time until depletion for water in hours: ", depletionMetrics(1)]);
%     disp(["OUTPUT: The final amount of water at end of mission in L: ", data.potablewaterstorelevel(simtimeDepletionIndex)]);
%     disp(["OUTPUT: The time until depletion for power in hours: ", depletionMetrics(2)]); % usually NaN
%     disp(["OUTPUT: The Battery Size in Whr was: ", batteryCapacity]);
%     disp(["OUTPUT: The Solar Panel Size in kWhr was: ", solarPanelSize]);
%     disp(["OUTPUT: The ISRU power Reqired was: ", isruPwrReq]);
%     disp(["OUTPUT: The ISRU production mass (Battery+SolarPanels+isruProd+Hoppers mass) [kg] is: ", isruProdMass]);
%     disp(["OUTPUT: The mass of earth delivered water landers (landed mass) in kg is: ", num2str(massAllEarthLanders)]);
    outputMetrics = [depletionMetrics(1), data.potablewaterstorelevel(simtimeDepletionIndex), depletionMetrics(2), batteryCapacity, solarPanelSize, isruPwrReq, isruProdMass, massAllEarthLanders];
    

    %% Helper DOE functions
    function allAlive = checkCrewFoodAlive(numCrew, crew, LettuceShelf)
        if numCrew ~= 4
            if crew.astro1.alive == 0 || crew.astro2.alive == 0 || LettuceShelf.hasDied >= 1
                allAlive = true;
            else
                allAlive = false;
            end
        else
            if crew.astro1.alive == 0 || crew.astro2.alive == 0 || crew.astro3.alive == 0 || crew.astro4.alive == 0 ||...
                LettuceShelf.hasDied >= 1
                allAlive = true;
            else
                allAlive = false;
            end
        end
    end
    %% End helper functions
end