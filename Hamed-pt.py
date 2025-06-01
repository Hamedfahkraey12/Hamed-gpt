import requests
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urlparse, urljoin
import socket
import warnings
import re
from bs4 import XMLParsedAsHTMLWarning
import argparse
import csv
import arabic_reshaper 
from bidi.algorithm import get_display 

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def get_page_title(html_text):
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            matn_input = (title)
            dorost = arabic_reshaper.reshape(matn_input) 
            p_do= get_display(dorost)
            if len(p_do) > 30:
                
                return p_do[:27] + "..."
            return p_do
        else:
            return "No Title"
    except Exception:
        return "No Title"


def extract_valid_iranian_phones(text):
  
    email_pattern = r'[a-zA-Z0-9_.+-]+@gmail\.[a-zA-Z]{2,}'
    
    # email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b" اگر بخواهیم ایمیل های جامع تری رو پوشش بده از این الگو استفاده میکنیم
    
    emails = re.findall(email_pattern, text)


    phone_pattern = r"(?:\+98|0098|0)?(9\d{9})\b"
    raw_phones = re.findall(phone_pattern, text)

    def is_valid(num):
        return (
            num.startswith("9") and
            len(num) == 10 and
            not re.fullmatch(r"(0|1|9)\1{8}", num)  
        )

    valid_phones = ["0" + num for num in raw_phones if is_valid(num)]

    emails_str = ", ".join(sorted(set(emails))) if emails else "No email found"
    phones_str = ", ".join(sorted(set(valid_phones))) if valid_phones else "No valid Iranian phone number found"

    return emails_str, phones_str



def crawl_site(start_url, max_depth=2):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    BLOCKED_DOMAINS = ["instagram.com", "linkedin.com", "twitter.com", "facebook.com",
        "support.google.com", "t.me", "youtube.com", "policies.google.com",
        "adssettings.google.com", "cyberpolice.ir", "play.google.com", "www.waze.com",
        "sustainability.google", "ai.google", "youtu.be", "l.vrgl.ir", "x.com",
        "www.netspi.com", "book.hacktricks.xyz", "Evss.ir", "filmilla.com"
    ]
    site_map = {}
    visited = set()

    queue = deque()
    queue.append((start_url, 0))

    while queue:
        url, depth_level = queue.popleft()

        if depth_level > max_depth or url in visited:
            continue

        visited.add(url)
        links = []

        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            for tag in soup.find_all("a", href=True):
                href = tag.get("href").strip()
                full_url = urljoin(url, href)

                if (
                    full_url.startswith("http")
                    and not any(domain in full_url for domain in BLOCKED_DOMAINS)
                    and full_url not in visited
                ):
                    links.append(full_url)
        except requests.exceptions.RequestException as e:
            print(f"[❌] Failed to fetch {url}: {e}")

        site_map[url] = sorted(links)
        for link in links:
            if link not in visited:
                queue.append((link, depth_level + 1))

    return site_map

def shorten_text(text, max_len=30):
    if len(text) <= max_len:
        return text
    return text[:15] + "..." + text[-12:]

def print_url_table(numbered_urls, domain, output_file="hamed.txt"):
    with open(output_file, "a", encoding="utf-8") as out_file:
        out_file.write(
            "| {:<5} | {:<50} | {:<15} | {:<6} | {:<8} | {:<30} | {:<30} | {:<20} |\n".format(
                "Index", "URL", "IP Address", "Status", "Type", "Title", "Emails", "Phones"
            )
        )
        out_file.write("-" * 205 + "\n")

        print("\n--- URL Table with IP, Status, Title, Emails & Phones ---")
        print("| {:<5} | {:<50} | {:<15} | {:<6} | {:<8} | {:<30} | {:<30} | {:<20} |".format(
            "Index", "URL", "IP Address", "Status", "Type", "Title", "Emails", "Phones"
        ))
        print("-" * 205)

        for index, url in numbered_urls.items():
            try:
                domain_name = urlparse(url).hostname
                ip_address = socket.gethostbyname(domain_name)
            except Exception:
                ip_address = "⛔️ Not Resolved"
                domain_name = None

            try:
                main_domain = urlparse("https://" + domain).hostname
                matn_input = ("داخلی")
                dorost = arabic_reshaper.reshape(matn_input) 
                p_do1 = get_display(dorost)
                matn_input = ("خارجی")
                dorost = arabic_reshaper.reshape(matn_input) 
                p_do2 = get_display(dorost)
                matn_input = ("نامشخص")
                dorost = arabic_reshaper.reshape(matn_input) 
                p_do3 = get_display(dorost)
                if domain_name and main_domain and domain_name.endswith(main_domain):
                
                    domain_type = (f"🟢 {p_do1} 🔴")
                else:
                    domain_type = (f"🌍{p_do2}")
            except:
                domain_type = (f"🌍{p_do3}")

            try:
                response = requests.get(url, timeout=5)
                status = response.status_code
                title_tag = get_page_title(response.text)
                emails, phones = extract_valid_iranian_phones(response.text)
            except Exception:
                status = "⚠️ Error"
                title_tag = "No Title"
                emails = "No email found"
                phones = "No phone found"

            line = "| {:<5} | {:<50} | {:<15} | {:<6} | {:<8} | {:<30} | {:<30} | {:<20} |".format(
                index, url, ip_address, str(status), domain_type,
                title_tag, emails, phones
            )

            print(line)
            out_file.write(line + "\n")  # ✅ الان داخل with هست
