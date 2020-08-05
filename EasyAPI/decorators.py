def APIProperty(gql_type):
    def APIPropertyWrapper(func):
        setattr(func, "_APIProperty", True)
        setattr(func, "_APIType", gql_type)
        return func

    return APIPropertyWrapper

def APIMutation(detail, read_only=False):
    def APIMutationWrapper(func):
        setattr(func, "_APIMutation", {'detail': detail, 'read_only': read_only})
        return func

    return APIMutationWrapper


def AddPermissionContext(context, permissions):
    def PermissionContextWrapper(model):
        contexts = getattr(model, "_permissions_contexts", {})
        if context in contexts:
            raise Exception(
                "Model %s already has permission context %s" % (model, context)
            )
        contexts[context] = permissions
        setattr(model, "_permissions_contexts", contexts)
        return model

    return PermissionContextWrapper
