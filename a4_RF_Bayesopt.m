function a4_RF_Bayesopt (Data)

filename='a5_RFmodel.mat';
Pred=Data(:,1:4);Resp=Data(:,5:7);

Mtype="Bag";
numFolds=5;
for j=1:3
    params=Optopt(Pred,Resp(:,j),Mtype);
    XY=[Pred Resp(:,j)];
    Rname=Resp.Properties.VariableNames{j};
    rng (1)
    cvs = cvpartition(height(XY),'KFold',numFolds);


    rng(1)
    results = bayesopt(@(paraz)SumSqr(paraz,XY,Rname,cvs,Mtype,'ita'),params,'ConditionalVariableFcn',@condition,'AcquisitionFunctionName','expected-improvement-plus',...
        'IsObjectiveDeterministic',true,'UseParallel',false,'MaxObjectiveEvaluations',60,'Verbose',1,'PlotFcn',[]);
    A1 = results.XAtMinObjective;
    [~,output]=SumSqr(A1,XY,Rname,cvs,Mtype,'final');
    A1.Resp=categorical({Rname});A1.R2=output{1};A1.R2CV=output{2};A1.Model=output(3);
    A1=movevars(A1,"Resp","Before",1);

    if exist(filename,'file')==2
        load (filename,'RF_result')
        RF_result=[RF_result;A1];
    else
        RF_result=A1;
    end
    save (filename,'RF_result')
end
disp('');



function X = condition(X)
if ismember('Method', X.Properties.VariableNames)
    X.LearnRate(X.Method ~= 'LSBoost') = NaN;
end
disp('');


function hyperset=Optopt(XX,YY,Modeltype)
hyperset = hyperparameters('fitrensemble',XX,YY,'Tree');
if strcmpi(Modeltype,'Bag')
    hyperset(1).Optimize = false;%'Method'
    hyperset(3).Optimize = false; %'LearnRate'
elseif strcmpi(Modeltype,'LSBoost')
    hyperset(1).Optimize = false;%'Method'
    hyperset(3).Optimize = true; %'LearnRate'
elseif strcmpi(Modeltype,'auto')
    hyperset(1).Optimize = true;%'Method'
    hyperset(3).Optimize = true; %'LearnRate'
end


hyperset(2).Optimize = true; %'NumLearningCycles'
%hyperset(2).Range=[10 500];

hyperset(4).Optimize = true; %'MinLeafSize'
%hyperset(4).Range=[1 37]; %[1 37]

hyperset(5).Optimize = true; %'MaxNumSplits'
%hyperset(5).Range=[1 73]; %[2 73]

hyperset(6).Optimize = true;%'NumVariablesToSample'
%hyperset(6).Range=[1 12]; %[1 13]

function [target,output]=SumSqr(z,XY,Rname,cvss,Mtype,cond)
if strcmp(Mtype,'auto')
    Name=char(z.Method);
else
    Name=Mtype;
end

para1={'NumVariablesToSample',z.NumVariablesToSample,'MinLeafSize',z.MinLeafSize,'MaxNumSplits',z.MaxNumSplits};
para2={'Method',Name,'NumLearningCycles',z.NumLearningCycles,};

if strcmp(Mtype,'LSBoost')
    para2=[para2,{'LearnRate',z.LearnRate}];
end
rng(1)
t = templateTree(para1{:},'PredictorSelection','interaction-curvature','Reproducible',true,'Surrogate','on','Type','regression');
Mdl = fitrensemble(XY,Rname,'Learners',t,para2{:});
Mdlcv=crossval (Mdl,'CVPartition',cvss);
R12CV=corr(kfoldPredict(Mdlcv),Mdlcv.Y)^2;

if strcmp(cond,'final')
    R12 = corr(predict(Mdl,XY),Mdl.Y)^2;
    % yHat = predict(Mdl,XY);
    % MSE_Mdl=resubLoss(Mdl);
    output={R12,R12CV,Mdl};
    target=[];
else
    target=1-R12CV;
    output=[];
end

disp('')

