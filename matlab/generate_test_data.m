% generate_test_data.m
% 生成测试数据和预期结果，用于验证 Python 实现
%
% 运行方式: 在 MATLAB 中执行此脚本
% 输出: test_validation_data.mat (包含所有测试用例和预期结果)

clear all;
clc;

fprintf('Generating validation data for Python testing...\n\n');

%% 1. DTW 测试用例
fprintf('1. DTW Test Cases\n');

% Case 1: 相同序列
r1 = [1.0, 2.0, 3.0, 4.0, 5.0];
t1 = [1.0, 2.0, 3.0, 4.0, 5.0];
[dist1, path1] = dtw(r1, t1);
fprintf('   Case 1 (identical): dist = %.6f\n', dist1);

% Case 2: 偏移序列
r2 = [1.0, 2.0, 3.0, 4.0, 5.0];
t2 = [2.0, 3.0, 4.0, 5.0, 6.0];
[dist2, path2] = dtw(r2, t2);
fprintf('   Case 2 (shifted): dist = %.6f\n', dist2);

% Case 3: 不同长度
r3 = [1.0, 2.0, 3.0];
t3 = [1.0, 1.5, 2.0, 2.5, 3.0];
[dist3, path3] = dtw(r3, t3);
fprintf('   Case 3 (diff length): dist = %.6f\n', dist3);

