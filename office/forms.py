from django.forms import ModelForm
from office.models import Commit, Document


class DocumentAdminForm(ModelForm):
    class Meta:
        model = Document
        #  https://docs.djangoproject.com/en/1.8/topics/forms/modelforms/#selecting-the-fields-to-use
        fields = '__all__'  # for django 1.8

    def clean_reference(self):
        """ unique fields that allow null in admin interface
        http://stackoverflow.com/a/1400046/1265727
        """
        return self.cleaned_data['reference'] or None

    def clean_repo_id(self):
        return self.cleaned_data['repo_id'] or None


class CommitForm(ModelForm):
    class Meta:
        model = Commit
        # fields =('content',)
        fields = '__all__'
