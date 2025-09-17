import requests
from concurrent.futures import ThreadPoolExecutor

M3U_URL = "https://raw.githubusercontent.com/mytv-android/China-TV-Live-M3U8/refs/heads/main/iptv.m3u"
# M3U_URL = "https://raw.githubusercontent.com/mytv-android/BRTV-Live-M3U8/refs/heads/main/iptv.m3u"

VALID_FILE = "valid.m3u"


def get_m3u():
    """下载远程 M3U 文件"""
    response = requests.get(M3U_URL, timeout=10)
    response.raise_for_status()
    return response.text


def check_url(url, timeout=5):
    """检测直播源是否可用（HEAD 优先，GET 兜底）"""
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return True
    except Exception:
        pass

    try:
        r = requests.get(url, stream=True, timeout=timeout)
        if r.status_code == 200:
            for _ in r.iter_content(chunk_size=1024):
                return True
    except Exception:
        return False

    return False


def generate_valid_m3u():
    """解析、检测并保存有效频道"""
    data = get_m3u().splitlines()

    def parse_channel(i):
        line = data[i].strip()
        if line.startswith("#EXTINF"):
            if "," in line:
                channel_name = line.split(",")[-1]
            else:
                channel_name = "未知频道"

            if i + 1 < len(data) and data[i + 1].startswith("http"):
                url = data[i + 1].strip()
                if check_url(url):
                    return f"{line}\n{url}"
        return None

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(parse_channel, range(len(data)))

    valid_entries = ["#EXTM3U"] + [r for r in results if r]

    with open(VALID_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(valid_entries))

    print(f"[保存成功] {VALID_FILE}, 可用频道数: {len(valid_entries) - 1}")


if __name__ == "__main__":
    generate_valid_m3u()
