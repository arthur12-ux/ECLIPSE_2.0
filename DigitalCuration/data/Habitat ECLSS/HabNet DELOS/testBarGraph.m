A = [2.994978852844970,5.989957705689939,8.98493655853491; 2.9950    5.9900    8.9849; 0, 0, 0; 0, 0, 0]
c = categorical(A,2.3*(0:4)/24 * 1e3 / (2*15.999),{'0%','25%','50%','75%','100%'})
B = [countcats(c),zeros(1,5-length(countcats(c)))] %,{'0%','25%','50%','75%','100%'});
% missionData.ogsO2Produced
figure
bar(c, A)
habnetPlotting(missionData,crew,{'OGSFrequency'});