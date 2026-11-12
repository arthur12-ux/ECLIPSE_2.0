%% Optimize HabNet OGS controls for failures in the UPA
missionDuration = 5000;
% Generate random UPA failure scenarios
% UPAFailures = [];
% load('UPAFailureScenarios.mat')
% i=length(UPAFailures);
% while i <= 100
%     thisFailure = randomFailureScenarioGenerator(missionDuration,{'waterRS.UPA'});
%     if ~isempty(thisFailure) && length(thisFailure) == 1
%         UPAFailures{i} = thisFailure;
%         i = i+1;
%     end
% end
% save('UPAFailureScenarios','UPAFailures')
% load('UPAFailureScenarios.mat');

% for i = 2:length(UPAFailures)

% failureScenario = UPAFailures{i};

% load('NominalOGAOperation.mat');
% NominalOGAOperation(NominalOGAOperation==0) = 0.01;
% NominalOGAOperation(NominalOGAOperation==1) = 0.99;

[data,crew] = resilientHabitat(missionDuration,failureScenario,false,false,[]);
% Calculate resilience of normal operation
if length(data.LabO2level) < 5000
    data.LabO2level = [data.LabO2level zeros(1,5000-length(data.LabO2level))];
    data.LabTotalMoles = [data.LabTotalMoles zeros(1,5000-length(data.LabO2level))];
    data.LoftO2level = [data.LoftO2level zeros(5000-length(data.LabO2level),1)];
    data.LoftTotalMoles = [data.LoftTotalMoles zeros(5000-length(data.LabO2level),1)];
    data.PCMO2level = [data.PCMO2level zeros(5000-length(data.LabO2level),1)];
    data.PLMO2level = [data.PLMO2level zeros(5000-length(data.LabO2level),1)];    
    data.SuitlockO2level = [data.SuitlockO2level zeros(5000-length(data.LabO2level),1)];
    data.PCMTotalMoles = [data.PCMTotalMoles zeros(5000-length(data.LabO2level),1)];
    data.PLMTotalMoles = [data.PLMTotalMoles zeros(5000-length(data.LabO2level),1)];
    data.SuitlockTotalMoles = [data.SuitlockTotalMoles zeros(5000-length(data.LabO2level),1)];
    data.o2storelevel = [data.o2storelevel zeros(5000-length(data.LabO2level),1)];
    data.potablewaterstorelevel = [data.potablewaterstorelevel zeros(5000-length(data.LabO2level),1)];
end
% calculate resilience for the metrics of interest and aggregate them all
% currently weights everything evenly
labO2Resilience = habnetResilienceCalculation(data.LabO2level./data.LabTotalMoles,0.32,failureScenario,true);
loftO2Resilience = habnetResilienceCalculation(data.LoftO2level./data.LoftTotalMoles,0.32,failureScenario,true);
PCMO2Resilience = habnetResilienceCalculation(data.PCMO2level./data.PCMTotalMoles,0.32,failureScenario,true);
PLMO2Resilience = habnetResilienceCalculation(data.PLMO2level./data.PLMTotalMoles,0.32,failureScenario,true);
SuitlockO2Resilience = habnetResilienceCalculation(data.SuitlockO2level./data.SuitlockTotalMoles,0.32,failureScenario,true);
o2StoreResilience = 1-sum(((data.o2storelevel(1) - data.o2storelevel)/data.o2storelevel(1)).^2)/length(data.potablewaterstorelevel);
h2oStoreResilience = 1-sum(((data.potablewaterstorelevel(1) - data.potablewaterstorelevel)/data.potablewaterstorelevel(1)).^2)/length(data.potablewaterstorelevel);
% o2StoreSlope = getCentralDifference(data.o2storelevel)';
% o2StoreResilience = habnetResilienceCalculation(o2StoreSlope+abs(min(o2StoreSlope)+1),-1.0939+abs(min(o2StoreSlope)+1),failureScenario,false);
% h2oStoreSlope = getCentralDifference(data.potablewaterstorelevel)';
% h2oStoreResilience = habnetResilienceCalculation(h2oStoreSlope+abs(min(h2oStoreSlope)+1),-0.1699+abs(min(h2oStoreSlope)+1),failureScenario,false);
aggregate_resilience = -1/3*(1/5*(labO2Resilience.resilience + loftO2Resilience.resilience + ... 
    PCMO2Resilience.resilience + PLMO2Resilience.resilience + ...
    SuitlockO2Resilience.resilience) + o2StoreResilience + ...
    h2oStoreResilience);
results.baselineResilience = aggregate_resilience;

DefaultOGAOperation = cellfun(@str2num,cellstr(categorical(data.ogsO2Produced,unique(data.ogsO2Produced),{'0','0.25','0.5','0.75','1'})));
DefaultOGAOperation(DefaultOGAOperation==0) = 0.01;
DefaultOGAOperation(DefaultOGAOperation==1) = 0.99;
x0 = DefaultOGAOperation(failureScenario.Start:min(failureScenario.Start+failureScenario.Duration-1,5000));
results.x0 = x0;
% Need function handle that just takes the factors as inputs
fun = @(x)objectiveFunctionCall(missionDuration,failureScenario,x);
% Use fmincon for optimization, set lower and upper bounds
    % options = optimoptions('fmincon','DiffMinChange',0.25,'HessianApproximation','lbfgs');
    % [x,fval,exitflag,output] = fmincon(@(x)objectiveFunctionCall(missionDuration,failureScenario,x),x0,[],[],[],[],zeros(5000,1),ones(5000,1),[],options);

