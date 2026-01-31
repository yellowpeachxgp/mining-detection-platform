function y = creat_sample(s, len, p1, p2)

sample=zeros(11,len+1);

sample(1,:)=[s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,len-round(0.25*len)+1) 1]; 
sample(2,:)=[s(2)*ones(1, round(len/2)-1) s(1)*ones(1,len-round(len/2)+1) 2];
sample(3,:)=[s(2)*ones(1,round(0.75*len)-1) s(1)*ones(1,len-round(0.75*len)+1) 3];
sample(4,:)=[p1*s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,len-round(0.25*len)+1) 4]; 
sample(5,:)=[p1*s(2)*ones(1, round(len/2)-1) s(1)*ones(1,len-round(len/2)+1) 5];
sample(6,:)=[p1*s(2)*ones(1,round(0.75*len)-1) s(1)*ones(1,len-round(0.75*len)+1) 6];
sample(7,:)=[p2*s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,len-round(0.25*len)+1) 7]; 
sample(8,:)=[p2*s(2)*ones(1, round(len/2)-1) s(1)*ones(1,len-round(len/2)+1) 8];
sample(9,:)=[p2*s(2)*ones(1,round(0.75*len)-1) s(1)*ones(1,len-round(0.75*len)+1) 9];

% 1 1
sample(10,:)=[s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,round(0.375*len-0.5)) vegetation_recovery(s,[1:len-round(0.25*len)+1-round(0.375*len-0.5)]) 10]; 
sample(11,:)=[s(2)*ones(1, round(len/2)-1) s(1)*ones(1,round(0.25*len-0.5)) vegetation_recovery(s,[1:len-round((len)/2)+1-round(0.25*len-0.5)]) 11];
sample(12,:)=[s(2)*ones(1, round(0.75*len)-1) s(1)*ones(1,round(0.125*len-0.5)) vegetation_recovery(s,[1:len-round(0.75*len)+1-round(0.125*len-0.5)]) 12];
% p1 1
sample(13,:)=[p1*s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,round(0.375*len-0.5)) vegetation_recovery(s,[1:len-round(0.25*len)+1-round(0.375*len-0.5)]) 13]; 
sample(14,:)=[p1*s(2)*ones(1, round(len/2)-1) s(1)*ones(1,round(0.25*len-0.5)) vegetation_recovery(s,[1:len-round((len)/2)+1-round(0.25*len-0.5)]) 14];
sample(15,:)=[p1*s(2)*ones(1, round(0.75*len)-1) s(1)*ones(1,round(0.125*len-0.5)) vegetation_recovery(s,[1:len-round(0.75*len)+1-round(0.125*len-0.5)]) 15];
% 1 p1
sample(16,:)=[s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,round(0.375*len-0.5)) vegetation_recovery([s(1) p1*s(2)],[1:len-round(0.25*len)+1-round(0.375*len-0.5)]) 16]; 
sample(17,:)=[s(2)*ones(1, round(len/2)-1) s(1)*ones(1,round(0.25*len-0.5)) vegetation_recovery([s(1) p1*s(2)],[1:len-round((len)/2)+1-round(0.25*len-0.5)]) 17];
sample(18,:)=[s(2)*ones(1, round(0.75*len)-1) s(1)*ones(1,round(0.125*len-0.5)) vegetation_recovery([s(1) p1*s(2)],[1:len-round(0.75*len)+1-round(0.125*len-0.5)]) 18];
% p1 p1
sample(19,:)=[p1*s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,round(0.375*len-0.5)) vegetation_recovery([s(1) p1*s(2)],[1:len-round(0.25*len)+1-round(0.375*len-0.5)]) 19]; 
sample(20,:)=[p1*s(2)*ones(1, round(len/2)-1) s(1)*ones(1,round(0.25*len-0.5)) vegetation_recovery([s(1) p1*s(2)],[1:len-round((len)/2)+1-round(0.25*len-0.5)]) 20];
sample(21,:)=[p1*s(2)*ones(1, round(0.75*len)-1) s(1)*ones(1,round(0.125*len-0.5)) vegetation_recovery([s(1) p1*s(2)],[1:len-round(0.75*len)+1-round(0.125*len-0.5)]) 21];

% p2 1
sample(22,:)=[p2*s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,round(0.375*len-0.5)) vegetation_recovery(s,[1:len-round(0.25*len)+1-round(0.375*len-0.5)]) 22];
sample(23,:)=[p2*s(2)*ones(1, round(len/2)-1) s(1)*ones(1,round(0.25*len-0.5)) vegetation_recovery(s,[1:len-round((len)/2)+1-round(0.25*len-0.5)]) 23];
sample(24,:)=[p2*s(2)*ones(1, round(0.75*len)-1) s(1)*ones(1,round(0.125*len-0.5)) vegetation_recovery(s,[1:len-round(0.75*len)+1-round(0.125*len-0.5)]) 24];

