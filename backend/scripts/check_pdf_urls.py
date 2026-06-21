import httpx

def main():
    urls = [
        "https://www.w3.org/WAI/WCAG21/Techniques/pdf/sample.pdf",
        "https://pdfobject.com/pdf/sample.pdf",
        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=1200"
    ]
    for url in urls:
        try:
            r = httpx.get(url, follow_redirects=True, timeout=10.0)
            print(f"URL: {url}")
            print(f"  Status: {r.status_code}")
            print(f"  Content-Type: {r.headers.get('content-type')}")
            print(f"  Content-Length: {r.headers.get('content-length')}")
            print(f"  Server: {r.headers.get('server')}")
        except Exception as e:
            print(f"URL: {url} failed: {e}")
        print("-" * 50)

if __name__ == "__main__":
    main()
