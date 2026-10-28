function a3_myheatanalysis(Tabs)
T=[Tabs{1};Tabs{2};Tabs{3};Tabs{4}];
T1=T(:,["Str_Suc_COD","Str_Lcht_COD","Str_Biomass"]);
T2=T(:,["COD_utilized","Fnl_biomass","Polymer"]);
figure()
set(gcf,'color','w');
[p,c]=corr(T1{:,:},T2{:,:});
h=heatmap(p);
h.Title= '(a)';
h.XDisplayLabels={"COD utilized","Biomass","Polymer"};%T2.Properties.VariableNames;
h.YDisplayLabels={"Sucrose COD","BL COD","Initial biomass"};%T1.Properties.VariableNames;
h.NodeChildren(3).XAxis.TickLabelInterpreter = 'none';
h.NodeChildren(3).YAxis.TickLabelInterpreter = 'none';
h.NodeChildren(3).XTickLabelRotation=30;
h.CellLabelColor='none'; %;%%'auto'
h.Colormap=jet;
h.GridVisible = 'on';
h.XLabel='Responses';
h.YLabel='Preditors';
copygraphics(h,'Resolution',600,'BackgroundColor','white','Padding','tight','PreserveAspectRatio','on')
disp('')