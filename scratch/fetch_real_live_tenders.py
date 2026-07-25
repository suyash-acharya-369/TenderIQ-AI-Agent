import sys
import os
import json
import httpx
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))


def test_live_sources():
    print("=== 1. WORLD BANK REAL PROCUREMENT API ===")
    try:
        url = "https://search.worldbank.org/api/v2/procurement?format=json&rows=10"
        res = httpx.get(url, timeout=10.0, headers={"User-Agent": "Mozilla/5.0"})
        data = res.json()
        proc = data.get("procnotices", {})
        count = 0
        for k, v in proc.items():
            if isinstance(v, dict):
                count += 1
                notice_id = v.get("id") or k
                proj_name = v.get("project_name") or v.get("title") or "World Bank Project"
                country = v.get("countryname") or "Global"
                proc_url = v.get("url") or f"https://projects.worldbank.org/en/projects-operations/procurement-detail/{notice_id}"
                date_str = v.get("submission_date") or v.get("posting_date")
                print(f"[{count}] ID: {notice_id} | Country: {country} | Project: {proj_name[:60]}")
                print(f"     URL: {proc_url}")
                if count >= 5:
                    break
    except Exception as e:
        print("WB API Error:", e)

    print("\n=== 2. UNGM REAL PUBLIC RSS NOTICES ===")
    try:
        url = "https://www.ungm.org/Public/Notice/Feed/Rss"
        res = httpx.get(url, timeout=10.0, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(res.content)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []
        for i, item in enumerate(items[:5], 1):
            title = item.findtext("title")
            link = item.findtext("link")
            guid = item.findtext("guid")
            print(f"[{i}] Title: {title}")
            print(f"     Link: {link} | Ref/GUID: {guid}")
    except Exception as e:
        print("UNGM RSS Error:", e)

    print("\n=== 3. DEVNET JOBS REAL PUBLIC TENDERS ===")
    try:
        url = "https://devnetjobs.org"
        res = httpx.get(url, timeout=10.0, headers={"User-Agent": "Mozilla/5.0"})
        print(f"DevNetJobs Status: {res.status_code}")
    except Exception as e:
        print("DevNetJobs Error:", e)


if __name__ == "__main__":
    test_live_sources()
