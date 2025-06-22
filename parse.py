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

def write_csv(rows, out_path):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Category","Technology","Description","Tags","First Detected","Last Detected","Emojis"])
        writer.writerows(rows)

if __name__ == "__main__":
    # Example usage
    with open("builtwith.html", encoding="utf-8") as f:
        html = f.read()
    rows = parse_builtwith_html(html)
    write_csv(rows, "technologies.csv")
    print("CSV written to technologies.csv")