% 1 p2
sample(25,:)=[s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,round(0.375*len-0.5)) vegetation_recovery([s(1) p2*s(2)],[1:len-round(0.25*len)+1-round(0.375*len-0.5)]) 25];
sample(26,:)=[s(2)*ones(1, round(len/2)-1) s(1)*ones(1,round(0.25*len-0.5)) vegetation_recovery([s(1) p2*s(2)],[1:len-round((len)/2)+1-round(0.25*len-0.5)]) 26];
sample(27,:)=[s(2)*ones(1, round(0.75*len)-1) s(1)*ones(1,round(0.125*len-0.5)) vegetation_recovery([s(1) p2*s(2)],[1:len-round(0.75*len)+1-round(0.125*len-0.5)]) 27];

% p2 p2
sample(28,:)=[p2*s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,round(0.375*len-0.5)) vegetation_recovery([s(1) p2*s(2)],[1:len-round(0.25*len)+1-round(0.375*len-0.5)]) 28];
sample(29,:)=[p2*s(2)*ones(1, round(len/2)-1) s(1)*ones(1,round(0.25*len-0.5)) vegetation_recovery([s(1) p2*s(2)],[1:len-round((len)/2)+1-round(0.25*len-0.5)]) 29];
sample(30,:)=[p2*s(2)*ones(1, round(0.75*len)-1) s(1)*ones(1,round(0.125*len-0.5)) vegetation_recovery([s(1) p2*s(2)],[1:len-round(0.75*len)+1-round(0.125*len-0.5)]) 30];

% p2 p1
sample(31,:)=[p2*s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,round(0.375*len-0.5)) vegetation_recovery([s(1) p1*s(2)],[1:len-round(0.25*len)+1-round(0.375*len-0.5)]) 31];
sample(32,:)=[p2*s(2)*ones(1, round(len/2)-1) s(1)*ones(1,round(0.25*len-0.5)) vegetation_recovery([s(1) p1*s(2)],[1:len-round((len)/2)+1-round(0.25*len-0.5)]) 32];
sample(33,:)=[p2*s(2)*ones(1, round(0.75*len)-1) s(1)*ones(1,round(0.125*len-0.5)) vegetation_recovery([s(1) p1*s(2)],[1:len-round(0.75*len)+1-round(0.125*len-0.5)]) 33];

% p1 p2
sample(34,:)=[p1*s(2)*ones(1,round(0.25*len)-1) s(1)*ones(1,round(0.375*len-0.5)) vegetation_recovery([s(1) p2*s(2)],[1:len-round(0.25*len)+1-round(0.375*len-0.5)]) 34];
sample(35,:)=[p1*s(2)*ones(1, round(len/2)-1) s(1)*ones(1,round(0.25*len-0.5)) vegetation_recovery([s(1) p2*s(2)],[1:len-round((len)/2)+1-round(0.25*len-0.5)]) 35];
sample(36,:)=[p1*s(2)*ones(1, round(0.75*len)-1) s(1)*ones(1,round(0.125*len-0.5)) vegetation_recovery([s(1) p2*s(2)],[1:len-round(0.75*len)+1-round(0.125*len-0.5)]) 36];

sample(37,:)=[s(1)*ones(1, len) 37];

sample(38,:)=[s(2)*ones(1, len) 38];
sample(39,:)=[p1*s(2)*ones(1, len) 39];
sample(40,:)=[p2*s(2)*ones(1, len) 40];

sample(41,:)=[s(1)*ones(1,round(0.25*len)-1) vegetation_recovery(s,[1:len-round(0.25*len)+1]) 41];
sample(42,:)=[s(1)*ones(1, round(len/2)-1) vegetation_recovery(s,[1:len-round(len/2)+1]) 42];
sample(43,:)=[s(1)*ones(1,round(0.75*len)-1) vegetation_recovery(s,[1:len-round(0.75*len)+1]) 43]; 
sample(44,:)=[s(1)*ones(1,round(0.25*len)-1) vegetation_recovery([s(1) p1*s(2)],[1:len-round(0.25*len)+1]) 44]; sample(45,:)=[s(1)*ones(1, round(len/2)-1) vegetation_recovery([s(1) p1*s(2)],[1:len-round(len/2)+1]) 45];
sample(46,:)=[s(1)*ones(1,round(0.75*len)-1) vegetation_recovery([s(1) p1*s(2)],[1:len-round(0.75*len)+1]) 46]; 
sample(47,:)=[s(1)*ones(1,round(0.25*len)-1) vegetation_recovery([s(1) p2*s(2)],[1:len-round(0.25*len)+1]) 47]; sample(48,:)=[s(1)*ones(1, round(len/2)-1) vegetation_recovery([s(1) p2*s(2)],[1:len-round(len/2)+1]) 48];
sample(49,:)=[s(1)*ones(1,round(0.75*len)-1) vegetation_recovery([s(1) p2*s(2)],[1:len-round(0.75*len)+1]) 49];

y= sample;
end