import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
from datetime import datetime
from collections import Counter, defaultdict

# URL of the Wikipedia page
url = "https://en.wikipedia.org/wiki/List_of_World_Rally_Championship_drivers"

# Load zodiac signs from file
def load_zodiac_signs(filename):
    zodiac_signs = []
    with open(filename, 'r', encoding='utf-8') as file:
        next(file)  # Skip header
        next(file)  # Skip separator line
        for line in file:
            parts = line.strip().split('|')
            if len(parts) == 2:
                sign = parts[0].strip()
                dates = parts[1].strip()
                date_range = dates.split('-')
                if len(date_range) == 2:
                    start_date = datetime.strptime(date_range[0].strip(), "%d.%m")
                    end_date = datetime.strptime(date_range[1].strip(), "%d.%m")
                    zodiac_signs.append((sign, start_date, end_date))
    return zodiac_signs

# Determine zodiac sign based on date of birth
def get_zodiac_sign(birth_date, zodiac_signs):
    birth_date = datetime.strptime(birth_date, "%d-%m-%Y")
    birth_date = birth_date.replace(year=1900)  # Use a common year to compare
    for sign, start_date, end_date in zodiac_signs:
        if start_date <= birth_date <= end_date:
            return sign
    # Handle Capricorn case that spans the end of the year
    if birth_date >= datetime(1900, 12, 22) or birth_date <= datetime(1900, 1, 19):
        return "Steinbock"
    return None

# Send a GET request to the URL
response = requests.get(url)
response.raise_for_status()  # Ensure we notice bad responses

# Parse the HTML content of the page
soup = BeautifulSoup(response.content, "html.parser")

# Find the table containing the drivers
table = soup.find("table", {"class": "wikitable sortable"})

# Initialize an empty list to store the driver names, links, birth dates, and zodiac signs
drivers = []

# Function to fetch and parse the driver's birth date from their profile page
def get_birth_date(profile_url):
    retries = 3
    for _ in range(retries):
        try:
            profile_response = requests.get(profile_url, timeout=10)
            profile_response.raise_for_status()
            profile_soup = BeautifulSoup(profile_response.content, "html.parser")
            bday_span = profile_soup.find("span", {"class": "bday"})
            if bday_span:
                birth_date = bday_span.get_text(strip=True)
                # Convert date from YYYY-MM-DD to DD-MM-YYYY
                birth_date = datetime.strptime(birth_date, "%Y-%m-%d").strftime("%d-%m-%Y")
                return birth_date
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            print(f"Error fetching birth date from {profile_url}, retrying...")
            time.sleep(2)  # Wait before retrying
    return None

# Load zodiac signs
zodiac_signs = load_zodiac_signs("zodiac.txt")

# Loop through the table rows and extract the driver names, links, birth dates, and zodiac signs
rows = table.find_all("tr")[1:]  # Skip the header row
for row in tqdm(rows, desc="Processing drivers"):
    driver_cell = row.find_all("td")[0]
    a_tags = driver_cell.find_all("a")
    if len(a_tags) > 1:
        driver_name = a_tags[1].get_text(strip=True)
        driver_link = "https://en.wikipedia.org" + a_tags[1]['href']
        if "/w/" in driver_link:
            driver_link = None
            birth_date = None
            zodiac_sign = None
        else:
            birth_date = get_birth_date(driver_link)
            zodiac_sign = get_zodiac_sign(birth_date, zodiac_signs) if birth_date else None
    else:
        driver_name = driver_cell.get_text(strip=True)
        driver_link = None
        birth_date = None
        zodiac_sign = None
    drivers.append({"namee": driver_name, "link": driver_link, "birth_date": birth_date, "zodiac_sign": zodiac_sign})

# Print the list of driver names, birth dates, zodiac signs, and links in the order they appear in the table
for driver in drivers:
    if driver['link']:
        print(f"{driver['name']}, {driver['birth_date']}, {driver['zodiac_sign']}, {driver['link']}")
    else:
        print(driver['name'])

# Group drivers by zodiac sign
zodiac_groups = defaultdict(list)
for driver in drivers:
    if driver['zodiac_sign']:
        zodiac_groups[driver['zodiac_sign']].append(driver['name'])

# Sort the zodiac sign counts in descending order and print
sorted_zodiac_groups = sorted(zodiac_groups.items(), key=lambda item: len(item[1]), reverse=True)

# Print the count of people per zodiac sign along with their names
print("\nZodiac Sign Counts:")
for sign, names in sorted_zodiac_groups:
    print(f"{sign}: {len(names)} Fahrer")
    print(", ".join(names))
