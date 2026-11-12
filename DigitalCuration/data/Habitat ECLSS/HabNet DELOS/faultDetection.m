function faultDetection(timestep, failureScenario, maxDelay, subSystems, missionData)
%% Description
% This function currently takes in the failure scenario and gives back the
% status of subsystems with a response delay. The worse a subsystem is
% degraded the sooner it is identified. The maximum delay is given as an
% input.

% *To Do*: This function analyzes data that would be likely to be provided by
% sensors/meters to determine if a subsystem is not performing correctly
% and estimates how much it is degraded


%% Code
    %     FailureScenario Names
    %     {'LabPCA','LoftPCA','PCMPCA','SuitlockPCA','PLMPPRV',...
    %     'LabCCAA','LoftCCAA','PCMCCAA','SuitlockCCAA','mainvccr','ogs',...
    %     'crs.Compressor','crs.Reactor','crs.Separator',...
    %     'waterRS.WPA','waterRS.UPA','Lab2PCMFan','PLM2PCMFan',...
    %     'Loft2PCMFan','Lab2AirlockFan'}
    
    %     Subsystems Names
    %     subSystems.LabPCA, subSystems.LoftPCA, subSystems.PCMPCA,
    %     subSystems.SuitlockPCA, subSystems.PLMPPRV, subSystems.LabCCAA,
    %     subSystems.LoftCCAA, subSystems.PCMCCAA, subSystems.SuitlockCCAA,
    %     subSystems.mainvccr, subSystems.ogs, subSystems.crs,
    %     subSystems.waterRS, subSystems.Lab2PCMFan, subSystems.PLM2PCMFan,
    %     subSystems.Loft2PCMFan, subSystems.Lab2AirlockFan,

    for i = 1:length(failureScenario)
        % Find subSystem object that has a failure
        if contains(failureScenario(i).Name,'.')
            % For crs and waterRS, need to extract the substring before the
            % '.' to match with subSystems structure fieldnames
            subSystem = subSystems.(char(extractBefore(failureScenario(i).Name,'.')));
            componentName = char(extractAfter(failureScenario(i).Name,'.'));
        else
            subSystem = subSystems.(failureScenario(i).Name);
            componentName = '';
        end
        
        % if subSystem has been run equal to or greater than
        % maxDelay*(1-performanceDegradation)+1 times since the fault was
        % activated and we haven't already identified the degradation, then 
        % mark the degradation as successfully identified
        if subSystem.([componentName,'NumDegradedRuns']) >= maxDelay && subSystem.([componentName,'KnownDegradation']) == 0
            subSystem.([componentName,'KnownDegradation']) = failureScenario(i).Impact;
            disp([failureScenario(i).Name, ' has detected a degradation of ', num2str(subSystem.([componentName,'KnownDegradation'])), ' after ', num2str(subSystem.([componentName,'NumDegradedRuns'])), ' degraded runs.']);
        end
    end
end