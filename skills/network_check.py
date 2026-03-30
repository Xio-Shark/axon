# DESC: 检测网络连通性和外网 IP
import urllib.request
import json


def main():
    print("=" * 40)
    print("  网络连通性检测")
    print("=" * 40)

    # 测试连通性
    targets = [
        ("百度", "https://www.baidu.com"),
        ("GitHub", "https://github.com"),
    ]
    for name, url in targets:
        try:
            urllib.request.urlopen(url, timeout=5)
            print(f"  ✅ {name}: 可达")
        except Exception:
            print(f"  ❌ {name}: 不可达")

    # 获取外网 IP
    try:
        resp = urllib.request.urlopen(
            "https://httpbin.org/ip", timeout=5,
        )
        ip = json.loads(resp.read())["origin"]
        print(f"\n  外网 IP: {ip}")
    except Exception:
        print("\n  外网 IP: 获取失败")


if __name__ == "__main__":
    main()