def scan_subdomains(domain, input_file="wordlist.txt", output_file="hamed.txt"):
    PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 8080]

    success_count = 0
    fail_count = 0

    try:
        with open(output_file, "w", encoding="utf-8") as out_file:
            try:
                with open(input_file, "r", encoding="utf-8") as file:
                    for line in file:
                        sub = line.strip()
                        if not sub:
                            continue

                        full_domain = f"{sub}.{domain}"

                        try:
                            ip = socket.gethostbyname(full_domain)
                        except socket.gaierror:
                            ip = None

                        if ip is None:
                            fail_count += 1
                            status = "⛔️ Not Resolved"
                            ports_info = "-"
                            title_tag = "No Title"
                            print(f"[❌] {full_domain} cannot be resolved.")
                            out_file.write(f"{fail_count}  {full_domain}  {status}  {ports_info}  {title_tag}\n")
                            continue

                        status = "N/A"
                        title_tag = "No Title"
                        try:
                            response = requests.get(f"https://{full_domain}", timeout=5)
                            status = response.status_code
                            title_tag = get_page_title(response.text)
                        except requests.exceptions.RequestException:
                            try:
                                response = requests.get(f"http://{full_domain}", timeout=5)
                                status = response.status_code
                                title_tag = get_page_title(response.text)
                            except requests.exceptions.RequestException:
                                status = "⚠️ No Response"
                                title_tag = "No Title"

                        if len(title_tag) > 40:
                            title_tag = title_tag[:37] + "..."

                        open_ports = []
                        for port in PORTS:
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.settimeout(0.5)
                            try:
                                s.connect((ip, port))
                                open_ports.append(port)
                            except:
                                pass
                            finally:
                                s.close()

                        if open_ports:
                            ports_info = "Open ports: " + ", ".join(str(p) for p in open_ports)
                        else:
                            ports_info = "No open ports"

                        success_count += 1
                        print(f"{success_count} [✅] {full_domain} → {ip} | Status: {status} | Open Ports: {ports_info} | Title: {title_tag}")
                        out_file.write(f"{success_count}  {full_domain}  {ip}  {status}  Ports: {ports_info}  Title: {title_tag}\n")

            except FileNotFoundError:
                print("❗️ file wordlist.txt not found.")

    except Exception as e:
        print("Error writing output file:", e)
import whois

def get_whois_info(domain):
    print("\n--- WHOIS Info ---")
    try:
        w = whois.whois(domain)
        print(f"Domain: {domain}")
        print(f"Registrar: {w.registrar}")
        print(f"Creation Date: {w.creation_date}")
        print(f"Expiration Date: {w.expiration_date}")
        print(f"Name Servers: {w.name_servers}")
        print(f"Emails: {w.emails}")
        print(f"Country: {w.country}")
    except Exception as e:
        print(f"Failed to fetch WHOIS info: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Crawler & Subdomain Scanner")
    parser.add_argument("--domain", required=True, help="Website domain without https:// (e.g. example.com)")
    args = parser.parse_args()

    domain = args.domain.strip()
    start_url = "https://" + domain

    site_map = crawl_site(start_url, max_depth=2)

    counter = 1
    numbered_urls = {}
    seen_urls = set()

    for url, links in site_map.items():
        if url not in seen_urls:
            numbered_urls[counter] = url
            counter += 1
            seen_urls.add(url)

        for link in links:
            if link not in seen_urls:
                numbered_urls[counter] = link
                counter += 1
                seen_urls.add(link)

    print_url_table(numbered_urls, domain)


    get_whois_info(domain)
    
    scan_subdomains(domain,output_file="hamed.txt")
    
    # python .\Hamed-pt.py --domain 