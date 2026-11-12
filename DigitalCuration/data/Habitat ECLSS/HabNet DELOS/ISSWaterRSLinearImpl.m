classdef ISSWaterRSLinearImpl < handle
    %ISSWaterRSLinear Summary of this class goes here
    %   By: Sydney Do (sydneydo@mit.edu)
    %   Date Created: 8/10/2014
    %   Last Updated: 8/10/2014
    %   This is a simple implementation of a water processing system
    %   Taken from comments in BioSim code:
    %   The Water Recovery System takes grey (humidity condensate)/dirty 
    %   (urine) water and refines it to potable water for the crew members 
    %   and grey water for the crops.. 
    %   Class modeled after the paper:. "Intelligent Control of a Water 
    %   Recovery System: Three Years in the Trenches" by Bonasso, 
    %   Kortenkamp, and Thronesbery
    
    %   Note this implementation assumes 100% water processing efficiency
    
    %   UPDATE LOG
    %   2/24/2015 - Removed "return" calls so that UPA and WPA code is
    %   still cycled through when there's an error. Specifically, so that
    %   WPA runs even if there's a UPA error
    
    %% Notes to tune to the ISS UPA and WPA
    % From: "ECLSS Design for the International Space Station Nodes 2 and 3" (1999):
    % Urine is plumbed from the W&HC's urinal to the Urine Processor Assembly (UPA) portion of the WRS. 
    % The product distillate from this process is combined with other wastewater and further processed 
    % by the Water Processor Assembly (WPA). The WPA processes up to 93.4 kg/day (206 lb/day) wastewater [5]

    % From ISS Water Balance Operations (2011):
    % UPA feeds about 4.5L of urine condensate per day to the WPA
    
    % From ISS Water Balance Operations (2011):
    % "The WPA waste water tank has a total capacity of 100 lbs of water mixed between distillate and condensate. 
    % Until recently, working tank preferred upper limit was limited to 65 lbs of water due to concerns 
    % with biofouling in downstream components.

    % From: Status of ISS Water Management and Recovery 2013
    % The UPA was designed to process a nominal load of 9 kg/day (19.8 lbs/day) of wastewater consisting of urine and
    % flush water. This is the equivalent of a 6-crew load on ISS, though in reality the UPA typically processes only the
    % urine generated in the US Segment. Product water from the UPA has been evaluated on the ground to verify it
    % meets the requirements for conductivity, pH, ammonia, particles, and total organic carbon. The UPA was designed
    % to recover 85% of the water content from the pretreated urine, though issues with urine quality encountered in 2009
    % have required the recovery to be dropped to 74%.
    
    % From: Status of the Regenerative ECLSS Water Recovery and Oxygen Generation Systems (2006):
    % "The WPA operates in batch mode, processing water nominally at 5.9 Kg/hr (13 lb/hr) consuming an 
    % average of 320 W-hr/hr when processing and 133 W-hr/hr while in standby."
    
    % From: Status of the Regenerative ECLSS Water Recovery and Oxygen Generation Systems (2006):
    % The UPA is designed to process a nominal load of 8.4kg/day (18.6 lbs/day) of wastewater consisting 
    % of urine, flush water, and a small amount of waste from Environmental Health System water samples. 
    % At a maximum load, the UPA can process 13.6 kg (30 lbs) of wastewater over an 18-hour period per day. 
    % Like the WPA, it operates in a batch mode, consuming a maximum average power of 315 W when processing,
    % and 56 W during standby. Product water from the UPA must meet specification quality requirements for 
    % conductivity, pH, ammonia, particles, and total organic carbon. It must recover a minimum of 85% of 
    % the water content in the specified wastewater stream.
    
    %% Simulation Assumptions and Notes
    % For the purposes of this simulation, we will treat dirty water as
    % urine (processed by the UPA at its efficiency level) and grey water
    % as humidity condensate (of which 100% of the water content is
    % recovered
    
    % Control: UPA and WPA start when the grey and dirty water tanks are
    % full
    
    properties
        % Consumer/Producer Definitions
        DirtyWaterConsumerDefinition        % Corresponds to urine and humidity condensate - Input Store for UPA
        GreyWaterConsumerDefinition         % Corresponds to wash water and water for plant growth - Input store for WPA
        GreyWaterProducerDefinition         % Output store for UPA
        DryWasteProducerDefinition          % Corresponds to the UPA ARFTA
        PotableWaterProducerDefinition
        PowerConsumerDefinition
        
        UPAwasteWaterTank
        WPAwasteWaterTank
%         UPAerror = 0
        UPAPerformanceDegradation = 0 % Amount of degradation resulting from error (0 = no degradation; 1 = not functioning)
        UPAKnownDegradation = 0    % Indicates the degradation recognized by the crew/ALSS - for use in faultDetection.m
        UPANumDegradedRuns = 0    % Number of times that the system performance has been compromised by the degradation - for use in faultDetection.m

        %         WPAerror = 0
        WPAPerformanceDegradation = 0 % Amount of degradation resulting from error (0 = no degradation; 1 = not functioning)
        WPAKnownDegradation = 0    % Indicates the degradation recognized by the crew/ALSS - for use in faultDetection.m
        WPANumDegradedRuns = 0    % Number of times that the system performance has been compromised by the degradation - for use in faultDetection.m

    end
    
    properties (SetAccess = private)
       UrineProcessingEfficiency = 0.74     % UPA Water Recovery Efficiency
       UPAmaxprocessingpower = 315          % Watts, max power consumed while processing
       UPAstandbypower = 56                 % Watts, power consumed while in standby mode
       UPAwasteWaterTankCapacity = 18/2.2   % in Liters (converted from 18lb of water, assuming 1000kg/m^3 density for water) (REF: International Space Station Water Balance Operations = AIAA 2011-5150)
       UPAmaxprocessingRate = 13.6/18       % in Liters per hour (REF: Status of the Regenerative ECLSS Water Recovery and Oxygen Generation Systems (2006))
       WPAprocessingpower = 320             % Watts, power consumed while processing
       WPAstandbypower = 133                % Watts, power consumed while in standby mode
       WPAwasteWaterTankCapacity = 0.65*100/2.2  % in Liters (converted from 65% 100lb of WPA wastewater tank (to prevent biofouling of downstream components - see above notes), assuming 1000kg/m^3 density for water) (REF: International Space Station Water Balance Operations = AIAA 2011-5150)
       WPAprocessingRate = 5.9              % in Liters per hour (REF: Status of the Regenerative ECLSS Water Recovery and Oxygen Generation Systems (2006))
    end
    
    methods
        %% Constructor
        function obj = ISSWaterRSLinearImpl(DirtyWaterInput,GreyWaterInput,GreyWaterOutput,WasteOutput,PotableWaterOutput,PowerSource)
            obj.DirtyWaterConsumerDefinition = ResourceUseDefinitionImpl(DirtyWaterInput);
            obj.GreyWaterConsumerDefinition = ResourceUseDefinitionImpl(GreyWaterInput);
            obj.GreyWaterProducerDefinition = ResourceUseDefinitionImpl(GreyWaterOutput);           
            obj.DryWasteProducerDefinition = ResourceUseDefinitionImpl(WasteOutput);
            obj.PotableWaterProducerDefinition = ResourceUseDefinitionImpl(PotableWaterOutput);
            obj.PowerConsumerDefinition = ResourceUseDefinitionImpl(PowerSource);
            
            % Initialize internal process stores
            obj.UPAwasteWaterTank = StoreImpl('Urine - Dirty Water','Material',obj.UPAwasteWaterTankCapacity,0);
            obj.WPAwasteWaterTank = StoreImpl('Condensate - Grey Water','Material',obj.WPAwasteWaterTankCapacity,0);
        end
        
        %% tick
        function [UPAGreyWaterProduced,UPAPowerConsumed,WPAPotableWaterProduced,WPAPowerConsumed] = tick(obj,operationLevel)
%             disp('ticking ISSWaterRSLinearImpl');
            % if PerformanceDegradation = 0, then NumDegradedRuns and KnownDegradation should be
            % reset to 0, this is needed once a degradation has been fixed
            if obj.UPAPerformanceDegradation == 0
                obj.UPANumDegradedRuns = 0;
                obj.UPAKnownDegradation = 0;
            end
            if obj.WPAPerformanceDegradation == 0
                obj.WPANumDegradedRuns = 0;
                obj.WPAKnownDegradation = 0;
            end
            
            %%  UPA
  
            % Only run if there is no system error
%             if obj.UPAerror == 0
                % Modified 11/2019 to take in optional commanded
                % production setting input                
                if nargin == 2
                    % if we're controlling upa, fill up tank to make sure
                    % we have enough dirty water
                    dirtyWaterToTake = obj.UPAwasteWaterTankCapacity - obj.UPAwasteWaterTank.currentLevel;
                    dirtyWaterTaken = obj.DirtyWaterConsumerDefinition.ResourceStore.take(dirtyWaterToTake);
%                     disp([num2str(dirtyWaterTaken), ' L dirty water taken for filtering - ISSWaterRSLinearImpl added to UPAwasteWaterTank']);
                    obj.UPAwasteWaterTank.add(dirtyWaterTaken);
                    
                % Start Running UPA if UPAwasteWaterTankLevel is full
                % Note that UPA processes dirty water into condensate (which we
                % call grey water for the purposes of this simulation)
                elseif obj.DirtyWaterConsumerDefinition.ResourceStore.currentLevel >= obj.UPAwasteWaterTankCapacity && obj.UPAwasteWaterTank.currentLevel == 0
                    
                    % Take water from dirty water store
                    dirtyWaterTaken = obj.DirtyWaterConsumerDefinition.ResourceStore.take(obj.UPAwasteWaterTankCapacity);
%                     disp([num2str(dirtyWaterTaken), ' L dirty water taken for filtering - ISSWaterRSLinearImpl added to UPAwasteWaterTank']);
                    obj.UPAwasteWaterTank.add(dirtyWaterTaken);
                    
                end
                
                % Run UPA in batch mode
                if obj.UPAwasteWaterTank.currentLevel > 0
                    
                    % Gather Power Required
                    currentPowerConsumed = obj.PowerConsumerDefinition.ResourceStore.take(obj.UPAmaxprocessingpower);     % Take max power when possible
                    
                    % Tune UPA processing rate based on power consumed
                    % Operating points are:
                    % - max processing rate: (13.6/18)L/hr @ max power = 315W
                    % - min processing rate: 0L/hr @ standby power = 56W
                    
                    % Modified 11/2019 to take in optional commanded
                    % production setting input                
                    if nargin == 2
                        currentUPAprocessingRate = max([min(operationLevel(1)*obj.UPAmaxprocessingRate/(obj.UPAmaxprocessingpower-obj.UPAstandbypower)*(currentPowerConsumed-obj.UPAstandbypower),(1-obj.UPAPerformanceDegradation)*obj.UPAmaxprocessingRate),0]);   % Max command in case currentPowerConsumed < obj.UPAstandbypower
                    else
                        % Modified 09/2019 to account for variable degradations
                        currentUPAprocessingRate = max([min(obj.UPAmaxprocessingRate/(obj.UPAmaxprocessingpower-obj.UPAstandbypower)*(currentPowerConsumed-obj.UPAstandbypower),(1-obj.UPAPerformanceDegradation)*obj.UPAmaxprocessingRate),0]);   % Max command in case currentPowerConsumed < obj.UPAstandbypower
                    end
                    % if the degradation limited performance, then
                    % increment NumDegradedRuns
                    if obj.UPAPerformanceDegradation > 0 && find([obj.UPAmaxprocessingRate/(obj.UPAmaxprocessingpower-obj.UPAstandbypower)*(currentPowerConsumed-obj.UPAstandbypower),(1-obj.UPAPerformanceDegradation)*obj.UPAmaxprocessingRate] == currentUPAprocessingRate) == 2
                        obj.UPANumDegradedRuns = obj.UPANumDegradedRuns + 1;
                    end
                    
                    % Modified 09/2019 to return excess power in case of
                    % degradation
                    actualPowerConsumed = currentUPAprocessingRate/obj.UPAmaxprocessingRate*(obj.UPAmaxprocessingpower-obj.UPAstandbypower)+obj.UPAstandbypower;
                    obj.PowerConsumerDefinition.ResourceStore.add(max([currentPowerConsumed - actualPowerConsumed,0]));
                    UPAPowerConsumed = actualPowerConsumed;
                    % Process Dirty Water and send condensate to GreyWaterStore
                    UrineToProcess = obj.UPAwasteWaterTank.take(currentUPAprocessingRate);      % Take urine from UPAwasteWaterTank based on currentUPAprocessingRate
                    UPAGreyWaterProduced = obj.GreyWaterProducerDefinition.ResourceStore.add(obj.UrineProcessingEfficiency*UrineToProcess);
%                     disp([num2str(UPAGreyWaterProduced), ' L of grey water produced from ISSWaterRS UrinePA']);
                    obj.DryWasteProducerDefinition.ResourceStore.add((1-obj.UrineProcessingEfficiency)*UrineToProcess);     % Send brine to dry waste store (we lose this amount of water) - this equivalent to sending brine to the UPA ARFTA (note that dry waste is measured in kg)
                    
%                     disp([num2str((1-obj.UrineProcessingEfficiency)*UrineToProcess), ' L of Brine loss from ISSWaterRS UrinePA']);
                else
                    % Gather Standby Power
                    currentPowerConsumed = obj.PowerConsumerDefinition.ResourceStore.take(obj.UPAstandbypower);     % Take max power when possible
                    UPAPowerConsumed = currentPowerConsumed;
                    UPAGreyWaterProduced = 0;
                    if currentPowerConsumed < obj.UPAstandbypower
                        disp('UPA shut down due to insufficient power input')
                        obj.UPAerror = 1;
                        return
                    end
                    
                end
                
%             else
%                 % There is an error in the UPA
%                 % skip the tick function
%                 return
                
%             end
            
            %% WPA
            % Start running WPA if WPAwasteWaterTankLevel is full
            % Note that UPA processes dirty water into condensate (which we
            % call grey water for the purposes of this simulation)
            
            % Only run if there is no system error
%             if obj.WPAerror == 0
                % Modified 11/2019 to take in optional commanded
                % production setting input                
                if nargin == 2
                    % if we're controlling wpa, fill up tank to make sure
                    % we have enough grey water
                    greyWaterToTake = obj.WPAwasteWaterTankCapacity - obj.WPAwasteWaterTank.currentLevel;
                    greyWaterTaken = obj.GreyWaterConsumerDefinition.ResourceStore.take(greyWaterToTake);
%                     disp([num2str(greyWaterTaken), ' L of grey water taken ISSWaterRS WastePA']);
                    obj.WPAwasteWaterTank.add(greyWaterTaken);

                elseif obj.GreyWaterConsumerDefinition.ResourceStore.currentLevel >= obj.WPAwasteWaterTankCapacity && obj.WPAwasteWaterTank.currentLevel == 0
                    
                    % Take water from grey water store
                    greyWaterTaken = obj.GreyWaterConsumerDefinition.ResourceStore.take(obj.WPAwasteWaterTankCapacity);
%                     disp([num2str(greyWaterTaken), ' L of grey water taken ISSWaterRS WastePA']);
                    obj.WPAwasteWaterTank.currentLevel = greyWaterTaken;
                    
                end
                
                % Run WPA in batch mode
                if obj.WPAwasteWaterTank.currentLevel > 0
                    
                    % Gather Power Required
                    currentPowerConsumed = obj.PowerConsumerDefinition.ResourceStore.take(obj.WPAprocessingpower);     % Take max power when possible
                    
                    % Tune WPA processing rate based on power consumed
                    % Operating points are:
                    % - average processing rate: 5.9L/hr @ average power = 320W
                    % - min processing rate: 0L/hr @ standby power = 133W
                    
                    % Modified 11/2019 to take in optional commanded
                    % production setting input                
                    if nargin == 2
                        currentWPAprocessingRate = max([min(operationLevel(1)*obj.WPAprocessingRate/(obj.WPAprocessingpower-obj.WPAstandbypower)*(currentPowerConsumed-obj.WPAstandbypower),(1-obj.WPAPerformanceDegradation)*obj.WPAprocessingRate),0]);   % Max command in case currentPowerConsumed < obj.WPAstandbypower
                    else
                        % Modified 09/2019 to account for variable degradations
                        currentWPAprocessingRate = max([min(obj.WPAprocessingRate/(obj.WPAprocessingpower-obj.WPAstandbypower)*(currentPowerConsumed-obj.WPAstandbypower),(1-obj.WPAPerformanceDegradation)*obj.WPAprocessingRate),0]);   % Max command in case currentPowerConsumed < obj.WPAstandbypower
                    end
                    % if the degradation limited performance, then
                    % increment NumDegradedRuns
                    if obj.WPAPerformanceDegradation > 0 && find([obj.WPAprocessingRate/(obj.WPAprocessingpower-obj.WPAstandbypower)*(currentPowerConsumed-obj.WPAstandbypower),(1-obj.WPAPerformanceDegradation)*obj.WPAprocessingRate] == currentWPAprocessingRate) == 2
                        obj.WPANumDegradedRuns = obj.WPANumDegradedRuns + 1;
                    end
                    
                    % Modified 09/2019 to return excess power in case of
                    % degradation
                    actualPowerConsumed = currentWPAprocessingRate/obj.WPAprocessingRate*(obj.WPAprocessingpower-obj.WPAstandbypower)+obj.WPAstandbypower;
                    obj.PowerConsumerDefinition.ResourceStore.add(max([currentPowerConsumed - actualPowerConsumed,0]));
                    WPAPowerConsumed = actualPowerConsumed;
                    % Process Dirty Water and send condensate to GreyWaterStore
                    CondensateToProcess = obj.WPAwasteWaterTank.take(currentWPAprocessingRate);
                    WPAPotableWaterProduced = obj.PotableWaterProducerDefinition.ResourceStore.add(CondensateToProcess);      % Assume 100% water recovery in WPA
%                     disp([num2str(WPAPotableWaterProduced), ' L of potable water produced ISSWaterRS WastePA']);
                    
                else
                    % Gather Standby Power
                    currentPowerConsumed = obj.PowerConsumerDefinition.ResourceStore.take(obj.WPAstandbypower);     % Take max power when possible
                    WPAPowerConsumed = currentPowerConsumed;
                    WPAPotableWaterProduced = 0;
                    if currentPowerConsumed < obj.WPAstandbypower
                        disp('WPA shut down due to insufficient power input')
                        obj.WPAerror = 1;
                        return
                    end
                    
                end
                
%             else
%                 % There is an error in the UPA
%                 % skip the tick function
%                 return
                
%             end
        end
        
    end
    
end

