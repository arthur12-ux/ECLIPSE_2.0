clear
clc

number = 4; % Example number
[part1, part2] = splitNumber(number);
disp(['Part 1: ', num2str(part1)]);
disp(['Part 2: ', num2str(part2)]);



function [part1, part2] = splitNumber(number)
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


