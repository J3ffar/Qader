# qader_backend/apps/admin_panel/tests/api/test_user_management_unified.py

import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth.models import User

from apps.users.models import UserProfile, RoleChoices
from apps.users.tests.factories import UserFactory  # Assuming you have this
from apps.admin_panel.models import AdminPermission
from apps.admin_panel.data.admin_permissions_data import (
    ADMIN_PERMISSIONS_DATA,
)  # To populate permissions


# Helper function to create permissions
def create_test_permissions():
    created_permissions = {}
    for perm_data in ADMIN_PERMISSIONS_DATA:
        perm, _ = AdminPermission.objects.get_or_create(
            slug=perm_data["slug"],
            defaults={
                "name": perm_data["name"],
                "description": perm_data["description"],
            },
        )
        created_permissions[perm_data["slug"]] = perm
    return created_permissions


@pytest.fixture(autouse=True)  # Ensure permissions exist for all tests in this module
def setup_permissions(db):
    return create_test_permissions()


@pytest.fixture
def superuser_client(api_client, db):
    user = UserFactory(username="superuser", is_superuser=True, is_staff=True)
    api_client.force_authenticate(user=user)
    api_client.user = user  # Attach user to client for convenience in tests
    UserProfile.objects.get_or_create(
        user=user, defaults={"full_name": "Super User", "role": RoleChoices.ADMIN}
    )
    return api_client


@pytest.fixture
def main_admin_client(
    api_client, db, setup_permissions
):  # Renamed from admin_client for clarity
    user = UserFactory(username="mainadmin", is_staff=True, is_superuser=False)
    profile, _ = UserProfile.objects.get_or_create(
        user=user, defaults={"full_name": "Main Admin"}
    )
    profile.role = RoleChoices.ADMIN
    profile.save()
    api_client.force_authenticate(user=user)
    api_client.user = user
    return api_client


@pytest.fixture
def sub_admin_client_view_users(api_client, db, setup_permissions):
    user = UserFactory(username="subadmin_viewer", is_staff=True)
    profile, _ = UserProfile.objects.get_or_create(
        user=user, defaults={"full_name": "SubAdmin Viewer"}
    )
    profile.role = RoleChoices.SUB_ADMIN
    profile.admin_permissions.add(setup_permissions["view_users"])
    profile.save()
    api_client.force_authenticate(user=user)
    api_client.user = user
    return api_client


@pytest.fixture
def sub_admin_client_manage_users(api_client, db, setup_permissions):
    user = UserFactory(username="subadmin_manager", is_staff=True)
    profile, _ = UserProfile.objects.get_or_create(
        user=user, defaults={"full_name": "SubAdmin Manager"}
    )
    profile.role = RoleChoices.SUB_ADMIN
    profile.admin_permissions.add(
        setup_permissions["view_users"],
        setup_permissions[
            "create_users"
        ],  # Assuming 'create_users' allows creating non-admin roles
        setup_permissions["edit_users"],
        setup_permissions["view_user_data"],
    )
    profile.save()
    api_client.force_authenticate(user=user)
    api_client.user = user
    return api_client


@pytest.fixture
def student_user(db):
    user = UserFactory(
        username="student1",
        profile_data={"role": RoleChoices.STUDENT, "full_name": "Student One"},
    )
    return user


@pytest.fixture
def teacher_user(db):
    user = UserFactory(
        username="teacher1",
        profile_data={"role": RoleChoices.TEACHER, "full_name": "Teacher One"},
    )
    return user


