%% mlTrainingDataFromOptimizedOGA
% Run HabNet with Optimized OGA for each failure scenario and save output
% for ML algorithm

% load in the failure scenarios
load('UPAFailureScenarios.mat');

missionDuration = 5000;

for i = 1:length(UPAFailures)
    failureScenario = UPAFailures{i};
    % load in the optimized oga operation for this failure
    load(['UPAFailure' num2str(i) 'Optimum.mat'])
    
    % create full OGAControl input
    OGAInput = [NaN*ones(1,failureScenario.Start-1) results.x NaN*ones(1,missionDuration - failureScenario.Start - failureScenario.Duration + 1)];
    
    % run Habnet
    [data,crew] = resilientHabitat(missionDuration,failureScenario,false,false,OGAInput);
    
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
    resilience.aggregate_resilience = -1/7*(resilience.labO2Resilience.resilience + resilience.loftO2Resilience.resilience + ... 
        resilience.PCMO2Resilience.resilience + resilience.PLMO2Resilience.resilience + ...
        resilience.SuitlockO2Resilience.resilience + resilience.o2StoreResilience + ...
        resilience.h2oStoreResilience);

    
    % save all HabNet data for future use
    save(['UPAFailureScenario' num2str(i) 'OGAOptData.mat'],'data','crew','failureScenario','OGAInput','resilience');
    
    % extract and save data needed for ML
    MLData = struct('OGAInput',OGAInput,'UPAKnownDegradation',data.UPAKnownDegradation,'o2storelevel',data.o2storelevel,'potablewaterstorelevel',data.potablewaterstorelevel,'LabO2level',data.LabO2level,'LoftO2level',data.LoftO2level,'PCMO2level',data.PCMO2level,'PLMO2level',data.PLMO2level,'SuitlockO2level',data.SuitlockO2level);
    save(['MLUPAFailureScenario' num2str(i) 'OGAOpt.mat'],'MLData');
end

% Now create 2 master data sets with features and targets for ML
featuresML = [];
targetsML = [];
featuresOptML = [];
targetsOptML = [];
featuresDefML = [];
targetsDefML = [];
for i = 1:100
     failureScenario = UPAFailures{i};
%     load(['MLUPAFailureScenario' num2str(i) 'OGAOpt.mat'])
%     load(['UPAFailure' num2str(i) 'Optimum.mat'])
%     
%     OGAInput = (data.ogsPowerConsumed-469)./(2971-469);
%     MLData.OGAInput = OGAInput;
%     save(['MLUPAFailureScenario' num2str(i) 'OGAOpt.mat'],'MLData');

    optData = load(['UPAFailureScenario' num2str(i) 'OGAOptData.mat']);
    iFeaturesML = [optData.data.UPAKnownDegradation;optData.data.LabO2level;optData.data.LoftO2level;optData.data.PCMO2level;optData.data.PLMO2level;optData.data.SuitlockO2level;optData.data.o2storelevel;optData.data.potablewaterstorelevel];
    featuresML(1:8,(i-1)*5000+1:i*5000) = iFeaturesML;
    ogsOps = [0,.25,.5,.75,1];
    iTargetsML = ogsOps(categorical(round(optData.data.ogsO2Produced*100)/100,round(2.3*(0:4)/24 * 1e3 / (2*15.999)*100)/100,{'0','.25','.5','.75','1'}));
    targetsML(1,(i-1)*5000+1:i*5000) = iTargetsML;
    
    failureInds = [1:5000]>=failureScenario.Start & [1:5000]<failureScenario.Start+failureScenario.Duration;
    featuresOptML = [featuresOptML iFeaturesML(:,failureInds)];
%     featuresDefML = [featuresDefML iFeaturesML(:,find(iFeaturesML,length(iFeaturesML),2)~=failureScenario.Start:failureScenario.Start+failureScenario.Duration-1)];
    featuresDefML = [featuresDefML iFeaturesML(:,~failureInds)]; 
    targetsOptML = [targetsOptML iTargetsML(failureInds)];
    targetsDefML = [targetsDefML iTargetsML(~failureInds)];
end
    
    save('MLUPAFailureOGAOptFeatures.mat','featuresML')
    save('MLUPAFailureOGAOptTargets.mat','targetsML')
    save('OptMLUPAFailureOGAOptFeatures.mat','featuresOptML')
    save('DefMLUPAFailureOGAOptFeatures.mat','featuresDefML')
    save('OptMLUPAFailureOGAOptTargets.mat','targetsOptML')
    save('DefMLUPAFailureOGAOptTargets.mat','targetsDefML')
