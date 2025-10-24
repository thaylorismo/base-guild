import requests
import time
from colorama import init, Fore

# Initialize colorama for colored output
init(autoreset=True)

# API endpoint and parameters
BASE_URL = "https://portal-api.plume.org/api/v1/stats/leaderboard"
PARAMS = {
    "walletAddress": "undefined",
    "overrideDay1Override": "false",
    "preview": "false",
    "count": 10000
}

# Total records to fetch
TOTAL_RECORDS = 360000
RECORDS_PER_PAGE = 10000
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Define XP ranges
XP_RANGES = {
    "300000+": lambda x: x >= 300000,
    "200000-299999": lambda x: 200000 <= x <= 299999,
    "100000-199999": lambda x: 100000 <= x <= 199999,
    "80000-99999": lambda x: 80000 <= x <= 99999,
    "60000-79999": lambda x: 60000 <= x <= 79999,
    "40000-59999": lambda x: 40000 <= x <= 59999,
    "20000-39999": lambda x: 20000 <= x <= 39999,
    "10000-19999": lambda x: 10000 <= x <= 19999,
    "1000-9999": lambda x: 1000 <= x <= 9999,
    "0-1000": lambda x: 0 <= x <= 1000
}

def format_number(number):
    """Format a number with dots as thousand separators (e.g., 100000 -> 100.000)."""
    return f"{number:,}".replace(",", ".")

def fetch_leaderboard_page(offset):
    """Fetch a single page of leaderboard data."""
    params = PARAMS.copy()
    params["offset"] = offset
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()  # Raise an exception for 4xx/5xx errors
            data = response.json()
            return data.get("data", {}).get("leaderboard", [])
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar offset {format_number(offset)}: {e}")
            if attempt < MAX_RETRIES - 1:
                print(f"Tentando novamente em {RETRY_DELAY} segundos...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"Falha ao buscar offset {format_number(offset)} após {MAX_RETRIES} tentativas.")
                return []
    return []

def sum_total_xp_and_count_ranges():
    """Fetch 280,000 records, sum totalXp, sum XP for wallets above 10,000, and count wallets in XP ranges."""
    total_xp = 0
    above_10000_xp = 0
    range_counts = {range_name: 0 for range_name in XP_RANGES}
    pages = (TOTAL_RECORDS + RECORDS_PER_PAGE - 1) // RECORDS_PER_PAGE  # Ceiling division

    for page in range(pages):
        offset = page * RECORDS_PER_PAGE
        print(f"Buscando registros {format_number(offset)} a {format_number(offset + RECORDS_PER_PAGE - 1)}...")
        leaderboard = fetch_leaderboard_page(offset)
        
        if not leaderboard:
            print(f"Nenhum dado retornado para offset {format_number(offset)}. Continuando para a próxima página.")
            continue

        # Calculate partial sum and count wallets in ranges for this page
        page_xp = 0
        for entry in leaderboard:
            xp = entry.get("totalXp", 0)
            page_xp += xp
            if xp > 10000:
                above_10000_xp += xp
            for range_name, condition in XP_RANGES.items():
                if condition(xp):
                    range_counts[range_name] += 1
                    break

        total_xp += page_xp
        print(f"{Fore.GREEN}XP parcial para registros {format_number(offset)} a {format_number(offset + len(leaderboard) - 1)}: {format_number(page_xp)}")

        # Respect potential rate limits
        time.sleep(1)

    return total_xp, above_10000_xp, range_counts

def main():
    print("Iniciando a coleta de dados do leaderboard...")
    total_xp, above_10000_xp, range_counts = sum_total_xp_and_count_ranges()
    print(f"\n{Fore.YELLOW}Total final de XP para {format_number(TOTAL_RECORDS)} carteiras: {format_number(total_xp)}")
    print(f"{Fore.YELLOW}Total de XP para carteiras com mais de 10.000 pontos: {format_number(above_10000_xp)}")
    print("\nDistribuição de carteiras por faixa de XP:")
    for range_name, count in range_counts.items():
        print(f"{Fore.CYAN}{range_name}: {format_number(count)} carteiras")

if __name__ == "__main__":
    main()