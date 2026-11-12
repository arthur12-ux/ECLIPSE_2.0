function habnetPlotting(habnetDataStructure,crew,plotCommands)

%% Random plot commands used in code validation exercise
% % Atmospheric molar fractions
% hold on
t = 1:(length(habnetDataStructure.o2storelevel));
data = habnetDataStructure;

if(any(strcmp(plotCommands,'O2StoreDepletion')))
    figure
    plot(t,timeUntilDepletion.O2Store)
    title('O_{2} Store')
    xlabel('Timestep')
    ylabel('Estimated Hours Until Depletion')
    ylim([0 simtime+100])
    grid on
    cloudplot
end
if(any(strcmp(plotCommands,'LabO2Depletion')))
figure;
    plot(t,timeUntilDepletion.LabO2)
    title('Lab O_{2} Level')
    xlabel('Timestep')
    ylabel('Estimated Hours Until Depletion')
    ylim([0 simtime+100])
    grid on
    cloudplot
end
if(any(strcmp(plotCommands,'potableWaterStoreDepletion')))
    figure;
    plot(t,timeUntilDepletion.potableWaterStore)
    title('Predicted Potable Water Store')
    xlabel('Timestep')
    ylabel('Estimated Hours Until Depletion')
    ylim([0 simtime+100])
    grid on
    cloudplot
end
if(any(strcmp(plotCommands,'potableWaterStore')))
    figure;
    plot(t,data.potablewaterstorelevel)
    title('Potable Water Store')
    xlabel('Timestep')
    ylabel('Liters of Water')
    ylim([0 inf])
    grid on
    cloudplot
end
if(any(strcmp(plotCommands,'O2Store')))
    figure;
    plot(t,data.o2storelevel)
    title('O_{2} Store')
    xlabel('Timestep')
    ylabel('Moles')
    ylim([0 inf])
    grid on
    cloudplot
end
if(any(strcmp(plotCommands,'LabO2')))
    figure
    plot(t,data.LabO2level)
    title('Lab O_{2}')
    xlabel('Timestep')
    ylabel('Moles')
    ylim([0 inf])
    grid on
    cloudplot
end
if(any(strcmp(plotCommands,'OGSO2')))
    figure
    plot(t,data.ogsO2Produced)
    title('OGS O_{2} Production')
    xlabel('Timestep')
    ylabel('Moles')
    grid on
    cloudplot
end

