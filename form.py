import json
import streamlit as st

config_json = "config.json"
with open(config_json, "r") as config_file:
    config_data = json.load(config_file)

data = config_data[0]

form_name = data["name"]
form_type = data["type"]
fields = data["fields"]

result = {}
field_functions = {
    "text": st.text_input,
    "number": st.number_input,
    "date": st.date_input,
    "check": st.checkbox,
    "select": st.selectbox,
    "multiselect": st.multiselect,
    "textarea": st.text_area,
    "toggle": st.toggle,
    "radio": st.radio,
}

option_fields = ["select", "multiselect", "radio"]

for field in fields:
    field_type = field["type"]
    field_name = field["field_name"]
    message = field["message"]

    if field_type in field_functions:
        if field_type in option_fields:
            options = field["options"]
            data = field_functions[field_type](message, options=options)
        else:
            data = field_functions[field_type](message)
        result[field_name] = data

if st.button("Send Data"):
    st.write(result)
