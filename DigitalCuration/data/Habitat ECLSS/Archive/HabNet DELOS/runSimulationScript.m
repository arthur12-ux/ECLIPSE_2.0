%% set mission parameters
missionDuration = 168;

% create failure scenario

    % ErrorList = {'LabPCA','LoftPCA','PCMPCA','SuitlockPCA','PLMPPRV',...
    %     'LabCCAA','LoftCCAA','PCMCCAA','SuitlockCCAA','mainvccr','ogs',...
    %     'crs.Compressor','crs.Reactor','crs.Separator',...
    %     'waterRS.WPA','waterRS.UPA','Lab2PCMFan','PLM2PCMFan',...
    %     'Loft2PCMFan','Lab2AirlockFan'};

    failureScenario = struct('Name',{},'Start',{},'Duration',{},'Impact',{});
    %struct('Name',{'ogs','LabPCA'},'Start',{100,50},'Duration',{300,50},'Impact',{.2,.8});
% failureScenario = struct('Name',{'crs.Compressor'},'Start',{100},'Duration',{1000},'Impact',{1});
% failureScenario = randomFailureScenarioGenerator(missionDuration);

% set random crew schedule to be true or false
randomSchedule = false;

% set to use methane pyrolysis or not
methanePyrolysis = false;

% set if using controlled OGA operation or NaN if not
ogaOperation = NaN;
%% run habnet
tic
[missionData,crew, timeUntilDepletion] = resilientHabitat(missionDuration,failureScenario,randomSchedule,methanePyrolysis,ogaOperation);
toc

%% run resilience calculations
% resilienceData = habnetResilienceCalculation(missionData);

%% plot figures
    %habnetPlotting(missionData,crew,{'crewO2','crewCalories','crewActivity'});
    % habnetPlotting(missionData.Perc100,crew,plotCommands);
        %plotCommands =
        %{'O2Store','potableWaterStore','LabO2','OGSO2','OGSFrequency','crewO2','crewCalories','crewActivity'}
% habnetPlotting(missionData,crew,{'O2Store','potableWaterStore','LabO2','OGSOutput','OGSFrequency','crewO2','crewCalories','crewActivity'});
        %{'O2Store','potableWaterStore','LabO2','OGSOutput','OGSFrequency','crewO2','crewCalories','crewActivity'}
habnetPlotting(missionData,crew,{'O2Store','potableWaterStore','LabO2','OGSOutput','OGSFrequency','crewO2','crewCalories','crewActivity'});
