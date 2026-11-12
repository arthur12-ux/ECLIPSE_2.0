%% Habitat Failure Distribution Fit
% This script uses data from the ISS UPA to fit weibull distributions to
% component failures.

%% Find Number of Hours Between Failures
% ****Change file path as necessary!
load('C:\Users\mrines3\Documents\Github\7140_NASA_ALS_Resilience\ISSUPAData.mat');
hoursBetweenFailures = [diff(UPAFluidsPumpDegradations.InstallDate); diff(UPAPurgePumpDegradations.InstallDate)];
% remove NaN entries (first and last elements)
hoursBetweenFailures = hours(hoursBetweenFailures(~isnan(hoursBetweenFailures)));

%% Find time between failure and replacement
% From the NASA ISS Excel Sheet
% "The previously installed unit's failure date is the previous entry in
% Column C"
    % This is referring to the previous date listed in the data tables

failureHoursFluids = [];
failureHoursPurge = [];
installHoursFluids = [];
installHoursPurge = [];
% remove first and last indices that are NaT (Not a Time)
installDatesFluids = UPAFluidsPumpDegradations.InstallDate(~isnat(UPAFluidsPumpDegradations.InstallDate));
installDatesPurge = UPAPurgePumpDegradations.InstallDate(~isnat(UPAPurgePumpDegradations.InstallDate));

% loop through each installDate and find the last datetime in the pump data
% that is less than it
for i = 1:length(installDatesFluids)
    arr = UPAFluidsPump.ProcessRunDate(UPAFluidsPump.ProcessRunDate < installDatesFluids(i));
    % if the installDate is less than all dates in pump data, then record
    % NaN (to be removed later). Will fill with 0, when indexing next
    % element if don't do this
    if isempty(arr)
        installHoursFluids(i) = NaN;
        failureHoursFluids(i) = NaN;
    else
        % find the number of hours since either the first pump data time or
        % install time
        installHoursFluids(i) = hours(diff([min(UPAFluidsPump.ProcessRunDate(1),UPAFluidsPumpDegradations.InstallDate(1)),installDatesFluids(i)]));
        failureHoursFluids(i) = hours(diff([min(UPAFluidsPump.ProcessRunDate(1),UPAFluidsPumpDegradations.InstallDate(1)),arr(length(arr))]));
    end
end
for i = 1:length(installDatesPurge)
    arr = UPAPurgePump.ProcessRunDate(UPAPurgePump.ProcessRunDate < installDatesPurge(i));
    % if the installDate is less than all dates in pump data, then record
    % NaN (to be removed later). Will fill with 0, when indexing next
    % element if don't do this
    if isempty(arr)
        installHoursPurge(i) = NaN;
        failureHoursPurge(i) = NaN;
    else
        % find the number of hours since either the first pump data time or
        % install time
        installHoursPurge(i) = hours(diff([min(UPAPurgePump.ProcessRunDate(1),UPAPurgePumpDegradations.InstallDate(1)),installDatesPurge(i)]));
        failureHoursPurge(i) = hours(diff([min(UPAPurgePump.ProcessRunDate(1),UPAPurgePumpDegradations.InstallDate(1)),arr(length(arr))]));
    end
end

% compare the failureHour to the installHour
failureDurations = [installHoursFluids,installHoursPurge]-[failureHoursFluids,failureHoursPurge];
failureDurations = failureDurations(~isnan(failureDurations));
%% Plots for Time Between Failures and Weibull Fit

% Plot Hours Between Failures and Empirical CFD
figure;
plot(hoursBetweenFailures,ones(1,length(hoursBetweenFailures))./2,'o')
hold on
cdfplot(hoursBetweenFailures)
hold off
title('Hours Between Failures')
legend('ISS Data','Empirical CDF','location','best')
xlabel('Hours')

% Plot Histograms with Different Numbers of Bins and Boxplots
% To-do: scale yaxes b/c boxplot autoscales it and cuts off histogram
figure;
suptitle('ISS UPA Failure Distribution')
subplot(2,2,1)
hold on
boxplot(hoursBetweenFailures,'orientation','horizontal')
histogram(hoursBetweenFailures,4)
hold off
title('4 bins')
xlabel('hours')
ylim([0, inf])
subplot(2,2,2)
histogram(hoursBetweenFailures,5)
hold on
boxplot(hoursBetweenFailures,'orientation','horizontal')
hold off
title('5 bins')
xlabel('hours')
subplot(2,2,3)
histogram(hoursBetweenFailures,6)
hold on
boxplot(hoursBetweenFailures,'orientation','horizontal')
hold off
title('6 bins')
xlabel('hours')
subplot(2,2,4)
histogram(hoursBetweenFailures,7)
hold on
boxplot(hoursBetweenFailures,'orientation','horizontal')
hold off
title('7 bins')
xlabel('hours')

%check to see if the data likely follows a weibull distribution
figure;
wblplot(hoursBetweenFailures)
h1 = lillietest(log(hoursBetweenFailures),'Distribution','extreme value');

% fit a weibull distribution to the data
parmhat = wblfit(hoursBetweenFailures);

