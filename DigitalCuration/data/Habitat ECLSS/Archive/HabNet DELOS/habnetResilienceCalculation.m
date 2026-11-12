function resilienceData = habnetResilienceCalculation(data,desiredCapability,failureScenario,targetTF)
%% Main
% function resilienceData = get_resilience(capability, baselineCapability, desiredCapability, tThreats)

% nominalO2 = xlsread('Nominal.xlsx','Sheet1');
% nominalTP = xlsread('Nominal.xlsx','Sheet2');
% 
% faultTProw = [t; data.LabPressure(t)];
% faultTP = transpose(faultTProw);
% nominalO2 = xlsread('Nominal20000.xlsx','O2Store');
% nominalH2O = xlsread('Nominal20000.xlsx','H2OStore');
% 
% faultO2row = [t; data.LabO2level(t)./data.LabTotalMoles(t).*data.LabPressure(t)];

faultrow = [1:length(data);data];
fault = transpose(faultrow);

capability = fault;
% baselineCapability = nominalO2;
% desiredCapability = median(nominalO2(1:end,2));%nominalO2(1,2); 18.228;
tThreats = length(failureScenario);

% capability = faultH2O;
% baselineCapability = nominalH2O(1:5000,:);
% desiredCapability = median(nominalH2O(1:5000,2));
% tThreats = 1;

% capability = faultTP;
% baselineCapability = nominalTP;
% desiredCapability = 56.446;
% tThreats = 1;

% constants
EPOCH_BUFFER_FRACTION = 0.05;	% determines how much of the end of each epoch is ignored
STEADY_STATE_SLOPE_FRACTION = 0.1;	% capability slope value used to identify steady-state (fraction of desired capability)
STEADY_STATE_VARIATION_FRACTION = STEADY_STATE_SLOPE_FRACTION*3;	% limits the variation allowed during the steady-state period

% initializes values
if length(desiredCapability) == 1
    desiredCapability = ones(size(tThreats))*desiredCapability; % converts scalar desired capability to a vector of desired capabilities for each epoch
end
tMax = max(capability(:,1));	% maximum time in simulation
tEpochs = vertcat(tThreats, tMax);  % epoch start/end times
capabilitySlope = [capability(1:length(capability) - 1,1) capability(2:end,2) - capability(1:length(capability) - 1,2)];	% forward difference slope of the capability data
Delta = ones(size(tThreats))*-Inf;	% Delta for each epoch
rho = ones(size(tThreats))*-Inf;	% rho for each epoch
nOscillations = ones(size(tThreats))*-Inf;  % number of oscillations for each epoch
delta = ones(size(tThreats))*-Inf;  % delta for each epoch
zeta = ones(size(tThreats))*-Inf;	% zeta for each epoch
integrationFraction = ones(size(tThreats))*-Inf;	% integration fraction for each epoch
tau = ones(size(tThreats))*-Inf;	% tau for each epoch

% loops through each epoch (threat event) to calculate resilience values
for i = 1:length(tEpochs) - 1
    tStart = tEpochs(i)+1;    % epoch start time
    tEnd = tEpochs(i+1) - ceil((tEpochs(i+1) - tStart)*EPOCH_BUFFER_FRACTION);	% epoch end time (last EPOCH_BUFFER_FRACTION of epoch is not included to prevent/buffer slope calculations from being affected by next epoch)
    iCapability = capability(tStart:tEnd,:);	% capability data for the current epoch
    iCapabilitySlope = capabilitySlope(tStart:tEnd,:);	% capability slope data for the current epoch
    
    % calculates Delta (minimum capability without recovery relative to
    % desired)
