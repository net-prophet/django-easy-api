from rest_framework.permissions import BasePermission
from django.db.models import QuerySet

class AllowNone(BasePermission):
    def has_permission(self, request, view):
        return False


class AuditLog(list):
    def log(self, *args):
        self.append(" ".join(args))

    def add_child(self, other):
        self += ["  " + line for line in other]

    def __str__(self):
        return "\n".join(line for line in self)

def get_action_permission(resource, action, user):
    context = resource.get_permission_context()
    audit = AuditLog(
        [
            "get_action_permissions on %s:%s %s for %s"
            % (context, action, resource.name, user)
        ]
    )

    contexts = getattr(resource.model, "_permissions_contexts", {})
    permission = None

    if callable(context):
        audit.log("Provided callable context")
        context = context(resource)

    if context in [True, False, None]:
        audit.log("Callable context is a boolean, returning %s" % context)
        return context, audit

    if permission is None and not contexts:
        audit.log("No contexts, returning None")
        return None, audit

    if permission is None and context not in contexts:
        if "*" in contexts:
            audit.log("%s not found in contexts, falling back to * context" % context)
            context = "*"
        else:
            audit.log(
                "%s not found in contexts %s for %s, returning None"
                % (context, list(contexts.keys()), resource.name)
            )
            return None, audit

    if callable(contexts[context]):
        audit.log("Matched callable permission for context %s" % (context))
        return permission, audit

    permission = contexts[context]

    if isinstance(permission, dict):
        if action in permission:
            audit.log("Matched context action", context, action)
            permission = permission[action]
        elif action in ["list", "retrieve", "metadata"] and "read" in permission:
            audit.log("Matched readonly action", context, action)
            permission = permission["read"]
        elif "*" in permission:
            audit.log("Matched global action", context)
            permission = contexts[context]["*"]
        else:
            audit.log("%s not found in context %s, denying" % (action, context))
            permission = None

    if callable(permission):
        audit.log("Returning callable permission...")
        return permission, audit

    if isinstance(permission, str):
        if permission is "*":
            audit.log("Permission is *, allowing...")
            return True, audit

    if permission in [True, False, None]:
        audit.log("Permission is %s" % permission)
        return permission, audit

    audit.log("Unknown permission %s, returning it" % permission)
    return permission, audit


def get_permitted_queryset(resource, action, user=None, qs=None):
    audit = AuditLog(["get_permitted_queryset on %s for %s" % (resource.name, user)])

    if not qs:
        audit.log(
            "No queryset specified, starting with %s.objects.all()"
            % resource.model._meta.object_name
        )
        qs = resource.model.objects.all()

    permission, sub_audit = resource.get_action_permission(action, user=user)

    audit.add_child(sub_audit)

    if callable(permission):
        audit.log("Evaluating callable permission...")
        permission = permission(user, qs)

    if isinstance(permission, str):
        if permission is "*":
            audit.log("Permission is *, allowing...")
            permission = True
        if permission in resource.relations:
            audit.log(
                'Permission is a string "%s", looking for relations...' % permission
            )
            related_field = resource.model_fields[permission]
            related_resource = resource.api.get_resource_for_model(
                related_field.remote_field.model
            )
            audit.log(
                "Matched permission %s to relation %s"
                % (permission, related_resource)
            )
            sub_query, sub_audit = related_resource.get_permitted_queryset(
                action, user=user
            )
            permission = qs.filter(
                **{
                    "%s_id__in"
                    % permission: sub_query.values_list("id", flat=True).distinct()
                }
            )
            audit += ["  " + line for line in sub_audit]
        else:
            audit.log(
                'Couldnt match permission "%s" to any relation on %s'
                % (permission, resource.model)
            )
            permission = False

    if isinstance(permission, QuerySet):
        audit.log("Found a queryset, returning it")
        return permission, audit

    if permission is True:
        audit.log("Permission is True, returning full queryset")
        return qs.all(), audit
    if permission in [False, None]:
        audit.log("Permission denied, returning none")
        return qs.none(), audit

    audit.log("Unknown permission %s, returning nothing" % permission)
    return qs.none(), audit

def get_permitted_object(resource, id, action, user=None, qs=None):
    qs, audit = resource.get_permitted_queryset(action, user=user, qs=qs)
    result = qs.filter(id=id).first()
    audit.append("Filtering queryset for id=%s, got: %s" % (id, result))
    return result, audit