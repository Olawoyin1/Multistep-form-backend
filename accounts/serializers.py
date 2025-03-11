from rest_framework import serializers
from .models import User, OTPVerification


# Step 1: User Info (Collect Email and other info)
class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'dob', 'gender']


    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# Step 2: OTP Verification (Only OTP is required)
class OTPVerifySerializer(serializers.Serializer):
    otp_code = serializers.CharField(max_length=6)
    
    def validate(self, data):
        email = data['email']
        otp_code = data['otp_code']
        
        otp_instance = OTPVerification.objects.filter(otp_code=otp_code).first()
        if not otp_instance:
            raise serializers.ValidationError({"otp_code": "Invalid OTP."})

        if otp_instance.is_expired():
            raise serializers.ValidationError({"otp_code": "OTP expired."})

        otp_instance.delete()
        return data


# Step 3: Final Registration (Full user details)
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
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found. Please restart the registration process."})

        return data
    
    def update(self, instance, validated_data):
        instance.password = validated_data['password']
        instance.save()
        return instance
    
    

    # def create(self, validated_data):
    #     validated_data.pop('confirmPassword')
    #     return User.objects.create_user(**validated_data)
