
clear all;
clc;

% 设置开始年份 (需要根据你的数据修改)
startyear = 2015;  % ****开始年份设置****

[a R]=geotiffread('F:\挑战杯\6\Tif\NDVIfileclip.tif');     %****represents the location where the NDVI time series data is stored on the host computer
info=geotiffinfo('F:\挑战杯\6\Tif\NDVIfileclip.tif');
% a=double(a);
a(a==0)=NaN; %Set the background as NaN
a(a>=1)=NaN;
a(a<-1)=0;
[m n l]=size(a);
% for i=1:l
%     s=ljpl(a(:,:,i));
%     a(:,:,i) = (a(:,:,i)-s(1))/(s(2)-s(1));
% end
s=ljpl(a);
a(a>1)=1;
a(a<0)=0;
b=reshape(a,m*n,l,1); % testdata
b(all(isnan(b),2),:)=0;
clear a;
e=b;
b(all(b==0,2),:)=[];

sample=creat_sample(s, l, 0.8, 0.6)    % Create samples
 
sample_label = sample(:,l+1);

sample_label = single(sample_label);
 
trainData = sample(:,1:l);

trainData = single(trainData);
% testData = dlmread('IRIS_test_data.txt');
 
k = 1;
 
[c,y1,y2] = knn(trainData, sample_label, b, k);


h=find(all(e==0,2));
for i=1:length(h)
        c=[c(1:h(i)-1);zeros(1,1);c(h(i):end)];      % C is the trajectory type
        y1=[y1(1:h(i)-1);zeros(1,1);y1(h(i):end)];   % y1 is the disutrbance year
        y2=[y2(1:h(i)-1);zeros(1,1);y2(h(i):end)];   % y2 is the recovery year
end
res_disturbance=reshape(c,m,n);          
yeardisturbance=reshape(y1,m,n);
yearrecovery=reshape(y2,m,n);
bw = res_disturbance;
bw(bw==38|bw==39|bw==40|isnan(bw))=0;
bw(bw~=0)=1;
se = strel('disk',2);
openbw=imopen(bw,se);
[polygon_disturbance,num] = bwlabel(openbw,8); 
potential_disturbance = polygon_disturbance;

[barecoal_p R]=geotiffread('F:\挑战杯\6\Tif\barecoal_pclip.tif');     % read the probability of exposed coal
barecoal_p(isnan(barecoal_p))=0; 
barecoal_p(barecoal_p<=0.5)=0; 
barecoal_p(barecoal_p>0.5)=1;
sum_barecoal=sum(barecoal_p,3);  
sum_barecoal(sum_barecoal~=0)=1;
sum_barecoal = medfilt2(sum_barecoal,[5 5]);

%Topological judgment between exposed coal and potential mining disturbances%
Union = sum_barecoal.*polygon_disturbance;
[m n]=size(sum_barecoal);
Union = reshape(Union,m*n,1);
Union(Union==0)=[];
Union = unique(Union);

for i=1:length(Union)
    s = polygon_disturbance;
    s(s~=Union(i))=0;
    s(s==Union(i))=1;
    total_num = sum(sum(s));
    s1 = s.*sum_barecoal;
    s1(s1~=0)=1;
    union_num = sum(sum(s1));
    if  total_num >=1111 & (union_num >= 222 & union_num/total_num >= 0.02)
       polygon_disturbance(polygon_disturbance==Union(i))=-1; 
    end
end
polygon_disturbance(polygon_disturbance~=-1)=0;
polygon_disturbance(polygon_disturbance==-1)=1;
year_miningdisturbance = polygon_disturbance.*yeardisturbance;
year_miningdisturbance = year_miningdisturbance + startyear - 1; % startyear is the starting year of the data
year_miningdisturbance(year_miningdisturbance== startyear - 1)=0;
year_miningrecovery = polygon_disturbance.*yearrecovery;
year_miningrecovery = year_miningrecovery + startyear - 1;
year_miningrecovery(year_miningrecovery== startyear - 1)=0;
geotiffwrite('F:\挑战杯\6\Tif\polygon_disturbanc.tif',polygon_disturbance,R);
geotiffwrite('F:\挑战杯\6\Tif\year_miningdisturbance.tif',year_miningdisturbance,R);
geotiffwrite('F:\挑战杯\6\Tif\year_miningrecovery.tif',year_miningrecovery,R);
geotiffwrite('F:\挑战杯\6\Tif\potential_disturbance.tif',potential_disturbance,R);
geotiffwrite('F:\挑战杯\6\Tif\res_disturbance.tif',res_disturbance,R);
geotiffwrite('F:\挑战杯\6\Tif\yeardisturbance.tif',yeardisturbance,R);
geotiffwrite('F:\挑战杯\6\Tif\yearrecovery.tif',yearrecovery,R);

