function [y, yd, yr] = knn(trainData, sample_label, testData, k)
 
%KNN k-Nearest Neighbors Algorithm.
%
%   INPUT:  trainData:       training sample Data, M-by-N matrix.
%           sample_label:    training sample labels, 1-by-N row vector.
%           testData:        testing sample Data, M-by-N_test matrix.
%           K:               the k in k-Nearest Neighbors
%
%   OUTPUT: y    : predicted labels, 1-by-N_test row vector.
%
 
[M_train, N] = size(trainData);
[M_test, ~] = size(testData);
 
%calculate the distance between testData and trainData
 
Dis = zeros(M_train,1);
class_test = zeros(M_test,1);
class_yd = zeros(M_test,1);
class_yr = zeros(M_test,1);
path = zeros(100,2,N);
for n = 1:M_test
    test_ts = testData(n,:);
    id_nan = find(isnan(test_ts));
    test_ts(isnan(test_ts))=[];
    test_ts = BWlvbo(test_ts);
    temp_path = zeros(100,2);
    for i = 1:M_train
                  [Dis(i,1), w] = dtw(trainData(i,:),test_ts); %DTW
                   temp_path(1:length(w),:) = w;
                   path(:,:,i) = temp_path;
    end
 
    %find the k nearest neighbor
    [~, index] = sort(Dis);
    class_test(n) = sample_label(index(1));
    py = path(:,:,class_test(n));
    switch class_test(n)
        case {1,4,7}
        py(all(py==0,2),:)=[];
        for s=1:length(id_nan)
            h=find(py(:,2)==id_nan(s));
            if ~isempty(h)
            py(h(1):end,2) = py(h(1):end,2)+1;
            end
        end
        t_dis = find(py(:,1)==round(0.25*N));
        class_yd(n)= py(t_dis(1), 2);
        class_yr(n) = 0;
    
        case {2,5,8}
        py(all(py==0,2),:)=[];
        for s=1:length(id_nan)
            h=find(py(:,2)==id_nan(s));
            if ~isempty(h)
            py(h(1):end,2) = py(h(1):end,2)+1;
            end
        end
        t_dis = find(py(:,1)==round(N/2));
        class_yd(n)= py(t_dis(1), 2);
        class_yr(n) = 0;
    
        case {3,6,9}
        py(all(py==0,2),:)=[];
        for s=1:length(id_nan)
            h=find(py(:,2)==id_nan(s));
            if ~isempty(h)
            py(h(1):end,2) = py(h(1):end,2)+1;
            end
        end
        t_dis = find(py(:,1)==round(0.75*N));
        class_yd(n)= py(t_dis(1), 2);
        class_yr(n) = 0;
    
              
        case {10,13,16,19,22,25,28,31,34}
        py(all(py==0,2),:)=[];
        for s=1:length(id_nan)
            h=find(py(:,2)==id_nan(s));
            if ~isempty(h)
            py(h(1):end,2) = py(h(1):end,2)+1;
            end
        end
        t_dis = find(py(:,1)==round(0.25*N));
        class_yd(n)= py(t_dis(1), 2);
        t_recovery = find(py(:,1)==round(0.25*N)-1+round(0.375*N-0.5)+1);
        class_yr(n) = py(t_recovery(1), 2);
               
        case {11,14,17,20,23,26,29,32,35}
        py(all(py==0,2),:)=[];
        for s=1:length(id_nan)
            h=find(py(:,2)==id_nan(s));
            if ~isempty(h)
             py(h(1):end,2) = py(h(1):end,2)+1;
            end
        end
        t_dis = find(py(:,1)==round(N/2));
        class_yd(n)= py(t_dis(1), 2);
        t_recovery = find(py(:,1)==round(N/2)-1+round(0.25*N-0.5)+1);
        class_yr(n) = py(t_recovery(1), 2);
        
        case {12,15,18,21,24,27,30,33,36}
        py(all(py==0,2),:)=[];
        for s=1:length(id_nan)
            h=find(py(:,2)==id_nan(s));
            if ~isempty(h)
            py(h(1):end,2) = py(h(1):end,2)+1;
            end
        end
         t_dis = find(py(:,1)==round(0.75*N));
         class_yd(n)= py(t_dis(1), 2);
         t_recovery = find(py(:,1)==round(0.75*N)-1+round(0.125*N-0.5)+1);
         class_yr(n) = py(t_recovery(1), 2);
       
        case {37,38,39,40}
        class_yd(n)= 0;
        class_yr(n) = 0;
        
        
        case {41,44,47}
        py(all(py==0,2),:)=[];
        for s=1:length(id_nan)
            h=find(py(:,2)==id_nan(s));
            if ~isempty(h)
            py(h(1):end,2) = py(h(1):end,2)+1;
            end
        end
        class_yd(n)= 0;
        t_recovery = find(py(:,1)==round(0.25*N));
        class_yr(n) = py(t_recovery(1), 2);
        
        case {42,45,48}
        py(all(py==0,2),:)=[];
        for s=1:length(id_nan)
            h=find(py(:,2)==id_nan(s));
            if ~isempty(h)
            py(h(1):end,2) = py(h(1):end,2)+1;
            end
        end
        class_yd(n)= 0;
        t_recovery = find(py(:,1)==round(N/2));
        class_yr(n) = py(t_recovery(1), 2);
        
        case {43,46,49}
        py(all(py==0,2),:)=[];
        for s=1:length(id_nan)
            h=find(py(:,2)==id_nan(s));
            if ~isempty(h)
            py(h(1):end,2) = py(h(1):end,2)+1;
            end
        end
        class_yd(n)= 0;
        t_recovery = find(py(:,1)==round(0.75*N));
        class_yr(n) = py(t_recovery(1), 2);
        
      
    end
end
y = class_test;
yd = class_yd;
yr = class_yr;