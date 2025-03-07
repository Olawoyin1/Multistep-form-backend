import random
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from .models import User, OTPVerification
from .serializers import EmailSerializer, OTPVerifySerializer, AccountSerializer


# ✅ Step 1: Send OTP
class SendOTPView(APIView):
    def post(self, request):
        user_data = request.data
        serializer = EmailSerializer(data=user_data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            user, created = User.objects.get_or_create(email=email)

            otp_code = OTPVerification.generate_otp()
            OTPVerification.objects.create(user=user, otp_code=otp_code)

            # Replace this with your real email logic
            send_mail(
                'Your OTP Code',
                f'Your OTP is {otp_code}',
                'your_email@gmail.com',
                [email],
                fail_silently=False,
            )

            return Response({"message": "OTP sent successfully!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            otp_code = serializer.validated_data['otp_code']

            otp_instance = OTPVerification.objects.filter(otp_code=otp_code).first()
            if not otp_instance:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

            if timezone.now() > otp_instance.created_at + timezone.timedelta(minutes=5):
                return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

            otp_instance.delete()
            return Response({"message": "OTP verified successfully!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterUserView(APIView):
    def post(self, request):
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
