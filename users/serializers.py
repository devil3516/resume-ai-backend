from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    profilePicture = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'name', 'profilePicture')
        read_only_fields = ('id',)
    
    def get_profilePicture(self, obj):
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return f"http://localhost:8000{obj.profile_picture.url}"
        return None

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'name')

    def validate_email(self, value):
        """
        Check that the email is not already registered
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email is already registered. Please use a different email or try logging in.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        
        # Handle name field - use name if it's not empty/default, otherwise use first_name + last_name
        if user.name and user.name != '1' and user.name.strip():
            display_name = user.name
        else:
            # Fallback to first_name + last_name
            first_name = user.first_name or ''
            last_name = user.last_name or ''
            display_name = f"{first_name} {last_name}".strip() or user.email
        
        # Get full URL for profile picture
        profile_picture_url = None
        if user.profile_picture:
            request = self.context.get('request')
            if request:
                profile_picture_url = request.build_absolute_uri(user.profile_picture.url)
            else:
                profile_picture_url = f"http://localhost:8000{user.profile_picture.url}"
        
        response_data = {
            'id': user.id,
            'email': user.email,
            'name': display_name,
            'profilePicture': profile_picture_url,
        }
        
        data.update(response_data)
        return data

class UpdateUserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ('name', 'email', 'profile_picture')

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance 