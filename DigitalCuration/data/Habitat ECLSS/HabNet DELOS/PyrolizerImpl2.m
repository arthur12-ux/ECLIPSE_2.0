classdef PyrolizerImpl2
    %PyrolizerImpl Summary of this class goes here
    %   By: Sydney Do (sydneydo@mit.edu)
    %   Date Created: 5/16/2014
    %   Last Updated: 5/16/2014
    %   Pyrolisis system that recovers hydrogen from methane
    %
    % Changes made by Nihad Ljubuncic to implement methane pyrolysis
    % Dated modified: 9/23/2019
    % Changes:
    % methane pyrolysis implemented using supporting data to calculate
    % efficiencies
    % Model will assume 80% recovery rate at 2073K given this is near the
    % reaction efficiency of two separate researched pyrolysis reactors
    % As of 10/24/2019 Power requirements are not taken into consideration
    %% RAW DATA
    % From: Experimental Evaluation of Indirect Heating Tubular Reactors
    % for Solar Methane Pyrolysis (2010)
    % "Complete methane conversion and hydrogen yield beyond 80% were
    % achieved at 2073K."
    % "The expected production was estimated to be about 2.47 Nm^3/hr H2
    % and 386 gr/hr carbon black for 1.47 Nm^3/hr of CH4 injected."
    %% Notes
    % 1.47Nm^3 CH4 = 65.625 mol CH4
    %  2.47Nm^3 H2 = 110.26 mol H2
    
    
    properties
        % Consumer/Producer Definitions
        PowerConsumerDefinition
        MethaneLevel
        H2ProducerDefinition
        DryWasteProducerDefinition
        WaterOutput
        CarbonProducerDefinition
    end
    
    properties (Access = private)
        ConversionRate = .84
        H2Produced = 110.26       % Moles
        CarbonProduced = 386      % Grams
        MethaneConsumed = 65.625  % Moles
        PowerConsumed = 50e3      % Watts
    end
    
    methods
        %% Constructor
        %% Change input
        function obj = PyrolizerImpl2(CH4Output, H2Store, DryWasteStore, MainPowerStore)
            obj.PowerConsumerDefinition = ResourceUseDefinitionImpl(MainPowerStore);
            %           obj.WaterOutput = WaterOutput;
            %           obj.CarbonProducerDefinition = ResourceUseDefinitionImpl(0);
            obj.MethaneLevel = ResourceUseDefinitionImpl(CH4Output);
            obj.H2ProducerDefinition = ResourceUseDefinitionImpl(H2Store);
            obj.DryWasteProducerDefinition = ResourceUseDefinitionImpl(DryWasteStore);

        end
        
        %%tick
        function H2Produced = tick(obj)
            if obj.MethaneLevel.ResourceStore.currentLevel > 0
                if obj.MethaneLevel.ResourceStore.currentLevel >= obj.MethaneConsumed 
                    obj.MethaneLevel.ResourceStore.take(obj.MethaneConsumed); % Removing amount of methane processed in an hour/tick
                    obj.H2ProducerDefinition.ResourceStore.add(obj.H2Produced); % Adding the expected amount of H2 (mol) from 65.625mol of CH4 per hour/tick
                    % obj.CarbonProducerDefinition.ResourceStore.add(obj.CarbonProduced); % Adding 386 grams of coke per hour/tick
                    obj.DryWasteProducerDefinition.ResourceStore.add(obj.CarbonProduced);
                    obj.PowerConsumerDefinition.ResourceStore.take(obj.PowerConsumed);
                    H2Produced = obj.H2ProducerDefinition.ResourceStore.currentLevel;
                    
                    
                else
                    obj.H2ProducerDefinition.ResourceStore.add(2*(obj.MethaneLevel.ResourceStore.currentLevel) * obj.ConversionRate);
                    % obj.CarbonProducerDefinition.ResourceStore.add((obj.MethaneLevel.ResourceStore/obj.MethaneConsumed)*obj.CarbonProduced); %Adding a proportionate amount of carbon to carbon storage
                    obj.DryWasteProducerDefinition.ResourceStore.add((obj.MethaneLevel.ResourceStore.currentLevel/obj.MethaneConsumed)*obj.CarbonProduced); %Adding a proportionate amount of carbon to Dry Waste storage
                    MethaneRatio = (obj.MethaneLevel.ResourceStore.currentLevel/obj.MethaneConsumed);
                    obj.MethaneLevel.ResourceStore.take(obj.MethaneConsumed);
                    obj.PowerConsumerDefinition.ResourceStore.take(MethaneRatio*obj.PowerConsumed); %Using a percentage of power based on a ratio of how much methane was actually used vs the amount it could be using
                    H2Produced = obj.H2ProducerDefinition.ResourceStore.currentLevel;
                end
            else
            H2Produced = 0;                
            end

        end
    end
end