% crew.astro1.ScheduleNames = [];
% crew.astro2.ScheduleNames = [];
% crew.astro3.ScheduleNames = [];
% crew.astro4.ScheduleNames = [];
% for i = 1:length(max(length(crew.astro1.Schedule),length(crew.astro4.Schedule),length(crew.astro4.Schedule),length(crew.astro4.Schedule)))
%     crew.astro1.ScheduleNames(i) = crew.astro1.Schedule(i).Name;
%     crew.astro2.ScheduleNames(i) = crew.astro2.Schedule(i).Name;
%     crew.astro3.ScheduleNames(i) = crew.astro3.Schedule(i).Name;
%     crew.astro4.ScheduleNames(i) = crew.astro4.Schedule(i).Name;
% end
if(any(strcmp(plotCommands,'crewEVA')))
    crew.NumEVA.astro1 = nnz(arrayfun(@(x)strcmp(x.Name,'EVA'),crew.astro1.Schedule));
    crew.NumEVA.astro2 = nnz(arrayfun(@(x)strcmp(x.Name,'EVA'),crew.astro2.Schedule));
    crew.NumEVA.astro3 = nnz(arrayfun(@(x)strcmp(x.Name,'EVA'),crew.astro3.Schedule));
    crew.NumEVA.astro4 = nnz(arrayfun(@(x)strcmp(x.Name,'EVA'),crew.astro4.Schedule));
    crew.EVAID.astro1 = arrayfun(@(x)x.ID,crew.astro1.Schedule(arrayfun(@(x)strcmp(x.Name,'EVA'),crew.astro1.Schedule)));
    crew.EVAID.astro2 = arrayfun(@(x)x.ID,crew.astro2.Schedule(arrayfun(@(x)strcmp(x.Name,'EVA'),crew.astro2.Schedule)));
    crew.EVAID.astro3 = arrayfun(@(x)x.ID,crew.astro3.Schedule(arrayfun(@(x)strcmp(x.Name,'EVA'),crew.astro3.Schedule)));
    crew.EVAID.astro4 = arrayfun(@(x)x.ID,crew.astro4.Schedule(arrayfun(@(x)strcmp(x.Name,'EVA'),crew.astro4.Schedule)));
    astro1EVAScheduleRepeat = arrayfun(@(x)x.ID,crew.astro1.Schedule(arrayfun(@(x)strcmp(x.Name,'EVA'),crew.astro1.Schedule(1:crew.astro1.CurrentActivity.ID))));
    astro2EVAScheduleRepeat = arrayfun(@(x)x.ID,crew.astro2.Schedule(arrayfun(@(x)strcmp(x.Name,'EVA'),crew.astro2.Schedule(1:crew.astro2.CurrentActivity.ID))));
    astro3EVAScheduleRepeat = arrayfun(@(x)x.ID,crew.astro3.Schedule(arrayfun(@(x)strcmp(x.Name,'EVA'),crew.astro3.Schedule(1:crew.astro3.CurrentActivity.ID))));
    astro4EVAScheduleRepeat = arrayfun(@(x)x.ID,crew.astro4.Schedule(arrayfun(@(x)strcmp(x.Name,'EVA'),crew.astro4.Schedule(1:crew.astro4.CurrentActivity.ID))));
    crew.EVAID.astro1 = [find(crewEVAScheduleLogical(1,:)==1),crew.EVAID.astro1,astro1EVAScheduleRepeat];
    crew.EVAID.astro2 = [find(crewEVAScheduleLogical(2,:)==1),crew.EVAID.astro2,astro2EVAScheduleRepeat];
    crew.EVAID.astro3 = [find(crewEVAScheduleLogical(3,:)==1),crew.EVAID.astro3,astro3EVAScheduleRepeat];
    crew.EVAID.astro4 = [find(crewEVAScheduleLogical(4,:)==1),crew.EVAID.astro4,astro4EVAScheduleRepeat];
    crew.ActivityTime.astro1 = cumsum([[crew.astro1.Schedule.Duration],[crew.astro1.Schedule(1:crew.astro1.CurrentActivity.ID).Duration]]);
    crew.ActivityTime.astro2 = cumsum([[crew.astro2.Schedule.Duration],[crew.astro2.Schedule(1:crew.astro2.CurrentActivity.ID).Duration]]);
    crew.ActivityTime.astro3 = cumsum([[crew.astro3.Schedule.Duration],[crew.astro3.Schedule(1:crew.astro3.CurrentActivity.ID).Duration]]);
    crew.ActivityTime.astro4 = cumsum([[crew.astro4.Schedule.Duration],[crew.astro4.Schedule(1:crew.astro4.CurrentActivity.ID).Duration]]);


    figure;
    hold off
    scatter([crew.ActivityTime.astro1(crew.EVAID.astro1),crew.ActivityTime.astro2(crew.EVAID.astro2),crew.ActivityTime.astro3(crew.EVAID.astro3),crew.ActivityTime.astro4(crew.EVAID.astro4)],7500*[ones(length(crew.EVAID.astro1),1);ones(length(crew.EVAID.astro2),1);ones(length(crew.EVAID.astro3),1);ones(length(crew.EVAID.astro4),1)])
    hold on
    dayhours = repmat(24*(1:840),4,1);
    scatter(dayhours(crewEVAScheduleLogical),17500*ones(length(dayhours(crewEVAScheduleLogical)),1),'+')
    title('EVAs')
    xlabel('Hour')
    legend('Conducted EVAs','Scheduled EVAs')
    ylim([0 3])
    xlim([0 simtime])
    ax = gca;
    grid(ax,'on')
    box(ax,'on')
    ax.YAxis.TickLabels = {};
end
    
% LabO2level = sgolayfilt(LabPcaOnly.data.LabO2level,5,11);
% LabCO2level = sgolayfilt(LabPcaOnly.data.LabCO2level,5,11);
% LabPressure = sgolayfilt(LabPcaOnly.data.LabPressure,5,11);



