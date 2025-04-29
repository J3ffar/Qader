from rest_framework import permissions
from apps.users.models import UserProfile, RoleChoices


class IsAdminUserOrSubAdminWithPermission(permissions.BasePermission):
    """
    Allows access only to admin users (is_superuser or role=ADMIN)
    or sub-admins with a specific granular permission.
    Permission slug is checked via `view.required_permissions`.
    """

    def has_permission(self, request, view):
        # Allow access if the user is a superuser or has the main ADMIN role
        if (
            request.user
            and request.user.is_authenticated
            and (
                request.user.is_superuser
                or (
                    hasattr(request.user, "profile")
                    and request.user.profile.role == RoleChoices.ADMIN
                )
            )
        ):
            return True

        # Check for required granular permissions if the user is a sub-admin
        if (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "profile")
            and request.user.profile.role == RoleChoices.SUB_ADMIN
            and request.user.is_staff
        ):
            required_permissions = getattr(view, "required_permissions", [])

            # If no specific permissions are required for this view/action,
            # a sub-admin can access as long as they are authenticated staff.
            # Adjust this logic if NO sub-admin should ever access a view
            # without explicit permission. Currently, staff+SUB_ADMIN is base.
            if not required_permissions:
                return True  # Or return False if no base access without explicit perm

            # Check if the sub-admin has *any* of the required permissions
            # Use 'all' if they must have ALL permissions: all(request.user.profile.has_permission(p) for p in required_permissions)
            # Use 'any' if having at least one is enough: any(request.user.profile.has_permission(p) for p in required_permissions)
            # The requirement "specifying certain permissions" implies 'any' is more likely per endpoint action.
            return any(
                request.user.profile.has_permission(p) for p in required_permissions
            )

        # Deny access by default
        return False

    # Optional: Implement object-level permissions if sub-admins can only manage certain objects (e.g., users in their school)
    # def has_object_permission(self, request, view, obj):
    #     # If they are a superuser or main admin, they have object permission
    #     if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == RoleChoices.ADMIN):
    #         return True
    #
    #     # Check object-level permissions for sub-admins
    #     if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == RoleChoices.SUB_ADMIN:
    #         # Example: Check if the sub-admin can 'view_user_data' for this specific obj (a UserProfile)
    #         # This requires custom logic based on the relationship between the admin and the object
    #         # e.g., is the user profile (obj) linked to the sub-admin's school?
    #         # required_permissions = getattr(view, 'required_object_permissions', []) # Define this on view
    #         # if 'view_user_data' in required_permissions:
    #         #     return request.user.profile.can_manage_user(obj.user) # Implement this method on UserProfile
    #
    #         pass # Object-level permission logic for sub-admins goes here
    #
    #     # Deny by default
    #     return False
