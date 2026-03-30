# DESC: 显示当前系统状态（CPU、内存、磁盘）
"""系统状态查看技能 — 展示基本系统信息。"""

import platform
import shutil
import os


def main():
    print("=" * 40)
    print("  系统状态报告")
    print("=" * 40)

    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"机器架构: {platform.machine()}")
    print(f"Python:   {platform.python_version()}")

    # 磁盘
    usage = shutil.disk_usage("/")
    total_gb = usage.total / (1024 ** 3)
    used_gb = usage.used / (1024 ** 3)
    free_gb = usage.free / (1024 ** 3)
    print(f"\n磁盘: {used_gb:.1f}GB / {total_gb:.1f}GB (剩余 {free_gb:.1f}GB)")

    # 负载
    load = os.getloadavg()
    print(f"系统负载: {load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}")

    print("=" * 40)


if __name__ == "__main__":
    main()
