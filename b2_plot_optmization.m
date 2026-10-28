function b2_plot_optmization
close all  
clc
clear variables
load b1_Ind_min_max_gen_report.mat mytable
load b1_Ind_min_max Masterresult


idx = find(mytable(:,1) == 0);           % Find where iteration resets
idx(end+1) = size(mytable,1)+1;          % Add end index

C = cell(numel(idx)-1,1);          % Preallocate cell array

for i = 1:numel(idx)-1
    C{i} = mytable(idx(i):idx(i+1)-1, :);  % Extract submatrix between zeros
end
Ylabel={'COD utilized (g l^{-1})','Biomass (g l^{-1})','Polymer (g l^{-1})'};
title='a':'z';

fig=figure();
set(gcf,'color','w');
for i=1:3
    subplot(1,3,i)
    dd=[1 -1 -1].*C{i};
    h=plot(dd(:,1),dd(:,2:3),'o-');
    h(1).Parent.XLabel.String='Iterations';
    h(1).Parent.YLabel.String=Ylabel{i};
    h(1).Parent.Title.String=['(' title(i) ')'];
    [h.LineWidth]=deal(1.5); %% line with of plot
    h(1).Parent.LineWidth=1.5;%% line width of axes
    h(1).Parent.FontSize=12;
    h(1).Parent.LabelFontSizeMultiplier=1.1;

 
    % % h(1).Parent.YLim=[-40 40];
    % % h(1).Parent.XLim=[0 31];
    % h(1).Parent.ColorOrder=[1 0 0 ; 0 1 0; 0 0 1; 1 0 1];
    % h(1).Parent.YLabel.String='Residuals (standardized)';
    % yline([-3 3],'--r');
    h2=legend;
    h2.String={"Best","Population avg"};
    h2.Interpreter="none";
    h2.Location='best';
    box on
end
copygraphics(fig,'Resolution',600,'BackgroundColor','white','Padding','tight','PreserveAspectRatio','on')
exportgraphics(fig,'Fig S1.png','Resolution',600)
disp (" ");