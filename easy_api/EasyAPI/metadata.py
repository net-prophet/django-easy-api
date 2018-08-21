from rest_framework.metadata import SimpleMetadata


class EasyAPIMetadata(SimpleMetadata):

    def determine_metadata(self, request, view):
        data = super(EasyAPIMetadata, self).determine_metadata(request, view)

        def model_metadata(self, request, view, data):
            name = view.get_view_name().capitalize()
            label = view.model._meta.app_label
            actions = [(k, v.__dict__['__doc__']) for k, v in
                       view.actions.items()]
            filters = [(k, v.__dict__['lookup_expr']) for k, v in
                       view.filter_class().filters.items()]
            data.update({
                'name': name,
                'label': label,
                'description': view.description,
                'model_name': view.model._meta.model_name,
                'actions': actions,
                'filters': filters,
            })
            return data

        def api_metadata(self, request, view, data):
            name = view.get_view_name()
            perms = [(k, v.__dict__['__doc__']) for k, v in view.perms.items()]
            data.update({
                'name': name,
                'actions': perms,
            })
            return data

        if hasattr(view, 'model'):
            return model_metadata(self, request, view, data)
        else:
            return api_metadata(self, request, view, data)
