from rest_framework import permissions


class IsTicketOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a ticket to view/edit it.
    Assumes the view context has the ticket object.
    """

    def has_object_permission(self, request, view, obj):
        # obj is the SupportTicket instance
        return obj.user == request.user


class IsTicketOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow owners or admin users.
    """

    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the ticket
        if obj.user == request.user:
            return True
        # Check if the user is an admin (staff or superuser)
        return request.user and request.user.is_staff
