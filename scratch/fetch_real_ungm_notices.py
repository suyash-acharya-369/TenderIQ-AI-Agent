import httpx
from bs4 import BeautifulSoup
import re

def fetch_ungm_notices():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    url = "https://www.ungm.org/Public/Notice"
    with httpx.Client(timeout=15.0, follow_redirects=True, headers=headers) as client:
        res = client.get(url)
        print(f"UNGM Status: {res.status_code}, Length: {len(res.text)}")
        soup = BeautifulSoup(res.text, "lxml")

        # Search for notice rows or links
        notice_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            txt = a.get_text(strip=True)
            if "/Public/Notice/" in href and href != "/Public/Notice":
                notice_links.append((txt, "https://www.ungm.org" + href if href.startswith("/") else href))

        print(f"Found {len(notice_links)} notice links:")
        for txt, link in notice_links[:10]:
            print(f" - {txt[:50]} | {link}")

if __name__ == "__main__":
    fetch_ungm_notices()
