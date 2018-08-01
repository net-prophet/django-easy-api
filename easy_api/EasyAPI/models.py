from django.db import models


class ModelAPI(models.Model):
    crud = ['c', 'r', 'u', 'd']
    class Meta:
        app_label = 'EasyAPI'

    def __init__(self, model, api_fields):
        self.model = model
        self.api_fields = api_fields
        super(ModelAPI, self).__init__()

