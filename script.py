# Libraries
import pandas as pd
import json
import datetime
from datetime import datetime
import requests
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
  "Tuvalu"
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


# =============================================================================
# Where it gets difficult

# Explore
reliefweb_list[6]['fields']['country'][0]['name']

reliefweb_list[0]['fields']
date = reliefweb_list[4]['fields']['country'][1]['name']

# Normalize the list into a DataFrame
test = pd.json_normalize(reliefweb_list, sep='_')

# Further normalize the DataFrame, for those that also include lists
def extract_and_join(row, field_name):
    if isinstance(row, list) and all(isinstance(elem, dict) for elem in row):
        return ', '.join([str(elem.get(field_name, '')) for elem in row])
    return row

test['fields_country_name'] = test['fields_country'].apply(extract_and_join, field_name='name')
test['fields_format'] = test['fields_country'].apply(extract_and_join, field_name='name')
test.iloc[4]

test['fields_category'] = pd.json_normalize(test['fields_format'].explode(), sep='_')['name']
test.iloc[4]



# ============================================================================= THIS IS WHAT I GOT UP TO





# See the number of rows
test_fields_country = pd.json_normalize(test['fields_country'].explode(), sep='_')
test_fields_country.head(8)
len(test_fields_country)

reliefweb_list[0]['fields']['country']

# # Now let's flatten the data and create the DataFrame
# flattened_data = [flatten_dict(record) for record in reliefweb_list]
# flattened_data[1]
# reliefweb_df = pd.DataFrame(flattened_data)
# reliefweb_df.head(2)


# Convert the list of dictionaries to a DataFrame
reliefweb_df = pd.DataFrame(reliefweb_list)











# Access a specific cell in reliefweb_df
reliefweb_df.iloc[1]['fields']

reliefweb_df['fields'] = reliefweb_df['fields'].apply(flatten)
reliefweb_df = pd.json_normalize(reliefweb_df['fields'])
reliefweb_df.columns.to_list()
reliefweb_df.iloc[1]

'date_changed': '2017-05-08T13:12:36+00:00', 
'date_created': '2017-05-08T12:32:08+00:00', 
'date_original': '2017-05-08T00:00:00+00:00', 
'country_href': 'https://api.reliefweb.int/v1/countries/120', 
'country_name': 'Indonesia', 
'country_location_lon': 117.37, 
'country_location_lat': -2.28, 
'country_id': 120, 
'country_shortname': 'Indonesia', 
'country_iso3': 'idn', 
'country_primary': True

# ============================================================================= THIS IS WHAT I GOT UP TO

# Extract needed columns and rename them
extracted_df = json_df[['date.created', 
                        'primary_country.name', 
                        'format',
                        # Category
                        # 'format.name', 
                        # Author
                        # 'source.shortname',
                        'title', 
                        'origin', 
                        'url', 
                        'body', 
                        # 'url_alias', 
                        # 'file.preview.url.thumb'
                        ]]

extracted_df.columns = ['Date', 'Country', 'Category', 'Author', 'Title', 'Origin_Link', 'Alt_Link',
                        'Summary', 'Link', 'Image']

# Concatenate the new DataFrame with the original one
reliefweb_df = pd.concat([reliefweb_df, extracted_df], axis=1)

# Drop the json_data column as it's no longer needed
reliefweb_df = reliefweb_df.drop('json_data', axis=1)




# Select the desired columns and rename them
reliefweb_df = reliefweb_df[['fields.date.created', 'fields.primary_country.name', 'fields.format.name', 
                             'fields.source.shortname', 'fields.title', 'fields.origin', 
                             'fields.file.url', 'fields.body', 'fields.url_alias', 
                             'fields.file.preview.url.thumb']].copy()


# =============================================================================
# Manual Extraction from Excel File
evidence_dataset = pd.read_excel('evidence_dataset.xlsx')

evidence_dataset.info()
evidence_dataset = pd.DataFrame(evidence_dataset)
evidence_dataset = evidence_dataset.filter(['Country', 'Title', 'Category', 'Date', 'Link', 'Image'])
evidence_dataset = evidence_dataset.drop_duplicates(keep='first')
# evidence_dataset['Date'] = evidence_dataset['Date'].dt.date
evidence_dataset['Date'] = evidence_dataset['Date'].dt.strftime('%Y-%m-%d')
evidence_dataset = evidence_dataset.sort_values(by=['Date', 'Country'])
evidence_dataset['Image'] = evidence_dataset['Image'].fillna('https://raw.githubusercontent.com/ctedja/evidence_app/main/static/images/empty.png')
evidence_dataset = evidence_dataset.fillna("")
records = evidence_dataset.to_dict(orient='records')

# Create new dictionary with desired structure
data = {'data': records}

# Dump dictionary to json file
with open('data.json', 'w') as f:
    json.dump(data, f)

# evidence_dataset.to_json(path_or_buf="data3.json", orient='values')

d = {"data": evidence_dataset.to_dict('records')}
with open("data.json", "w") as f:
    json.dump(d, f, default=str)

#evidence_dataset = evidence_dataset.to_json(orient='values')
evidence_dataset = evidence_dataset.values.tolist()