from tj_dual_arm import TJDualArm
import time

if __name__ == '__main__':
    tj = TJDualArm()
    t1 = time.perf_counter()
    print(tj.get_current_joints())
    print(time.perf_counter()-t1)