@pytest.mark.django_db
class TestAdminUserViewSet:
    # --- URLS ---
    USER_LIST_URL = reverse(
        "api:v1:admin_panel:admin-user-list"
    )  # basename is 'admin-user'

    @staticmethod
    def USER_DETAIL_URL(user_profile_pk):
        return reverse(
            "api:v1:admin_panel:admin-user-detail", kwargs={"pk": user_profile_pk}
        )

    # --- Permission Tests ---
    def test_list_users_permission_anonymous(self, api_client):
        response = api_client.get(self.USER_LIST_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_users_permission_standard_user(
        self, authenticated_client
    ):  # Standard client
        response = authenticated_client.get(self.USER_LIST_URL)
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        )  # Regular users can't access

    def test_list_users_permission_sub_admin_no_permission(
        self,
        api_client,
        db,
        setup_permissions,
    ):
        sub_admin_no_perm = UserFactory(username="subadmin_noperm", is_staff=True)
        # Get the profile created by the factory/signal and update its role
        profile = UserProfile.objects.get(
            user=sub_admin_no_perm
        )  # Or sub_admin_no_perm.profile
        profile.role = RoleChoices.SUB_ADMIN
        profile.full_name = "No Perm Sub"
        # Ensure no permissions are assigned for this test case
        profile.admin_permissions.clear()  # Explicitly clear if factory might add some
        profile.save()

        api_client.force_authenticate(user=sub_admin_no_perm)
        response = api_client.get(self.USER_LIST_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_users_permission_sub_admin_with_view_permission(
        self, sub_admin_client_view_users
    ):
        response = sub_admin_client_view_users.get(self.USER_LIST_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_list_users_permission_main_admin(self, main_admin_client):
        response = main_admin_client.get(self.USER_LIST_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_list_users_permission_superuser(self, superuser_client):
        response = superuser_client.get(self.USER_LIST_URL)
        assert response.status_code == status.HTTP_200_OK

    # --- List & Filter Tests ---
    def test_list_users_content(self, superuser_client, student_user, teacher_user):
        response = superuser_client.get(self.USER_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 3  # superuser, student, teacher
        # Check if one of the users is present
        results = response.data["results"]
        assert any(
            item["user"]["username"] == student_user.username for item in results
        )
        assert any(
            item["user"]["username"] == teacher_user.username for item in results
        )

    def test_filter_users_by_role_student(
        self, superuser_client, student_user, teacher_user
    ):
        response = superuser_client.get(
            self.USER_LIST_URL, {"role": RoleChoices.STUDENT}
        )
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert len(results) > 0
        assert all(item["role"] == RoleChoices.STUDENT for item in results)
        assert any(
            item["user"]["username"] == student_user.username for item in results
        )
        assert not any(
            item["user"]["username"] == teacher_user.username for item in results
        )

    def test_filter_users_by_multiple_roles(
        self, superuser_client, student_user, teacher_user
    ):
        url = f"{self.USER_LIST_URL}?role={RoleChoices.STUDENT}&role={RoleChoices.TEACHER}"
        response = superuser_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert len(results) >= 2
        roles_in_results = {item["role"] for item in results}
        assert RoleChoices.STUDENT in roles_in_results
        assert RoleChoices.TEACHER in roles_in_results

    def test_search_users_by_username(self, superuser_client, student_user):
        response = superuser_client.get(
            self.USER_LIST_URL, {"search": student_user.username[:5]}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1
        assert any(
            item["user"]["username"] == student_user.username
            for item in response.data["results"]
        )

    # --- Create User Tests ---
    def test_create_student_user(self, superuser_client):
        payload = {
            "username": "newstudent",
            "email": "newstudent@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "full_name": "New Student User",
            "role": RoleChoices.STUDENT,
            "grade": "10",
        }
        response = superuser_client.post(self.USER_LIST_URL, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username="newstudent").exists()
        profile = UserProfile.objects.get(user__username="newstudent")
        assert profile.role == RoleChoices.STUDENT
        assert profile.preferred_name == "New Student User"  # Auto-populated
        assert profile.grade == "10"
        assert not profile.user.is_staff

    def test_create_teacher_with_mentees(self, superuser_client, student_user):
        student_profile_pk = student_user.profile.pk
        payload = {
            "username": "newteacher",
            "email": "newteacher@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "full_name": "New Teacher",
            "role": RoleChoices.TEACHER,
            "mentee_ids": [student_profile_pk],
        }
        response = superuser_client.post(self.USER_LIST_URL, payload)
        assert response.status_code == status.HTTP_201_CREATED
        profile = UserProfile.objects.get(user__username="newteacher")
        assert profile.role == RoleChoices.TEACHER
        assert profile.mentees.count() == 1
        assert profile.mentees.first().user.username == student_user.username
        assert profile.user.is_staff

    def test_create_sub_admin_with_permissions(
        self, superuser_client, setup_permissions
    ):
        view_users_perm_pk = setup_permissions["view_users"].pk
        edit_users_perm_pk = setup_permissions["edit_users"].pk
        payload = {
            "username": "newsubadmin",
            "email": "newsubadmin@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "full_name": "New SubAdmin",
            "role": RoleChoices.SUB_ADMIN,
            "permission_ids": [view_users_perm_pk, edit_users_perm_pk],
        }
        response = superuser_client.post(self.USER_LIST_URL, payload)
        assert response.status_code == status.HTTP_201_CREATED
        profile = UserProfile.objects.get(user__username="newsubadmin")
        assert profile.role == RoleChoices.SUB_ADMIN
        assert profile.admin_permissions.count() == 2
        assert profile.admin_permissions.filter(slug="view_users").exists()
        assert profile.user.is_staff

    def test_create_user_preferred_name_auto_population(self, superuser_client):
        payload = {
            "username": "autonameuser",
            "email": "autoname@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "full_name": "Auto Preferred Name",
            "role": RoleChoices.STUDENT,
            # "preferred_name": "" # Explicitly empty or not provided
        }
        response = superuser_client.post(self.USER_LIST_URL, payload)
        assert response.status_code == status.HTTP_201_CREATED
        profile = UserProfile.objects.get(user__username="autonameuser")
        assert profile.preferred_name == "Auto Preferred Name"

    def test_create_user_fail_non_superuser_creating_admin(self, main_admin_client):
        # Main admin (not superuser) trying to create another ADMIN
        payload = {
            "username": "anotheradmin",
            "email": "anotheradmin@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "full_name": "Another Admin",
            "role": RoleChoices.ADMIN,
        }
        response = main_admin_client.post(self.USER_LIST_URL, payload)
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        )  # Based on perform_create logic

    def test_create_user_fail_sub_admin_creating_sub_admin(
        self, sub_admin_client_manage_users
    ):
        # Sub-admin (with create_users perm) trying to create another SUB_ADMIN
        payload = {
            "username": "subsubadmin",
            "email": "subsub@example.com",
            "password": "password123",
            "password_confirm": "password123",
            "full_name": "Sub Sub Admin",
            "role": RoleChoices.SUB_ADMIN,
        }
        response = sub_admin_client_manage_users.post(self.USER_LIST_URL, payload)
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        )  # Based on perform_create logic

    # --- Retrieve User Tests ---
    def test_retrieve_student_user_by_superuser(self, superuser_client, student_user):
        url = self.USER_DETAIL_URL(student_user.profile.pk)
        response = superuser_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"]["username"] == student_user.username
        assert response.data["role"] == RoleChoices.STUDENT
        assert (
            "assigned_mentor_details" in response.data
        )  # Should be present, null if no mentor
        assert (
            "mentees_details" not in response.data
            or response.data["mentees_details"] == []
        )  # Students don't have mentees
        assert (
            "admin_permissions" not in response.data
            or response.data["admin_permissions"] == []
        )  # Students don't have admin perms

    def test_retrieve_teacher_user_with_mentees_by_superuser(
        self, superuser_client, teacher_user, student_user
    ):
        teacher_user.profile.mentees.add(student_user.profile)
        url = self.USER_DETAIL_URL(teacher_user.profile.pk)
        response = superuser_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["user"]["username"] == teacher_user.username
        assert response.data["role"] == RoleChoices.TEACHER
        assert len(response.data["mentees_details"]) == 1
        assert response.data["mentees_details"][0]["user_id"] == student_user.profile.pk

    # --- Update User Tests ---
    def test_update_user_full_name(self, superuser_client, student_user):
        url = self.USER_DETAIL_URL(student_user.profile.pk)
        new_full_name = "Updated Student Name"
        payload = {"full_name": new_full_name}
        response = superuser_client.patch(url, payload)  # PATCH for partial update
        assert response.status_code == status.HTTP_200_OK
        student_user.profile.refresh_from_db()
        assert student_user.profile.full_name == new_full_name
        assert (
            student_user.profile.preferred_name == new_full_name
        )  # Auto-updated if preferred_name was same or empty

    def test_update_student_assign_mentor(
        self, superuser_client, student_user, teacher_user
    ):
        url = self.USER_DETAIL_URL(student_user.profile.pk)
        payload = {"assigned_mentor_id": teacher_user.profile.pk}
        response = superuser_client.patch(url, payload)
        assert response.status_code == status.HTTP_200_OK
        student_user.profile.refresh_from_db()
        assert student_user.profile.assigned_mentor.pk == teacher_user.profile.pk
        # Check retrieve reflects this
        response_get = superuser_client.get(url)
        assert (
            response_get.data["assigned_mentor_details"]["user_id"]
            == teacher_user.profile.pk
        )

    def test_update_teacher_add_mentee(
        self, superuser_client, teacher_user, student_user
    ):
        another_student = UserFactory(
            username="student2",
            profile_data={"role": RoleChoices.STUDENT, "full_name": "Student Two"},
        )
        url = self.USER_DETAIL_URL(teacher_user.profile.pk)
        # Assume teacher_user already has student_user as mentee from another test or setup
        # teacher_user.profile.mentees.add(student_user.profile)
        payload = {"mentee_ids": [student_user.profile.pk, another_student.profile.pk]}
        response = superuser_client.patch(url, payload)
        assert response.status_code == status.HTTP_200_OK, response.data
        teacher_user.profile.refresh_from_db()
        assert teacher_user.profile.mentees.count() == 2
        assert teacher_user.profile.mentees.filter(
            pk=another_student.profile.pk
        ).exists()

    def test_update_change_role_student_to_teacher(
        self, superuser_client, student_user
    ):
        url = self.USER_DETAIL_URL(student_user.profile.pk)
        payload = {"role": RoleChoices.TEACHER}
        response = superuser_client.patch(url, payload)
        assert response.status_code == status.HTTP_200_OK
        student_user.profile.refresh_from_db()
        assert student_user.profile.role == RoleChoices.TEACHER
        assert student_user.profile.user.is_staff  # Should be updated by model's save

    def test_update_fail_main_admin_change_role_to_admin(
        self, main_admin_client, student_user
    ):
        url = self.USER_DETAIL_URL(student_user.profile.pk)
        payload = {"role": RoleChoices.ADMIN}  # Trying to promote to ADMIN
        response = main_admin_client.patch(url, payload)
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        )  # perform_update restriction

    # --- Delete User Tests ---
    def test_delete_user_by_superuser(self, superuser_client, student_user):
        url = self.USER_DETAIL_URL(student_user.profile.pk)
        response = superuser_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not UserProfile.objects.filter(pk=student_user.profile.pk).exists()
        assert not User.objects.filter(pk=student_user.pk).exists()

    def test_delete_user_fail_by_main_admin(self, main_admin_client, student_user):
        url = self.USER_DETAIL_URL(student_user.profile.pk)
        response = main_admin_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_user_fail_by_sub_admin(
        self, sub_admin_client_manage_users, student_user
    ):
        # sub_admin_client_manage_users does not have delete permissions by default
        url = self.USER_DETAIL_URL(student_user.profile.pk)
        response = sub_admin_client_manage_users.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
