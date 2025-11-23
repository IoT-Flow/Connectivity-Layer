"""
TDD Test Suite for User Model and User Management
Following TDD approach - write tests first, then implement functionality
"""

import pytest
import os
from datetime import datetime, timezone

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from src.models import db, User


@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self, app):
        """Test creating a new user"""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash='hashed_password'
            )
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.user_id is not None
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.is_active is True
            assert user.is_admin is False
            assert user.created_at is not None
    
    def test_user_id_is_unique(self, app):
        """Test that user_id is automatically generated and unique"""
        with app.app_context():
            user1 = User(username='user1', email='user1@example.com', password_hash='hash1')
            user2 = User(username='user2', email='user2@example.com', password_hash='hash2')
            
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            assert user1.user_id != user2.user_id
            assert len(user1.user_id) == 32
            assert len(user2.user_id) == 32
    
    def test_username_must_be_unique(self, app):
        """Test that username must be unique"""
        with app.app_context():
            user1 = User(username='testuser', email='test1@example.com', password_hash='hash1')
            user2 = User(username='testuser', email='test2@example.com', password_hash='hash2')
            
            db.session.add(user1)
            db.session.commit()
            
            db.session.add(user2)
            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()
    
    def test_email_must_be_unique(self, app):
        """Test that email must be unique"""
        with app.app_context():
            user1 = User(username='user1', email='test@example.com', password_hash='hash1')
            user2 = User(username='user2', email='test@example.com', password_hash='hash2')
            
            db.session.add(user1)
            db.session.commit()
            
            db.session.add(user2)
            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()
    
    def test_user_to_dict(self, app):
        """Test user to_dict method"""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                password_hash='hashed_password'
            )
            db.session.add(user)
            db.session.commit()
            
            user_dict = user.to_dict()
            
            assert user_dict['username'] == 'testuser'
            assert user_dict['email'] == 'test@example.com'
            assert user_dict['is_active'] is True
            assert user_dict['is_admin'] is False
            assert 'password_hash' not in user_dict  # Should not expose password
            assert 'created_at' in user_dict
    
    def test_user_can_be_deactivated(self, app):
        """Test that user can be deactivated"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()
            
            user.is_active = False
            db.session.commit()
            
            assert user.is_active is False
    
    def test_user_can_be_admin(self, app):
        """Test that user can be set as admin"""
        with app.app_context():
            user = User(username='admin', email='admin@example.com', password_hash='hash')
            user.is_admin = True
            db.session.add(user)
            db.session.commit()
            
            assert user.is_admin is True
    
    def test_user_last_login_tracking(self, app):
        """Test that last_login can be updated"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()
            
            assert user.last_login is None
            
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            assert user.last_login is not None


class TestUserPasswordManagement:
    """Test user password management functionality"""
    
    def test_user_has_set_password_method(self, app):
        """Test that user can set password (method should exist)"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password_hash='temp')
            
            # This test expects a set_password method to exist
            assert hasattr(user, 'set_password'), "User should have set_password method"
    
    def test_user_has_check_password_method(self, app):
        """Test that user can check password (method should exist)"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password_hash='temp')
            
            # This test expects a check_password method to exist
            assert hasattr(user, 'check_password'), "User should have check_password method"
    
    def test_set_password_hashes_password(self, app):
        """Test that set_password properly hashes the password"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password_hash='temp')
            
            if hasattr(user, 'set_password'):
                user.set_password('mypassword123')
                
                # Password should be hashed, not stored in plain text
                assert user.password_hash != 'mypassword123'
                assert len(user.password_hash) > 20  # Hashed passwords are long
    
    def test_check_password_validates_correctly(self, app):
        """Test that check_password validates password correctly"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password_hash='temp')
            
            if hasattr(user, 'set_password') and hasattr(user, 'check_password'):
                user.set_password('mypassword123')
                
                # Correct password should return True
                assert user.check_password('mypassword123') is True
                
                # Wrong password should return False
                assert user.check_password('wrongpassword') is False


