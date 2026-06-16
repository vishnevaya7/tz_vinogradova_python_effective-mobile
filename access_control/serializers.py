from rest_framework import serializers

from access_control.models import Action, Resource, Role, RolePermission


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'name')


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ('id', 'name')


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ('id', 'name')


class RolePermissionSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    resource_name = serializers.CharField(source='resource.name', read_only=True)
    action_name = serializers.CharField(source='action.name', read_only=True)

    class Meta:
        model = RolePermission
        fields = ('id', 'role', 'resource', 'action', 'role_name', 'resource_name', 'action_name')
