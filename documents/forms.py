from django import forms


# content_types =(
#     ('1', 'application/pdf'),
#     ('2', 'text/plain'),
#     ('3', 'text/markdown'),
# )
# content_types = [("text/markdown", "Markdown Text"), ("application/pdf", "PDF"), ("text/plain", "Plain Text")]
content_types = [
    ("", "Select Content Type"),  # Empty default option
    ("application/pdf", "PDF"),
    ("text/plain", "Plain Text"),
    ("text/html", "HTML"),
    ("text/csv", "CSV"),
    ("application/json", "JSON"),
    ("application/xml", "XML"),
    ("application/msword", "Microsoft Word (.doc)"),
    ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "Microsoft Word (.docx)"),
    ("application/vnd.ms-excel", "Microsoft Excel (.xls)"),
    ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "Microsoft Excel (.xlsx)"),
    ("application/zip", "ZIP Archive"),
    ("application/gzip", "GZIP Archive"),
    ("text/markdown", "Markdown"),
    ("text/x-python", "Python Script (.py)"),
    ("text/x-c", "C Source Code (.c)"),
    ("text/x-java", "Java Source Code (.java)"),
    ("text/x-utf8", "UTF-8 Encoded Text")  # Custom type for UTF-8
]

content_type = forms.ChoiceField(choices=content_types, required=False)


content_type = forms.ChoiceField(choices=content_types, required=False)

class DocumentForm(forms.Form):
    title = forms.CharField(max_length=255, required=True)
    file = forms.FileField(required=True)
    content_type = forms.ChoiceField(choices=content_types,required=True)
