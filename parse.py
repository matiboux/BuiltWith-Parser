import csv
from bs4 import BeautifulSoup

def parse_builtwith_html(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []

    # Each technology category is a .card with a .card-title
    for card in soup.select(".card"):
        # Get category
        cat_title = card.select_one(".card-title")
        if not cat_title:
            continue
        category = cat_title.get_text(strip=True)

        # Each technology is a .row.mb-1.mt-1
        for tech_row in card.select(".row.mb-1.mt-1"):
            tech_col = tech_row.select_one(".col-12")
            if not tech_col:
                continue

            # Technology name
            tech_name = ""
            tech_link = tech_col.select_one("h2 a.text-dark")
            if tech_link:
                tech_name = tech_link.get_text(strip=True)
            else:
                continue

            # Description: first <p> after h2
            desc = ""
            h2 = tech_col.select_one("h2")
            if h2:
                p = h2.find_next_sibling("p")
                if p:
                    desc = p.get_text(strip=True)

            # Tags: look for <p class="small text-muted">, comma-separated
            tags = ""
            tags_p = tech_col.select_one("p.small.text-muted")
            if tags_p:
                tags = ", ".join([a.get_text(strip=True) for a in tags_p.select("a") if a.get_text(strip=True)])

            # First/Last Detected and Emojis: not present in free view, leave blank
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
    return rows

def parse_builtwith_detailed(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    current_category = None

    # Find the main table with technologies
    table = soup.find("table", class_="table")
    if not table:
        return rows

    for tr in table.find_all("tr"):
        # Category header row
        tds = tr.find_all("td")
        if len(tds) >= 2 and "font-weight-bold" in tds[1].get("class", []):
            # This is a category row
            current_category = tds[1].get_text(strip=True)
            continue

        # Technology row
        if len(tds) >= 5 and tds[1].find("a"):
            tech_name = tds[1].find("a").get_text(strip=True)
            # Description: in <div class="small"> inside tds[1]
            desc = ""
            desc_div = tds[1].find("div", class_="small")
            if desc_div:
                # If there are <a> tags, join their text as tags, not description
                if desc_div.find("a"):
                    desc = ""
                else:
                    desc = desc_div.get_text(strip=True)
            # Tags: all <a class="text-muted"> inside desc_div
            tags = ""
            if desc_div:
                tag_links = desc_div.find_all("a", class_="text-muted")
                tags = ", ".join([a.get_text(strip=True) for a in tag_links])
            # First/Last Detected
            first_detected = tds[2].get_text(strip=True) if len(tds) > 2 else ""
            last_detected = tds[3].get_text(strip=True) if len(tds) > 3 else ""
            # Emojis: in tds[4]
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
    # Merge by (Category, Technology) as key, prefer detailed view if duplicate
    merged = {}
    for row in rows1 + rows2:
        key = (row[0], row[1])
        merged[key] = row
    return list(merged.values())

def write_csv(rows, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Category","Technology","Description","Tags","First Detected","Last Detected","Emojis"])
        writer.writerows(rows)

if __name__ == "__main__":
    # Example usage: parse both files and merge
    with open("builtwith.html", encoding="utf-8") as f:
        html_free = f.read()
    with open("builtwith_details.html", encoding="utf-8") as f:
        html_detailed = f.read()

    rows_free = parse_builtwith_html(html_free)
    rows_detailed = parse_builtwith_detailed(html_detailed)
    all_rows = merge_tech_rows(rows_free, rows_detailed)
    write_csv(all_rows, "technologies.csv")
    print("CSV written to technologies.csv")
