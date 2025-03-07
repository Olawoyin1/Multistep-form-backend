from rest_framework import serializers
from .models import User


# ✅ Step 1: User Info (Collect Email and other info)
class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


# ✅ Step 2: OTP Verification (Only OTP is required)
class OTPVerifySerializer(serializers.Serializer):
    otp_code = serializers.CharField(max_length=6)


# ✅ Step 3: Final Registration (Full user details)
class AccountSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'username', 'phonenumber','dob', 'gender' 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)
