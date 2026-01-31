function outputs = detectMiningDisturbance(ndviPath, bareCoalPath, outDir, startyear)
% ndviPath: NDVI长时序GeoTIFF（多波段）
% bareCoalPath: 裸煤概率GeoTIFF（多波段）
% outDir: 输出目录（本函数会创建）
% startyear: 起始年份（整数）

    if ~exist(outDir, 'dir')
        mkdir(outDir);
    end

    % 统一输出文件名（平台前端/后端都按这些名字找结果）
    out_mask            = fullfile(outDir, 'mining_disturbance_mask.tif');  % polygon_disturbance
    out_dist_year       = fullfile(outDir, 'mining_disturbance_year.tif');  % year_miningdisturbance
    out_recv_year       = fullfile(outDir, 'mining_recovery_year.tif');     % year_miningrecovery

    out_potential       = fullfile(outDir, 'potential_disturbance.tif');    % 中间
    out_res_type        = fullfile(outDir, 'res_disturbance_type.tif');     % 中间
    out_year_disturb    = fullfile(outDir, 'year_disturbance_raw.tif');     % 中间
    out_year_recovery   = fullfile(outDir, 'year_recovery_raw.tif');        % 中间

    % ============ 粘贴你的 MATLAB 核心代码到这里，并将读写路径改为参数变量 ============
    clearvars -except ndviPath bareCoalPath outDir startyear out_mask out_dist_year out_recv_year out_potential out_res_type out_year_disturb out_year_recovery;
    clc;

    [a, R] = geotiffread(ndviPath);
    info = geotiffinfo(ndviPath); %#ok<NASGU>

    a(a==0)=NaN;
    a(a>=1)=NaN;
    a(a<-1)=0;
    [m, n, l] = size(a);

    s = ljpl(a);
    a(a>1)=1;
    a(a<0)=0;
    b = reshape(a, m*n, l, 1);
    b(all(isnan(b),2),:) = 0;
    clear a;
    e = b;
    b(all(b==0,2),:) = [];

    sample = creat_sample(s, l, 0.8, 0.6);
    sample_label = single(sample(:, l+1));
    trainData = single(sample(:, 1:l));

    k = 1;
    [c, y1, y2] = knn(trainData, sample_label, b, k);

    h = find(all(e==0,2));
    for i=1:length(h)
        c  = [c(1:h(i)-1);  zeros(1,1); c(h(i):end)];
        y1 = [y1(1:h(i)-1); zeros(1,1); y1(h(i):end)];
        y2 = [y2(1:h(i)-1); zeros(1,1); y2(h(i):end)];
    end

    res_disturbance = reshape(c, m, n);
    yeardisturbance = reshape(y1, m, n);
    yearrecovery    = reshape(y2, m, n);

    bw = res_disturbance;
    bw(bw==38 | bw==39 | bw==40 | isnan(bw)) = 0;
    bw(bw~=0) = 1;
    se = strel('disk',2);
    openbw = imopen(bw, se);
    [polygon_disturbance, ~] = bwlabel(openbw, 8);
    potential_disturbance = polygon_disturbance;

    [barecoal_p, ~] = geotiffread(bareCoalPath);
    barecoal_p(isnan(barecoal_p))=0;
    barecoal_p(barecoal_p<=0.5)=0;
    barecoal_p(barecoal_p>0.5)=1;
    sum_barecoal = sum(barecoal_p, 3);
    sum_barecoal(sum_barecoal~=0)=1;
    sum_barecoal = medfilt2(sum_barecoal, [5 5]);

    Union = sum_barecoal .* polygon_disturbance;
    Union = reshape(Union, m*n, 1);
    Union(Union==0) = [];
    Union = unique(Union);

    for i=1:length(Union)
        s2 = polygon_disturbance;
        s2(s2~=Union(i))=0;
        s2(s2==Union(i))=1;
        total_num = sum(sum(s2));
        s1 = s2 .* sum_barecoal;
        s1(s1~=0)=1;
        union_num = sum(sum(s1));
        if total_num >= 1111 && (union_num >= 222 && union_num/total_num >= 0.02)
            polygon_disturbance(polygon_disturbance==Union(i)) = -1;
        end
    end

    polygon_disturbance(polygon_disturbance~=-1)=0;
    polygon_disturbance(polygon_disturbance==-1)=1;

    year_miningdisturbance = polygon_disturbance .* yeardisturbance;
    year_miningdisturbance = year_miningdisturbance + startyear - 1;
    year_miningdisturbance(year_miningdisturbance == startyear - 1) = 0;

    year_miningrecovery = polygon_disturbance .* yearrecovery;
    year_miningrecovery = year_miningrecovery + startyear - 1;
    year_miningrecovery(year_miningrecovery == startyear - 1) = 0;

    % 写出结果（统一按平台文件名写）
    geotiffwrite(out_mask, polygon_disturbance, R);
    geotiffwrite(out_dist_year, year_miningdisturbance, R);
    geotiffwrite(out_recv_year, year_miningrecovery, R);

    % 中间变量
    geotiffwrite(out_potential, potential_disturbance, R);
    geotiffwrite(out_res_type, res_disturbance, R);
    geotiffwrite(out_year_disturb, yeardisturbance, R);
    geotiffwrite(out_year_recovery, yearrecovery, R);
    % ============ 到这里结束 ============

    outputs = struct();
    outputs.mask = out_mask;
    outputs.disturbance_year = out_dist_year;
    outputs.recovery_year = out_recv_year;
    outputs.potential = out_potential;
    outputs.res_type = out_res_type;
    outputs.year_disturb_raw = out_year_disturb;
    outputs.year_recovery_raw = out_year_recovery;
end