% figure, 
% subplot(2,3,1), plot(t,LabO2level(t)./LabTotalMoles,t,LabCO2level./LabTotalMoles,t,LabN2level./LabTotalMoles,t,LabVaporlevel./LabTotalMoles,t,LabOtherlevel./LabTotalMoles,'LineWidth',2), title('Lab'),legend('O2','CO2','N2','Vapor','Other'), grid on, xlabel('Time (hours)'), ylabel('Molar Fraction')
% subplot(2,3,2), plot(t,PCMO2level(t)./PCMTotalMoles,t,PCMCO2level./PCMTotalMoles,t,PCMN2level./PCMTotalMoles,t,PCMVaporlevel./PCMTotalMoles,t,PCMOtherlevel./PCMTotalMoles,'LineWidth',2), title('PCM'),legend('O2','CO2','N2','Vapor','Other'), grid on, xlabel('Time (hours)'), ylabel('Molar Fraction')
% subplot(2,3,3), plot(t,PLMO2level(t)./PLMTotalMoles(t),t,PLMCO2level(t)./PLMTotalMoles(t),t,PLMN2level(t)./PLMTotalMoles(t),t,PLMVaporlevel(t)./PLMTotalMoles(t),t,PLMOtherlevel(t)./PLMTotalMoles(t),'LineWidth',2), title('PLM'),legend('O2','CO2','N2','Vapor','Other'), grid on, xlabel('Time (hours)'), ylabel('Molar Fraction')
% subplot(2,3,4), plot(t,LoftO2level(t)./LoftTotalMoles,t,LoftCO2level./LoftTotalMoles,t,LoftN2level./LoftTotalMoles,t,LoftVaporlevel./LoftTotalMoles,t,LoftOtherlevel./LoftTotalMoles,'LineWidth',2), title('Loft'),legend('O2','CO2','N2','Vapor','Other'), grid on, xlabel('Time (hours)'), ylabel('Molar Fraction')
% subplot(2,3,5), plot(t,SuitlockO2level(t)./SuitlockTotalMoles,t,SuitlockCO2level./SuitlockTotalMoles,t,SuitlockN2level./SuitlockTotalMoles,t,SuitlockVaporlevel./SuitlockTotalMoles,t,SuitlockOtherlevel./SuitlockTotalMoles,'LineWidth',2), title('Suitlock'),legend('O2','CO2','N2','Vapor','Other'), grid on, xlabel('Time (hours)'), ylabel('Molar Fraction')

% Partial Pressures
% figure, 
% plot(t,LabO2level(t)./LabTotalMoles(t).*LabPressure(t),t,LabCO2level(t)./LabTotalMoles(t).*LabPressure(t),t,LabN2level(t)./LabTotalMoles(t).*LabPressure(t),t,LabVaporlevel(t)./LabTotalMoles(t).*LabPressure(t),t,LabOtherlevel(t)./LabTotalMoles(t).*LabPressure(t),'LineWidth',2), title('Lab: Partial Pressures Over Time'),legend('O2','CO2','N2','Vapor','Other'), grid on, xlabel('Time (hours)'), ylabel('Partial Pressure (kPa)')
% subplot(2,3,1), plot(t,LabO2level(t)./LabTotalMoles(t).*LabPressure(t),t,LabCO2level(t)./LabTotalMoles(t).*LabPressure(t),t,LabN2level(t)./LabTotalMoles(t).*LabPressure(t),t,LabVaporlevel(t)./LabTotalMoles(t).*LabPressure(t),t,LabOtherlevel(t)./LabTotalMoles(t).*LabPressure(t),'LineWidth',2), title('Lab'),legend('O2','CO2','N2','Vapor','Other'), grid on, xlabel('Time (hours)'), ylabel('Partial Pressure')
% subplot(2,3,2), plot(t,PCMO2level(t)./PCMTotalMoles(t).*PCMPressure(t),t,PCMCO2level(t)./PCMTotalMoles(t).*PCMPressure(t),t,PCMN2level(t)./PCMTotalMoles(t).*PCMPressure(t),t,PCMVaporlevel(t)./PCMTotalMoles(t).*PCMPressure(t),t,PCMOtherlevel(t)./PCMTotalMoles(t).*PCMPressure(t),'LineWidth',2), title('PCM'),legend('O2','CO2','N2','Vapor','Other'), grid on, xlabel('Time (hours)'), ylabel('Partial Pressure')
% subplot(2,3,3), plot(t,PLMO2level(t)./PLMTotalMoles(t).*PLMPressure(t),t,PLMCO2level(t)./PLMTotalMoles(t).*PLMPressure(t),t,PLMN2level(t)./PLMTotalMoles(t).*PLMPressure(t),t,PLMVaporlevel(t)./PLMTotalMoles(t).*PLMPressure(t),t,PLMOtherlevel(t)./PLMTotalMoles(t).*PLMPressure(t),'LineWidth',2), title('PLM'),legend('O2','CO2','N2','Vapor','Other'), grid on, xlabel('Time (hours)'), ylabel('Partial Pressure')
% subplot(2,3,4), plot(t,LoftO2level(t)./LoftTotalMoles(t).*LoftPressure(t),t,LoftCO2level(t)./LoftTotalMoles(t).*LoftPressure(t),t,LoftN2level(t)./LoftTotalMoles(t).*LoftPressure(t),t,LoftVaporlevel(t)./LoftTotalMoles(t).*LoftPressure(t),t,LoftOtherlevel(t)./LoftTotalMoles(t).*LoftPressure(t),'LineWidth',2), title('Loft'),legend('O2','CO2','N2','Vapor','Other'), grid on, xlabel('Time (hours)'), ylabel('Partial Pressure')
% subplot(2,3,5), plot(t,SuitlockO2level(t)./SuitlockTotalMoles(t).*SuitlockPressure(t),t,SuitlockCO2level(t)./SuitlockTotalMoles(t).*SuitlockPressure(t),t,SuitlockN2level(t)./SuitlockTotalMoles(t).*SuitlockPressure(t),t,SuitlockVaporlevel(t)./SuitlockTotalMoles(t).*SuitlockPressure(t),t,SuitlockOtherlevel(t)./SuitlockTotalMoles(t).*SuitlockPressure(t),'LineWidth',2), title('Suitlock'),legend('O2','CO2','N2','Vapor','Other'), grid on, xlabel('Time (hours)'), ylabel('Partial Pressure')

