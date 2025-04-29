from django.utils.translation import gettext_lazy as _

ADMIN_PERMISSIONS_DATA = [
    # --- User Management ---
    {
        "slug": "view_users",
        "name": _("View All Users"),
        "description": _(
            "Allows viewing the list of all user accounts (students, sub-admins, etc.)."
        ),
    },
    {
        "slug": "view_user_data",
        "name": _("View User Details & Progress"),
        "description": _(
            "Allows viewing detailed profile information, statistics, and activity logs, test history, etc. for individual users."
        ),
    },
    {
        "slug": "edit_users",
        "name": _("Edit User Details"),
        "description": _(
            "Allows modifying basic user profile fields (name, grade, gender, etc.) and account status (active/inactive). Does NOT include role or sensitive subscription details."
        ),
    },
    {
        "slug": "reset_user_password",
        "name": _("Trigger User Password Reset"),
        "description": _("Allows sending a password reset email to a user."),
    },
    {
        "slug": "manage_user_points",
        "name": _("Adjust User Points"),
        "description": _(
            "Allows manually adding or subtracting points from a user's account."
        ),
    },
    # --- Sub-Admin Management (Requires higher-level admin/superuser) ---
    {
        "slug": "view_sub_admins",
        "name": _("View Sub-Admins"),
        "description": _(
            "Allows viewing the list and details of other sub-admin accounts."
        ),
    },
    {
        "slug": "create_sub_admins",
        "name": _("Create Sub-Admins"),
        "description": _(
            "Allows creating new sub-admin accounts and assigning their permissions."
        ),
    },
    {
        "slug": "edit_sub_admins",
        "name": _("Edit Sub-Admins"),
        "description": _(
            "Allows modifying details, permissions, or status of other sub-admin accounts."
        ),
    },
    {
        "slug": "delete_sub_admins",
        "name": _("Delete Sub-Admins"),
        "description": _("Allows deleting sub-admin accounts."),
    },
    # --- Content & Feature Management ---
    {
        "slug": "manage_static_content",
        "name": _("Manage Static Content"),
        "description": _(
            "Allows editing website static pages (Homepage components, About Us, Terms, Story)."
        ),
    },
    {
        "slug": "manage_faq",
        "name": _("Manage FAQ Content"),
        "description": _(
            "Allows managing Frequently Asked Questions categories and items."
        ),
    },
    {
        "slug": "manage_partners",
        "name": _("Manage Success Partners"),
        "description": _(
            "Allows managing Success Partner categories and related settings."
        ),
    },
    {
        "slug": "manage_learning_content",
        "name": _("Manage Learning Content"),
        "description": _(
            "Allows creating, editing, and deleting learning sections, subsections, skills, and questions."
        ),
    },
    {
        "slug": "manage_serial_codes",
        "name": _("Manage Serial Codes"),
        "description": _(
            "Allows viewing, generating, and managing the status and details of subscription serial codes."
        ),
    },
    {
        "slug": "manage_gamification_settings",
        "name": _("Manage Gamification Settings"),
        "description": _(
            "Allows managing the list and properties of badges and reward store items."
        ),
    },
    {
        "slug": "manage_subscription_plans",
        "name": _("Manage Subscription Plans"),
        "description": _(
            "Allows managing the available subscription plans and their details."
        ),
    },
    # --- Communication & Support ---
    {
        "slug": "view_contact_messages",
        "name": _("View Contact Us Messages"),
        "description": _(
            "Allows viewing messages submitted via the 'Contact Us' form."
        ),
    },
    {
        "slug": "reply_contact_messages",
        "name": _("Reply to Contact Us Messages"),
        "description": _("Allows sending replies to users for 'Contact Us' messages."),
    },
    {
        "slug": "view_support_tickets",
        "name": _("View Support Tickets"),
        "description": _(
            "Allows viewing all user support tickets, including message logs."
        ),
    },
    {
        "slug": "reply_support_tickets",
        "name": _("Reply to Support Tickets"),
        "description": _(
            "Allows adding replies (visible to user or internal notes) to user support tickets."
        ),
    },
    {
        "slug": "manage_support_tickets",
        "name": _("Manage Support Tickets Workflow"),
        "description": _(
            "Allows assigning, changing status, or prioritizing support tickets."
        ),
    },
    # --- Analytics & Reporting ---
    {
        "slug": "view_aggregated_statistics",
        "name": _("View Platform Statistics"),
        "description": _(
            "Allows viewing aggregated platform analytics and dashboards (user counts, overall scores, usage trends)."
        ),
    },
    {
        "slug": "export_data",
        "name": _("Export Data"),
        "description": _("Allows triggering data export tasks for reporting."),
    },
    # --- Community Moderation ---
    {
        "slug": "moderate_community",
        "name": _("Moderate Community"),
        "description": _(
            "Allows managing (hiding, deleting, editing) community posts and replies."
        ),
    },
]