% Use patternsearch because fmincon uses differencing on every input
% dimension to find the gradient - takes forever...
options = optimoptions('patternsearch','Cache','on','UseParallel',true,'Display','iter','TolMesh',0.11);
% options = optimoptions('patternsearch','Cache','on','Display','iter','TolMesh',0.1);
[x,fval,exitflag,output] = patternsearch(@(x)objectiveFunctionCall(missionDuration,failureScenario,x),x0,[],[],[],[],zeros(length(x0),1),ones(length(x0),1),[],options);
results.x = x;
results.fval = fval;
results.exitflag = exitflag;
results.output = output;
% save(strcat('UPAFailure',num2str(i),'Optimum.mat'),'results');
save(strcat('UPAFailureExtremeOptimumAltRes.mat'),'results');

% end

% This is the objective function that actually computes stuff
function aggregate_resilience = objectiveFunctionCall(missionDuration,failureScenario,subsystemControls)
% run a HabNet simulation with the current failureScenario and the current
% subsystemControls point
[data,crew] = resilientHabitat(missionDuration,failureScenario,false,false,[NaN*ones(1,failureScenario.Start-1) subsystemControls NaN*ones(1,missionDuration - failureScenario.Start - failureScenario.Duration + 1)]);

% if the mission ended prematurely, add zeros to the end of the data arrays
% to penalize the failed mission before calculating resilience

if length(data.LabO2level) < 5000
    data.LabO2level = [data.LabO2level zeros(1,5000-length(data.LabO2level))];
    data.LabTotalMoles = [data.LabTotalMoles zeros(1,5000-length(data.LabO2level))];
    data.LoftO2level = [data.LoftO2level zeros(5000-length(data.LabO2level),1)];
    data.LoftTotalMoles = [data.LoftTotalMoles zeros(5000-length(data.LabO2level),1)];
    data.PCMO2level = [data.PCMO2level zeros(5000-length(data.LabO2level),1)];
    data.PLMO2level = [data.PLMO2level zeros(5000-length(data.LabO2level),1)];    
    data.SuitlockO2level = [data.SuitlockO2level zeros(5000-length(data.LabO2level),1)];
    data.PCMTotalMoles = [data.PCMTotalMoles zeros(5000-length(data.LabO2level),1)];
    data.PLMTotalMoles = [data.PLMTotalMoles zeros(5000-length(data.LabO2level),1)];
    data.SuitlockTotalMoles = [data.SuitlockTotalMoles zeros(5000-length(data.LabO2level),1)];
    data.o2storelevel = [data.o2storelevel zeros(5000-length(data.LabO2level),1)];
    data.potablewaterstorelevel = [data.potablewaterstorelevel zeros(5000-length(data.LabO2level),1)];
end
% calculate resilience for the metrics of interest and aggregate them all
% currently weights everything evenly
resilience.labO2Resilience = habnetResilienceCalculation(data.LabO2level./data.LabTotalMoles,0.32,failureScenario,true);
resilience.loftO2Resilience = habnetResilienceCalculation(data.LoftO2level./data.LoftTotalMoles,0.32,failureScenario,true);
resilience.PCMO2Resilience = habnetResilienceCalculation(data.PCMO2level./data.PCMTotalMoles,0.32,failureScenario,true);
resilience.PLMO2Resilience = habnetResilienceCalculation(data.PLMO2level./data.PLMTotalMoles,0.32,failureScenario,true);
resilience.SuitlockO2Resilience = habnetResilienceCalculation(data.SuitlockO2level./data.SuitlockTotalMoles,0.32,failureScenario,true);
resilience.o2StoreResilience = 1-sum(((data.o2storelevel(1) - data.o2storelevel)/data.o2storelevel(1)).^2)/length(data.potablewaterstorelevel);
resilience.h2oStoreResilience = 1-sum(((data.potablewaterstorelevel(1) - data.potablewaterstorelevel)/data.potablewaterstorelevel(1)).^2)/length(data.potablewaterstorelevel);
% o2StoreSlope = getCentralDifference(data.o2storelevel)';
% o2StoreResilience = habnetResilienceCalculation(o2StoreSlope+abs(min(o2StoreSlope)+1),-1.0939+abs(min(o2StoreSlope)+1),failureScenario,false);
% h2oStoreSlope = getCentralDifference(data.potablewaterstorelevel)';
% h2oStoreResilience = habnetResilienceCalculation(h2oStoreSlope+abs(min(h2oStoreSlope)+1),-0.1699+abs(min(h2oStoreSlope)+1),failureScenario,false);
resilience.aggregate_resilience = -1/3*(1/5*(resilience.labO2Resilience.resilience + resilience.loftO2Resilience.resilience + ... 
    resilience.PCMO2Resilience.resilience + resilience.PLMO2Resilience.resilience + ...
    resilience.SuitlockO2Resilience.resilience) + resilience.o2StoreResilience + ...
    resilience.h2oStoreResilience);
aggregate_resilience = resilience.aggregate_resilience;

% save(strcat('UPAFailure',num2str(i),'OptimumData.mat'),'resilience','data','crew');

end

function slopes = getCentralDifference(data)
% this function gets the slope of the store level data
    slopes = zeros(length(data),1);
    slopes(1) = data(2)-data(1);
    for i = 2:length(data)-1
        slopes(i) = (data(i+1)-data(i-1))/2;
    end
    slopes(end) = data(end)-data(end-1);
end
