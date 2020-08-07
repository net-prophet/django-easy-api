def APIProperty(gql_type):
    def APIPropertyWrapper(func):
        setattr(func, "_APIProperty", True)
        setattr(func, "_APIType", gql_type)
        return func

    return APIPropertyWrapper

def APIAction(detail=None, many=None, read_only=False, context="*", permission=None):
    if detail and many or (not detail and not many):
        raise Exception("Must use either detail=true or many=true on %s" % func)
    detail = not many

    def APIActionWrapper(func):
        setattr(
            func,
            "_APIAction",
            {
                "detail": detail,
                "many": many,
                "read_only": read_only,
                "context": context,
            },
        )
        return func

    return APIActionWrapper


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
