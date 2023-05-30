# Libraries
import pandas as pd
import json
import datetime
from datetime import datetime
import requests
import numpy as np
import ast

# from flask import Flask, render_template, jsonify, render_template_string, request, flash


# =============================================================================
# Extract Data from API

# Define the API query
api_country_query = [
    "Afghanistan",
    "Bangladesh",
    "Bhutan",
    "Cambodia",
    "Democratic%20People's%20Republic%20of%20Korea",
    "Fiji",
    "Indonesia",
    "Kyrgyzstan",
    "Lao%20People's%20Democratic%20Republic%20(the)",
    "Myanmar",
    "Nepal",
    "Pakistan",
    "Papua%20New%20Guinea",
    "Philippines",
    "Samoa",
    "Sri%20Lanka",
    "Tajikistan",
    "Timor-Leste",
    "Tonga",
    "Tuvalu",
]

api_country_query = "".join(
    f"&filter[conditions][0][conditions][{i}][field]=primary_country&filter[conditions][0][conditions][{i}][value]={country}"
    for i, country in enumerate(api_country_query)
)

base_url = "https://api.reliefweb.int/v1/reports?appname=apidoc&profile=full&limit=1000&filter[operator]=AND&filter[conditions][0][operator]=OR"

years = list(range(2017, 2024))

api_urls = [
    f"{base_url}{api_country_query}&filter[conditions][1][field]=date.created&filter[conditions][1][value][from]={year}-01-01T00:00:00%2B00:00&filter[conditions][1][value][to]={year}-12-31T23:59:59%2B00:00&filter[conditions][2][field]=source.shortname&filter[conditions][2][value]=WFP"
    for year in years
]

# Now load the APIs here. We have to build multiple because the limit for this API is 1,000.
reliefweb_raws = [requests.get(api_url) for api_url in api_urls]

# Ensure that all requests were successful
assert all(reliefweb_raw.status_code == 200 for reliefweb_raw in reliefweb_raws)

reliefweb_list = [
    item for reliefweb_raw in reliefweb_raws for item in reliefweb_raw.json()["data"]
]

# Explore
reliefweb_list[6]["fields"]["country"][0]["name"]


# =============================================================================
# Transform the API's output into a dataframe

# Normalize the list into a DataFrame
df = pd.json_normalize(reliefweb_list, sep="_")


# Create functions to normalize the DataFrame for those that are nested into lists, with comma separated values, or to extract the thumbnail which is nested deeper
def extract_and_join(row, field_name):
    if isinstance(row, list) and all(isinstance(elem, dict) for elem in row):
        return ", ".join([str(elem.get(field_name, "")) for elem in row])
    return row


def get_url_thumb(files):
    if isinstance(files, list) and files:
        first_file = files[0]  # access the first file dictionary
        if isinstance(first_file, dict) and "preview" in first_file:
            preview = first_file["preview"]  # access the 'preview' dictionary
            if isinstance(preview, dict) and "url-thumb" in preview:
                return preview["url-thumb"]  # return the 'url-thumb' value


# Extract for countries (where there are multiple), format (which is category), source (which is author), and thumbnail
df["multiple_country_names"] = df["fields_country"].apply(
    extract_and_join, field_name="name"
)
df["category"] = df["fields_format"].apply(extract_and_join, field_name="name")
df["author"] = df["fields_source"].apply(extract_and_join, field_name="shortname")
df["thumb"] = df["fields_file"].apply(get_url_thumb)

# Extract needed columns and rename them
df = df[
    [
        "fields_date_created",
        "fields_primary_country_name",
        "category",
        "author",
        "fields_title",
        "fields_origin",
        "fields_url_alias",
        "fields_body",
        "thumb",
    ]
]

df.columns = [
    "date",
    "country",
    "category",
    "author",
    "title",
    "origin_link",
    "alt_link",
    "summary",
    "thumb",
]


# =============================================================================
# Clean the dataframe

# Convert to datetime (and remove timezone)
df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

# Rename certain categories
df["category"] = df["category"].fillna("")
df["category"] = np.select(
    [
        # Where it is a certain word
        (df["category"] == "Map"),
        (df["category"] == "Infographic"),
        (df["category"] == "Evaluation and Lessons Learned"),
        (df["category"] == "Assessment"),
        (df["category"] == "Analysis"),
        (df["category"] == "News and Press Release"),
        (df["category"] == "Appeal"),
        # Where it contains certain words
        df["title"].str.contains("market", case=False, na=False),
        df["title"].str.contains("price", case=False, na=False),
        df["title"].str.contains("annual country report", case=False, na=False),
    ],
    [
        "Dashboards/Maps/Infographics",
        "Dashboards/Maps/Infographics",
        "Evaluations",
        "Assessments (Food Security and Nutrition)",
        "Analysis/Research",
        "Stories/Articles",
        "Response Plans/Appeals",
        "Market/Price Monitoring",
        "Market/Price Monitoring",
        "Annual Country Report",
    ],
    default=df["category"],
)

# Rename certain countries to match the spatial dataset
df["country"] = np.select(
    [
        (df["country"] == "Lao People's Democratic Republic (the)"),
        (df["country"] == "American Samoa"),
    ],
    [
        "Lao People's Democratic Republic",
        "Samoa",
    ],
    default=df["country"],
)

# Note #1: In R, I removed certain text from summary, but not sure it's needed here mutate(Summary = gsub("\\*", "", Summary))
# Note #2: In R, I joined the manual dataset but it's not needed here.
# Note #3: In R, I included subnational designations based on the title, but it's not needed here

# =============================================================================
# Manual Extraction from Excel File
evidence_dataset = pd.read_excel("evidence_dataset.xlsx")
evidence_dataset = pd.DataFrame(evidence_dataset)
evidence_dataset.info()

evidence_dataset = evidence_dataset.filter(
    ["Country", "Title", "Category", "Date", "Link", "Image"]
)


evidence_dataset.info()


evidence_dataset = evidence_dataset.drop_duplicates(keep="first")
# evidence_dataset['Date'] = evidence_dataset['Date'].dt.date
evidence_dataset["Date"] = evidence_dataset["Date"].dt.strftime("%Y-%m-%d")
evidence_dataset = evidence_dataset.sort_values(by=["Date", "Country"])
evidence_dataset["Image"] = evidence_dataset["Image"].fillna(
    "https://raw.githubusercontent.com/ctedja/evidence_app/main/static/images/empty.png"
)
evidence_dataset = evidence_dataset.fillna("")
records = evidence_dataset.to_dict(orient="records")

# Create new dictionary with desired structure
data = {"data": records}

# Dump dictionary to json file
with open("data.json", "w") as f:
    json.dump(data, f)

# evidence_dataset.to_json(path_or_buf="data3.json", orient='values')

d = {"data": evidence_dataset.to_dict("records")}
with open("data.json", "w") as f:
    json.dump(d, f, default=str)

# evidence_dataset = evidence_dataset.to_json(orient='values')
evidence_dataset = evidence_dataset.values.tolist()
