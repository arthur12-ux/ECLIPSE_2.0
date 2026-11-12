classdef ISSPayloadImpl < handle
    %ShelfImpl4 Summary of this class goes here
    %   By: Michael Szostak (mszostak3@gatech.edu)
    %   Date Created: 11/10/2020
    %   Last Updated: 11/10/2020
    %
    %   This class file acts like typical ISS payload power draw and water use

    properties
       waterLossPerHour = (0.18+0.24)/24; % Literes per day used by payloads on ISS from Figure 1 in https://ntrs.nasa.gov/api/citations/20110012703/downloads/20110012703.pdf
       potableWaterUsedPerHour = 0.84/24; % Litres per day for reuse and turned into grey water 
       GreyWaterProducerDefinition
       PotableWaterConsumerDefinition
       powerRequired = 500*2*8; % assumes 8x MidDeckLockers containing 500 watts cooling and 500 watts power for payload power draw (table A-4 in https://www.nasa.gov/pdf/501115main_ISS_Payload_Integration_Process_Primer_final_submission_baseline.pdf) and size here: http://wsn.spaceflight.esa.int/docs/Factsheets/14%20MSG%20HR.pdf
       PowerConsumerDefinition; % assumes 4x Lockers per Microgravity Science Glovebox (MSG) AND 2x of the MSGs; https://www.nasa.gov/centers/marshall/news/background/facts/MSG.html
    end 
    
    methods
        function obj = ISSPayloadImpl(PotableWaterInput, GreyWaterOutput, PowerSource)
            obj.GreyWaterProducerDefinition = ResourceUseDefinitionImpl(GreyWaterOutput);           
            obj.PotableWaterConsumerDefinition = ResourceUseDefinitionImpl(PotableWaterInput);
            obj.PowerConsumerDefinition = ResourceUseDefinitionImpl(PowerSource, obj.powerRequired, obj.powerRequired);
        end

		function obj = tick(obj)
            obj.PowerConsumerDefinition.ResourceStore.take(obj.powerRequired,obj.PowerConsumerDefinition); % use power
            obj.PotableWaterConsumerDefinition.ResourceStore.take(obj.potableWaterUsedPerHour+obj.waterLossPerHour);
            obj.GreyWaterProducerDefinition.ResourceStore.add(obj.potableWaterUsedPerHour); % consume water from potable and convert it to grey with an amout left out
		end 
	end
end