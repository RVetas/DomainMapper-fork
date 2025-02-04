﻿import os
import requests
import dns.resolver
from concurrent.futures import ThreadPoolExecutor
import ipaddress
import re
import configparser

# URLs
urls = {
    'Antifilter community edition': "https://community.antifilter.download/list/domains.lst",
    'Youtube': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-youtube.txt",
    'Facebook': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-facebook.txt",
    'Openai': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-openai.txt",
    'Tik-Tok': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-tiktok.txt",
    'Instagram': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-instagram.txt",
    'Twitter': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-twitter.txt",
    'Netflix': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-netflix.txt",
    'Bing': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-bing.txt",
    'Adobe': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-adobe.txt",
    'Apple': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-apple.txt",
    'Google': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-google.txt",
    'Tor-Truckers': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-ttruckers.txt",
    'Search-engines': "https://raw.githubusercontent.com/Ground-Zerro/DomainMapper/main/platforms/dns-search-engines.txt",
}

# Function to resolve DNS
def resolve_dns_and_write(service, url, unique_ips_all_services, include_cloudflare, threads):
    try:
        print(f"Загрузка данных - {service}")
        response = requests.get(url)
        response.raise_for_status()
        dns_names = response.text.split('\n')

        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = ['9.9.9.9', '149.112.112.112', '8.8.8.8', '8.8.4.4', '208.67.222.222', '208.67.220.220', '1.1.1.1', '1.0.0.1', '91.239.100.100', '89.233.43.71', '4.2.2.1', '4.2.2.2', '4.2.2.3', '4.2.2.4', '4.2.2.5', '4.2.2.6'] # Public DNS servers
        resolver.timeout = 1
        resolver.lifetime = 1

        if include_cloudflare:
            cloudflare_ips = get_cloudflare_ips()
        else:
            cloudflare_ips = set()

        unique_ips_current_service = set()  # Set to store unique IP addresses for the current service

        print(f"Анализ DNS имен платформы: {service}")

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = []
            for domain in dns_names:
                if domain.strip():
                    futures.append(executor.submit(resolve_domain, resolver, domain, unique_ips_current_service, unique_ips_all_services, cloudflare_ips))

        return '\n'.join(unique_ips_current_service) + '\n'
        print(f"Список IP-адресов для платформы {service} создан.")
    except Exception as e:
        print(f"Не удалось сопоставить IP адреса {service} его доменным именам.", e)
        return ""


# Function to get Cloudflare IP addresses
def get_cloudflare_ips():
    try:
        response = requests.get("https://www.cloudflare.com/ips-v4/")
        response.raise_for_status()
        cloudflare_ips = set()

        # Extract CIDR blocks from the response text using regular expressions
        cidr_blocks = re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})', response.text)
        
        for cidr in cidr_blocks:
            ip_network = ipaddress.ip_network(cidr)
            for ip in ip_network:
                cloudflare_ips.add(str(ip))

        return cloudflare_ips
    except Exception as e:
        print("Ошибка при получении IP адресов Cloudflare:", e)
        return set()

# Function to write result to file
def resolve_domain(resolver, domain, unique_ips_current_service, unique_ips_all_services, cloudflare_ips):
    try:
        ips = resolver.resolve(domain)
        for ip in ips:
            ip_address = ip.address
            if (ip_address not in ('127.0.0.1', '0.0.0.1') and 
                ip_address not in resolver.nameservers and
                ip_address not in cloudflare_ips and
                ip_address not in unique_ips_all_services):  # Check for uniqueness
                unique_ips_current_service.add(ip_address)
                unique_ips_all_services.add(ip_address)
    except dns.resolver.NoAnswer:
        pass
    except dns.resolver.NXDOMAIN:
        pass
    except dns.resolver.Timeout:
        pass
    except Exception as e:
        print(f"Ошибка при разрешении доменного имени {domain}: {e}")

# Function to read configuration file
def read_config(filename):
    # Default values
    default_values = ('all', 20, 'domain-ip-resolve.txt', '', 'ip', '0.0.0.0', 'echo "Ground_Zerro 2024"')
    
    try:
        config = configparser.ConfigParser()
        config.read(filename)

        if 'DomainMapper' in config:
            domain_mapper_config = config['DomainMapper']

            service = domain_mapper_config.get('service', default_values[0]) or 'all'
            threads = int(domain_mapper_config.get('threads', default_values[1])  or 20)
            outfilename = domain_mapper_config.get('outfilename', default_values[2]) or 'domain-ip-resolve.txt'
            cloudflare = domain_mapper_config.get('cloudflare', default_values[3]) or ''
            type_ = domain_mapper_config.get('type', default_values[4]) or 'ip'
            gateway = domain_mapper_config.get('gateway', default_values[5]) or '0.0.0.0'
            run_command = domain_mapper_config.get('run', default_values[6]) or 'echo "Ground_Zerro 2024"'

            return service, threads, outfilename, cloudflare, type_, gateway, run_command
        else:
            return default_values

    except Exception as e:
        return default_values

# Main function
def main():
    # Read parameters from the configuration file
    service, threads, outfilename, cloudflare, type_, gateway, run_command = read_config('config.txt')
    
    total_resolved_domains = 0
    total_errors = 0
    selected_services = []

    # Interactive service selection
    while True:
        os.system('clear')
        print("Выберите сервисы:\n")
        print("0 - Отметить все")
        for idx, (service, url) in enumerate(urls.items(), 1):
            checkbox = "[*]" if service in selected_services else "[ ]"
            print(f"{idx}. {service.capitalize()}  {checkbox}")

        selection = input("\nВведите номер сервиса и нажмите Enter (Пустая строка и Enter для старта): ")
        if selection == "0":
            selected_services = list(urls.keys())
        elif selection.isdigit():
            idx = int(selection) - 1
            if 0 <= idx < len(urls):
                service = list(urls.keys())[idx]
                if service in selected_services:
                    selected_services.remove(service)
                else:
                    selected_services.append(service)
        elif selection == "":
            break

    # Check if to include Cloudflare IPs based on configuration or user input
    if cloudflare.lower() == 'yes':
        include_cloudflare = True
    elif cloudflare.lower() == 'no':
        include_cloudflare = False
    else:
        include_cloudflare = input("Исключить IP адреса Cloudflare из итогового списка? (yes - исключить, Enter - оставить): ").strip().lower() == "yes"

    unique_ips_all_services = set()  # Set to store unique IP addresses across all services

    # Check if domain-ip-resolve.txt exists and clear it if it does
    if os.path.exists(outfilename):
        os.remove(outfilename)

    # DNS resolution for selected services
    with open(outfilename, 'w') as file:  # Open file for writing
        for service in selected_services:
            result = resolve_dns_and_write(service, urls[service], unique_ips_all_services, include_cloudflare, threads)
            file.write(result)  # Write unique IPs directly to the file
            total_resolved_domains += len(result.split('\n')) - 1

    print("\nПроверка завершена.")
    print(f"Проверено DNS имен: {total_resolved_domains + total_errors}")
    print(f"Сопоставлено IP адресов доменам: {total_resolved_domains}")
    print(f"Не удалось обработать доменных имен: {total_errors}")
    print("Результаты проверки сохранены в файл:", outfilename)

# Executing the command after the program is completed, if it is specified in the configuration file
    if run_command:
        print("\nВыполнение команды после завершения программы...")
        os.system(run_command)

if __name__ == "__main__":
    main()
