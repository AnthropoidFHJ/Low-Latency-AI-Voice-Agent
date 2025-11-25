def open_form():
    return {"action": "open_form"}

def update_field(field, value):
    return {"action": "update", "field": field, "value": value}

def submit_form():
    return {"action": "submit"}
