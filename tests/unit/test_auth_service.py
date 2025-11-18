"""
Unit tests for AuthService.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.user import User, UserRole
from src.schemas.auth import UserCreate, UserUpdate
from src.services.auth_service import AuthenticationError, AuthService, RegistrationError


@pytest.fixture
def sample_user():
    """Create sample user for testing."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="$2b$12$hashedpassword",
        full_name="Test User",
        role=UserRole.USER,
        is_active=True,
        created_at=datetime.utcnow(),
        last_login=None,
    )


@pytest.fixture
def sample_admin():
    """Create sample admin user for testing."""
    return User(
        id=2,
        username="admin",
        email="admin@example.com",
        password_hash="$2b$12$hashedpassword",
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
        created_at=datetime.utcnow(),
        last_login=None,
    )


@pytest.fixture
def mock_user_repo():
    """Create mock user repository."""
    repo = MagicMock()
    repo.username_exists = AsyncMock()
    repo.email_exists = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_username_or_email = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    repo.update_last_login = AsyncMock()
    return repo


@pytest.fixture
def auth_service(db_session, mock_user_repo):
    """Create auth service with mocked repository."""
    return AuthService(session=db_session, user_repo=mock_user_repo)


@pytest.mark.asyncio
class TestUserRegistration:
    """Tests for user registration."""

    async def test_register_user_success(self, auth_service, mock_user_repo, sample_user):
        """Test successful user registration."""
        mock_user_repo.username_exists.return_value = False
        mock_user_repo.email_exists.return_value = False
        mock_user_repo.create.return_value = sample_user

        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePassword123!",
            full_name="Test User",
        )

        with patch("src.services.auth_service.get_password_hash") as mock_hash:
            mock_hash.return_value = "$2b$12$hashedpassword"
            result = await auth_service.register_user(user_data)

        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.role == UserRole.USER
        assert result.is_active is True
        mock_user_repo.create.assert_called_once()

    async def test_register_user_duplicate_username(self, auth_service, mock_user_repo):
        """Test registration with existing username."""
        mock_user_repo.username_exists.return_value = True
        mock_user_repo.email_exists.return_value = False

        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePassword123!",
            full_name="Test User",
        )

        with pytest.raises(RegistrationError, match="Username already exists"):
            await auth_service.register_user(user_data)

    async def test_register_user_duplicate_email(self, auth_service, mock_user_repo):
        """Test registration with existing email."""
        mock_user_repo.username_exists.return_value = False
        mock_user_repo.email_exists.return_value = True

        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePassword123!",
            full_name="Test User",
        )

        with pytest.raises(RegistrationError, match="Email already exists"):
            await auth_service.register_user(user_data)


@pytest.mark.asyncio
class TestAuthentication:
    """Tests for user authentication."""

    async def test_authenticate_user_success(
        self, auth_service, mock_user_repo, db_session, sample_user
    ):
        """Test successful authentication."""
        mock_user_repo.get_by_username_or_email.return_value = sample_user

        with patch("src.services.auth_service.verify_password") as mock_verify:
            mock_verify.return_value = True
            result = await auth_service.authenticate_user("testuser", "password123")

        assert result.username == "testuser"
        mock_user_repo.update_last_login.assert_called_once_with(sample_user.id)

    async def test_authenticate_user_not_found(self, auth_service, mock_user_repo):
        """Test authentication with nonexistent user."""
        mock_user_repo.get_by_username_or_email.return_value = None

        with pytest.raises(AuthenticationError, match="Invalid username or password"):
            await auth_service.authenticate_user("nonexistent", "password123")

    async def test_authenticate_user_inactive(self, auth_service, mock_user_repo, sample_user):
        """Test authentication with inactive user."""
        sample_user.is_active = False
        mock_user_repo.get_by_username_or_email.return_value = sample_user

        with pytest.raises(AuthenticationError, match="Account is inactive"):
            await auth_service.authenticate_user("testuser", "password123")

    async def test_authenticate_user_wrong_password(
        self, auth_service, mock_user_repo, sample_user
    ):
        """Test authentication with wrong password."""
        mock_user_repo.get_by_username_or_email.return_value = sample_user

        with patch("src.services.auth_service.verify_password") as mock_verify:
            mock_verify.return_value = False
            with pytest.raises(AuthenticationError, match="Invalid username or password"):
                await auth_service.authenticate_user("testuser", "wrongpassword")


