
def form_nullify_fields(cleaned_data, fields):
    """Sets field value to Null.

    To be used for unused fields.
    """

    for field in fields:
        cleaned_data[field] = None

    return cleaned_data