% Airlock ppCO2
% figure, plot(t,SuitlockCO2level./SuitlockTotalMoles.*SuitlockPressure,'LineWidth',2),grid on, title('Airlock ppCO2')

% % O2 molar fraction
% figure, 
% subplot(2,3,1), plot(t,LabO2level(t)./LabTotalMoles(t),'LineWidth',2), title('Lab'), grid on, xlabel('Time (hours)'), ylabel('O2 Molar Fraction')
% subplot(2,3,2), plot(t,PCMO2level(t)./PCMTotalMoles(t),'LineWidth',2), title('PCM'), grid on, xlabel('Time (hours)'), ylabel('O2 Molar Fraction')
% subplot(2,3,3), plot(t,PLMO2level(t)./PLMTotalMoles(t),'LineWidth',2), title('PLM'), grid on, xlabel('Time (hours)'), ylabel('O2 Molar Fraction')
% subplot(2,3,4), plot(t,LoftO2level(t)./LoftTotalMoles(t),'LineWidth',2), title('Loft'), grid on, xlabel('Time (hours)'), ylabel('O2 Molar Fraction')
% subplot(2,3,5), plot(t,SuitlockO2level(t)./SuitlockTotalMoles(t),'LineWidth',2), title('Suitlock'), grid on, xlabel('Time (hours)'), ylabel('O2 Molar Fraction')

% O2 Partial Pressure
% figure, 
% plot(t,LabO2level(t)./data.LabTotalMoles(t).*LabPressure(t),'LineWidth',2), title('Lab: O_2 Partial Pressure Over Time'), grid on, xlabel('Time (hours)'), ylabel('Partial Pressure (kPa)'), ylim([0 19]), hline = refline(0,15.168); hline.Color = 'r';
% subplot(2,3,1), plot(t,LabO2level(t)./LabTotalMoles(t).*LabPressure(t),'LineWidth',2), title('Lab'), grid on, xlabel('Time (hours)'), ylabel('O2 Partial Pressure')
% subplot(2,3,2), plot(t,PCMO2level(t)./PCMTotalMoles(t).*PCMPressure(t),'LineWidth',2), title('PCM'), grid on, xlabel('Time (hours)'), ylabel('O2 Partial Pressure')
% subplot(2,3,3), plot(t,PLMO2level(t)./PLMTotalMoles(t).*PLMPressure(t),'LineWidth',2), title('PLM'), grid on, xlabel('Time (hours)'), ylabel('O2 Partial Pressure')
% subplot(2,3,4), plot(t,LoftO2level(t)./LoftTotalMoles(t).*PLMPressure(t),'LineWidth',2), title('Loft'), grid on, xlabel('Time (hours)'), ylabel('O2 Partial Pressure')
% subplot(2,3,5), plot(t,SuitlockO2level(t)./SuitlockTotalMoles(t).*PLMPressure(t),'LineWidth',2), title('Suitlock'), grid on, xlabel('Time (hours)'), ylabel('O2 Partial Pressure')
% o2pphenry = LabO2level(t)./LabTotalMoles(t).*LabPressure(t);
xt = transpose(t);
% yo2pp = xlsread('Nominal.xlsx','o2pp');
% figure,
% plot(xt,yo2pp(1:length(xt),:),'LineWidth',2), title('Lab: O_2 Partial Pressure with Failures'),legend('Nominal','Failure 1','Failure 2'), grid on, xlabel('Time (hours)'), ylabel('Partial Pressure (kPa)'), ylim([0 19]), hline = refline(0,15.168); hline.Color = 'r';
% 
% yo2store = xlsread('Nominal.xlsx','o2store');
% figure,
% plot(xt,yo2store(1:length(xt),:),'LineWidth',2), title('Lab: O_2 Store Levels with Failures'),legend('Nominal','Failure 1','Failure 2'), grid on, xlabel('Time (hours)'), ylabel('Partial Pressure (kPa)'), ylim([0 2.2e4]), hline = refline(0,1); hline.Color = 'r';

