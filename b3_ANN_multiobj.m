function b3_ANN_multiobj % Solving the system, check
close all
clearvars,clc, format short g, format compact
profile on
%global IDs
%%%%%%%%%%%%%%%%%%%%%
%% https://www.sciencedirect.com/science/article/pii/S1568494621000144#sec3
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
load a1_Summary_Polymer.mat Datacomp
Data=Datacomp;
Pred=Data(:,1:4);Resp=Data(:,5:7);
load a5_ANNmodel.mat ANN_result
load b1_Ind_min_max.mat Masterresult
Maxres=Masterresult{1,2};
Mdl=ANN_result{:,end};
Pnames=Pred.Properties.VariableNames;

Temp=[double(categorical(Pred.MO)) Pred{:,2:4} ];
lw=min(Temp,[],1);%% upper and lower limits of predictors explored %% two predictor
uw=max(Temp,[],1);

% options = optimoptions(@gamultiobj,'PlotFcn',{@gaplotpareto,@gaplotscorediversity});
% [ParaOpt,Fvalue,~,outp]=gamultiobj({@MainGA,Mdl,Pnames,Maxres},numel(lw),[],[],[],[],lw,uw,[],1,options);
% Fvalue=-(Fvalue.*Maxres);
% save b4_Multi_objective_result.mat ParaOpt Fvalue outp
load b4_Multi_objective_result.mat ParaOpt Fvalue outp
outp.generations;
%myfigure(ParaOpt,Fvalue)
myfigure2(ParaOpt,Fvalue)
disp('')




function performance = MainGA(z,Mod,Pnames,MaxR)
vec_cell = num2cell(z);

% If third entry is 1, replace with 'No'
if z(1) == 1
    vec_cell{1} = 'PHA';
else
    vec_cell{1} = 'PL';
end
T = cell2table(vec_cell);
T.Properties.VariableNames = Pnames;

performance(1)=-predict(Mod{1},T)/MaxR(1); %% COD to increase,
performance(2)=-predict(Mod{2},T)/MaxR(2); %% Biomass to increase
performance(3)=-predict(Mod{3},T)/MaxR(3); %% Polymer to increase
disp('')

function myfigure2(ParaOpt,Fvalue)
col=colororder("dye");
col = num2cell(col, 2);  % each row (color) becomes a cell

%ParaOpt=[1 1 5 500].*ParaOpt;
ParaOpt=zscore(ParaOpt);
b=repmat({'A','B','C','D'},size(ParaOpt,1),1);
b=reshape(b,[],1);
ParaOpt=reshape(ParaOpt,[],1);

C=figure();
set(gcf,'color','w')
colororder("dye")

subplot(1,2,1)
h=boxchart(categorical(b),ParaOpt,'GroupByColor',b,'ColorGroupLayout','overlaid');

[h.Notch]=deal("off");
[h.BoxFaceAlpha]=deal(0);
[h.BoxMedianLineColor]=deal(col{1:4});
[h.BoxEdgeColor]=deal(col{1:4}); 

h(1).Parent.XTickLabel={'Polymer','COD_{\itS,i}','COD_{\itBL,i} (\times5)' ,'Inoculum (\times500)'};
h(1).Parent.Title.String='(a)';
h(1).Parent.YLabel.String={'Predictor level'};
h(1).Parent.XLabel.String={'Predictors'};
box on



subplot(1,2,2)
x=Fvalue(:,1);
y=Fvalue(:,2);
z=Fvalue(:,3);
j=scatter3(x,y,z,"filled");
j.Parent.Title.String='(b)';
j.Parent.XLabel.String={'COD utilized (g/l)'};
j.Parent.XLabel.Rotation=5;
j.Parent.YLabel.String={'Biomass (g/l)'};
j.Parent.YLabel.Rotation=-15;
j.Parent.ZLabel.String={'Polymer (g/l)'};
view(-30,10)
box on
copygraphics(C,'Resolution',600,'BackgroundColor','white','Padding','tight','PreserveAspectRatio','on')