@pytest.mark.asyncio
class TestLogin:
    """Tests for login functionality."""

    async def test_login_success(self, auth_service, mock_user_repo, db_session, sample_user):
        """Test successful login with token generation."""
        mock_user_repo.get_by_username_or_email.return_value = sample_user

        with patch("src.services.auth_service.verify_password") as mock_verify, patch(
            "src.services.auth_service.create_access_token"
        ) as mock_token:
            mock_verify.return_value = True
            mock_token.return_value = (
                "test_token_12345",
                datetime.utcnow().replace(microsecond=0),
            )

            result = await auth_service.login("testuser", "password123")

        assert result.access_token == "test_token_12345"
        assert result.token_type == "bearer"
        assert result.expires_in >= 0

    async def test_login_invalid_credentials(self, auth_service, mock_user_repo):
        """Test login with invalid credentials."""
        mock_user_repo.get_by_username_or_email.return_value = None

        with pytest.raises(AuthenticationError):
            await auth_service.login("wronguser", "wrongpass")


@pytest.mark.asyncio
class TestUserRetrieval:
    """Tests for user retrieval."""

    async def test_get_user_by_id_success(self, auth_service, mock_user_repo, sample_user):
        """Test getting user by ID."""
        mock_user_repo.get_by_id.return_value = sample_user

        result = await auth_service.get_user_by_id(1)

        assert result.id == 1
        assert result.username == "testuser"

    async def test_get_user_by_id_not_found(self, auth_service, mock_user_repo):
        """Test getting nonexistent user."""
        mock_user_repo.get_by_id.return_value = None

        result = await auth_service.get_user_by_id(999)

        assert result is None


@pytest.mark.asyncio
class TestUserUpdate:
    """Tests for user profile updates."""

    async def test_update_user_success(self, auth_service, mock_user_repo, sample_user):
        """Test successful user update."""
        mock_user_repo.get_by_id.return_value = sample_user
        # Modify sample_user directly
        sample_user.full_name = "Updated Name"
        mock_user_repo.update.return_value = sample_user

        update_data = UserUpdate(full_name="Updated Name")
        result = await auth_service.update_user(1, update_data)

        assert result.full_name == "Updated Name"
        mock_user_repo.update.assert_called_once()

    async def test_update_user_email(self, auth_service, mock_user_repo, sample_user):
        """Test updating user email."""
        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.get_by_email.return_value = None
        # Modify sample_user directly
        sample_user.email = "newemail@example.com"
        mock_user_repo.update.return_value = sample_user

        update_data = UserUpdate(email="newemail@example.com")
        result = await auth_service.update_user(1, update_data)

        assert result.email == "newemail@example.com"

    async def test_update_user_duplicate_email(self, auth_service, mock_user_repo, sample_user):
        """Test updating to existing email."""
        # Create other user with proper constructor
        from datetime import datetime

        other_user = User(
            id=2,
            username="otheruser",
            email="existing@example.com",
            password_hash="$2b$12$hashedpassword",
            full_name="Other User",
            role=UserRole.USER,
            is_active=True,
            created_at=datetime.utcnow(),
        )

        mock_user_repo.get_by_id.return_value = sample_user
        mock_user_repo.get_by_email.return_value = other_user

        update_data = UserUpdate(email="existing@example.com")

        with pytest.raises(ValueError, match="Email already exists"):
            await auth_service.update_user(1, update_data)

    async def test_update_user_not_found(self, auth_service, mock_user_repo):
        """Test updating nonexistent user."""
        mock_user_repo.get_by_id.return_value = None

        update_data = UserUpdate(full_name="New Name")

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.update_user(999, update_data)

    async def test_update_user_password(self, auth_service, mock_user_repo, sample_user):
        """Test updating user password."""
        mock_user_repo.get_by_id.return_value = sample_user
        # Modify sample_user directly
        sample_user.password_hash = "$2b$12$newhashedpassword"
        mock_user_repo.update.return_value = sample_user

        with patch("src.services.auth_service.get_password_hash") as mock_hash:
            mock_hash.return_value = "$2b$12$newhashedpassword"
            update_data = UserUpdate(password="NewPassword123!")
            result = await auth_service.update_user(1, update_data)

        assert result is not None
        mock_hash.assert_called_once_with("NewPassword123!")


