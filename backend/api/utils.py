def get_serializer_method_field_value(
        context, model, obj, field_1, field_2
):
    return (
        context
        and context['request'].user.is_authenticated
        and model.objects.filter(
            **{f'{field_1}': context['request'].user.id, f'{field_2}': obj}
        ).exists()
    )