% ytotalpressure = xlsread('Nominal.xlsx','totalpressure');
% figure,
% % plot(xt,ytotalpressure,'LineWidth',2), title('Lab: Total Pressure with Failures'),legend('Nominal','Failure 1','Failure 2'), grid on, xlabel('Time (hours)'), ylabel('Partial Pressure (kPa)'), ylim([0 58]), hline = ylim([0 58]); hline.Color = 'r';
% plot(xt,ytotalpressure(1:length(xt),:),'LineWidth',2), title('Lab: Total Pressure with Failures'),legend('Nominal','Failure 1','Failure 2'), grid on, xlabel('Time (hours)'), ylabel('Pressure (kPa)'), ylim([0 58]), hline = refline(0,20.7); hline.Color = 'r'; 

% % CO2 molar fraction
% figure, 
% subplot(2,3,1), plot(t,LabCO2level(t)./LabTotalMoles(t),'LineWidth',2), title('Lab'), grid on, xlabel('Time (hours)'), ylabel('CO2 Molar Fraction')
% subplot(2,3,2), plot(t,PCMCO2level(t)./PCMTotalMoles(t),'LineWidth',2), title('PCM'), grid on, xlabel('Time (hours)'), ylabel('CO2 Molar Fraction')
% subplot(2,3,3), plot(t,PLMCO2level(t)./PLMTotalMoles(t),'LineWidth',2), title('PLM'), grid on, xlabel('Time (hours)'), ylabel('CO2 Molar Fraction')
% subplot(2,3,4), plot(t,LoftCO2level(t)./LoftTotalMoles(t),'LineWidth',2), title('Loft'), grid on, xlabel('Time (hours)'), ylabel('CO2 Molar Fraction')
% subplot(2,3,5), plot(t,SuitlockCO2level(t)./SuitlockTotalMoles(t),'LineWidth',2), title('Suitlock'), grid on, xlabel('Time (hours)'), ylabel('CO2 Molar Fraction')


% CO2 Partial Pressure
% figure, 
% plot(t,LabCO2level(t)./LabTotalMoles(t).*LabPressure(t),'LineWidth',2), title('Lab: CO_2 Partial Pressure Over Time'), grid on, xlabel('Time (hours)'), ylabel('Partial Pressure (kPa)'), ylim([0 1]), hline = refline(0,0.482); hline.Color = 'r';
% subplot(2,3,1), plot(t,LabCO2level(t)./LabTotalMoles(t).*LabPressure(t),'LineWidth',2), title('Lab'), grid on, xlabel('Time (hours)'), ylabel('CO2 Partial Pressure')
% subplot(2,3,2), plot(t,PCMCO2level(t)./PCMTotalMoles(t).*PCMPressure(t),'LineWidth',2), title('PCM'), grid on, xlabel('Time (hours)'), ylabel('CO2 Partial Pressure')
% subplot(2,3,3), plot(t,PLMCO2level(t)./PLMTotalMoles(t).*PLMPressure(t),'LineWidth',2), title('PLM'), grid on, xlabel('Time (hours)'), ylabel('CO2 Partial Pressure')
% subplot(2,3,4), plot(t,LoftCO2level(t)./LoftTotalMoles(t).*LoftPressure(t),'LineWidth',2), title('Loft'), grid on, xlabel('Time (hours)'), ylabel('CO2 Partial Pressure')
% subplot(2,3,5), plot(t,SuitlockCO2level(t)./SuitlockTotalMoles(t).*SuitlockPressure(t),'LineWidth',2), title('Suitlock'), grid on, xlabel('Time (hours)'), ylabel('CO2 Partial Pressure')

% subplot(2,2,3),line([1 length(t)],0.482633011*ones(1,2),'LineWidth',2,'Color','r')

% figure, 
% plot(t,PCMCO2level(t)./PCMTotalMoles(t).*PCMPressure(t),'LineWidth',2), 
% title('PCM CO2 Levels with CDRA Failure'), grid on, xlabel('Mission Elapsed Time (hours)'), ylabel('CO2 Partial Pressure')
% line([1 length(t)],0.482633011*ones(1,2),'LineWidth',2,'Color','r')

