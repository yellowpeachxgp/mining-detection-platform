#!/usr/bin/env python
"""
检测MATLAB引擎是否可用
"""

print("\n" + "="*60)
print("  MATLAB Engine Detection Tool")
print("="*60 + "\n")

# 检查1: 导入MATLAB引擎
print("[1/3] Checking MATLAB.engine module...")
try:
    import matlab.engine
    print("✓ MATLAB.engine module found")
except ImportError as e:
    print(f"✗ MATLAB.engine not found: {e}")
    print("\nSolution:")
    print("  1. Find your MATLAB installation directory")
    print("  2. Go to: <MATLAB_ROOT>\\extern\\engines\\python")
    print("  3. Run: python setup.py install")
    print("\nExample for MATLAB 2024b:")
    print("  cd E:\\Matlab2024b\\extern\\engines\\python")
    print("  python setup.py install")
    exit(1)

# 检查2: 启动MATLAB
print("\n[2/3] Starting MATLAB engine...")
try:
    eng = matlab.engine.start_matlab()
    print("✓ MATLAB engine started successfully")
except Exception as e:
    print(f"✗ Failed to start MATLAB: {e}")
    print("\nPossible issues:")
    print("  - MATLAB not installed")
    print("  - MATLAB license expired")
    print("  - MATLAB is already running elsewhere")
    exit(1)

# 检查3: 测试简单函数
print("\n[3/3] Testing MATLAB functionality...")
try:
    result = eng.version(nargout=1)
    print(f"✓ MATLAB version: {result}")
    print("\n✓ MATLAB engine is working correctly!")
except Exception as e:
    print(f"✗ MATLAB function failed: {e}")
    exit(1)

print("\n" + "="*60)
print("All tests passed! MATLAB is ready to use.")
print("="*60 + "\n")

# 关闭引擎
try:
    eng.quit()
except:
    pass
