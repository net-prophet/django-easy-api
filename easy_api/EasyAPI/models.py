from django.db import models


class ModelAPI(models.Model):
    class Meta:
        app_label = 'EasyAPI'

    def __init__(self, model, api):
        print('init this model bruh')
        self.model = model
        self.api = api
        super().__init__()