% % N2 Partial Pressure
% figure, 
% subplot(2,2,1), plot(t,LabN2level(t)./LabTotalMoles(t).*LabPressure(t),'LineWidth',2), title('Inflatable 1'), grid on, xlabel('Time (hours)'), ylabel('N2 Partial Pressure')
% subplot(2,2,2), plot(t,PCMN2level(t)./PCMTotalMoles(t).*PCMPressure(t),'LineWidth',2), title('Living Unit 1'), grid on, xlabel('Time (hours)'), ylabel('N2 Partial Pressure')
% subplot(2,2,3), plot(t,lifeSupportUnitN2level(t)./lifeSupportUnitTotalMoles(t).*lifeSupportUnitPressure(t),'LineWidth',2), title('Life Support Unit 1'), grid on, xlabel('Time (hours)'), ylabel('N2 Partial Pressure')
% subplot(2,2,4), plot(t,PLMN2level(t)./PLMTotalMoles(t).*PLMPressure(t),'LineWidth',2), title('Cargo Unit 1'), grid on, xlabel('Time (hours)'), ylabel('N2 Partial Pressure')

% % Vapor Partial Pressure
% figure, 
% subplot(2,3,1), plot(t,LabVaporlevel(t)./LabTotalMoles(t).*LabPressure(t),'LineWidth',2), title('Lab'), grid on, xlabel('Time (hours)'), ylabel('Vapor Partial Pressure')
% subplot(2,3,2), plot(t,PCMVaporlevel(t)./PCMTotalMoles(t).*PCMPressure(t),'LineWidth',2), title('PCM'), grid on, xlabel('Time (hours)'), ylabel('Vapor Partial Pressure')
% subplot(2,3,3), plot(t,PLMVaporlevel(t)./PLMTotalMoles(t).*PLMPressure(t),'LineWidth',2), title('PLM'), grid on, xlabel('Time (hours)'), ylabel('Vapor Partial Pressure')
% subplot(2,3,4), plot(t,LoftVaporlevel(t)./LoftTotalMoles(t).*LoftPressure(t),'LineWidth',2), title('Loft'), grid on, xlabel('Time (hours)'), ylabel('Vapor Partial Pressure')
% subplot(2,3,5), plot(t,SuitlockVaporlevel(t)./SuitlockTotalMoles(t).*SuitlockPressure(t),'LineWidth',2), title('Suitlock'), grid on, xlabel('Time (hours)'), ylabel('Vapor Partial Pressure')

% % Vapor Molar Fraction
% figure, 
% subplot(2,3,1), plot(t,LabVaporlevel(t)./LabTotalMoles(t),'LineWidth',2), title('Lab'), grid on, xlabel('Time (hours)'), ylabel('Vapor Molar Fraction')
% subplot(2,3,2), plot(t,PCMVaporlevel(t)./PCMTotalMoles(t),'LineWidth',2), title('PCM'), grid on, xlabel('Time (hours)'), ylabel('Vapor Molar Fraction')
% subplot(2,3,3), plot(t,PLMVaporlevel(t)./PLMTotalMoles(t),'LineWidth',2), title('PLM'), grid on, xlabel('Time (hours)'), ylabel('Vapor Molar Fraction')
% subplot(2,3,4), plot(t,LoftVaporlevel(t)./LoftTotalMoles(t),'LineWidth',2), title('Loft'), grid on, xlabel('Time (hours)'), ylabel('Vapor Molar Fraction')
% subplot(2,3,5), plot(t,SuitlockVaporlevel(t)./SuitlockTotalMoles(t),'LineWidth',2), title('Suitlock'), grid on, xlabel('Time (hours)'), ylabel('Vapor Molar Fraction')

% Total Pressure
% figure, 
% plot(t,LabPressure(t),'LineWidth',2), title('Lab: Total Pressure Over Time'), grid on, xlabel('Time (hours)'), ylabel('Pressure (kPa)'), ylim([0 58]), hline = refline(0,20.7); hline.Color = 'r'; 
% subplot(2,3,1), plot(t,LabPressure(t),'LineWidth',2), title('Lab'), grid on, xlabel('Time (hours)'), ylabel('Total Pressure')
% subplot(2,3,2), plot(t,PCMPressure(t),'LineWidth',2), title('PCM'), grid on, xlabel('Time (hours)'), ylabel('Total Pressure')
% subplot(2,3,3), plot(t,PLMPressure(t),'LineWidth',2), title('PLM'), grid on, xlabel('Time (hours)'), ylabel('Total Pressure')
% subplot(2,3,4), plot(t,LoftPressure(t),'LineWidth',2), title('Loft'), grid on, xlabel('Time (hours)'), ylabel('Total Pressure')
% subplot(2,3,5), plot(t,SuitlockPressure(t),'LineWidth',2), title('Suitlock'), grid on, xlabel('Time (hours)'), ylabel('Total Pressure')

