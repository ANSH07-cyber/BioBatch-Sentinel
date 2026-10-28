function a6_modelscatter()

load a5_ANNmodel.mat ANN_result
TT=ANN_result;

close all
color={"r","g","b","c"};
titles='a':'z';
leg=TT.Resp;

fg=figure();
set(gcf,'color','w')
for i=1:height(TT) %% number response variables
    subplot(2,3,i)
    M=TT.Model{i};
    exp=M.Y;pred=predict(M,M.X);
    resu=(pred-exp);
    MAE=(resu./std(resu,1)); %% standardized residuals

    xylim=[min([exp,pred],[],'all') max([exp,pred],[],'all')];
    h1=scatter(exp,pred);
    h1.Parent.XLim=[0.9 1.1].*xylim;
    h1.Parent.YLim=[0.9 1.1].*xylim;
    h1.MarkerEdgeColor=color{i};
    h1.Parent.XLabel.String="Experimental";
    h1.Parent.YLabel.String="Model";
    h1.Parent.TitleHorizontalAlignment="center";
    h1.Parent.Title.String=['(' titles(i) ')'];
    txt = ['R^{2}: ' num2str(round(TT.R2(i),4,"significant"))];
    text(mean(h1.Parent.XLim),0.75*mean(h1.Parent.YLim),txt)
    h2=lsline;
    h2.Color=color{i};h2.LineStyle="-";h2.LineWidth=1;
    legend(leg(i),'Location','northwest','Interpreter','none','Box','off')
    box 'on'

    subplot(2,3,i+3)
    h=stem(1:numel(MAE),MAE);
    h(1).Parent.XLabel.String='Observations';
    h(1).Parent.Title.String=['(' titles(i+3) ')'];
    h(1).Parent.YLim=[-4 4];
    % h(1).Parent.XLim=[0 31];
    %h(1).Parent.ColorOrder=[1 0 0 ; 0 1 0; 0 0 1; 1 0 1];
    h(1).Parent.YLabel.String='Std. residuals';
    h(1).Color=color{i};
    h(1).MarkerEdgeColor=color{i};
    yline([-3 3],'--r');
    % [h.LineWidth]=deal(0.5);
    % h(1).Parent.LineWidth=1.5;
    % h(1).Parent.FontSize=10;
    % h(1).Parent.LabelFontSizeMultiplier=1.2;
end
copygraphics(fg,'Resolution',600,'BackgroundColor','white','Padding','tight','PreserveAspectRatio','on') 
disp(' ');