% plot fitted weibull distribution pdf and cdf with iss data
figure;
subplot(2,1,1)
plot(wblpdf(1:45000,parmhat(1),parmhat(2)))
hold on
histogram(hoursBetweenFailures,6,'normalization','pdf')
plot(hoursBetweenFailures,median(wblpdf(1:45000,parmhat(1),parmhat(2))),'k.');
hold off
xlabel('Hours')
ylabel('f(x)')
title('PDF')
legend('Weibull Fit','ISS Hist','ISS Data','location','best')
xlim([0,inf])
subplot(2,1,2)
plot(wblcdf(1:45000,parmhat(1),parmhat(2)))
hold on
cdfplot(hoursBetweenFailures)
xlabel('Hours')
title('CDF')
legend('Weibull Fit','ISS Data','location','best')
xlim([0,inf])
hold off

% Compare random points from fitted distribution to ISS Data
figure;
fitData = wblrnd(parmhat(1),parmhat(2),1,10000);
subplot(2,1,1)
histogram(fitData,5,'BinLimits',[0,45000],'normalization','pdf')
title('Weibull Failure Model - 10000 Random Points')
ylabel('f(x)')
xlabel('Hours')
ylim([0 6E-5])
xlim([0 45000])
subplot(2,1,2)
histogram(hoursBetweenFailures,5,'normalization','pdf')
title('ISS UPA Data')
ylabel('f(x)')
xlim([0 45000])
xlabel('Hours')

% Constrain to within HabNet 5000 hour mission
figure;
fitData = wblrnd(parmhat(1),parmhat(2),1,10000);
subplot(2,1,1)
histogram(fitData,5,'BinLimits',[0,5000],'normalization','pdf')
title('Weibull Failure Model - 10000 Random Points')
ylabel('f(x)')
ylim([0 1E-4])
xlim([0 5000])
xlabel('Hours')
subplot(2,1,2)
histogram(hoursBetweenFailures,5,'BinLimits',[0,5000],'normalization','pdf')
title('ISS UPA Data')
ylabel('f(x)')
ylim([0 1E-4])
xlim([0 5000])
xlabel('Hours')

%% Plot Duration Values

% Plot empirical pdf and data points
figure;
suptitle('ISS UPA Failure Duration Distribution')
subplot(2,1,1)
boxplot(failureDurations,'orientation','horizontal')
xlim([0,inf])
xlabel('Hours')
subplot(2,1,2)
plot(failureDurations,ones(1,length(failureDurations))./2,'ko')
xlabel('Hours')
hold on
histogram(failureDurations,5,'BinLimits',[0,180])
hold off

% remove outlier from data before fitting distribution
[outlierValue,outlierIndex] = max(failureDurations);
failureDurations = failureDurations(failureDurations~=outlierValue);

%check to see if the data likely follows a weibull distribution
figure;
wblplot(failureDurations)
h2 = lillietest(log(failureDurations),'Distribution','extreme value');

% fit a weibull distribution to the data
parmhat = wblfit(failureDurations);

% plot fitted weibull distribution pdf and cdf with iss data
figure;
subplot(2,1,1)
plot(wblpdf(0:200,parmhat(1),parmhat(2)))
hold on
histogram(failureDurations,5,'BinLimits',[0,200],'normalization','pdf')
plot(failureDurations,median(wblpdf(0:200,parmhat(1),parmhat(2))),'k.');
hold off
xlabel('Hours')
ylabel('f(x)')
title('PDF')
legend('Weibull Fit','ISS Hist','ISS Data','location','best')
xlim([0,inf])
subplot(2,1,2)
plot(wblcdf(1:200,parmhat(1),parmhat(2)))
hold on
cdfplot(failureDurations)
xlabel('Hours')
title('CDF')
legend('Weibull Fit','ISS Data','location','best')
xlim([0,inf])
hold off

% Compare random points from fitted distribution to ISS Data
figure;
fitData = wblrnd(parmhat(1),parmhat(2),1,10000);
subplot(2,1,1)
histogram(fitData,5,'BinLimits',[0,200],'normalization','pdf')
title('Weibull Failure Model - 10000 Random Points')
ylabel('f(x)')
xlabel('Hours')
ylim([0 1E-3])
xlim([0 200])
subplot(2,1,2)
histogram(failureDurations,5,'BinLimits',[0,200],'normalization','pdf')
title('ISS UPA Data')
ylabel('f(x)')
xlim([0 200])
xlabel('Hours')

% Zoom to 200 hour durations
figure;
fitData = wblrnd(parmhat(1),parmhat(2),1,10000);
subplot(2,1,1)
histogram(fitData,5,'BinLimits',[0,200],'normalization','pdf')
title('Weibull Failure Model - 10000 Random Points')
ylabel('f(x)')
xlabel('Hours')
ylim([0,.011])
xlim([0 200])
subplot(2,1,2)
histogram(failureDurations,5,'BinLimits',[0,200],'normalization','pdf')
title('ISS UPA Data')
ylabel('f(x)')
ylim([0,.011])
xlim([0 200])
xlabel('Hours')