% % Environmental N2 Store plots
% figure, 
% subplot(2,2,1), plot(1:simtime,crewN2level,'LineWidth',2), title('Crew Quarters Environmental N2 Level'), grid on
% subplot(2,2,2), plot(1:simtime,lifeSupportUnitN2level,'LineWidth',2), title('Galley Environmental N2 Level'), grid on
% subplot(2,2,3), plot(1:simtime,labsN2level,'LineWidth',2), title('Labs Environmental N2 Level'), grid on
% subplot(2,2,4), plot(1:simtime,maintN2level,'LineWidth',2), title('Maintenance Environmental N2 Level'), grid on

% i = i-1;
% figure, plot(1:(i-1),crewO2level(1:(i-1)),1:(i-1),crewCO2level(1:(i-1)),...
%     1:(i-1),crewN2level(1:(i-1)),1:(i-1),crewOtherlevel(1:(i-1)),1:(i-1),crewVaporlevel(1:(i-1)),'LineWidth',2),...
%    legend('O_2','CO_2','N_2','Other','Vapor'), grid on
% title('MATLAB Crew Quarters')
% 
% figure, plot(1:(i-1),maintO2level(1:(i-1)),1:(i-1),maintCO2level(1:(i-1)),...
%     1:(i-1),maintN2level(1:(i-1)),1:(i-1),maintOtherlevel(1:(i-1)),1:(i-1),maintVaporlevel(1:(i-1)),'LineWidth',2),...
%    legend('O_2','CO_2','N_2','Other','Vapor'), grid on
% title('MATLAB Maintenance Module')
% 
% figure, plot(1:(i-1),labsO2level(1:(i-1)),1:(i-1),labsCO2level(1:(i-1)),...
%     1:(i-1),labsN2level(1:(i-1)),1:(i-1),labsOtherlevel(1:(i-1)),1:(i-1),labsVaporlevel(1:(i-1)),'LineWidth',2),...
%    legend('O_2','CO_2','N_2','Other','Vapor'), grid on
% title('MATLAB Labs Module')
% 
% figure, plot(1:(i-1),galleyO2level(1:(i-1)),1:(i-1),galleyCO2level(1:(i-1)),...
%     1:(i-1),lifeSupportUnitN2level(1:(i-1)),1:(i-1),lifeSupportUnitOtherlevel(1:(i-1)),1:(i-1),lifeSupportUnitVaporlevel(1:(i-1)),'LineWidth',2),...
%    legend('O_2','CO_2','N_2','Other','Vapor'), grid on
% title('MATLAB Galley Module')

% figure, plot(maintN2level,'LineWidth',2),grid on

% figure, plot(1:length(crewO2level),crewO2level), grid on
% figure, plot(1:length(N2level),N2level), grid on
% figure, plot(1:length(crewCO2level),crewCO2level), grid on
% figure, plot(1:(i-1),H2level(1:(i-1)),'LineWidth',2), title('MATLAB H_2 Store'), grid on
% figure, plot(1:length(H2level),H2level), grid on
% figure, plot(1:length(CH4level),CH4level), grid on
% figure, plot(1:length(crewVaporlevel),crewVaporlevel,'LineWidth',2), grid on, title('MATLAB Crew Quarters Vapor Level')
% figure, plot(1:(i-1),maintVaporlevel(1:(i-1)),'LineWidth',2), grid on, title('MATLAB Maintenance Vapor Level')
% % % figure, plot(1:(i-1),H2Ostorelevel(1:(i-1)),'LineWidth',2), title('MATLAB Potable Water Store'), grid on
% figure, plot(1:(i-1),DirtyH2Ostorelevel(1:(i-1)),'LineWidth',2), title('MATLAB Dirty Water Store'), grid on
% figure, plot(1:length(DirtyH2Ostorelevel),DirtyH2Ostorelevel), grid on
% figure, plot(1:length(FoodStoreLevel),FoodStoreLevel), grid on
% figure, plot(1:length(DryWasteStoreLevel),DryWasteStoreLevel), grid on
% figure, plot(1:(i-1),DryWasteStoreLevel(1:(i-1)),'LineWidth',2), title('MATLAB Dry Waste Store'), grid on
% figure, plot(1:(i-1),GreyH2Ostorelevel(1:(i-1)),'LineWidth',2), title('MATLAB Grey Water Store'), grid on


% figure, 
% plot(1:(i-1),o2storelevel(1:(i-1)),'LineWidth',2), title('O_2 Store Levels (3 Tanks)'),xlabel('Time (hours)'), ylabel('Mass (kg)'), grid on, ylim([0 2.2e4])
% % henry = xlsread('Trial Resiliency Plot.xlsx',2,'A1:A500');
% % figure, plot(1:500,henry,'LineWidth',2), title('O_2 Store Levels (3 Tanks)'),xlabel('Time (hours)'), ylabel('Mass (kg)'), grid on, ylim([0 2.2e4]), hline = refline(0,20938); hline.Color = 'r';


