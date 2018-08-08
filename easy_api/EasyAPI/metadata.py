from rest_framework.metadata import SimpleMetadata


class EasyAPIMetadata(SimpleMetadata):

    def determine_metadata(self, request, view):
        data = super(EasyAPIMetadata, self).determine_metadata(request, view)
        name = view.model._meta.model_name.capitalize()
        label = view.model._meta.app_label

        data.update({
            'name': name,
            'label': label,
            'crud_permisisons': view.crud_permissions(request),
            'model_name': view.model._meta.model_name,
        })
        return data


'''
            'permissions': view.model.permissions(request),

            'filters': [(k, v) for k, v in filters.items()],
        filters = {
            name: {
                'title': info.get('title', name),
                'style': info.get('style', 'select'),
                'options': [
                    (param, option.get('title', param))
                    for param, option in info['options'](request)
                ],
            }
            for name, info in view.model.filters.items()
        }
            groups = view.model.field_group_info()
            'list_title': '%s List'%title,
            'list_fields': view.model.get_list_fields_meta(),
            'list_api_url': reverse('%s-list'%label),
            'list_url': reverse('%s-list'%label).replace('/api/','/#/'),
            'ordering_fields': view.model.get_ordering_fields(),
'''

