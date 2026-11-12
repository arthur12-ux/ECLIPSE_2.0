function cloudplot( usefig )
%CLOUDPLOT is used to coordinate all cloud-related plots
%   Created by Dominic Barone
% https://www.mathworks.com/matlabcentral/fileexchange/47221-number-to-words


if nargin < 1
	usefig = gcf;
end

% Figure Specific Options
FigOpts.Color = 'none';			% transparent Background

% Axes Specific Options
%AxesOpts.FontName = 'Courier';
AxesOpts.FontSize = 14;
% AxesOpts.FontUnits = 'normalized';
AxesOpts.FontWeight = 'Bold';
AxesOpts.LineWidth = 2;
AxesOpts.Box = 'on';
AxesOpts.Color = 'none';
% AxesOpts.XColor = [.65 .65 .65];
% AxesOpts.YColor = [.65 .65 .65];
AxesOpts.XColor = [1 1 1];
AxesOpts.YColor = [1 1 1];

% Plot Object Options
PlotOpts.Line.One.LineWidth = 2;
PlotOpts.Line.One.Color = [237/255 172/255 9/255]; %gold
PlotOpts.Line.Two.LineWidth = 2;
PlotOpts.Line.Two.Color = [.5 .5 .5]; %gray
PlotOpts.Line.Three.LineWidth = 2;
PlotOpts.Line.Three.Color = [175/255 202/255 235/255]; %light blue
PlotOpts.Line.FourOrMore.LineWidth = 2;

PlotOpts.Bar.One.EdgeColor = 'none';
PlotOpts.Bar.One.FaceColor = [237/255 172/255 9/255]; %gold
PlotOpts.Bar.One.FaceAlpha = 1;
PlotOpts.Bar.Two.EdgeColor = 'none';
PlotOpts.Bar.Two.FaceColor = [.5 .5 .5]; %gray
PlotOpts.Bar.Two.FaceAlpha = 1;
PlotOpts.Bar.Three.EdgeColor = 'none';
PlotOpts.Bar.Three.FaceColor = [175/255 202/255 235/255]; %light blue
PlotOpts.Bar.Three.FaceAlpha = 1;
PlotOpts.Bar.FourOrMore.EdgeColor = 'none';
PlotOpts.Bar.FourOrMore.FaceAlpha = 1;

PlotOpts.Scatter.One.CData = [237/255 172/255 9/255]; %gold
PlotOpts.Scatter.Two.CData = [.5 .5 .5]; %gray
PlotOpts.Scatter.Three.CData = [175/255 202/255 235/255]; %light blue
PlotOpts.Scatter.FourOrMore.MarkerFaceAlpha = 1;

% Plot Text Options (Not Axes Labels)
TextOpts.FontSize = 14;
% TextOpts.FontUnits = 'normalized';
TextOpts.FontWeight = 'Bold';
TextOpts.Color = 'w';
% TextOpts.XColor = 'w';
% TextOpts.YColor = 'w';

% Set Figure Options
set(usefig,FigOpts);

fig_axes = get(usefig,'children');

