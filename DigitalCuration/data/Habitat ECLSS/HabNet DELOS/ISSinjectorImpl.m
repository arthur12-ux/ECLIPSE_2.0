classdef ISSinjectorImpl < handle
    %ISSinjectorImpl Summary of this class goes here
    %   By: Sydney Do (sydneydo@mit.edu)
    %   Date Created: 8/5/2014
    %   Last Updated: 8/5/2014
    %   This is the same implementation as that of the AccumulatorImpl
    %   In BioSim, both InjectorImpl and AccumulatorImpl reference a parent
    %   class called ResourceMover
    %   Comments within the InjectorImpl class code provide the following
    %   description:
    %   * The basic Accumulator Implementation. Can be configured to take any modules
    %   * as input, and any modules as output. It takes as much as it can (max taken
    %   * set by maxFlowRates) from one module and pushes it into another module.
    %   * Functionally equivalent to an Accumulator at this point.
    
    %   File modified from BioSim injector class on 8/5/2014
    
    %   The PCA vents air, rather than individual atmospheric constituents
    %   As a result, we model this class as a PCA, rather than an injector
    
    %   This code focuses on maintaining O2 partial pressure and total
    %   pressure
    %   We adjust O2 partial pressure first, then total pressure
    
    %% NOTE:
    % We compose this file to act as either an ISS Pressure Control
    % Assembly (PCA) (allows input of gases as well as venting of gases),
    % or a Positive Pressure Relief Valve (PPRV), which allows for only the
    % passive venting of gases. The manner in which this code operates is
    % dictated by the "PCAmode" input
    
    properties
        OperatingMode = 'PCA'     % Mode that the object will act in. PCA mode is the default mode that we set the code to.
        TargetTotalPressure      % Target absolute pressure to be maintained within cabin
        TargetO2PartialPressure        % Target O2 partial pressure for PCA (in kPa)
        TargetO2MolarFraction         % Target O2 molar fraction
        O2Vented = 0            % Total amount of O2 vented (in moles)
        CO2Vented = 0           % Total amount of CO2 vented (in moles)
        N2Vented = 0            % Total amount of N2 vented (in moles)
        VaporVented = 0         % Total amount of Water Vapor vented (in moles)
        OtherGasesVented = 0    % Total amount of Other Gases vented (in moles)
        O2Source    % Source of O2 Make Up Gas
        N2Source    % Source of N2 Make Up Gas
        Environment  % Environment whose atmosphere is being monitored and controlled
        Error = 0;      % Error flag (error sources include insufficient gases in stores and insufficient power
        PerformanceDegradation = 0 % Amount of degradation resulting from error (0 = no degradation; 1 = not functioning)
        KnownDegradation = 0    % Indicates the degradation recognized by the crew/ALSS - for use in faultDetection.m
        NumDegradedRuns = 0    % Number of times that the system performance has been compromised by the degradation - for use in faultDetection.m
        UpperPPO2PercentageLimit = 0.3;     % PPO2 can reach 30% (flammability limit) for 70.3kPa/26.5% O2 atmospheres (REF: Section 5.1 EAWG)
    end
    
    properties (SetAccess = private)
        PartialPressureBoundingBox = 1.37895146     % in kPa (converted from 0.2psia), extent of control box around which pressure is controled (REF: Section 5.1 EAWG)
        VentPortDiameter = 0.056         % in meters (vent port diameter of Vent Relief Valve of the ISS PCA, REF: pg 89, Living Together in Space)
        MoonMeanAtmPressure = 3.08*10^(-13)   % in kPa, Mean atmospheric pressure at Moon surface (REF: https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html)
        MoonMeanAtmDensity = 2.9916e-18       % in kg/m^3, Mean atmospheric density at Moon surface (REF: https://www.space.com/18067-moon-atmosphere.html#:~:text=In%20the%20moon's%20atmosphere%2C%20there,as%20a%20loaded%20dump%20truck)
        idealGasConstant = 8.314;        % J/K/mol
        O2molarMass = 2*15.999;          % g/mol
        CO2molarMass = 12.011+2*15.999;   % g/mol
        N2molarMass = 2*14.007;          % g/mol
        VapormolarMass = 2*1.008+15.999; % g/mol
        OthermolarMass =  0.265*2*15.999 + (1-0.265)*2*14.007;	% g/mol (assuming that it is equal to the average molecular mass of the ideal 70.3kPa/26.5% O2 mixture
    end
    
    
    methods
        %% Constructor
        function obj = ISSinjectorImpl(targetTotalPressure,targetO2molarFraction,O2source,N2source,environment,PCAmode)
            
            if nargin > 0
                if ~(strcmpi(class(O2source),'StoreImpl') || strcmpi(class(N2source),'StoreImpl'))
                    error('Third and Fourth Input arguments must be of type "StoreImpl"')
                end
                
                obj.TargetTotalPressure = targetTotalPressure;
                obj.TargetO2MolarFraction = targetO2molarFraction;
                obj.TargetO2PartialPressure = targetO2molarFraction*targetTotalPressure;
                
                limitingFlowRateInKg = 0.09*60;     % Limiting Flow Rate of ISS Pressure Control Assembly is 0.09kg/min (REF: pg 92, Living Together in Space)
                
                %                 O2molarmass = 2*15.999;
                %                 N2molarmass = 2*14.007;
                
                O2limitingFlowRateInMoles = limitingFlowRateInKg*1E3/obj.O2molarMass;
                N2limitingFlowRateInMoles = limitingFlowRateInKg*1E3/obj.N2molarMass;
                
                obj.O2Source = ResourceUseDefinitionImpl(O2source,O2limitingFlowRateInMoles,O2limitingFlowRateInMoles);
                obj.N2Source = ResourceUseDefinitionImpl(N2source,N2limitingFlowRateInMoles,N2limitingFlowRateInMoles);
                %                 obj.Environment = ResourceUseDefinitionImpl(environment,limitingFlowRateInMoles,limitingFlowRateInMoles);
                obj.Environment = environment;
                
                if nargin == 6
                    if ~(strcmpi(PCAmode,'PPRV') || strcmpi(PCAmode,'PCA') || strcmpi(PCAmode,'EMU'))
                        error('Input for the operating mode must be either "PCA", "PPRV", or "EMU"')
                    end
                    
                    obj.OperatingMode = PCAmode;
                end
                
            end
        end
        
        %% Set O2 molar fraction limit 
        function set.UpperPPO2PercentageLimit(obj,inputO2fractionlimit)
            obj.UpperPPO2PercentageLimit = inputO2fractionlimit;
        end
        
        %% tick
        function [action,molesVentedOrInjected] = tick(obj,previousAction,operationLevel)
            % if PerformanceDegradation = 0, then NumDegradedRuns and KnownDegradation should be
            % reset to 0, this is needed once a degradation has been fixed
            if obj.PerformanceDegradation == 0
                obj.NumDegradedRuns = 0;
                obj.KnownDegradation = 0;
            end
            
            % Need to build memory of previous timestep to allow for consecutive
            % actions to be performed to bring the atmospheric conditions back to a
            % desired state - we introduce the variable previousAction to account for
            % this - this is a 4x1 column vector, carrying the same information as the
            % "action" variable, but taken from the previous timestep
            
            % Variable tracking actions taken
            action = zeros(4,1);
            molesVentedOrInjected = 0;
            if obj.PerformanceDegradation == 1
                obj.Error = 1;
            end
            %% Implement power consumption for each if statement!
            
            %% Nominal PCA checks
                            
                switch obj.OperatingMode
                    
                    case 'PCA'
%                         if obj.Error == 0
                        % Only run if there is no system error

                        % Case for if injector is commanded to operate in
                        % PCA mode (i.e. we can both vent and introduce gases into the habitat)
                        
                        %% Check for O2 Flammability Limit
                        % If ppO2 is above flammability limit, add N2 to bring ppO2
                        % to target value (since we can't selectively vent O2)
                        % Modified 11/2019 to take in optional commanded
                        % production setting input
                        if (obj.Environment.O2Percentage > obj.UpperPPO2PercentageLimit) || (previousAction(1) == 1) || nargin == 3 && operationLevel(1) ~= 0 % if currentPPO2 is > upper bound of ppO2 bounding box, vent gas
                            if nargin == 3
                                n2MolesToIntroduce = operationLevel(1)*obj.N2Source.MaxFlowRate; % Total N2 moles commanded to be introduced
                            else
                                n2MolesToIntroduce = obj.Environment.O2Store.currentLevel/obj.TargetO2MolarFraction - obj.Environment.totalMoles; % Total N2 moles needed to be introduced to bring O2 molar percentage to desired value
                            end
                            % Modified 09/2019 to account for variable
                            % degradations  by limiting the O2 flow
                            % rate
                            makeupN2taken = obj.N2Source.ResourceStore.take(min(n2MolesToIntroduce,(1-obj.PerformanceDegradation)*obj.N2Source.MaxFlowRate),obj.N2Source);     % Take required makeup N2 amount from N2 Source
                            % if the degradation limited performance, then
                            % increment NumDegradedRuns
                            if obj.PerformanceDegradation > 0 && find([n2MolesToIntroduce,(1-obj.PerformanceDegradation)*obj.N2Source.MaxFlowRate] == min(n2MolesToIntroduce,(1-obj.PerformanceDegradation)*obj.N2Source.MaxFlowRate)) == 2
                                obj.NumDegradedRuns = obj.NumDegradedRuns + 1;
                            end
                            
                            if makeupN2taken < n2MolesToIntroduce
                                disp(['Insufficient N2 available to perform pressure control action at tick ',num2str(obj.Environment.tickcount),'. ',num2str(obj.Environment.name),' is in a high O2% condition'])
                                obj.Error = 1;
                                return
                            end
                            
                            obj.Environment.NitrogenStore.add(makeupN2taken);         % add take makeup N2 to environment
                            molesVentedOrInjected = makeupN2taken;
                            action(1) = 1;      % Record action taken
                            
                        end
                        
                        %% Check for overpressure
                        % Vent if total pressure is greater than target pressure +
                        % bounding box
                        % Modified 11/2019 to take in optional commanded
                        % production setting input
                        if obj.Environment.pressure > (obj.TargetTotalPressure + obj.PartialPressureBoundingBox) || nargin == 3 && operationLevel(2) ~= 0 
                            currentTargetTotalMoles = obj.TargetTotalPressure * obj.Environment.volume / (obj.idealGasConstant*(obj.Environment.temperature+273.15));   % No. of moles corresopnding to target absolute pressure
                            airToVent = obj.Environment.totalMoles - currentTargetTotalMoles;
                            
                            % Calculate current maximum vent rate based on pressure
                            % difference between cabin and Martian environment
                            currentAverageDensity = (obj.Environment.O2Store.currentLevel*obj.O2molarMass + obj.Environment.CO2Store.currentLevel*obj.CO2molarMass...
                                + obj.Environment.NitrogenStore.currentLevel*obj.N2molarMass + obj.Environment.VaporStore.currentLevel*obj.VapormolarMass...
                                + obj.Environment.OtherStore.currentLevel*obj.OthermolarMass) / obj.Environment.volume;        % Density in g/L = kg/m^3
                            
                            currentMaxVentRate = sqrt(2*(obj.Environment.pressure - obj.MoonMeanAtmPressure)*1E3/currentAverageDensity);    % in meters per second (m/s)
                            currentVolumetricFlowRate = currentMaxVentRate*pi*obj.VentPortDiameter^2/4*3600;      % in m^3/hr (hence the *3600 factor)
                            maxVentRate = obj.Environment.pressure*currentVolumetricFlowRate*1E3/(obj.idealGasConstant*(obj.Environment.temperature+273.15));       % maximum venting rate in moles/hr
                            
                            if nargin == 3
                                finalAmountVented = min(operationLevel(2)*maxVentRate,maxVentRate*(1-obj.PerformanceDegradation));
                                % if the degradation limited performance, then
                                % increment NumDegradedRuns
                                if obj.PerformanceDegradation > 0 && find([operationLevel(2)*maxVentRate,finalAmountVented] == min([operationLevel(2)*maxVentRate,finalAmountVented])) == 2
                                    obj.NumDegradedRuns = obj.NumDegradedRuns + 1;
                                end
                            else
                                % Modified 09/2019 to account for variable
                                % degradations by limiting the vent port area
                                finalAmountVented = min([airToVent,maxVentRate*(1-obj.PerformanceDegradation)]);   % Final amount that can be vented is the minimum of the maximum possible vent rate, and the desired amount of air to vent
                                % if the degradation limited performance, then
                                % increment NumDegradedRuns
                                if obj.PerformanceDegradation > 0 && find([airToVent,finalAmountVented] == min([airToVent,finalAmountVented])) == 2
                                    obj.NumDegradedRuns = obj.NumDegradedRuns + 1;
                                end
                            end

                            currentO2percentage = obj.Environment.O2Percentage;
                            currentCO2percentage = obj.Environment.CO2Percentage;
                            currentN2percentage = obj.Environment.N2Percentage;
                            currentVaporpercentage = obj.Environment.VaporPercentage;
                            currentOtherpercentage = obj.Environment.OtherPercentage;
                            
                            % Take corresponding airToVent from Environment atmosphere
                            O2ToVent = obj.Environment.O2Store.take(currentO2percentage*finalAmountVented);
                            CO2ToVent = obj.Environment.CO2Store.take(currentCO2percentage*finalAmountVented);
                            N2ToVent = obj.Environment.NitrogenStore.take(currentN2percentage*finalAmountVented);
                            VaporToVent = obj.Environment.VaporStore.take(currentVaporpercentage*finalAmountVented);
                            OtherToVent = obj.Environment.OtherStore.take(currentOtherpercentage*finalAmountVented);
                            
                            % Update object properties
                            obj.O2Vented = obj.O2Vented + O2ToVent;
                            obj.CO2Vented = obj.CO2Vented + CO2ToVent;
                            obj.N2Vented = obj.N2Vented + N2ToVent;
                            obj.VaporVented = obj.VaporVented + VaporToVent;
                            obj.OtherGasesVented = obj.OtherGasesVented + OtherToVent;
                            
                            molesVentedOrInjected = finalAmountVented;
                            action(2) = 1;      % Record action taken
                            
                        end
                        
                        %% Check to see if current O2 partial pressure is within desired
                        % range
                        
                        % This if statement corresponds to a continuation from the
                        % previous timestep was activated. This is necessary because
                        % the flow rate of O2 introduced into the cabin is limited by
                        % the PCA hardware. Once the ppO2 is brought within the desired
                        % range, it takes two activations of the PCA to bring ppO2 to
                        % the desired set pressure
                        if previousAction(3) == 1 && nargin == 2 % don't do this if being commanded
                            % Note that we now ignore the bounding box as we
                            % are trying to bring the pressure back to a
                            % nominal state
                            if (obj.Environment.pressure*obj.Environment.O2Percentage) < obj.TargetO2PartialPressure    % in kPa
                                currentTargetO2Moles = obj.TargetO2PartialPressure * obj.Environment.volume / (obj.idealGasConstant*(obj.Environment.temperature+273.15));      % Number of moles corresponding to desired ppO2
                                makeupO2MolesRequired = currentTargetO2Moles - obj.Environment.O2Store.currentLevel;       % Determine makeup O2 required (in moles)
                                % Modified 09/2019 to account for variable
                                % degradations  by limiting the O2 flow
                                % rate
                                makeupO2taken = obj.O2Source.ResourceStore.take(min(makeupO2MolesRequired,(1-obj.PerformanceDegradation)*obj.O2Source.MaxFlowRate),obj.O2Source);     % Take required makeup O2 amount from O2 Source
                                % if the degradation limited performance, then
                                % increment NumDegradedRuns
                                if obj.PerformanceDegradation > 0 && find([makeupO2MolesRequired,(1-obj.PerformanceDegradation)*obj.O2Source.MaxFlowRate] == makeupO2taken) == 2
                                    obj.NumDegradedRuns = obj.NumDegradedRuns + 1;
                                end
                                %                     % Error Check
                                %                     if makeupO2taken < makeupO2MolesRequired
                                %                         disp('Insufficient O2 available to perform pressure control action. ppO2 is below safe threshold')
                                %                         obj.Error = 1;
                                %                         return
                                %                     end
                                molesVentedOrInjected = makeupO2taken;
                                obj.Environment.O2Store.add(makeupO2taken);         % add take makeup O2 to environment
                            end
                        end
                        
                        % Check to see if ppO2 is within desired bounding box
                        % Modified 11/2019 to take in optional commanded
                        % production setting input
                        if (obj.Environment.pressure*obj.Environment.O2Percentage) < (obj.TargetO2PartialPressure - obj.PartialPressureBoundingBox) || nargin == 3 && operationLevel(3) ~= 0   % in kPa
                            currentTargetO2Moles = obj.TargetO2PartialPressure * obj.Environment.volume / (obj.idealGasConstant*(obj.Environment.temperature+273.15));      % Number of moles corresponding to desired ppO2
                            if nargin == 3
                                makeupO2MolesRequired = operationLevel(3)*obj.O2Source.MaxFlowRate;
                            else
                                makeupO2MolesRequired = currentTargetO2Moles - obj.Environment.O2Store.currentLevel;       % Determine makeup O2 required (in moles)
                            end
                            % Modified 09/2019 to account for variable
                            % degradations  by limiting the O2 flow
                            % rate
                            makeupO2taken = obj.O2Source.ResourceStore.take(min(makeupO2MolesRequired,(1-obj.PerformanceDegradation)*obj.O2Source.MaxFlowRate),obj.O2Source);     % Take required makeup O2 amount from O2 Source
                            % if the degradation limited performance, then
                            % increment NumDegradedRuns
                            if obj.PerformanceDegradation > 0 && find([makeupO2MolesRequired,(1-obj.PerformanceDegradation)*obj.O2Source.MaxFlowRate] == makeupO2taken) == 2
                                obj.NumDegradedRuns = obj.NumDegradedRuns + 1;
                            end

%                             if makeupO2taken < makeupO2MolesRequired
%                                 disp('not enough flow rate')
%                             end
                            obj.Environment.O2Store.add(makeupO2taken);         % add take makeup O2 to environment
                            
                            molesVentedOrInjected = makeupO2taken;
                            action(3) = 1;      % Record action taken
                            
                        end
                        
                        %% Check for under pressure condition - add N2 to bring total pressure back to desired value
                        % This is the last step given that O2 values have been modified
                        % prior to this
                        
                        % Check for influence of previous actions - to command PCA to drive atmospheric constituents back to a constant state
                        if previousAction(4) == 1 && nargin == 2 %don't do this if being commanded
                            % Note that we now ignore the bounding box as we
                            % are trying to bring the pressure back to a
                            % nominal state
                            if obj.Environment.pressure < obj.TargetTotalPressure
                                targetTotalMoles = obj.TargetTotalPressure * obj.Environment.volume / (obj.idealGasConstant*(obj.Environment.temperature+273.15));      % Number of moles corresponding to desired total pressure
                                makeupN2MolesRequired = targetTotalMoles - obj.Environment.totalMoles;       % Determine makeup N2 required (in moles)
                                % Modified 09/2019 to account for variable
                                % degradations  by limiting the N2 flow
                                % rate
                                makeupN2taken = obj.N2Source.ResourceStore.take(min(makeupN2MolesRequired,(1-obj.PerformanceDegradation)*obj.N2Source.MaxFlowRate),obj.N2Source);     % Take required makeup N2 amount from N2 Source
                                % if the degradation limited performance, then
                                % increment NumDegradedRuns
                                if obj.PerformanceDegradation > 0 && find([makeupN2MolesRequired,(1-obj.PerformanceDegradation)*obj.N2Source.MaxFlowRate] == makeupN2taken) == 2
                                    obj.NumDegradedRuns = obj.NumDegradedRuns + 1;
                                end

                                molesVentedOrInjected = makeupN2taken;
                                obj.Environment.NitrogenStore.add(makeupN2taken);         % add take makeup N2 to environment
                            end
                            
                        end
                        
                        % Check to see if total pressure is within desired bounding box
                        % Modified 11/2019 to take in optional commanded
                        % production setting input
                        if obj.Environment.pressure < (obj.TargetTotalPressure - obj.PartialPressureBoundingBox) || nargin == 3 && operationLevel(4) ~= 0
                            targetTotalMoles = obj.TargetTotalPressure * obj.Environment.volume / (obj.idealGasConstant*(obj.Environment.temperature+273.15));      % Number of moles corresponding to desired total pressure
                            if nargin == 3
                                makeupN2MolesRequired = operationLevel(4)*obj.N2Source.MaxFlowRate;
                            else
                                makeupN2MolesRequired = targetTotalMoles - obj.Environment.totalMoles;       % Determine makeup N2 required (in moles)
                            end
                            % Modified 09/2019 to account for variable
                            % degradations  by limiting the N2 flow
                            % rate
                            makeupN2taken = obj.N2Source.ResourceStore.take(min(makeupN2MolesRequired,(1-obj.PerformanceDegradation)*obj.N2Source.MaxFlowRate),obj.N2Source);     % Take required makeup N2 amount from N2 Source
                            % if the degradation limited performance, then
                            % increment NumDegradedRuns
                            if obj.PerformanceDegradation > 0 && find([makeupN2MolesRequired,(1-obj.PerformanceDegradation)*obj.N2Source.MaxFlowRate] == makeupN2taken) == 2
                                obj.NumDegradedRuns = obj.NumDegradedRuns + 1;
                            end

                            %                     if makeupN2taken < makeupN2MolesRequired
                            %                         disp('Insufficient N2 available to perform pressure control action. Module is in an underpressure condition')
                            %                         obj.Error = 1;
                            %                         return
                            %                     end
                            
                            obj.Environment.NitrogenStore.add(makeupN2taken);         % add take makeup N2 to environment
                            
                            molesVentedOrInjected = makeupN2taken;
                            action(4) = 1;      % Record action taken
                            
                        end
                        
%                         else
%                             return
%                         end

                        
                    case 'PPRV'
                        % Case for if injector is commanded to only operate
                        % in PPRV mode (i.e. we can only vent from the
                        % habitat)
                        %% Check for overpressure
                        % Vent if total pressure is greater than target pressure +
                        % bounding box
                        if obj.Environment.pressure > (obj.TargetTotalPressure + obj.PartialPressureBoundingBox)
                            currentTargetTotalMoles = obj.TargetTotalPressure * obj.Environment.volume / (obj.idealGasConstant*(obj.Environment.temperature+273.15));   % No. of moles corresopnding to target absolute pressure
                            airToVent = obj.Environment.totalMoles - currentTargetTotalMoles;
                            
                            % Calculate current maximum vent rate based on pressure
                            % difference between cabin and Martian environment
                            currentAverageDensity = (obj.Environment.O2Store.currentLevel*obj.O2molarMass + obj.Environment.CO2Store.currentLevel*obj.CO2molarMass...
                                + obj.Environment.NitrogenStore.currentLevel*obj.N2molarMass + obj.Environment.VaporStore.currentLevel*obj.VapormolarMass...
                                + obj.Environment.OtherStore.currentLevel*obj.OthermolarMass) / obj.Environment.volume;        % Density in g/L = kg/m^3
                            
                            currentMaxVentRate = sqrt(2*(obj.Environment.pressure - obj.MoonMeanAtmPressure)*1E3/currentAverageDensity);    % in meters per second (m/s)
                            % Modified 09/2019 to account for variable
                            % degradations  by limiting the vent port area
                            currentVolumetricFlowRate = currentMaxVentRate*(1-obj.PerformanceDegradation)*pi*obj.VentPortDiameter^2/4*3600;      % in m^3/hr (hence the *3600 factor)
                            maxVentRate = obj.Environment.pressure*currentVolumetricFlowRate*1E3/(obj.idealGasConstant*(obj.Environment.temperature+273.15));       % maximum venting rate in moles/hr
                            
                            finalAmountVented = min([airToVent,maxVentRate]);   % Final amount that can be vented is the minimum of the maximum possible vent rate, and the desired amount of air to vent
                            % if the degradation limited performance, then
                            % increment NumDegradedRuns
                            if obj.PerformanceDegradation > 0 && find([airToVent,maxVentRate] == finalAmountVented) == 2
                                obj.NumDegradedRuns = obj.NumDegradedRuns + 1;
                            end
                            
                            currentO2percentage = obj.Environment.O2Percentage;
                            currentCO2percentage = obj.Environment.CO2Percentage;
                            currentN2percentage = obj.Environment.N2Percentage;
                            currentVaporpercentage = obj.Environment.VaporPercentage;
                            currentOtherpercentage = obj.Environment.OtherPercentage;
                            
                            % Take corresponding airToVent from Environment atmosphere
                            O2ToVent = obj.Environment.O2Store.take(currentO2percentage*finalAmountVented);
                            CO2ToVent = obj.Environment.CO2Store.take(currentCO2percentage*finalAmountVented);
                            N2ToVent = obj.Environment.NitrogenStore.take(currentN2percentage*finalAmountVented);
                            VaporToVent = obj.Environment.VaporStore.take(currentVaporpercentage*finalAmountVented);
                            OtherToVent = obj.Environment.OtherStore.take(currentOtherpercentage*finalAmountVented);
                            
                            % Update object properties
                            obj.O2Vented = obj.O2Vented + O2ToVent;
                            obj.CO2Vented = obj.CO2Vented + CO2ToVent;
                            obj.N2Vented = obj.N2Vented + N2ToVent;
                            obj.VaporVented = obj.VaporVented + VaporToVent;
                            obj.OtherGasesVented = obj.OtherGasesVented + OtherToVent;
                            
                            molesVentedOrInjected = finalAmountVented;
                            action(2) = 1;      % Record action taken
                            
                        end
                        
                    case 'EMU'
                        % Case for if injector is commanded to only operate
                        % in PPRV mode (i.e. we can only vent from the
                        % habitat)
                        %% Check for overpressure
                        % Vent if total pressure is greater than target pressure +
                        % bounding box
                        if obj.Environment.pressure > (obj.TargetTotalPressure + obj.PartialPressureBoundingBox)
                            currentTargetTotalMoles = obj.TargetTotalPressure * obj.Environment.volume / (obj.idealGasConstant*(obj.Environment.temperature+273.15));   % No. of moles corresopnding to target absolute pressure
                            airToVent = obj.Environment.totalMoles - currentTargetTotalMoles;
                            
                            % Calculate current maximum vent rate based on pressure
                            % difference between cabin and Martian environment
                            currentAverageDensity = (obj.Environment.O2Store.currentLevel*obj.O2molarMass + obj.Environment.CO2Store.currentLevel*obj.CO2molarMass...
                                + obj.Environment.NitrogenStore.currentLevel*obj.N2molarMass + obj.Environment.VaporStore.currentLevel*obj.VapormolarMass...
                                + obj.Environment.OtherStore.currentLevel*obj.OthermolarMass) / obj.Environment.volume;        % Density in g/L = kg/m^3
                            
                            currentMaxVentRate = sqrt(2*(obj.Environment.pressure - obj.MoonMeanAtmPressure)*1E3/currentAverageDensity);    % in meters per second (m/s)
                            % Modified 09/2019 to account for variable
                            % degradations  by limiting the vent port area
                            currentVolumetricFlowRate = currentMaxVentRate*(1-obj.PerformanceDegradation)*pi*obj.VentPortDiameter^2/4*3600;      % in m^3/hr (hence the *3600 factor)
                            maxVentRate = obj.Environment.pressure*currentVolumetricFlowRate*1E3/(obj.idealGasConstant*(obj.Environment.temperature+273.15));       % maximum venting rate in moles/hr
                            
                            finalAmountVented = min([airToVent,maxVentRate]);   % Final amount that can be vented is the minimum of the maximum possible vent rate, and the desired amount of air to vent
                            % if the degradation limited performance, then
                            % increment NumDegradedRuns
                            if obj.PerformanceDegradation > 0 && find([airToVent,maxVentRate] == finalAmountVented) == 2
                                obj.NumDegradedRuns = obj.NumDegradedRuns + 1;
                            end

                            currentO2percentage = obj.Environment.O2Percentage;
                            currentCO2percentage = obj.Environment.CO2Percentage;
                            currentN2percentage = obj.Environment.N2Percentage;
                            currentVaporpercentage = obj.Environment.VaporPercentage;
                            currentOtherpercentage = obj.Environment.OtherPercentage;
                            
                            % Take corresponding airToVent from Environment atmosphere
                            O2ToVent = obj.Environment.O2Store.take(currentO2percentage*finalAmountVented);
                            CO2ToVent = obj.Environment.CO2Store.take(currentCO2percentage*finalAmountVented);
                            N2ToVent = obj.Environment.NitrogenStore.take(currentN2percentage*finalAmountVented);
                            VaporToVent = obj.Environment.VaporStore.take(currentVaporpercentage*finalAmountVented);
                            OtherToVent = obj.Environment.OtherStore.take(currentOtherpercentage*finalAmountVented);
                            
                            % Update object properties
                            obj.O2Vented = obj.O2Vented + O2ToVent;
                            obj.CO2Vented = obj.CO2Vented + CO2ToVent;
                            obj.N2Vented = obj.N2Vented + N2ToVent;
                            obj.VaporVented = obj.VaporVented + VaporToVent;
                            obj.OtherGasesVented = obj.OtherGasesVented + OtherToVent;
                            
                            molesVentedOrInjected = finalAmountVented;
                            action(2) = 1;      % Record action taken
                            
                        end
                        
                        %% Check for under pressure condition - add O2 to bring total pressure back to desired value
                        % This is the last step given that O2 values have been modified
                        % prior to this
                        
                        % For an EMU type PCA - bring pressure directly
                        % back to target pressure, ignoring influence of
                        % previous actions
                        
                        if obj.Environment.pressure < obj.TargetTotalPressure
                            targetTotalMoles = obj.TargetTotalPressure * obj.Environment.volume / (obj.idealGasConstant*(obj.Environment.temperature+273.15));      % Number of moles corresponding to desired total pressure
                            makeupO2MolesRequired = targetTotalMoles - obj.Environment.totalMoles;       % Determine makeup N2 required (in moles)
                            % Modified 09/2019 to account for variable
                            % degradations  by limiting the O2 flow
                            % rate
                            makeupO2taken = obj.O2Source.ResourceStore.take(min(makeupO2MolesRequired,(1-obj.PerformanceDegradation)*obj.O2Source.MaxFlowRate),obj.O2Source);     % Take required makeup O2 amount from O2 Source                           
                            % if the degradation limited performance, then
                            % increment NumDegradedRuns
                            if obj.PerformanceDegradation > 0 && find([makeupO2MolesRequired,(1-obj.PerformanceDegradation)*obj.O2Source.MaxFlowRate] == makeupO2taken) == 2
                                obj.NumDegradedRuns = obj.NumDegradedRuns + 1;
                            end

                            obj.Environment.O2Store.add(makeupO2taken);         % add take makeup N2 to environment
                            
                            molesVentedOrInjected = makeupO2taken;
                            action(4) = 1;      % Record action taken
                            
                        end
                end
                            
        end
        
    end
    
end

