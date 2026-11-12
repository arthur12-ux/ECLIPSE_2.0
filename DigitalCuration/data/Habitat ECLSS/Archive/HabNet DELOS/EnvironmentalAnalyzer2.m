function timeUntilDepletion = EnvironmentalAnalyzer(data,timeUntilDepletion,timestep)
% This function estimates the time until various resource stores will be
% depleted

%% Estimate time until resources will be depleted based on current usage
%determine how long until a resource runs out based on the previous data
%points

storesOfImportance = {'o2storelevel','n2storelevel',... 
'h2storelevel','ch4storelevel','potablewaterstorelevel','dirtywaterstorelevel',...
'greywaterstorelevel','carriedfoodstorelevel','powerlevel',...
'LabPressure','LabO2level','LoftPressure','LoftO2level',...
'PCMPressure','PCMO2level','PLMPressure','PLMO2level',...
'SuitlockPressure','SuitlockO2level'};

storesOfImportance = {'potablewaterstorelevel','dirtywaterstorelevel',...
'greywaterstorelevel','carriedfoodstorelevel','powerlevel',...
'LabPressure','LabO2level','LoftPressure','LoftO2level',...
'PCMPressure','PCMO2level','PLMPressure','PLMO2level',...
'SuitlockPressure','SuitlockO2level'};

% if timestep > 2
    %quadraticFunction = @(abc,x)(abc(1)*x^2+abc(2)*x+abc(3));
quadraticFunction = @(ab,x)(ab(1)*x+ab(2));
polynomialOrder = 1;

for i = 1:length(storesOfImportance)
    timeUntilDepletion.(storesOfImportance{i})(timestep) = fzero(@(x)(quadraticFunction(polyfit(1:timestep,data.(storesOfImportance{i})(1:timestep),polynomialOrder),x)),timestep) - timestep;
    if timeUntilDepletion.(storesOfImportance{i})(timestep) < 0
        timeUntilDepletion.(storesOfImportance{i})(timestep) = NaN;
    end
end
% else
%     timeUntilDepletionO2Store = NaN;
%     timeUntilDepletionLabO2 = NaN;
%     timeUntilDepletionPotableWaterStore = NaN;
% end
   
    
    
%     timeUntilDepletionO2Store = fzero(@(x)(quadraticFunction(polyfit(1:timestep,data.o2storelevel(1:timestep),polynomialOrder),x)),timestep) - timestep;
%     if isnan(timeUntilDepletionO2Store) | timeUntilDepletionO2Store < 0
%         timeUntilDepletionO2Store = NaN;
%     end
%     timeUntilDepletionLabO2 = fzero(@(x)(quadraticFunction(polyfit(1:timestep,data.LabO2level(1:timestep),polynomialOrder),x)),timestep) - timestep;
%     if isnan(timeUntilDepletionLabO2) | timeUntilDepletionLabO2 < 0
%         timeUntilDepletionLabO2 = NaN;
%     end
%     timeUntilDepletionPotableWaterStore = fzero(@(x)(quadraticFunction(polyfit(1:timestep,data.potablewaterstorelevel(1:timestep),polynomialOrder),x)),timestep) - timestep;
%     if isnan(timeUntilDepletionPotableWaterStore) | timeUntilDepletionPotableWaterStore < 0
%         timeUntilDepletionPotableWaterStore = NaN;
%     end

end