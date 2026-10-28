function a2_megaplot(Tabs)
groupVars = {'Set'};
ff=figure();
set(gcf,'color','w');
for i=1:4
    T = groupsummary(Tabs{i}, groupVars, {'mean','std'});
    stacked_group(T,i)
end

copygraphics(ff,'Resolution',600,'BackgroundColor','white','Padding','tight','PreserveAspectRatio','on')
disp('')

function stacked_group(T,id)
titles='a':'z';
Y_mean= T{:,["mean_Str_Suc_COD","mean_Str_Lcht_COD","mean_COD_utilized","mean_Fnl_biomass","mean_Polymer"]}; %T{:,[3 5 7 9 11]}; %% initial Sucrose, initial lechate, Final COD
Y_err=T{:,["std_Str_Suc_COD","std_Str_Lcht_COD","std_COD_utilized","std_Fnl_biomass","std_Polymer"]};%T{:,[4 6 8 10 12]}; %% initial Sucrose, initial lechate, Final COD

pos=[1 7 13 19];

subplot(2,2,id)

b1 = bar(Y_mean(:,[1 2]), 'stacked');
[b1.XData]=deal(pos);%% 1 3 5 7
[b1.BarWidth]=deal(0.12);
b1(1).Parent.Title.String=['(' titles(id) ')'];
b1(1).Parent.LineWidth=0.75;
% b1(1).Parent.FontSize=16;
% b1(1).Parent.LabelFontSizeMultiplier=1.2;
hold on
b2=cell(1,3);
for i=1:3
    b2{i}=bar(Y_mean(:,2+i));
    [b2{i}.XData]=pos+i;
    [b2{i}.BarWidth]=deal(0.12);

end


% b2=bar(Y_mean(:,[5 3 4]),'grouped');
% [b2.XData]=deal([3 8 13 18]);%% 1.75 3.75 5.75 7.75
% [b2.BarWidth]=deal(0.6);
% [b2.GroupWidth]=deal(0.6);

b1(1).Parent.XTick=pos+1.5;
b1(1).Parent.XLim=[0 26];
b1(1).Parent.XTickLabel={'Suc', 'BL (1%)', 'BL (2.5%)', 'BL (5%)'};

b2Ends = [b2{:}];

XX=[b1.XEndPoints b2Ends.XEndPoints];
YY=[b1.YEndPoints b2Ends.YEndPoints];
ZZ=reshape(Y_err,1,[]);

errorbar(XX,YY,ZZ,'k', 'linestyle', 'none', 'linewidth', 1)
xlabel('Expt. Sets')
ylabel('Conc.(g L^{-1})')
l=legend;
l.String={'COD S_{\iti}', 'COD BL_{\iti}', 'COD_{\itu}', 'Biomass_{\itf}','Polymer_{\itf}'};
l.Location="northeast";
grid off
hold off
disp('');