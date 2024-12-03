def get_serializer_method_field_value(
    context, model, obj, user_field, object_field
):
    return (
        context
        and model.objects.filter(
            **{
                f"{user_field}": context["request"].user.id,
                f"{object_field}": obj,
            }
        ).exists()
    )
