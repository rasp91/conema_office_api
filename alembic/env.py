import importlib
import os
import sys
from logging.config import fileConfig
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make sure the project root is on sys.path so src.* imports work
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database import DATABASE_URL
from src.database.base import Base


def import_all_models():
    """Automatically import all model files to register them with Base"""
    models_dir = Path(__file__).parent.parent / "src" / "database" / "models"

    if not models_dir.exists():
        print(f"⚠️  Models directory not found: {models_dir}")
        return

    imported_count = 0

    for py_file in models_dir.rglob("*.py"):
        if py_file.name.startswith("__") or py_file.name.startswith("."):
            continue

        relative_path = py_file.relative_to(models_dir.parent.parent.parent)
        module_path = str(relative_path.with_suffix("")).replace(os.sep, ".")

        try:
            importlib.import_module(module_path)
            imported_count += 1
            print(f"✅ Imported model: {module_path}")
        except ImportError as e:
            print(f"⚠️  Could not import {module_path}: {e}")
        except Exception as e:
            print(f"❌ Error importing {module_path}: {e}")

    print(f"📊 Successfully imported {imported_count} model files")
    print(f"🏗️  Total tables registered: {len(Base.metadata.tables)}")


import_all_models()

# Alembic Config object — gives access to alembic.ini values
config = context.config

# Override sqlalchemy.url with the value built from .env
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection required)."""
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
    """Run migrations in 'online' mode (live DB connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