for n = 1:length(fig_axes)
	useaxes = fig_axes(n);
	
    % Set Legend Options
    if contains(get(useaxes,'type'),'legend')
        useaxes.FontSize = TextOpts.FontSize;
        useaxes.TextColor = TextOpts.Color;
        useaxes.Color = AxesOpts.Color;
        useaxes.EdgeColor = 'none';
    elseif contains(get(useaxes,'type'),'colorbar')
        useaxes.FontSize = TextOpts.FontSize;
        useaxes.Color = AxesOpts.Color;
        useaxes.EdgeColor = 'none';
    elseif contains(get(useaxes,'type'),'axes')
	% Set Axes Options
	set(useaxes,AxesOpts);

	% Reset title and labels to new options
	title(useaxes,get(get(useaxes,'Title'),'string'),'Color',[1 1 1],'FontSize',TextOpts.FontSize+2);
 	xlabel(useaxes,get(get(useaxes,'Xlabel'),'string'));
 	ylabel(useaxes,get(get(useaxes,'Ylabel'),'string'));
 	zlabel(useaxes,get(get(useaxes,'Zlabel'),'string'));
	
	
	% Go through all of the plot objects and set properties
	child = get(useaxes,'children');
	for i=1:length(child)
        if i == 1
		switch get(child(i),'type')
			case 'text'
				set(child(i),TextOpts);
			case 'line'
                if i < 4
                    set(child(i),PlotOpts.Line.(num2words(i,'case','sentence')));
                else
                    set(child(i),PlotOpts.Line.FourOrMore);
                end
            case 'bar'
                if i < 4
                    set(child(i),PlotOpts.Bar.(num2words(i,'case','sentence')));
                else
                    set(child(i),PlotOpts.Bar.FourOrMore);
                end
            case 'histogram'
                if i < 4
                    set(child(i),PlotOpts.Bar.(num2words(i,'case','sentence')));
                else
                    set(child(i),PlotOpts.Bar.FourOrMore);
                end
            case 'scatter'
                if i < 4
                    set(child(i),PlotOpts.Scatter.(num2words(i,'case','sentence')));
                else
                    set(child(i),PlotOpts.Scatter.FourOrMore);
                end
            case 'hggroup'
                metachild = get(child(i),'children');
                for j = 1:length(metachild)
                    switch get(metachild(j),'tag')
                        case 'Box'
                            set(metachild(j),'Color','white')
                        case 'Lower Adjacent Value'
                            set(metachild(j),'Color','white')                        
                        case 'Lower Whisker'
                            set(metachild(j),'Color','white')                            
                        case 'Median'
                            set(metachild(j),'Color',[237/255 172/255 9/255])                            
                        case 'Outliers'
                            set(metachild(j),'MarkerEdgeColor','white')                            
                        case 'Upper Adjacent Value'
                            set(metachild(j),'Color',[.4 .4 .4])                            
                        case 'Upper Whisker'
                            set(metachild(j),'Color','white')
                        case 'Whisker'
                            set(metachild(j),'Color','white')
                        case 'MedianInner'
                            set(metachild(j),'MarkerEdgeColor','white')
                        case 'MedianOuter'
                            set(metachild(j),'MarkerEdgeColor','white')
                    end
                end
        end
        else
        switch get(child(i),'type')
			case 'text'
				set(child(i),TextOpts);
			case 'line'
                if i < 4
                    set(child(i),PlotOpts.Line.(num2words(i,'case','sentence')));
                else
                    set(child(i),PlotOpts.Line.FourOrMore);
                end
            case 'bar'
                if i < 4
                    set(child(i),PlotOpts.Bar.(num2words(i,'case','sentence')));
                    child(i).EdgeColor = 'none';
                else
                    set(child(i),PlotOpts.Bar.FourOrMore);
                    child(i).EdgeColor = 'none';
                end
            case 'scatter'
                if i < 4
                    set(child(i),PlotOpts.Scatter.(num2words(i,'case','sentence')));
                else
                    set(child(i),PlotOpts.Scatter.FourOrMore);
                end
            case 'hggroup'
                metachild = get(child(i),'children');
                for j = 1:length(metachild)
                    switch get(metachild(j),'tag')
                        case 'Box'
                            set(metachild(j),'Color','white')
                        case 'Lower Adjacent Value'
                            set(metachild(j),'Color','white')                        
                        case 'Lower Whisker'
                            set(metachild(j),'Color','white')                            
                        case 'Median'
                            set(metachild(j),'Color',[237/255 172/255 9/255])                            
                        case 'Outliers'
                            set(metachild(j),'MarkerEdgeColor','white')                            
                        case 'Upper Adjacent Value'
                            set(metachild(j),'Color',[.4 .4 .4])                            
                        case 'Upper Whisker'
                            set(metachild(j),'Color','white')
                        case 'Whisker'
                            set(metachild(j),'Color','white')
                        case 'MedianInner'
                            set(metachild(j),'MarkerEdgeColor','white')
                        case 'MedianOuter'
                            set(metachild(j),'MarkerEdgeColor','white')
                    end
                end
        end
        end
    end
    else
    end
end

drawnow;
end