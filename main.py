import aiohttp
import asyncio
import os
import random
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType

class ProxyAccessTool:
    def __init__(self, throttle_delay=2):
        self.working_proxies = []
        self.proxy_file = "socks5.txt"
        self.throttle_delay = throttle_delay

    async def get_public_proxies(self):
        url = "https://www.proxy-list.download/api/v1/get?type=https"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    proxy_list = await response.text()
                    proxies = proxy_list.strip().split("\r\n")
                    return proxies
        return []

    async def check_proxy(self, session, proxy):
        try:
            async with session.get("http://example.com", proxy=f"http://{proxy}", timeout=5) as response:
                if response.status == 200:
                    return proxy
        except:
            pass
        return None

    async def filter_proxies(self, proxies):
        async with aiohttp.ClientSession() as session:
            tasks = [self.check_proxy(session, proxy) for proxy in proxies]
            results = await asyncio.gather(*tasks)
            self.working_proxies = [proxy for proxy in results if proxy is not None]

    def load_proxies_from_file(self):
        if os.path.exists(self.proxy_file):
            with open(self.proxy_file, "r") as file:
                proxies = file.read().splitlines()
            return proxies
        return []

    def save_proxies_to_file(self):
        with open(self.proxy_file, "w") as file:
            for proxy in self.working_proxies:
                file.write(proxy + "\n")

    def add_proxy(self, proxy):
        self.working_proxies.append(proxy)

    def remove_proxy(self, proxy):
        if proxy in self.working_proxies:
            self.working_proxies.remove(proxy)

    def get_working_proxies(self):
        return self.working_proxies

    def rotate_proxy(self):
        if len(self.working_proxies) > 1:
            self.working_proxies.append(self.working_proxies.pop(0))

    async def throttle(self):
        for proxy in self.working_proxies:
            await asyncio.sleep(self.throttle_delay)

    async def get(self, url, browser):
        options = webdriver.ChromeOptions()
        proxy = random.choice(self.working_proxies)
        options.add_argument(f"--proxy-server=http://{proxy}")
        if browser == "chrome":
            driver = webdriver.Chrome(options=options)
        elif browser == "firefox":
            driver = webdriver.Firefox(options=options)
        elif browser == "opera":
            driver = webdriver.Opera(options=options)
        elif browser == "edge":
            driver = webdriver.Edge(options=options)

        driver.get(url)
        await asyncio.sleep(5)  # Đợi trang web tải xong
        html_response = driver.page_source
        driver.quit()
        return html_response

async def concurrent_access(url, proxies, browsers):
    proxy_tool = ProxyAccessTool(throttle_delay=2)
    proxy_tool.working_proxies = proxies

    for browser in browsers:
        html_response = await proxy_tool.get(url, browser)
        print(f"Response from {browser} using proxy: {html_response}")

if __name__ == "__main__":
    # Example of loading proxy IPs from a file
    proxy_file_path = "socks5.txt"
    proxy_list = []
    with open(proxy_file_path, "r") as file:
        proxy_list = file.read().splitlines()

    # Get public proxies if no proxy list is available
    if not proxy_list:
        loop = asyncio.get_event_loop()
        proxy_tool = ProxyAccessTool()
        proxy_list = loop.run_until_complete(proxy_tool.get_public_proxies())

    # Filter proxies
    loop = asyncio.get_event_loop()
    filter_tool = ProxyAccessTool()
    loop.run_until_complete(filter_tool.filter_proxies(proxy_list))

    print("Các proxy hoạt động sau khi kiểm tra:")
    for proxy in filter_tool.get_working_proxies():
        print(proxy)

    # User input for URL and number of requests
    url_to_access = input("Nhập URL của trang web cần truy cập: ")
    num_requests = int(input("Nhập số lượng yêu cầu truy cập cần gửi: "))

    # Example of accessing a website using multiple working proxies and browsers concurrently
    browsers_to_use = ["chrome", "firefox", "opera", "edge"]  # Thêm các trình duyệt khác nếu bạn muốn

    async def multiple_requests():
        tasks = [concurrent_access(url_to_access, filter_tool.get_working_proxies(), browsers_to_use) for _ in range(num_requests)]
        await asyncio.gather(*tasks)

    loop.run_until_complete(multiple_requests())
