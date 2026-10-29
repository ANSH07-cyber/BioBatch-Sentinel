function a7_mysanova(Tabs,Datacomp,lchatt)
myboxanova(Tabs)
% my1anova_seperate(Tabs)
% my1anova(Datacomp)
% lecplot(lchatt)

function myboxanova(Tabs)
   % https://in.mathworks.com/matlabcentral/answers/1964719-how-to-combine-boxplots-from-anova-into-subplots
name='a':'z';
ytitle={"PHA (g L^{-1})","PHA (g L^{-1})","Pullulan (g L^{-1})","Pullulan (g L^{-1})"};
lgnd={"CT","CS","CT","CS"};
Clr = orderedcolors("dye");
PLW=1.1;
LW=1.2;
FS=14;
LFM=1.2;
MS=8;


fga=figure();
set(fga,"color","white")
for i=1:4
    T=Tabs{i};
    T.Set=categorical(T.Set);
    subplot(2,2,i)
    b=boxchart(T,"Set","Polymer");
    b.Notch="on";
    b.Parent.FontSize=FS;
    b.Parent.LineWidth=PLW;
    b.LineWidth=LW;
    b.MarkerSize=MS;
    b.Parent.LabelFontSizeMultiplier=LFM;
    b.BoxFaceAlpha=0;
    b.BoxMedianLineColor="r";
    b.Parent.Title.String=['(' name(i) ')'];
    b.Parent.YLabel.String=ytitle{i};
    b.BoxEdgeColor=Clr(i,:);
    l=legend;
    l.String=lgnd{i};
    box on
end
copygraphics(fga,'Resolution',900,'BackgroundColor','white','Padding','tight','PreserveAspectRatio','on')
disp (" ");
disp(" ");


function my1anova_seperate(Tabs)
   % https://in.mathworks.com/matlabcentral/answers/1964719-how-to-combine-boxplots-from-anova-into-subplots
for i=1:4
    T=Tabs{i};
   [p,tbl,stats]= anova1(T.Polymer,T.Set,'off');
   [c,~,~,gnames] = multcompare(stats);
   
end



function my1anova(Datacomp)
[p,anvt,stats]=anova1(Datacomp.Polymer,Datacomp.MO);
disp(p)
disp(anvt)
[c,~,~,gnames] = multcompare(stats);
tbl = array2table(c,"VariableNames", ...
    ["Group A","Group B","Lower Limit","A-B","Upper Limit","P-value"]);
tbl.("Group A") = gnames(tbl.("Group A"));
tbl.("Group B") = gnames(tbl.("Group B"));
disp('');

function lecplot(lchatt)
groupVars = {'Set'};
T = groupsummary(lchatt, groupVars, {'mean','std'});

figure()
set(gcf,'color','w');
b=bar(T.mean_COD);
[b.BarWidth]=deal(0.12);
b.Parent.Title.String=['(' 'a' ')'];
b(1).Parent.XTickLabel={'BL (1%)', 'BL (2.5%)', 'BL (5%)'};
b(1).Parent.XLim=[0.5 3.5];

hold on
errorbar(b.XEndPoints,b.YEndPoints,T.std_COD,'r',"LineStyle","none");
xlabel('Expt. Sets')
ylabel('COD conc.(g l^{-1})')
% l=legend;
% l.String={'COD S_{\iti}', 'COD BL_{\iti}', 'COD_{\itf}', 'Biomass_{\itf}','Polymer_{\itf}'};
% l.Location="northeast";
hold off
disp (' ');