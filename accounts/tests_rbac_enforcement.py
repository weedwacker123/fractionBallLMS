from django.test import SimpleTestCase

from accounts import rbac
from content.cms_views import has_cms_access


class DummyUser:
    def __init__(self, perms, school_id=1, user_id=10, authenticated=True, is_superuser=False):
        self._perms = set(perms)
        self.school_id = school_id
        self.id = user_id
        self.is_authenticated = authenticated
        self.is_superuser = is_superuser

    def has_perm_key(self, key):
        return key in self._perms

    def can(self, action, obj=None):
        return rbac.can(self, action, obj=obj)


class DummyObj:
    def __init__(self, school_id=1, owner_id=10, status="DRAFT"):
        self.school_id = school_id
        self.owner_id = owner_id
        self.status = status


class RBACScopeTests(SimpleTestCase):
    def test_content_manager_can_access_cross_school_resource(self):
        user = DummyUser(
            perms={"resources_download", "cms_edit"},
            school_id=1,
            user_id=11,
        )
        resource = DummyObj(school_id=2, owner_id=22, status="DRAFT")
        self.assertTrue(rbac.can(user, "resource_download", obj=resource))

    def test_registered_user_cannot_access_cross_school_resource(self):
        user = DummyUser(
            perms={"resources_download"},
            school_id=1,
            user_id=11,
        )
        resource = DummyObj(school_id=2, owner_id=22, status="PUBLISHED")
        self.assertFalse(rbac.can(user, "resource_download", obj=resource))


class CMSAccessTests(SimpleTestCase):
    def test_cms_access_requires_permission(self):
        user = DummyUser(perms=set(), is_superuser=False)
        self.assertFalse(has_cms_access(user))

    def test_cms_access_allowed_by_permission(self):
        user = DummyUser(perms={"cms_view"}, is_superuser=False)
        self.assertTrue(has_cms_access(user))

    def test_superuser_always_has_cms_access(self):
        user = DummyUser(perms=set(), is_superuser=True)
        self.assertTrue(has_cms_access(user))
