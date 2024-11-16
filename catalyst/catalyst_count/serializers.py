from rest_framework import serializers
from django.contrib.auth.models import User

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    status = serializers.ChoiceField(choices=[("active", "active"), ("inactive", "inactive")], required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'status']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        status = validated_data.pop('status')
        user = User.objects.create_user(**validated_data)
        # Here, if you need to store the status, you could add it as a user profile attribute.
        # Assuming you want to keep it in User directly, you might extend User model.
        return user
