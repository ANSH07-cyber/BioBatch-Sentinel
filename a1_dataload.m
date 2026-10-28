function a1_dataload()
close all
clearvars,clc, format short g, format compact
profile on

fn='Summary_Polymer.xlsx';
opt=detectImportOptions(fn);
shts=sheetnames(fn);
n=numel(shts);
Tabs=cell(1,n);
for i=1:4
Tabs{i}=readtable(fn,opt,'Sheet',shts(i),'ReadVariableNames',true);
end
T=[Tabs{1};Tabs{2};Tabs{3};Tabs{4}];
T=T(:,["Str_Suc_COD","Str_Lcht_COD","Str_Biomass","COD_utilized","Fnl_biomass","Polymer"]);
T.MO=[repmat({'PHA'},24,1);repmat({'PL'},24,1)];
Datacomp=movevars(T,'MO','Before',1);

Lchatt = readtable("Leachate_COD.xlsx");

save a1_Summary_Polymer.mat Tabs Datacomp Lchatt







