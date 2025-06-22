import csv
import sys
import os
from bs4 import BeautifulSoup

CSV_HEADER = ["Category","Technology","Description","Tags","First Detected","Last Detected","Emojis"]
CSV_FILE = "technologies.csv"

def parse_builtwith_html(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for card in soup.select(".card"):
        cat_title = card.select_one(".card-title")
        if not cat_title:
            continue
        category = cat_title.get_text(strip=True)
        for tech_row in card.select(".row.mb-1.mt-1"):
            tech_col = tech_row.select_one(".col-12")
            if not tech_col:
                continue
            tech_name = ""
            tech_link = tech_col.select_one("h2 a.text-dark")
            if tech_link:
                tech_name = tech_link.get_text(strip=True)
            else:
                continue
            desc = ""
            h2 = tech_col.select_one("h2")
            if h2:
                ps = h2.find_next_siblings("p")
                for p in ps:
                    if "small" in p.get("class", []):
                        desc = p.get_text(strip=True)
                        break
            tags = ""
            tags_p = tech_col.select_one("p.small.text-muted")
            if tags_p:
                tags = ", ".join([a.get_text(strip=True) for a in tags_p.select("a") if a.get_text(strip=True)])
            first_detected = ""
            last_detected = ""
            emojis = ""
            rows.append([
                category,
                tech_name,
                desc,
                tags,
                first_detected,
                last_detected,
                emojis
            ])
            # --- Handle child/nested technologies ---
            for child in tech_col.find_all("div", class_="row"):
                child_col = child.select_one(".col-12, .col-12.ml-3")
                if not child_col:
                    continue
                h5 = child_col.select_one("h5")
                if not h5:
                    continue
                child_link = h5.select_one("a.text-dark")
                if not child_link:
                    continue
                child_name = child_link.get_text(strip=True)
                # Description: <p class="mb-0 small"> after h5
                child_desc = ""
                p_stats = h5.find_next_sibling("p")
                p_desc = p_stats.find_next_sibling("p") if p_stats else None
                if p_desc and "small" in p_desc.get("class", []):
                    child_desc = p_desc.get_text(strip=True)
                elif p_stats and "small" in p_stats.get("class", []):
                    child_desc = p_stats.get_text(strip=True)
                # Tags: not usually present for child, but check
                child_tags = ""
                tags_p = child_col.select_one("p.small.text-muted")
                if tags_p:
                    child_tags = ", ".join([a.get_text(strip=True) for a in tags_p.select("a") if a.get_text(strip=True)])
                rows.append([
                    category,
                    child_name,
                    child_desc,
                    child_tags,
                    "",
                    "",
                    ""
                ])
    return rows

def parse_builtwith_detailed(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    current_category = None
    table = soup.find("table", class_="table")
    if not table:
        return rows
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) >= 2 and "font-weight-bold" in tds[1].get("class", []):
            current_category = tds[1].get_text(strip=True)
            continue
        if len(tds) >= 5 and tds[1].find("a"):
            tech_name = tds[1].find("a").get_text(strip=True)
            desc = ""
            desc_div = tds[1].find("div", class_="small")
            if desc_div:
                if desc_div.find("a"):
                    desc = ""
                else:
                    desc = desc_div.get_text(strip=True)
            tags = ""
            if desc_div:
                tag_links = desc_div.find_all("a", class_="text-muted")
                tags = ", ".join([a.get_text(strip=True) for a in tag_links])
            first_detected = tds[2].get_text(strip=True) if len(tds) > 2 else ""
            last_detected = tds[3].get_text(strip=True) if len(tds) > 3 else ""
            emojis = tds[4].get_text(strip=True) if len(tds) > 4 else ""
            rows.append([
                current_category or "",
                tech_name,
                desc,
                tags,
                first_detected,
                last_detected,
                emojis
            ])
    return rows

def merge_tech_rows(rows1, rows2):
    # Use (Category, Technology) as key
    merged = {}
    for row in rows1:
        key = (row[0], row[1])
        merged[key] = row.copy()
    for row in rows2:
        key = (row[0], row[1])
        if key in merged:
            # Merge: prefer non-empty new values, else keep existing
            merged_row = []
            for i in range(len(row)):
                merged_row.append(row[i] if row[i].strip() else merged[key][i])
            merged[key] = merged_row
        else:
            merged[key] = row.copy()
    return list(merged.values())

def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        return [row for row in reader if row and len(row) == len(CSV_HEADER)]

def write_csv(rows, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)

def detect_view(html):
    soup = BeautifulSoup(html, "html.parser")
    if soup.find("table", class_="table"):
        return "detailed"
    if soup.select(".card"):
        return "free"
    return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python parse.py <report.html>")
        sys.exit(1)
    html_path = sys.argv[1]
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    view = detect_view(html)
    if view == "free":
        new_rows = parse_builtwith_html(html)
    elif view == "detailed":
        new_rows = parse_builtwith_detailed(html)
    else:
        print("Error: Not a recognized BuiltWith report.")
        sys.exit(2)

    # Read existing CSV if present
    existing_rows = read_csv(CSV_FILE)
    # Merge and check if changed
    merged_rows = merge_tech_rows(existing_rows, new_rows)
    # Sort for idempotency
    merged_rows_sorted = sorted(merged_rows, key=lambda r: (r[0], r[1]))
    existing_rows_sorted = sorted(existing_rows, key=lambda r: (r[0], r[1]))
    if merged_rows_sorted != existing_rows_sorted:
        write_csv(merged_rows_sorted, CSV_FILE)
        print(f"Updated {CSV_FILE} with {len(merged_rows_sorted)} technologies.")
    else:
        print(f"No changes. {CSV_FILE} is up to date.")

if __name__ == "__main__":
    main()
