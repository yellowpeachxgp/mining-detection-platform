function s = ljpl(a1)
[m n l]=size(a1);
a1=reshape(a1,m*n*l,1);
a1(a1==0)=[];
a1(isnan(a1))=[];
[len e]=size(a1);
a1=sort(a1);
s=[a1(floor(len*0.005)) a1(floor(len*0.995))];
end

