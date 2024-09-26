from bs4 import BeautifulSoup
import json

# Path to the HTML files

#file_path = r"C:\Users\timsargent\Downloads\List of Spirits - Spirit Island Wiki.htm"
#file_path = r"C:\Users\timsargent\Downloads\List of Power Cards - Spirit Island Wiki.htm"


# Open and read the HTML file
with open(file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# Create a BeautifulSoup object to parse the HTML content
soup = BeautifulSoup(html_content, "html.parser")

# Find all tables on the page
tables = soup.find_all("table")

# Print the number of tables found
print(f"Number of tables found: {len(tables)}")

thislist = []
# Optionally, print the HTML of each table
for i, table in enumerate(tables):
    print(f"\nTable {i+1}:")
    thislist.append(table)

# Select the second table (index 1)
mytable = thislist[1]
del thislist
del i

#for spirts
# Convert the table to a list of dictionaries

table_data = []
for row_index, row in enumerate(mytable.find_all("tr")):
    if row_index % 2 == 0:  # Skip every other row
        continue
    row_data = {}
    cells = row.find_all(["td", "th"])
    for i, cell in enumerate(cells[:4]):  # Limit to the first 4 columns
        if i == 0:  # First column
            img = cell.find("img")
            if img:
                src = img.get("src")
                # Keep only the last part of the string, delimited by "/"
                filename = src.split("/")[-1]
                # Remove the .png extension and all text before the first "-"
                filename = filename.split(".png")[0]
                filename = filename.split("-", 1)[-1]
                # Remove the "_box" from the result
                filename = filename.replace("_box", "")
                row_data["set"] = filename
            else:
                row_data["set"] = cell.get_text(strip=True)
        elif i == 2:  # Third column
            row_data["name"] = cell.get_text(strip=True)
        elif i == 3:  # Fourth column
            row_data["complex"] = cell.get_text(strip=True)
    table_data.append(row_data)

###

#for power cards
# Convert the table to a list of dictionaries
'''
table_data = []
for row in mytable.find_all("tr"):
    row_data = {}
    cells = row.find_all(["td", "th"])
    for i, cell in enumerate(cells[:3]):  # Limit to the first 3 columns
        if i == 0:  # First column
            img = cell.find("img")
            if img:
                src = img.get("src")
                # Keep only the last part of the string, delimited by "/"
                filename = src.split("/")[-1]
                # Remove the .png extension and all text before the first "-"
                filename = filename.split(".png")[0]
                filename = filename.split("-", 1)[-1]
                # Remove the "_box" from the result
                filename = filename.replace("_box", "")
                row_data["set"] = filename
            else:
                row_data["set"] = cell.get_text(strip=True)
        elif i == 1:  # Second column
            img = cell.find("img")
            if img:
                src = img.get("src")
                # Keep only the last part of the string, delimited by "/"
                filename = src.split("/")[-1]
                # Remove the .png extension and all text before the first "-"
                filename = filename.split(".png")[0]
                filename = filename.split("-", 1)[-1]
                # Remove the "_box" from the result
                filename = filename.replace("_box", "")
                row_data["type"] = filename
            else:
                row_data["type"] = cell.get_text(strip=True)
        elif i == 2:  # Third column
            row_data["name"] = cell.get_text(strip=True)
    table_data.append(row_data)
'''


# Save the result to a JSON file
with open('table_data.json', 'w') as json_file:
    json.dump(table_data, json_file, indent=4)
