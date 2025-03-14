from rest_framework import serializers
from .models import User, OTPVerification


# ✅ Step 1: Collect User Info (Email & Basic Details)
class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phonenumber', 'dob', 'gender']

    def create(self, validated_data):
        print("Creating User with Data:", validated_data)  # Debugging output
        
        user, created = User.objects.get_or_create(email=validated_data["email"], defaults=validated_data)

        if not created:  # If the user exists, update their details
            for key, value in validated_data.items():
                setattr(user, key, value)
            user.save()

        return user


# ✅ Step 2: OTP Verification (Only OTP is required)
class OTPVerifySerializer(serializers.Serializer):
    otp_code = serializers.CharField(max_length=6)

    def validate(self, data):
        otp_code = data['otp_code']
        
        otp_instance = OTPVerification.objects.filter(otp_code=otp_code).first()
        if not otp_instance:
            raise serializers.ValidationError({"otp_code": "Invalid OTP."})

        if otp_instance.is_expired():
            raise serializers.ValidationError({"otp_code": "OTP expired."})

        otp_instance.delete()
        return data


# ✅ Step 3: Final User Registration
class AccountSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirmPassword = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = '__all__'

    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise serializers.ValidationError("Passwords do not match.")
        
        if not User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Email not registered. Please complete OTP verification first."})

        return data
    
    def update(self, instance, validated_data):
        instance.password = validated_data['password']
        instance.save()
        return instance
