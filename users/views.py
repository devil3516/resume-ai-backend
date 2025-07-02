from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
    UpdateUserSerializer
)
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            return Response({
                'success': True,
                'message': 'User registered successfully! Welcome to ResumeAI.',
                'token': str(access_token),  # Frontend expects 'token'
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name,
                    'date_joined': user.date_joined.isoformat()
                }
            }, status=status.HTTP_201_CREATED)
        
        # Get the first error message from the serializer
        error_message = "Registration failed. Please check your information and try again."
        if serializer.errors:
            # Get the first field with errors
            first_field = list(serializer.errors.keys())[0]
            first_error = serializer.errors[first_field][0]
            error_message = first_error
        
        return Response({
            'success': False,
            'message': error_message,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Transform the response to match frontend expectations
        if response.status_code == 200:
            response.data = {
                'success': True,
                'message': 'Login successful',
                'token': response.data.get('access'),  # Frontend expects 'token'
                'user': {
                    'id': response.data.get('id'),
                    'email': response.data.get('email'),
                    'name': response.data.get('name'),
                    'date_joined': response.data.get('date_joined', '')
                }
            }
        
        return response

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

class UpdateUserView(generics.UpdateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UpdateUserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return the updated user data with full profile information
        user_serializer = UserSerializer(instance, context={'request': request})
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'user': user_serializer.data
        })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """
    Change user password with current password validation
    """
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not current_password or not new_password:
        return Response({
            'success': False,
            'message': 'Current password and new password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate current password
    if not user.check_password(current_password):
        return Response({
            'success': False,
            'message': 'Current password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate new password length
    if len(new_password) < 6:
        return Response({
            'success': False,
            'message': 'New password must be at least 6 characters long'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update password
    user.set_password(new_password)
    user.save()
    
    return Response({
        'success': True,
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    """
    Logout user by blacklisting the current token
    """
    try:
        # Get the authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({
                'success': False,
                'message': 'No valid authorization header found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract the token
        token = auth_header.split(' ')[1]
        
        # Blacklist the token
        try:
            # Create a token object and blacklist it
            token_obj = AccessToken(token)
            token_obj.blacklist()
            
            return Response({
                'success': True,
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # If token is invalid or already blacklisted, still return success
            # as the goal is to logout the user
            return Response({
                'success': True,
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Logout failed. Please try again.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
