import random
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from .models import User, OTPVerification
from .serializers import EmailSerializer, OTPVerifySerializer, AccountSerializer


# ✅ Step 1: Send OTP (Collect Email & Basic Info)
# class SendOTPView(APIView):
#     def post(self, request):
#         serializer = EmailSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()

#             # Generate and store OTP
#             otp_code = OTPVerification.generate_otp()
#             OTPVerification.objects.create(user=user, otp_code=otp_code)

#             # Send OTP email
#             send_mail(
#                 'Your OTP Verification Code',
#                 f"""
#                 Dear {user.first_name} {user.last_name},

#                 We are excited to have you on board! To complete your registration, we need you to verify your email.

#                 Your OTP Verification code is {otp_code}

#                 Please enter this code to activate your account. This code is valid for 10 minutes.
#                 """,
#                 'your_email@gmail.com',  
#                 [user.email],
#                 fail_silently=False,
#             )

#             return Response({"message": "OTP sent successfully!"}, status=status.HTTP_200_OK)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendOTPView(APIView):
    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            print(f"✅ User Created: {user.email}")

            try:
                # Generate OTP
                otp_code = OTPVerification.generate_otp()
                print(f"✅ OTP Generated: {otp_code}")

                OTPVerification.objects.create(user=user, otp_code=otp_code)
                print(f"✅ OTP Saved in Database for {user.email}")

                # Send OTP email
                send_mail(
                    "Your OTP Verification Code",
                    f"""
                    Dear {user.first_name},
                    
                    We are excited to have you on board! To complete your registration, we need you to verify your email address.
                    
                    Your OTP Verification code is {otp_code}. 
                    
                    Please enter this code to activate your account. This code is valid for 5 minutes.""",
                    "yustee2017@gmail.com",  
                    [user.email],
                    fail_silently=False,
                )
                print(f"✅ Email Sent to {user.email}")

                return Response({"message": "OTP sent successfully!"}, status=status.HTTP_200_OK)
            
            except Exception as e:
                print(f"❌ ERROR: {e}")  # This will log the exact error
                return Response({"error": "Something went wrong!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# ✅ Step 2: Verify OTP
class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get("email")  # Extract email from request
        
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = OTPVerifySerializer(data=request.data)

        if serializer.is_valid():
            return Response({"message": "OTP verified successfully!"}, status=status.HTTP_200_OK)
          

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Step 3: Resend OTP
class ResendOTPView(APIView):
    def post(self, request):
        try:
            email = request.data.get("email")

            if not email:
                return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=email).first()
            if not user:
                return Response({"error": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

            # Delete previous OTPs
            OTPVerification.objects.filter(user=user).delete()

            # Generate and store new OTP
            new_otp = OTPVerification.generate_otp()
            OTPVerification.objects.create(user=user, otp_code=new_otp)

            # Send email with the new OTP
            send_mail(
                "Your New OTP Verification Code",
                f"""
                Dear {user.first_name},

                Here is your new OTP: {new_otp}

                This code is valid for 10 minutes.
                """,
                "yustee2017@gmail.com",
                [email],
                fail_silently=False,
            )
            
        
        
           
        except Exception as e:
            print(f"❌ ERROR: {e}")  # This will log the exact error
            return Response({"error": "Something went wrong! {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "New OTP sent successfully!"}, status=status.HTTP_200_OK)


# ✅ Step 4: Register User
class RegisterUserView(APIView):
    serializer_class = AccountSerializer

    def get(self, request):
        users = User.objects.all()
        serializer = self.serializer_class(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        print("Request Data:", request.data)  # Debugging log

        
        try:
            
            email = request.data.get("email")
            user = User.objects.filter(email=email).first()

            if not user:
                return Response({"error": "Email not registered. Complete OTP verification first."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = AccountSerializer(user, data=request.data, partial=True)  # Update existing user

            if serializer.is_valid():
                serializer.save()
                return Response({"message": "User registered successfully!"}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
            
        except Exception as e:
            print(f"error : {e}")
            return Response({"error": "Something went wrong! {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# ✅ Step 5: Manage User Data
class AllUsersActions(APIView):
    serializer_class = AccountSerializer

    def get(self, request, pk):
        user = get_object_or_404(User, id=pk)
        serializer = self.serializer_class(user, many=True)
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
