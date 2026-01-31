function s = BWlvbo(a)   
[m n]=size(a);
c=[];
for i=1:n-2
   c=a(i:i+2);
   p1=(c(1)-c(2))/c(1);
   p2=(c(3)-c(2))/c(3);
   p3=c(3)-c(2);
   p4=c(1)-c(2);
   if p1>0.2&&p2>0.2&&p3/p4>0.4
       a(i+1)=(c(1)+c(3))/2;
   end
end
[b,cxd,lxd] = wden([a a(n)],'minimaxi','s','mln',2,'db7');
s=b;
end