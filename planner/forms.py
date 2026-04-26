from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(
        help_text='Upload an Excel file with Title, Description, Content, and Scheduled Time columns.'
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data['file']
        valid_extensions = ('.xls', '.xlsx')
        if not uploaded_file.name.lower().endswith(valid_extensions):
            raise forms.ValidationError('Please upload an Excel file (.xls or .xlsx).')
        return uploaded_file
