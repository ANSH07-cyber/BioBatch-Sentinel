function a0_all_analysis()
close all hidden
clc
clearvars,clc, format short g, format compact
profile on

a1_dataload()

load a1_Summary_Polymer.mat Tabs Datacomp Lchatt

a2_megaplot(Tabs)
a3_myheatanalysis(Tabs)
a4_ANN_Bayesopt (Datacomp)
a4_RF_Bayesopt (Datacomp)
a6_modelscatter()
a7_mysanova(Tabs,Datacomp,Lchatt)
b1_min_max_GA (Datacomp)
disp ('');











