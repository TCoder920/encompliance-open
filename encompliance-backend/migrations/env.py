from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import the models to include them in migrations
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import Base directly from database
from app.database import Base
from app.database import DATABASE_URL

# Import all models to ensure they're included in migrations
from app.models.user import User
from app.models.document import Document
from app.models.query_log import QueryLog
from app.models.facility_type import FacilityType, regulation_facility_types
from app.models.regulation import Regulation
from app.models.user_document import UserDocument
from app.models.thread_map import ThreadMap
from app.models.export_quota import ExportQuota
from app.models.export_request import ExportRequest
from app.models.note import Note
from app.models.notification import Notification
from app.models.push_subscription import PushSubscription
from app.models.notification_settings import NotificationSettings
from app.models.calendar_event import CalendarEvent

# Training Models
from app.models.training_program import TrainingProgram, training_program_facility_types
from app.models.staff_member import StaffMember
from app.models.training_assignment import TrainingAssignment
from app.models.training_material import TrainingMaterial
from app.models.training_completion import TrainingCompletion

# Authentication Models
from app.models.token import BlacklistedToken
from app.models.webauthn_credential import WebAuthnCredential
from app.models.user_otp import UserOTP
from app.models.magic_link import MagicLink
from app.models.oauth_identity import OAuthIdentity

# Support portal models are managed separately via SupportPortalBase

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the SQLAlchemy URL from our app config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