%     baselineMinimumCapability = max(min(baselineCapability(tStart:tEnd,2)), 0);
%     Delta(i) = baselineMinimumCapability/desiredCapability(i);
    Delta(i) = 1;
    
    % calculates capability steady-state - START HERE
    %   - steady-state within an epoch is assumed to be the earliest time
    %   when all following capability slopes are less than a value defined
    %   by the steady state slope fraction
    %   - if no clear steady-state is reached, steady-state is assumed to
    %   be the end of the epoch
    %   - recovered capability is assumed to be the steady-state capability
    largeSlopes = iCapabilitySlope(abs(iCapabilitySlope(:,2)) >= STEADY_STATE_SLOPE_FRACTION*desiredCapability(i),:);	% vector of times where the capability slope is larger than allowed
    if ~isempty(largeSlopes)
        tSteadyState = largeSlopes(end,1);	% time when steady-state was reached
        recoveredCapability = mean(iCapability(iCapability(:,1) >= tSteadyState,2));
        steadyStateVariation = iCapability(iCapability(:,1) >= tSteadyState,2) - recoveredCapability;
        if max(abs(steadyStateVariation)) > STEADY_STATE_VARIATION_FRACTION*desiredCapability(i)
            tSteadyState = iCapability(end,1);   % sets tau to be end of epoch if there is too much variation in capability following tau (e.g. slowly increasing capability)
            recoveredCapability = mean(iCapability(round(0.9*length(iCapability)):end,2));
        end
    else
        tSteadyState = iCapability(end,1);   % sets tau to be end of epoch if there is too much variation in capability following tau (e.g. slowly increasing capability)
        % set recoveredCapability to be average of last 10% of mission
        recoveredCapability = mean(iCapability(round(0.9*length(iCapability)):end,2));
    end
    
    % calculates tau
    tau(i) = find(iCapability(:,1) == tSteadyState)/(tEnd - tStart + 1);
    
    % calculates rho (recovered capability relative to desired)
    if targetTF
        rho(i) = 1-((desiredCapability(i) - recoveredCapability)/desiredCapability).^2;
%         rho(i) = 1-(recoveredCapability-desiredCapability(i))/desiredCapability;
    else
        rho(i) = recoveredCapability/desiredCapability(i);
    end
    % calculates delta (minimum capability with recovery relative to
    % desired)
    minimumCapability = min(iCapability(:,2));
    delta(i) = minimumCapability/desiredCapability(i);
    
    % calculates number of oscillations
    positiveSlopes = largeSlopes(:,2) > 0;  % logical array identifying large slopes that are positive
    slopeChanges = positiveSlopes(2:end) - positiveSlopes(1:length(positiveSlopes)-1);  % vector showing when slope changes from positive to negative (-1) and neg. to pos. (1)
    nSlopeChanges = length(find(slopeChanges ~= 0));    % number of times there were large slope changes (from pos.-neg. or neg.-pos.)
    nOscillations(i) = floor(nSlopeChanges/2); % assumes that 2 slope changes indicate an oscillation
    
    % calculates capability integration
    if targetTF
        integrationFraction(i) = 1-1/length(iCapability)/desiredCapability(i).^2*sum((desiredCapability(i) - iCapability(:,2)).^2);
%         integrationFraction(i) = 1-sum(iCapability(:,2)-desiredCapability(i))/(desiredCapability(i)*length(iCapability));
    else
        integrationFraction(i) = sum(iCapability(:,2))/(desiredCapability(i)*length(iCapability));
    end
    
    % calculates zeta (accounts for damping)
    if nOscillations(i) > 1
        zeta(i) = tau(i)/(nOscillations(i) - 1) + Delta(i)*delta(i);
    else
        zeta(i) = Delta(i)*delta(i);
    end
end
if any(ismember(vertcat(Delta, rho, nOscillations, delta, zeta, integrationFraction, tau), -Inf))
   error('ERROR: missing resilience metrics')
end

% calculates resilience
for i = 1:length(integrationFraction)
    if rho >= delta
        resilience(i) = integrationFraction(i).*rho(i).*(delta(i) + 1 - tau(i)^(rho(i)-delta(i)));
    else
        resilience(i) = integrationFraction(i).*rho(i).*delta(i);
    end
end
% creates resilience data structure
resilienceData.resilience = resilience;
resilienceData.Delta = Delta;
resilienceData.rho = rho;
resilienceData.nOscillations = nOscillations;
resilienceData.delta = delta;
resilienceData.zeta = zeta;
resilienceData.integrationFraction = integrationFraction;
resilienceData.tau = tau;
end