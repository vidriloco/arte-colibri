"""Reusable serializer fields — chiefly the bilingual {es, en} contract."""

from rest_framework import serializers


class BilingualField(serializers.Field):
    """Maps a pair of model fields (`*_es`, `*_en`) to/from a JSON `{es, en}`.

    Read: returns ``{"es": ..., "en": ...}``.
    Write: merges ``*_es`` / ``*_en`` into the parent serializer's
    ``validated_data`` (uses ``source='*'``).
    """

    def __init__(self, es_field, en_field, **kwargs):
        self.es_field = es_field
        self.en_field = en_field
        kwargs["source"] = "*"
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        return instance

    def to_representation(self, instance):
        return {
            "es": getattr(instance, self.es_field, "") or "",
            "en": getattr(instance, self.en_field, "") or "",
        }

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = {"es": data, "en": data}
        if not isinstance(data, dict):
            raise serializers.ValidationError("Expected an object with 'es'/'en' keys.")
        es = (data.get("es") or "").strip()
        en = (data.get("en") or "").strip()
        # Fall back across languages so a single-language submission still works.
        return {self.es_field: es or en, self.en_field: en or es}
