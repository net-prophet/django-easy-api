def APIProperty(gql_type):
    def APIPropertyWrapper(func):
        setattr(func, '_APIProperty', True)
        setattr(func, '_APIType', gql_type)
        return func
    return APIPropertyWrapper