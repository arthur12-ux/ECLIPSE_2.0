function failureScenario = randomFailureScenarioGenerator(missionDuration,failures)
%% This function outputs a Failure Scenario to be used in HabNet
% It uses the distributions developed in HabitatFailureDistributionFit.m,
% which are based on ISSUPAData.mat
% This function assumes all subsystem errors follow the same weibull
% distributions based on the UPA data
% The impact of the degradation is generated from a uniform distribution
% The failureScenario output is an array of Structures
if nargin == 2
    ErrorList = failures;
else
    % assume failures occur in all subsystems
    ErrorList = {'LabPCA','LoftPCA','PCMPCA','SuitlockPCA','PLMPPRV',...
        'LabCCAA','LoftCCAA','PCMCCAA','SuitlockCCAA','mainvccr','ogs',...
        'crs.Compressor','crs.Reactor','crs.Separator',...
        'waterRS.WPA','waterRS.UPA','Lab2PCMFan','PLM2PCMFan',...
        'Loft2PCMFan','Lab2AirlockFan'};
end

failureScenario = struct([]);
%struct('Name',{'ogs','LabPCA'},'Start',{100,50},'Duration',{300,50},'Impact',{.2,.8});

% set randomly prescribed numbers to start from index 1 of random list
% (for repeatability)
% rng(1);

% generate list of random numbers for failure start time since previous
% failure
% use weibull parameters from HabitatFailureDistributionFit.m based on
% UPA data - a=12,537; b=1.2008
failureStarts = wblrnd(12537,1.2008,5,length(ErrorList));
% generate list of random numbers for failure durations
% use weibull parameters from HabitatFailureDistributionFit.m based on
% UPA data - a=123.3805; b=0.5841
failureDurations = wblrnd(73.5466,1.0479,5,length(ErrorList));
% modify failureStarts to have successive failures start after the previous
% failure ended; so add in failureDurations
failureEnds = cumsum(failureStarts+failureDurations,1);
failureStarts = [failureStarts(1,:); failureStarts(2:end,:)+failureEnds(1:end-1,:)];
% generate list of random impact levels
% use uniform distribution
failureImpacts = rand(5,length(ErrorList));
%loop through subsystems and start assigning failures
for i = 1:size(failureStarts,2)
    for j = 1:size(failureStarts,1)
        %check that the failure start is less than the mission duration
        if failureStarts(j,i) < missionDuration
            fS.Name = ErrorList{i};
            fS.Start = ceil(failureStarts(j,i)); % ceil to nearest integer to avoid 0
            fS.Duration = ceil(failureDurations(j,i)); % ceil to nearest integer to avoid 0
            fS.Impact = failureImpacts(j,i);
            failureScenario = [failureScenario,fS];
        else
            % if the current failure start > mission duration, then all of 
            % the subsequent failures for this subsystem will also be 
            % >mission duration, so break the inner for loop and go to next
            % subsystem
            break
        end
    end
end

end