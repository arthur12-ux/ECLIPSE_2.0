failureScenarios = {};
failureScenarioSizes = zeros(1,1000);
for i = 1:1000
    failureScenarios{i} = randomFailureScenarioGenerator(5000);
    failureScenarioSizes(i) = length(failureScenarios{i});
end

meanFailureScenarioSize = mean(failureScenarioSizes);
meanDuration = mean(arrayfun(@(x)x.Duration,[failureScenarios{:}]));

figure;
subplot(2,2,1)
histogram(failureScenarioSizes)
ylabel('Frequency')
hold on
yyaxis right
histogram(failureScenarioSizes,'normalization','probability','FaceColor','none','EdgeColor','none')
ax = gca;
ax.YAxis(2).Color = 'black';
hold off
title('Failures Per Simulation')
xlabel('Number of Failures Per Simulation')
ylabel('Probability')
subplot(2,2,2)
histogram(arrayfun(@(x)x.Start,[failureScenarios{:}]))
ylabel('Frequency')
hold on
yyaxis right
histogram(arrayfun(@(x)x.Start,[failureScenarios{:}]),'normalization','probability','FaceColor','none','EdgeColor','none')
ax = gca;
ax.YAxis(2).Color = 'black';
hold off
title('Start Times')
xlabel('Start Time (Hours)')
ylabel('Probability')
xlim([0,inf])
subplot(2,2,3)
histogram(arrayfun(@(x)x.Duration,[failureScenarios{:}]))
ylabel('Frequency')
hold on
yyaxis right
histogram(arrayfun(@(x)x.Duration,[failureScenarios{:}]),'normalization','probability','FaceColor','none','EdgeColor','none')
ax = gca;
ax.YAxis(2).Color = 'black';
hold off
title('Durations')
xlabel('Duration (Hours)')
ylabel('Probability')
xlim([0,inf])
subplot(2,2,4)
histogram(arrayfun(@(x)x.Impact,[failureScenarios{:}]))
ylabel('Frequency')
hold on
yyaxis right
histogram(arrayfun(@(x)x.Impact,[failureScenarios{:}]),'normalization','probability','FaceColor','none','EdgeColor','none')
ax = gca;
ax.YAxis(2).Color = 'black';
hold off
title('Degradation/Impact')
xlabel('Impact')
ylabel('Probability')
xlim([0,inf])
suptitle('1000 Failure Scenarios - Statistics')
