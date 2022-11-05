# Libraries
import pandas as pd
import json
import datetime
from datetime import datetime
# from flask import Flask, render_template, jsonify, render_template_string, request, flash



evidence_dataset = pd.read_excel('evidence_dataset.xlsx')

evidence_dataset.info()
evidence_dataset = pd.DataFrame(evidence_dataset)
evidence_dataset = evidence_dataset.filter(['Country', 'Title', 'Category', 'Date', 'Link', 'Image'])
evidence_dataset['Date'] = evidence_dataset['Date'].dt.date
evidence_dataset = evidence_dataset.sort_values(by=['Date', 'Country'], ascending=False)
evidence_dataset['Image'] = evidence_dataset['Image'].fillna('https://raw.githubusercontent.com/ctedja/evidence_app/main/static/images/empty.png')
evidence_dataset = evidence_dataset.fillna("")
evidence_dataset.to_json(path_or_buf="data.json", orient='records')
evidence_dataset.to_json(path_or_buf="data2.json", orient='values')

d = {"data": evidence_dataset.to_dict('records')}
with open("data.json", "w") as f:
    json.dump(d, f, default=str)

#evidence_dataset = evidence_dataset.to_json(orient='values')
evidence_dataset = evidence_dataset.values.tolist()
