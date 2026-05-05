from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True, default=None)
    updated_at = serializers.DateTimeField(read_only=True, default=None)
    version = serializers.IntegerField(read_only=True, default=1)
