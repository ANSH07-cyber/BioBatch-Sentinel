function a4_ANN_Bayesopt (Data)
filename='a5_ANNmodel.mat';
%Pred=Data(:,1:4);Resp=Data(:,5:7);



for j=1:3
    XY=[Pred Resp(:,j)];
    Rname=Resp.Properties.VariableNames{j};
    numFolds = 5;
    rng (1)
    cvs = cvpartition(height(XY),'KFold',numFolds);
    results = bayesopt(@(paraz)SumSqr(paraz,XY,Rname,cvs),Optopt(),'ConditionalVariableFcn',@condition,'AcquisitionFunctionName','expected-improvement-plus',...
        'IsObjectiveDeterministic',true,'UseParallel',false,'MaxObjectiveEvaluations',60,'Verbose',1,'PlotFcn',[]);
    %,'ConditionalVariableFcn',@condition'AcquisitionFunctionName','expected-improvement-plus'
    A1=results.XAtMinObjective;
    [~,output]=SumSqr(A1,XY,Rname,cvs);
    A1.Resp=categorical({Rname});A1.R2=output{1};A1.R2CV=output{2};A1.Model=output(3);
    A1=movevars(A1,"Resp","Before","NumLayers");

    if exist(filename,'file')==2
        load (filename,'ANN_result')
        ANN_result=[ANN_result;A1];
    else
        ANN_result=A1;
    end
    save (filename,'ANN_result')

end
disp('')



function X = condition(X)
X.Layer_2(X.NumLayers ~= 2) = NaN;
disp('');


function [target,userdata]=SumSqr(z,XY,Rname,cvss)
msz=[z.Layer_1 z.Layer_2];
msz=msz(~isnan(msz));

rng (1)
mdl=fitrnet(XY,Rname,'CategoricalPredictors','MO','InitialStepSize','auto','Activations',char(z.Activation),'Standardize',1,'LayerSizes',msz);%'Lambda',z.(5),
mdlcv=crossval(mdl,'CVPartition',cvss);
% yHat = predict(mdl,XX);
% MSE_Mdl=resubLoss(mdl);
mdl_R2=corr(predict(mdl,mdl.X),mdl.Y)^2;
CV_R2=corr(kfoldPredict(mdlcv),mdlcv.Y)^2;%%'CVPartition',cvss,

userdata={mdl_R2,CV_R2,mdl};
target=1-CV_R2;





function vars=Optopt()
v1= optimizableVariable('NumLayers',[1 2],'Type','integer','Transform','none');
v2= optimizableVariable('Layer_1',[2 10],'Type','integer','Transform','log');
v3= optimizableVariable('Layer_2',[2 10],'Type','integer','Transform','log');
v4= optimizableVariable('Activation',{'tanh' 'sigmoid' 'relu'},'Type','categorical');

%v5= optimizableVariable('Regularization',[8.1301e-08 813.01],'Type','real','Transform','log');
vars=[v1 v2 v3 v4];

