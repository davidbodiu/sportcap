import csv
import re
import os
import io

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.csv")

# Years where value is in billions
BILLION_YEARS = {2024, 2025}

# Team name normalization
NAME_MAP = {
    "Los Angeles": "LAFC",
    "Austin": "Austin FC",
}

# Country to league mapping
LEAGUE_MAP = {
    "England": "Premier League",
    "Spain": "La Liga",
    "Germany": "Bundesliga",
    "Italy": "Serie A",
    "France": "Ligue 1",
    "United States": "MLS",
    "Netherlands": "Eredivisie",
    "Scotland": "Scottish Premiership",
    "Turkey": "Süper Lig",
    "Brazil": "Brasileirão",
}

def parse_value(val_str, year):
    val_str = val_str.strip().replace('"', '').replace(',', '')
    val = float(val_str)
    if year in BILLION_YEARS:
        val = val * 1000
    return val

def find_columns(headers):
    rank_col = None
    team_col = None
    country_col = None
    value_col = None

    for i, h in enumerate(headers):
        h_clean = ' '.join(h.lower().split())
        if rank_col is None and (h_clean in ('#', 'rank') or h_clean.startswith('rank')):
            rank_col = i
        elif 'team' in h_clean:
            team_col = i
        elif 'country' in h_clean:
            country_col = i
        elif 'value' in h_clean and value_col is None:
            value_col = i

    return rank_col, team_col, country_col, value_col

rows = []

for fname in sorted(os.listdir(DATA_DIR)):
    if not fname.endswith('.csv'):
        continue
    year = int(fname.replace('.csv', ''))
    fpath = os.path.join(DATA_DIR, fname)

    with open(fpath, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    # Use io.StringIO so csv.reader properly handles quoted multiline fields
    reader = csv.reader(io.StringIO(content))
    all_rows = list(reader)

    # Find header row - look for row containing both 'team' and 'value'
    header_idx = None
    for i, row in enumerate(all_rows):
        joined = ' '.join(c.lower() for c in row)
        if 'team' in joined and 'value' in joined:
            header_idx = i
            break

    if header_idx is None:
        print(f"Could not find headers in {fname}")
        continue

    headers = all_rows[header_idx]
    rank_col, team_col, country_col, value_col = find_columns(headers)

    if team_col is None or country_col is None or value_col is None:
        print(f"Missing columns in {fname}: team={team_col}, country={country_col}, value={value_col}")
        print(f"  Headers: {headers}")
        continue

    for row in all_rows[header_idx + 1:]:
        if len(row) <= max(team_col, country_col, value_col):
            continue

        rank_str = row[rank_col].strip() if rank_col is not None else ''
        try:
            rank = int(rank_str)
        except:
            rank = None

        team = row[team_col].strip()
        country = row[country_col].strip()
        value_str = row[value_col].strip()

        if not team or not value_str:
            continue

        try:
            value = parse_value(value_str, year)
        except:
            print(f"  Could not parse value '{value_str}' for {team} in {year}")
            continue

        team = NAME_MAP.get(team, team)
        league = LEAGUE_MAP.get(country, country)

        rows.append({
            'Year': year,
            'Rank': rank if rank else '',
            'Team': team,
            'League': league,
            'Value': int(value),
        })

# Sort by year, then value descending
rows.sort(key=lambda r: (r['Year'], -r['Value']))

with open(OUTPUT, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['Year', 'Rank', 'Team', 'League', 'Value'])
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to data.csv")

# Verify a few values
for y in [2007, 2015, 2025]:
    top = [r for r in rows if r['Year'] == y][:3]
    print(f"\n{y} top 3:")
    for r in top:
        print(f"  {r['Team']:25s} ${r['Value']:,}M")
