function b1_min_max_GA ()%Data
load a1_Summary_Polymer.mat Datacomp
Data=Datacomp;
pred=Data(:,1:4);Resp=Data(:,5:7);
load a5_ANNmodel.mat ANN_result
Modells=ANN_result{:,end};
%Modells,pred,Resp

lw=[1 min(pred{:,2:4},[],1)]; %% <0 PHA
uw=[2 max(pred{:,2:4},[],1)]; %% >=0 PL
Masterresult=cell(2,2);

gaset = {'PopulationSize', 100,'StallGenLimit', 20,'UseParallel','always','PlotFcn',"gaplotbestf",...
            'MaxGenerations',100,'OutputFcns',@ga_save_each_gen}; %
%psoset={'SwarmSize',100,'MaxIterations',100,'MaxStallIterations',20,'UseParallel','always','PlotFcn','pswplotbestf'};

if exist('b1_Ind_min_max_gen_report.mat', 'file') == 2
    delete('b1_Ind_min_max_gen_report.mat');
end


for j=1:2 
    for i=1:width(Resp) %% Four responses
        fun=@(x)MainGA(x,Modells{i},j);
        [ParaOpt{i},Fvalue(i),~,~]=ga(fun,numel(lw),[],[],[],[],lw,uw,[],1,optimoptions('ga',gaset{:}));
       % [ParaOpt{i},Fvalue(i),~,~,~]=particleswarm(fun,numel(lw),lw,uw,optimoptions('particleswarm',psoset{:}));

    end
    Masterresult(j,1)={ParaOpt};Masterresult(j,2)={(-1)^j*Fvalue};
end
save b1_Ind_min_max.mat Masterresult
disp('')

function performance = MainGA(z,Mdl,type)
z=array2table(z,"VariableNames",Mdl.PredictorNames);
if z.MO<1.5
    z.MO=categorical("PHA");
else
    z.MO=categorical("PL");
end

pr=predict(Mdl,z);

if type==1 %% maximize
    performance=-pr;
else
    performance=pr; %% minimize
end
disp('')

function [state,options,optchanged]=ga_save_each_gen(options,state,~)
Score_gen=state.Score;
Population_gen=state.Population; %#ok<NASGU>
[score,~]=sort(Score_gen);
best_score=score(1);
Generation_gen=state.Generation;
%best_gene=Population_gen(p(1),:);
optchanged=[];
out=[Generation_gen best_score mean(Score_gen)];
if exist('b1_Ind_min_max_gen_report.mat','file')==2
    load b1_Ind_min_max_gen_report.mat mytable
    mytable=[mytable;out];
else
    mytable=out;
end
save b1_Ind_min_max_gen_report.mat mytable

