import unittest
from app import create_app, db
from app.models import User, KPI, Area
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class UserModelCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_area_assign(self):
        u = User(username='john', email='john@example.com')
        a = Area(name='Talladega')
        db.session.add(u)
        db.session.add(a)
        db.session.commit()
        self.assertEqual(u.areas.all(), [])

        u.add_area(a)
        db.session.commit()
        self.assertTrue(u.is_assigned(a))
        self.assertEqual(u.areas.count(), 1)
        self.assertEqual(u.areas.first().name, 'Talladega')

        u.rm_area(a)
        db.session.commit()
        self.assertFalse(u.is_assigned(a))
        self.assertEqual(u.areas.count(), 0)

        a.add_user(u)
        db.session.commit()
        self.assertTrue(a.is_assigned(u))
        self.assertEqual(a.users.count(), 1)
        self.assertEqual(a.users.first().username, 'john')

        a.rm_user(u)
        db.session.commit()
        self.assertFalse(a.is_assigned(u))
        self.assertEqual(a.users.count(), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