@pytest.mark.asyncio
class TestPasswordChange:
    """Tests for password change functionality."""

    async def test_change_password_success(self, auth_service, mock_user_repo, sample_user):
        """Test successful password change."""
        mock_user_repo.get_by_id.return_value = sample_user
        # Modify sample_user directly
        mock_user_repo.update.return_value = sample_user

        with patch("src.services.auth_service.verify_password") as mock_verify, patch(
            "src.services.auth_service.get_password_hash"
        ) as mock_hash:
            mock_verify.return_value = True
            mock_hash.return_value = "$2b$12$newhashedpassword"

            result = await auth_service.change_password(1, "oldpassword", "newpassword")

        assert result is not None
        mock_user_repo.update.assert_called_once()

    async def test_change_password_wrong_current(self, auth_service, mock_user_repo, sample_user):
        """Test password change with wrong current password."""
        mock_user_repo.get_by_id.return_value = sample_user

        with patch("src.services.auth_service.verify_password") as mock_verify:
            mock_verify.return_value = False

            with pytest.raises(AuthenticationError, match="Current password is incorrect"):
                await auth_service.change_password(1, "wrongpassword", "newpassword")

    async def test_change_password_user_not_found(self, auth_service, mock_user_repo):
        """Test password change for nonexistent user."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.change_password(999, "oldpassword", "newpassword")


@pytest.mark.asyncio
class TestUserActivation:
    """Tests for user activation/deactivation."""

    async def test_deactivate_user_success(self, auth_service, mock_user_repo, sample_user):
        """Test deactivating user account."""
        # Modify sample_user directly
        sample_user.is_active = False
        mock_user_repo.update.return_value = sample_user

        result = await auth_service.deactivate_user(1)

        assert result.is_active is False
        mock_user_repo.update.assert_called_once_with(1, {"is_active": False})

    async def test_deactivate_user_not_found(self, auth_service, mock_user_repo):
        """Test deactivating nonexistent user."""
        mock_user_repo.update.return_value = None

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.deactivate_user(999)

    async def test_activate_user_success(self, auth_service, mock_user_repo, sample_user):
        """Test activating user account."""
        sample_user.is_active = False
        # Modify sample_user to activate
        sample_user.is_active = True
        mock_user_repo.update.return_value = sample_user

        result = await auth_service.activate_user(1)

        assert result.is_active is True
        mock_user_repo.update.assert_called_once_with(1, {"is_active": True})

    async def test_activate_user_not_found(self, auth_service, mock_user_repo):
        """Test activating nonexistent user."""
        mock_user_repo.update.return_value = None

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.activate_user(999)


@pytest.mark.asyncio
class TestUserRoleManagement:
    """Tests for user role management."""

    async def test_promote_to_admin_success(self, auth_service, mock_user_repo, sample_user):
        """Test promoting user to admin."""
        # Modify sample_user directly
        sample_user.role = UserRole.ADMIN
        mock_user_repo.update.return_value = sample_user

        result = await auth_service.promote_to_admin(1)

        assert result.role == UserRole.ADMIN
        mock_user_repo.update.assert_called_once_with(1, {"role": UserRole.ADMIN})

    async def test_promote_to_admin_not_found(self, auth_service, mock_user_repo):
        """Test promoting nonexistent user."""
        mock_user_repo.update.return_value = None

        with pytest.raises(ValueError, match="User not found"):
            await auth_service.promote_to_admin(999)


@pytest.mark.asyncio
class TestAuthServiceInitialization:
    """Tests for auth service initialization."""

    async def test_service_initialization_default_repo(self, db_session):
        """Test service initializes with default repository."""
        service = AuthService(session=db_session)

        assert service.session is db_session
        assert service.user_repo is not None

    async def test_service_initialization_custom_repo(self, db_session, mock_user_repo):
        """Test service initializes with custom repository."""
        service = AuthService(session=db_session, user_repo=mock_user_repo)

        assert service.session is db_session
        assert service.user_repo is mock_user_repo