% Case 4: 全相等序列 (测试路径优先级)
r4 = [1.0, 1.0, 1.0];
t4 = [1.0, 1.0, 1.0];
[dist4, path4] = dtw(r4, t4);
fprintf('   Case 4 (all equal - priority test): dist = %.6f\n', dist4);
fprintf('   Path: '); disp(path4');

dtw_tests = struct();
dtw_tests.case1 = struct('r', r1, 't', t1, 'dist', dist1, 'path', path1);
dtw_tests.case2 = struct('r', r2, 't', t2, 'dist', dist2, 'path', path2);
dtw_tests.case3 = struct('r', r3, 't', t3, 'dist', dist3, 'path', path3);
dtw_tests.case4 = struct('r', r4, 't', t4, 'dist', dist4, 'path', path4);

%% 2. BWlvbo 测试用例
fprintf('\n2. BWlvbo Test Cases\n');

% Case 1: 带尖峰的序列
signal1 = [0.8, 0.3, 0.8, 0.7, 0.75];
result1 = BWlvbo(signal1);
fprintf('   Case 1 (spike): input = [%.2f, %.2f, %.2f, %.2f, %.2f]\n', signal1);
fprintf('                   output length = %d\n', length(result1));

% Case 2: 平滑序列
signal2 = [0.7, 0.72, 0.68, 0.65, 0.63, 0.60, 0.58, 0.55, 0.52, 0.50];
result2 = BWlvbo(signal2);
fprintf('   Case 2 (smooth): output length = %d\n', length(result2));

bwlvbo_tests = struct();
bwlvbo_tests.case1 = struct('input', signal1, 'output', result1);
bwlvbo_tests.case2 = struct('input', signal2, 'output', result2);

%% 3. vegetation_recovery 测试用例
fprintf('\n3. vegetation_recovery Test Cases\n');

a_vr = [0.2, 0.8];  % [low, target]
b_vr = [1, 2, 3, 4, 5];
result_vr = vegetation_recovery(a_vr, b_vr);
fprintf('   a = [%.2f, %.2f], b = [1:5]\n', a_vr);
fprintf('   result = [%.4f, %.4f, %.4f, %.4f, %.4f]\n', result_vr);

vr_tests = struct();
vr_tests.case1 = struct('a', a_vr, 'b', b_vr, 'result', result_vr);

%% 4. creat_sample 测试用例
fprintf('\n4. creat_sample Test Cases\n');

s_cs = [0.2, 0.8];
length_cs = 15;
p1_cs = 0.8;
p2_cs = 0.6;
samples = creat_sample(s_cs, length_cs, p1_cs, p2_cs);
fprintf('   Shape: %d x %d\n', size(samples, 1), size(samples, 2));
fprintf('   Labels: %d to %d\n', min(samples(:, end)), max(samples(:, end)));
fprintf('   Template 1 (first 5): [%.2f, %.2f, %.2f, %.2f, %.2f]\n', samples(1, 1:5));
fprintf('   Template 37 (first 5): [%.2f, %.2f, %.2f, %.2f, %.2f]\n', samples(37, 1:5));
fprintf('   Template 38 (first 5): [%.2f, %.2f, %.2f, %.2f, %.2f]\n', samples(38, 1:5));

sample_tests = struct();
sample_tests.s = s_cs;
sample_tests.length = length_cs;
sample_tests.p1 = p1_cs;
sample_tests.p2 = p2_cs;
sample_tests.samples = samples;

%% 5. ljpl 测试用例
fprintf('\n5. ljpl Test Cases\n');

% 创建已知分布的测试数据
rng(42);  % 固定随机种子
data_ljpl = rand(10, 10, 5) * 0.8 + 0.1;  % 0.1 到 0.9
data_ljpl(1, 1, :) = 0;  % 添加零值
data_ljpl(2, 2, :) = NaN;  % 添加 NaN

result_ljpl = ljpl(data_ljpl);
fprintf('   Result: [%.6f, %.6f]\n', result_ljpl);

ljpl_tests = struct();
ljpl_tests.data = data_ljpl;
ljpl_tests.result = result_ljpl;

%% 6. KNN 年份提取测试
fprintf('\n6. Year Extraction Test Cases\n');

N_test = 15;
% 创建简单的恒等路径
path_test = [(1:15)', (1:15)'];

% 测试不同标签的年份提取
labels_to_test = [1, 2, 3, 10, 11, 12, 37, 38, 41, 42, 43];
year_results = zeros(length(labels_to_test), 3);  % [label, yd, yr]

for i = 1:length(labels_to_test)
    label = labels_to_test(i);
    [yd, yr] = extract_year_for_label(path_test, label, N_test);
    year_results(i, :) = [label, yd, yr];
    fprintf('   Label %d: yd=%d, yr=%d\n', label, yd, yr);
end

year_tests = struct();
year_tests.N = N_test;
year_tests.path = path_test;
year_tests.results = year_results;

%% 保存所有测试数据
fprintf('\nSaving validation data...\n');
save('test_validation_data.mat', 'dtw_tests', 'bwlvbo_tests', 'vr_tests', ...
     'sample_tests', 'ljpl_tests', 'year_tests', '-v7.3');
fprintf('Done! File saved as test_validation_data.mat\n');

%% 辅助函数：年份提取（简化版）
function [yd, yr] = extract_year_for_label(py, label, N)
    r = @(x) round(x);
    yd = 0;
    yr = 0;

    switch label
        case {1, 4, 7}
            target = r(0.25 * N);
            t_dis = find(py(:, 1) == target);
            if ~isempty(t_dis)
                yd = py(t_dis(1), 2);
            end

        case {2, 5, 8}
            target = r(N / 2);
            t_dis = find(py(:, 1) == target);
            if ~isempty(t_dis)
                yd = py(t_dis(1), 2);
            end

        case {3, 6, 9}
            target = r(0.75 * N);
            t_dis = find(py(:, 1) == target);
            if ~isempty(t_dis)
                yd = py(t_dis(1), 2);
            end

        case {10, 13, 16, 19, 22, 25, 28, 31, 34}
            target_d = r(0.25 * N);
            t_dis = find(py(:, 1) == target_d);
            if ~isempty(t_dis)
                yd = py(t_dis(1), 2);
            end
            target_r = r(0.25 * N) - 1 + r(0.375 * N - 0.5) + 1;
            t_rec = find(py(:, 1) == target_r);
            if ~isempty(t_rec)
                yr = py(t_rec(1), 2);
            end

        case {11, 14, 17, 20, 23, 26, 29, 32, 35}
            target_d = r(N / 2);
            t_dis = find(py(:, 1) == target_d);
            if ~isempty(t_dis)
                yd = py(t_dis(1), 2);
            end
            target_r = r(N / 2) - 1 + r(0.25 * N - 0.5) + 1;
            t_rec = find(py(:, 1) == target_r);
            if ~isempty(t_rec)
                yr = py(t_rec(1), 2);
            end

        case {12, 15, 18, 21, 24, 27, 30, 33, 36}
            target_d = r(0.75 * N);
            t_dis = find(py(:, 1) == target_d);
            if ~isempty(t_dis)
                yd = py(t_dis(1), 2);
            end
            target_r = r(0.75 * N) - 1 + r(0.125 * N - 0.5) + 1;
            t_rec = find(py(:, 1) == target_r);
            if ~isempty(t_rec)
                yr = py(t_rec(1), 2);
            end

        case {37, 38, 39, 40}
            yd = 0;
            yr = 0;

        case {41, 44, 47}
            target_r = r(0.25 * N);
            t_rec = find(py(:, 1) == target_r);
            if ~isempty(t_rec)
                yr = py(t_rec(1), 2);
            end

        case {42, 45, 48}
            target_r = r(N / 2);
            t_rec = find(py(:, 1) == target_r);
            if ~isempty(t_rec)
                yr = py(t_rec(1), 2);
            end

        case {43, 46, 49}
            target_r = r(0.75 * N);
            t_rec = find(py(:, 1) == target_r);
            if ~isempty(t_rec)
                yr = py(t_rec(1), 2);
            end
    end
end
