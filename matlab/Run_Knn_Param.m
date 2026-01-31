function Run_Knn_Param(startyear, ndvi_path, barecoal_path, out_dir)
% Run_Knn_Param Parameterized version of Run_Knn for pipeline execution.

if nargin < 4
    error('Run_Knn_Param requires startyear, ndvi_path, barecoal_path, out_dir');
end

[a, R] = geotiffread(ndvi_path);
info = geotiffinfo(ndvi_path); %#ok<NASGU>

% sanitize NDVI
A = double(a);
A(A == 0) = NaN;
A(A >= 1) = NaN;
A(A < -1) = 0;
[m, n, l] = size(A);

s = ljpl(A);
A(A > 1) = 1;
A(A < 0) = 0;

b = reshape(A, m * n, l, 1);
b(all(isnan(b), 2), :) = 0;
clear A;

e = b;
b(all(b == 0, 2), :) = [];

sample = creat_sample(s, l, 0.8, 0.6); % Create samples
sample_label = sample(:, l + 1);

sample_label = single(sample_label);
trainData = sample(:, 1:l);
trainData = single(trainData);

k = 1;
[c, y1, y2] = knn(trainData, sample_label, b, k);

h = find(all(e == 0, 2));
for i = 1:length(h)
    c = [c(1:h(i) - 1); zeros(1, 1); c(h(i):end)];
    y1 = [y1(1:h(i) - 1); zeros(1, 1); y1(h(i):end)];
    y2 = [y2(1:h(i) - 1); zeros(1, 1); y2(h(i):end)];
end

res_disturbance = reshape(c, m, n);
yeardisturbance = reshape(y1, m, n);
yearrecovery = reshape(y2, m, n);

bw = res_disturbance;
bw(bw == 38 | bw == 39 | bw == 40 | isnan(bw)) = 0;
bw(bw ~= 0) = 1;
se = strel('disk', 2);
openbw = imopen(bw, se);
[polygon_disturbance, num] = bwlabel(openbw, 8); %#ok<NASGU>
potential_disturbance = polygon_disturbance;

[barecoal_p, R2] = geotiffread(barecoal_path); %#ok<ASGLU>

barecoal_p(isnan(barecoal_p)) = 0;
barecoal_p(barecoal_p <= 0.5) = 0;
barecoal_p(barecoal_p > 0.5) = 1;

sum_barecoal = sum(barecoal_p, 3);
sum_barecoal(sum_barecoal ~= 0) = 1;
sum_barecoal = medfilt2(sum_barecoal, [5 5]);

Union = sum_barecoal .* polygon_disturbance;
[m2, n2] = size(sum_barecoal);
Union = reshape(Union, m2 * n2, 1);
Union(Union == 0) = [];
Union = unique(Union);

for i = 1:length(Union)
    s = polygon_disturbance;
    s(s ~= Union(i)) = 0;
    s(s == Union(i)) = 1;
    total_num = sum(sum(s));
    s1 = s .* sum_barecoal;
    s1(s1 ~= 0) = 1;
    union_num = sum(sum(s1));
    if total_num >= 1111 && (union_num >= 222 && union_num / total_num >= 0.02)
        polygon_disturbance(polygon_disturbance == Union(i)) = -1;
    end
end

polygon_disturbance(polygon_disturbance ~= -1) = 0;
polygon_disturbance(polygon_disturbance == -1) = 1;

year_miningdisturbance = polygon_disturbance .* yeardisturbance;
year_miningdisturbance = year_miningdisturbance + startyear - 1;
year_miningdisturbance(year_miningdisturbance == startyear - 1) = 0;

year_miningrecovery = polygon_disturbance .* yearrecovery;
year_miningrecovery = year_miningrecovery + startyear - 1;
year_miningrecovery(year_miningrecovery == startyear - 1) = 0;

if ~exist(out_dir, 'dir')
    mkdir(out_dir);
end

geotiffwrite(fullfile(out_dir, 'polygon_disturbanc.tif'), polygon_disturbance, R);
geotiffwrite(fullfile(out_dir, 'year_miningdisturbance.tif'), year_miningdisturbance, R);
geotiffwrite(fullfile(out_dir, 'year_miningrecovery.tif'), year_miningrecovery, R);
geotiffwrite(fullfile(out_dir, 'potential_disturbance.tif'), potential_disturbance, R);
geotiffwrite(fullfile(out_dir, 'res_disturbance.tif'), res_disturbance, R);
geotiffwrite(fullfile(out_dir, 'yeardisturbance.tif'), yeardisturbance, R);
geotiffwrite(fullfile(out_dir, 'yearrecovery.tif'), yearrecovery, R);

end
