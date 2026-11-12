%%
clear 
close all
clc

T = readtable('DoE_DELOS_Final_240404.xlsx');

numRows = height(T);
newData = zeros(numRows, 9); 
Variables = {'Min O2 (kPa)', 'Max CO2 (kPa)', 'Min Hab Pressure (kPa)', 'Max Hab Pressure (kPa)', 'Min O2 Store (kg)', 'Min Potable Water Store (kg)', 'Final Potable Water Store (kg)', 'Total Food Required (kg)', 'Days Till Failure (Days)','Error_Message'};
errorMessages = strings(numRows, 1);
T_new = [array2table(newData, 'VariableNames', Variables(1:end-1)), table(errorMessages, 'VariableNames', {'Error_Message'})];

T_combined = [T, T_new];


for rowIndex = 1:height(T)

    disp("Case:", rowIndex)

    current_case = table2array(T(rowIndex,:));    
    if current_case(12) == 1
        functionName = ['DELOS_Habnet_', num2str(current_case(2))];
        handle = str2func(functionName);
        
        Results = handle(current_case);
        
        startIndexForNewCols = width(T) + 1;
        for k = startIndexForNewCols:(width(T_combined)-1) 
            T_combined{rowIndex, k} = Results{k - startIndexForNewCols + 1};
        end
        
        T_combined.Error_Message(rowIndex) = string(Results{end}); 
    
    else
        [Hab1Crew, Hab2Crew] = splitCrew(current_case(2));
       
        current_case_hab1 = current_case;
        current_case_hab1(2) = Hab1Crew; 
        current_case_hab1(6) = current_case(6)*0.5;
        current_case_hab1(7) = current_case(7)*0.5;

        current_case_hab2 = current_case;
        current_case_hab2(2) = Hab2Crew; 
        current_case_hab2(6) = current_case(6)*0.5;
        current_case_hab2(7) = current_case(7)*0.5;
        
        functionNameHab1 = ['DELOS_Habnet_', num2str(Hab1Crew)];
        functionNameHab2 = ['DELOS_Habnet_', num2str(Hab2Crew)];

        handleHab1 = str2func(functionNameHab1);
        handleHab2 = str2func(functionNameHab2);

        ResultsHab1 = handleHab1(current_case_hab1);
        ResultsHab2 = handleHab2(current_case_hab2);

        Results = cell(1, 9);
        Results{1} = min([ResultsHab1{1}, ResultsHab2{1}]); % Min O2 (kPa)
        Results{2} = max([ResultsHab1{2}, ResultsHab2{2}]); % Max CO2 (kPa)
        Results{3} = min([ResultsHab1{3}, ResultsHab2{3}]); % Min Pressure (kPa)
        Results{4} = max([ResultsHab1{4}, ResultsHab2{4}]); % Max Pressure (kPa)
        Results{5} = min([ResultsHab1{5}, ResultsHab2{5}]); % Min O2 store (kg)
        Results{6} = min([ResultsHab1{6}, ResultsHab2{6}]); % Min Total Water (kg)
        Results{7} = min([ResultsHab1{7}, ResultsHab2{7}]); % Min End Water (kg)
        Results{8} = ResultsHab1{8} + ResultsHab2{8};       % Total food (kg)
        Results{9} = min([ResultsHab1{9}, ResultsHab2{9}]); % Min mission duration (Days)

        if ischar(ResultsHab1{10}) && ~isempty(ResultsHab1{10}) && ischar(ResultsHab2{10}) && ~isempty(ResultsHab2{10}) % If both have error messages
            Results{10} = strcat("Hab 1 error: ", ResultsHab1{10}, ", Hab 2 error: ", ResultsHab2{10});
        elseif ischar(ResultsHab1{10}) && ~isempty(ResultsHab1{10})
            % If only Hab 1 has an error message
            Results{10} = strcat("Hab 1 error: ", ResultsHab1{10});
        elseif ischar(ResultsHab2{10}) && ~isempty(ResultsHab2{10})
            % If only Hab 2 has an error message
            Results{10} = strcat("Hab 2 error: ", ResultsHab2{10});
        else
            % No errors
            Results{10} = "";
        end

        startIndexForNewCols = width(T) + 1;
        for k = startIndexForNewCols:(width(T_combined)-1) 
            T_combined{rowIndex, k} = Results{k - startIndexForNewCols + 1};
        end

        T_combined.Error_Message(rowIndex) = string(Results{end});

    end


%Results = [min(O2Results), max(CO2Results), min(HabPressureResults), max(HabPressureResults), min(data.potablewaterstorelevel), data.potablewaterstorelevel(end), CarriedTotalMass];

end 

%writetable(T_combined, 'DoE_Results_Test.csv')

%% FUNCTIONs %%
function [part1, part2] = splitCrew(number)
    if number < 4
        error('Number must be at least 4 to split into parts greater than or equal to 2.');
    end
    
    % Attempt to divide the number evenly
    part1 = ceil(number / 2);
    part2 = number - part1;
    
    % Adjust if either part is less than 2 (should not happen with proper input)
    if part1 < 2
        part1 = 2;
    end
    if part2 < 2
        part2 = 2;
    end
end
