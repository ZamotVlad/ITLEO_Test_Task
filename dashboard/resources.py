from import_export import resources


class VerboseNameResource(resources.ModelResource):
    """Uses each field's verbose_name as the export column header automatically."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            try:
                model_field = self._meta.model._meta.get_field(field_name)
                field.column_name = str(model_field.verbose_name)
            except Exception:
                pass
