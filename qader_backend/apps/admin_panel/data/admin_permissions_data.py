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
        "slug": "create_users",
        "name": _("Create Users"),
        "description": _(
            "Allows creating new user accounts (e.g., Students, Teachers). Does not include creating Admins/Sub-Admins unless also a main Admin."
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
    # --- REST API Permissions (General) ---
    {
        "slug": "api_list_all",
        "name": _("List All Resources"),
        "description": _("Allows listing all instances of any resource."),
    },
    {
        "slug": "api_retrieve_any",
        "name": _("Retrieve Any Resource"),
        "description": _("Allows retrieving details of any single resource."),
    },
    {
        "slug": "api_create_any",
        "name": _("Create Any Resource"),
        "description": _("Allows creating new instances of any resource."),
    },
    {
        "slug": "api_update_any",
        "name": _("Update Any Resource"),
        "description": _("Allows updating any existing resource."),
    },
    {
        "slug": "api_destroy_any",
        "name": _("Destroy Any Resource"),
        "description": _("Allows deleting any resource."),
    },
    # --- REST API Permissions (Specific Modules) ---
    {
        "slug": "api_manage_users",
        "name": _("Manage Users"),
        "description": _("Allows full CRUD operations on user accounts."),
    },
    {
        "slug": "api_manage_content",
        "name": _("Manage Content"),
        "description": _("Allows full CRUD operations on learning content."),
    },
    {
        "slug": "api_manage_blog",
        "name": _("Manage Blog"),
        "description": _("Allows full CRUD operations on blog posts and categories."),
    },
    {
        "slug": "api_manage_challenges",
        "name": _("Manage Challenges"),
        "description": _("Allows full CRUD operations on challenges."),
    },
    {
        "slug": "api_manage_community",
        "name": _("Manage Community"),
        "description": _(
            "Allows full CRUD operations on community posts and comments."
        ),
    },
    {
        "slug": "api_manage_gamification",
        "name": _("Manage Gamification"),
        "description": _(
            "Allows full CRUD operations on gamification elements (badges, rewards)."
        ),
    },
    {
        "slug": "api_manage_notifications",
        "name": _("Manage Notifications"),
        "description": _("Allows full CRUD operations on notifications."),
    },
    {
        "slug": "api_manage_support",
        "name": _("Manage Support"),
        "description": _(
            "Allows full CRUD operations on support tickets and messages."
        ),
    },
    {
        "slug": "api_manage_settings",
        "name": _("Manage Settings"),
        "description": _(
            "Allows full CRUD operations on application settings and configurations."
        ),
    },
]
