function a8_LIME_Shaply_finalplot
clc
close all
clear variables

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
load a1_Summary_Polymer.mat Datacomp 
Pred=Datacomp(:,1:4);Resp=Datacomp(:,5:7);
load a5_ANNmodel.mat ANN_result
Mdl=ANN_result{:,end};

Pnames=Pred.Properties.VariableNames;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
titles='a':'z';
fig=figure();
set(gcf,'color','yellow');
barclr=orderedcolors("dye");
for i=1:width(Resp)

    subplot(2,3,i)
    explainer = shapley(Mdl{i});
    queryPoints = Pred;
    explainer = fit(explainer,queryPoints);
    labi={'Polymer','Suc COD','BL COD','Inoculum'};
    [~,ord]=sort(explainer.MeanAbsoluteShapley.Value);
    labi=labi(ord);
    j=swarmchart(explainer);
    ytickangle(45);
    colormap jet
    j(1).Parent.Title.String='';
    j(1).Parent.TickLabelInterpreter='tex';
    j(1).Parent.YTickLabel=labi;
    title((['(' titles(i) ')']))
    k=colorbar;k.Ticks=[0 1];k.TickLabels={'Low','High'};
    k.Label.String = [];k.Label.Rotation=270;
    k.FontSize=13;
    j(1).Parent.LineWidth=1.5;
    j(1).Parent.FontSize=13;
    j(1).Parent.FontName='Times new roman';
    j(1).Parent.LabelFontSizeMultiplier=1.1;

    subplot(2,3,i+3)
    l=plot(explainer);
    l.Parent.Title.String=['(' titles(i+3) ')'];
    l.Parent.YTickLabel=labi;
    ytickangle(45);

    l(1).Parent.LineWidth=1.5;
    l(1).Parent.FontSize=13;
    l(1).Parent.FontName='Times new roman';
    l(1).Parent.LabelFontSizeMultiplier=1.1;
    l.FaceColor="flat";
    l.CData=barclr(ord,:);

    % subplot(1,3,i)
    % x=limelist.(lab{i})';
    % temp_lab=Pnames;
    % catlab=categorical(temp_lab);
    % rclab=reordercats(catlab,temp_lab);
    % y=repmat(rclab,size(x,1),1);
    % %clist=normalize(Pred{:,:},'range')';
    % clist=normCat(Pred)';
    % j= swarmchart(x,y,'YJitter','density');
    % j(1).CData=clist(1,:);j(2).CData=clist(2,:)';j(3).CData=clist(3,:)';
    % j(1).Parent.YGrid='on';j(1).Parent.XGrid='on';
    % j(1).Parent.YTickLabel={'X_{0} (g L^{-1})', 'BPE (g L^{-1})','Pretreated ?'};
    % [j.MarkerFaceColor]=deal('flat');[j.MarkerEdgeColor]=deal('none');
    % m=colorbar;m.Ticks=[0 1];m.TickLabels={'Low','High'};
    % m.Label.String = 'Predictor value';m.Label.Rotation=270;
    % xline(0)
    % box on
    % xlabel('Lime coefficient')
    % ylabel('Predictors')
    % title((['(' titles(i) ')']))
    % j(1).Parent.LineWidth=1.5;j(2).Parent.LineWidth=1.5;j(3).Parent.LineWidth=1.5;
    % j(1).Parent.FontSize=13;j(2).Parent.FontSize=13;j(3).Parent.FontSize=13;
    % j(1).Parent.FontName='Times new roman';j(2).Parent.FontName='Times new roman';j(3).Parent.FontName='Times new roman';
    % j(1).Parent.LabelFontSizeMultiplier=1.1;j(2).Parent.LabelFontSizeMultiplier=1.1;j(3).Parent.LabelFontSizeMultiplier=1.1;
end
    copygraphics(fig,'Resolution',600,'BackgroundColor','white','Padding','tight','PreserveAspectRatio','on')

function finalTable = normCat(T)
    isNum = varfun(@isnumeric, T, 'OutputFormat', 'uniform');
    isCat = ~isNum;
    normNumeric = normalize(T{:, isNum}, 'range');
    normEncoded=double(categorical(T{:,isCat}))-1;

    finalTable=zeros(size(T));
    finalTable(:,isNum)=normNumeric;
    finalTable(:,isCat)=normEncoded;
    disp('');
    