% figure, plot(1:(i-1),CH4Storelevel(1:(i-1)),'LineWidth',2), title('MATLAB Methane Store'), grid on
% figure, plot(1:(i-1),consumedWaterBuffer(1:(i-1)),'LineWidth',2), title('MATLAB Consumed Water Buffer'), grid on
% figure, plot(1:length(GreyH2Ostorelevel),GreyH2Ostorelevel), grid on
% figure, plot(1:(i-1),FoodStoreLevel(1:(i-1)),'LineWidth',2), title('MATLAB Food Store'), grid on
% figure, plot(1:length(CO2conc),CO2conc), grid on
% figure, plot(1:length(O2conc),O2conc), grid on
% figure, plot(1:length(vaporconc),vaporconc), grid on
% figure, plot(1:length(CO2concMain),CO2concMain), grid on
% figure, plot(1:length(O2concMain),O2concMain), grid on
% figure, plot(1:length(O2levelMain),O2levelMain), grid on
% figure, plot(1:length(pres),pres), grid on
% figure, plot(1:length(CO2storelevel),CO2storelevel), grid on
% figure, plot(1:length(powerlevel),powerlevel), grid on
% figure, plot(1:length(co2storelevel),co2storelevel, title('MATLAB CO_2 Store')), grid on
% figure, plot(1:(i-1),CO2Storelevel(1:(i-1)),'LineWidth',2), title('MATLAB CO_2 Store'), grid on
% figure, plot(1:length(intensity),intensity)


%% Plot Total Oxygen Consumed
if(any(strcmp(plotCommands,'crewO2')))
    figure;
    c = categorical({crew.astro1.Name,crew.astro2.Name,crew.astro3.Name,crew.astro4.Name});
    bar(c,[crew.astro1.O2Total,crew.astro2.O2Total,crew.astro3.O2Total,crew.astro4.O2Total].*0.032./(length(t)/24))
    title('Oxygen Consumed')
    ylabel('kg/Day')
    xlabel('Crew Member')
    cloudplot
end
%% Plot Total Calories Consumed
if(any(strcmp(plotCommands,'crewCalories')))
    figure;
    c = categorical({crew.astro1.Name,crew.astro2.Name,crew.astro3.Name,crew.astro4.Name});
    bar(c,[crew.astro1.caloriesTotal,crew.astro2.caloriesTotal,crew.astro3.caloriesTotal,crew.astro4.caloriesTotal]./(length(t)/24))
    title('Calories Consumed')
    ylabel('kCal/Day')
    xlabel('Crew Member')
    cloudplot
end
%% Plot Crew Activity Breakdown
if(any(strcmp(plotCommands,'crewActivity')))
    figure;
    c1 = [8 2 1 8].*countcats(categorical(arrayfun(@(x)(x.Name),crew.astro1.Schedule,'UniformOutput',false)));
    c2 = [8 2 1 8].*countcats(categorical(arrayfun(@(x)(x.Name),crew.astro2.Schedule,'UniformOutput',false)));
    c3 = [8 2 1 8].*countcats(categorical(arrayfun(@(x)(x.Name),crew.astro3.Schedule,'UniformOutput',false)));
    c4 = [8 2 1 8].*countcats(categorical(arrayfun(@(x)(x.Name),crew.astro4.Schedule,'UniformOutput',false)));

    c = categorical({crew.astro1.Name,crew.astro2.Name,crew.astro3.Name,crew.astro4.Name});
    bar(c,[c1;c2;c3;c4],'stacked')
    legend(categories(categorical(arrayfun(@(x)(x.Name),crew.astro1.Schedule,'UniformOutput',false))),'location','northeastoutside')
    title('Activity Breakdown')
    ylabel('Hours')
    xlabel('Crew Member')
    cloudplot
end
%% Plot OGS Output Frequency
if(any(strcmp(plotCommands,'OGSFrequency')))
    figure;
    c = categorical(habnetDataStructure.ogsO2Produced,2.3*(0:4)/24 * 1e3 / (2*15.999),{'0%','25%','50%','75%','100%'});
%     print(habnetDataStructure.ogsO2Produced)
    b = bar(c);%[countcats(c),zeros(1,5-length(countcats(c)))]);%,{'0%','25%','50%','75%','100%'});
    xlabel('Production Level')
    ylabel('Hours of Performance')
    title('OGS Performance Breakdown')
    xticklabels({'0%','25%','50%','75%','100%'})
    text(b.XData-0.15,b.YData+70,arrayfun(@(x)(num2str(x)),b.YData,'UniformOutput',false))
    cloudplot
end