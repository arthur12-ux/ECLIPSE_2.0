classdef isruPowerUseImpl < handle
    %ShelfImpl4 Summary of this class goes here
    %   By: Michael Szostak (mszostak3@gatech.edu)
    %   Date Created: 10/10/2020
    %   Last Updated: 10/10/2020
    %
    properties
       powerRequired
       PowerConsumerDefinition
       powerUsedThisTic
       powerUsed = 0;
    end 
    
    methods
        function obj = isruPowerUseImpl(isruPowerReq, PowerSource)
			 obj.powerRequired = isruPowerReq;
             obj.powerUsed = 0;
			 % function obj = ResourceUseDefinitionImpl(store,desiredFlowRate,maxFlowRate)
			 obj.PowerConsumerDefinition = ResourceUseDefinitionImpl(PowerSource,isruPowerReq,isruPowerReq);
        end
        % At each tick
		function beamPower(obj) 
			obj.powerUsedThisTic = obj.PowerConsumerDefinition.ResourceStore.take(obj.powerRequired,obj.PowerConsumerDefinition);   % note that the upper bound from the max and desired flow arets should be divided by the number of shelves (pushFractionalResources)
		end

		function obj = tick(obj)
% 			obj.powerUsed = obj.powerUsed + obj.powerUsedThisTic;
            beamPower(obj);
		end 
	end
end