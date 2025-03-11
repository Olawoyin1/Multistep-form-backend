import random
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from .models import User, OTPVerification
from django.shortcuts import get_object_or_404
from .serializers import EmailSerializer, OTPVerifySerializer, AccountSerializer


# ✅ Step 1: Send OTP
class SendOTPView(APIView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()         

            # Generate and store OTP
            otp_code = OTPVerification.generate_otp()
            OTPVerification.objects.create(user=user, otp_code=otp_code)

            # Use the updated values
            send_mail(
                'Your OTP Verification Code',
                f'''
                Dear {user.first_name} {user.last_name},

                We are excited to have you on board! To complete your registration, we need you to verify your email address.

                Your OTP Verification code is {otp_code}

                Please enter this code to activate your account. This code is valid for 5 minutes.
                ''',
                'your_email@gmail.com',  
                [user.email],
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
    serializer_class = AccountSerializer
    def get(self, request):
        user_data = User.objects.all()
        serializer = self.serializer_class(user_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request):
        print("Request Data:", request.data)  
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class AllUsersActions(APIView):
    serializer_class = AccountSerializer

    def get(self, request, pk):
        user = get_object_or_404(User, id=pk)
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        user = get_object_or_404(User, id=pk)
        serializer = self.serializer_class(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = get_object_or_404(User, id=pk)
        user.delete()
        return Response(
            {"message": "User deleted successfully"},
            status=status.HTTP_200_OK,
        )