class TestUserRoutes:
    """Test user management API routes"""
    

    def test_get_user_by_id(self, client, app):
        """Test getting user by ID (requires matching User ID or admin token)"""
        # Create a user
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()
            user_id = user.user_id
        
        # Get user by ID with matching User ID header
        response = client.get(
            f'/api/v1/users/{user_id}',
            headers={'X-User-ID': user_id}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['username'] == 'testuser'
        assert data['user']['email'] == 'test@example.com'
    
    def test_get_user_not_found(self, client):
        """Test getting non-existent user (with admin token)"""
        admin_token = os.environ.get('IOTFLOW_ADMIN_TOKEN', 'test')
        
        response = client.get(
            '/api/v1/users/nonexistent123',
            headers={'Authorization': f'admin {admin_token}'}
        )
        
        assert response.status_code == 404
    
    def test_update_user(self, client, app):
        """Test updating user information (requires matching User ID or admin token)"""
        # Create a user
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()
            user_id = user.user_id
        
        # Update user with matching User ID header
        response = client.put(
            f'/api/v1/users/{user_id}',
            headers={'X-User-ID': user_id},
            json={
                'email': 'newemail@example.com'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['user']['email'] == 'newemail@example.com'
    
    def test_delete_user(self, client, app):
        """Test deleting a user (requires admin token)"""
        admin_token = os.environ.get('IOTFLOW_ADMIN_TOKEN', 'test')
        
        # Create a target user
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()
            user_id = user.user_id
        
        # Delete user with admin token
        response = client.delete(
            f'/api/v1/users/{user_id}',
            headers={'Authorization': f'admin {admin_token}'}
        )
        
        assert response.status_code == 200
        
        # Verify user is permanently deleted (hard delete)
        response = client.get(
            f'/api/v1/users/{user_id}',
            headers={'Authorization': f'admin {admin_token}'}
        )
        assert response.status_code == 404  # User no longer exists
    
    def test_list_users(self, client, app):
        """Test listing all users (Admin only)"""
        admin_token = os.environ.get('IOTFLOW_ADMIN_TOKEN', 'test')
        
        # Create some users
        with app.app_context():
            user1 = User(username='user1', email='user1@example.com', password_hash='hash')
            user2 = User(username='user2', email='user2@example.com', password_hash='hash')
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
        
        # Test without token - should fail
        response = client.get('/api/v1/users')
        assert response.status_code == 401
        
        # Test with admin token - should succeed
        response = client.get(
            '/api/v1/users',
            headers={'Authorization': f'admin {admin_token}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert 'users' in data
        assert len(data['users']) >= 2
    



class TestUserAuthentication:
    """Test user authentication functionality"""
    
    def test_login_endpoint_exists(self, client):
        """Test that POST /api/v1/auth/login endpoint exists"""
        response = client.post(
            '/api/v1/auth/login',
            json={
                'username': 'testuser',
                'password': 'password123'
            }
        )
        
        # Should not return 404
        assert response.status_code != 404
    
    def test_login_success(self, client, app):
        """Test successful login"""
        # Create a user with known password
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password_hash='hash')
            if hasattr(user, 'set_password'):
                user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        # Login
        response = client.post(
            '/api/v1/auth/login',
            json={
                'username': 'testuser',
                'password': 'password123'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data or 'user' in data
    
    def test_login_wrong_password(self, client, app):
        """Test login with wrong password"""
        # Create a user
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password_hash='hash')
            if hasattr(user, 'set_password'):
                user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        # Try to login with wrong password
        response = client.post(
            '/api/v1/auth/login',
            json={
                'username': 'testuser',
                'password': 'wrongpassword'
            }
        )
        
        assert response.status_code == 401
    
    def test_login_inactive_user(self, client, app):
        """Test that inactive users cannot login"""
        # Create an inactive user
        with app.app_context():
            user = User(username='testuser', email='test@example.com', password_hash='hash')
            user.is_active = False
            if hasattr(user, 'set_password'):
                user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        # Try to login
        response = client.post(
            '/api/v1/auth/login',
            json={
                'username': 'testuser',
                'password': 'password123'
            }
        )
        
        assert response.status_code == 401


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
