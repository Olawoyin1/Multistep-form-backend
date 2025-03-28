import random
import requests
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import User, OTPVerification
from .serializers import EmailSerializer, OTPVerifySerializer, AccountSerializer, PasswordSetupSerializer
from decouple import config


BREVO_API_KEY = config("BREVO_API_KEY")
SENDER_EMAIL = config("SENDER_EMAIL")


def send_otp_email(to_email, subject, body):
    """
    Sends an email using the Brevo (Sendinblue) API.
    """
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
         "sender": {
            "name": "Study Lab 📚",  #  Set your desired display name here
            "email": SENDER_EMAIL  # Must be a verified email in Brevo
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "textContent": body
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)  # Added timeout
        response.raise_for_status()  # Raises an error for HTTP 4xx or 5xx
        return response
    except requests.exceptions.Timeout:
        print("❌ ERROR: Connection to Brevo API timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {e}")
        return None


# ✅ Step 1: Send OTP
class SendOTPView(APIView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            try:
                data = serializer.validated_data
                otp_code = OTPVerification.generate_otp()  # Generate a 6-digit OTP

                OTPVerification.objects.create(
                    email=data['email'],
                    otp_code=otp_code,
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    phonenumber=data['phonenumber'],
                    dob=data['dob'],
                    gender=data['gender'],
                    created_at=timezone.now()
                )

                # Send OTP email
                subject = "Your OTP Verification Code"
                body = f"""
                Dear {data['first_name']},
                
                Welcome to Study Lab! To complete your registration, please verify your email using the One-Time Password (OTP) below:

                Your OTP verification code is: {otp_code}
                
                This code is valid for 10 minutes. If you didn’t request this, please ignore this email.

                Need help? Contact our support team anytime.

                Happy Learning! 📚
                The Study Lab Team
                """

                response = send_otp_email(data['email'], subject, body)

                if response and response.status_code == 201:
                    return Response({"message": "OTP sent successfully!"}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Failed to send OTP email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as e:
                print(f"❌ ERROR: {e}")
                return Response({"error": "Something went wrong!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Step 2: Verify OTP
class VerifyOTPView(APIView):
    
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp_code = serializer.validated_data['otp_code']

            otp_entry = OTPVerification.objects.filter(email=email, otp_code=otp_code).first()

            if not otp_entry:
                return Response({"error": "Invalid OTP. Please try again."}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Check if OTP has expired
            if otp_entry.is_expired():
                return Response({"error": "OTP has expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Register user if OTP is valid
            user, created = User.objects.get_or_create(email=email)
            if created:
                user.first_name = otp_entry.first_name
                user.last_name = otp_entry.last_name
                user.phonenumber = otp_entry.phonenumber
                user.dob = otp_entry.dob
                user.gender = otp_entry.gender
            user.is_email_verified = True
            user.save()

            # ✅ Delete OTP after successful verification
            otp_entry.delete()

            return Response({"message": "OTP verified successfully!"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# ✅ Step 3: Resend OTP
class ResendOTPView(APIView):
     def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            try:
                data = serializer.validated_data
                otp_code = OTPVerification.generate_otp()  # Generate a 6-digit OTP

                OTPVerification.objects.create(
                    email=data['email'],
                    otp_code=otp_code,
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    phonenumber=data['phonenumber'],
                    dob=data['dob'],
                    gender=data['gender'],
                    created_at=timezone.now()
                )

                # Send OTP email
                subject = "Your New OTP Verification Code"
                body = f"""
                Dear {data['first_name']},
                
                You requested a new OTP to verify your email on Study Lab. Here’s your new code:

                Your new OTP is: {otp_code}
                
                This code is valid for 10 minutes. If you didn’t request this, please ignore this email.

                For assistance, feel free to reach out to our support team.

                Happy Learning! 📚
                The Study Lab Team
                """

                response = send_otp_email(data['email'], subject, body)

                if response and response.status_code == 201:
                    return Response({"message": "New OTP sent successfully!"}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Failed to Resend OTP email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as e:
                print(f"❌ ERROR: {e}")
                return Response({"error": "Something went wrong!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    


# ✅ Step 4: Register User
class RegisterUserView(APIView):
    def get(self, request):
        user = User.objects.all()
        serializer = AccountSerializer(user, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = PasswordSetupSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Call the update_password method from serializer
                serializer.update_password()
                return Response({"message": "Password set successfully."}, status=status.HTTP_200_OK)

            except Exception as e:
                print(f"❌ ERROR: {e}")
                return Response({"error": "Something went wrong!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# ✅ Step 5: Manage User Data
class AllUsersActions(APIView):
    def get(self, request, pk):
        user = get_object_or_404(User, id=pk)
        serializer = AccountSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        user = get_object_or_404(User, id=pk)
        serializer = AccountSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = get_object_or_404(User, id=pk)
        user.delete()
        return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)
