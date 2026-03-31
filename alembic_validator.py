"""
Enhanced Database Validator for Röchling Production API
A comprehensive database schema validation tool using Alembic.
"""

import logging
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import required modules
try:
    from alembic.runtime.migration import MigrationContext
    from alembic.autogenerate import compare_metadata
    from alembic.script import ScriptDirectory
    from alembic.config import Config
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("Make sure SQLAlchemy and Alembic are installed in your virtual environment.")
    print("Run: pip install sqlalchemy alembic")
    sys.exit(1)

# Import project modules
try:
    # Import Base and core modules first
    # Auto-discover and import all models
    import importlib

    from src.database.base import Base
    from src.database import engine
    from src.config import config

    def import_all_models():
        """Automatically import all model files to register them with Base"""
        models_dir = Path(__file__).parent / "src" / "database" / "models"

        if not models_dir.exists():
            logger.warning(f"⚠️  Models directory not found: {models_dir}")
            return 0

        imported_count = 0

        # Walk through all Python files in the models directory
        for py_file in models_dir.rglob("*.py"):
            if py_file.name.startswith("__") or py_file.name.startswith("."):
                continue

            # Convert file path to module path
            relative_path = py_file.relative_to(models_dir.parent.parent.parent)
            module_path = str(relative_path.with_suffix("")).replace(os.sep, ".")

            try:
                importlib.import_module(module_path)
                imported_count += 1
                logger.debug(f"✅ Imported model: {module_path}")
            except ImportError as e:
                logger.warning(f"⚠️  Could not import {module_path}: {e}")
            except Exception as e:
                logger.error(f"❌ Error importing {module_path}: {e}")

        logger.info(f"📊 Auto-imported {imported_count} model files")
        logger.info(f"🏗️  Total tables registered: {len(Base.metadata.tables)}")
        return imported_count

    # Import all models automatically
    model_count = import_all_models()
    logger.info("✅ All project modules imported successfully")

except ImportError as e:
    print(f"❌ Error importing project modules: {e}")
    print("Make sure you're running this from the project root directory.")
    print("Current directory:", os.getcwd())
    sys.exit(1)


@dataclass
class SchemaDifference:
    """Represents a difference between model and database schema"""

    type: str  # 'add_table', 'remove_table', 'add_column', 'modify_type', etc.
    table: str
    detail: str
    raw_diff: Any


class DatabaseValidator:
    """Enhanced database validator for Röchling Production API"""

    def __init__(self):
        """Initialize validator with project configuration"""
        self.alembic_config_path = project_root / "alembic.ini"

        if not self.alembic_config_path.exists():
            raise FileNotFoundError(f"Alembic config not found at {self.alembic_config_path}")

        self.alembic_cfg = Config(str(self.alembic_config_path))
        self.engine = engine
        self.metadata = Base.metadata
        self.config = config

    def test_database_connection(self) -> bool:
        """Test if database connection is working"""
        try:
            with self.engine.connect():
                pass
            logger.info("✅ Database connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about registered models"""
        models = []
        for table_name, table in self.metadata.tables.items():
            models.append(
                {
                    "table_name": table_name,
                    "columns": len(table.columns),
                    "primary_keys": [col.name for col in table.primary_key.columns],
                    "foreign_keys": len(table.foreign_keys),
                    "indexes": len(table.indexes),
                }
            )

        return {"total_models": len(models), "models": sorted(models, key=lambda x: x["table_name"])}

    def check_migration_status(self) -> Dict[str, Any]:
        """Check if database is at the latest migration"""
        script = ScriptDirectory.from_config(self.alembic_cfg)

        with self.engine.begin() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        head_rev = script.get_current_head()

        return {
            "current": current_rev,
            "head": head_rev,
            "is_up_to_date": current_rev == head_rev,
            "pending_upgrades": current_rev != head_rev,
        }

    def detect_schema_differences(self) -> List[SchemaDifference]:
        """Detect differences between models and database using Alembic autogenerate"""
        differences = []

        with self.engine.begin() as connection:
            context = MigrationContext.configure(connection)
            diff = compare_metadata(context, self.metadata)

            for item in diff:
                if isinstance(item, list) and len(item) == 1:
                    item = item[0]
                diff_type = item[0]

                if diff_type == "add_table":
                    table = item[1]
                    differences.append(
                        SchemaDifference(
                            type="add_table",
                            table=table.name,
                            detail=f"Table '{table.name}' exists in models but not in database",
                            raw_diff=item,
                        )
                    )

                elif diff_type == "remove_table":
                    table = item[1]
                    differences.append(
                        SchemaDifference(
                            type="remove_table",
                            table=table.name,
                            detail=f"Table '{table.name}' exists in database but not in models",
                            raw_diff=item,
                        )
                    )

                elif diff_type == "add_column":
                    table_name, column = item[2], item[3]
                    differences.append(
                        SchemaDifference(
                            type="add_column",
                            table=table_name,
                            detail=f"Column '{column.name}' missing in database table '{table_name}'",
                            raw_diff=item,
                        )
                    )

                elif diff_type == "remove_column":
                    table_name, column = item[2], item[3]
                    differences.append(
                        SchemaDifference(
                            type="remove_column",
                            table=table_name,
                            detail=f"Column '{column.name}' in database but not in model '{table_name}'",
                            raw_diff=item,
                        )
                    )

                elif diff_type == "modify_type":
                    table_name, column_name = item[2], item[3]
                    existing_type, new_type = item[5], item[6]
                    differences.append(
                        SchemaDifference(
                            type="modify_type",
                            table=table_name,
                            detail=f"Type mismatch in '{table_name}.{column_name}': DB has {existing_type}, model expects {new_type}",
                            raw_diff=item,
                        )
                    )

                elif diff_type == "modify_nullable":
                    table_name, column_name = item[2], item[3]
                    existing_nullable, new_nullable = item[5], item[6]
                    differences.append(
                        SchemaDifference(
                            type="modify_nullable",
                            table=table_name,
                            detail=f"Nullable mismatch in '{table_name}.{column_name}': DB={existing_nullable}, model={new_nullable}",
                            raw_diff=item,
                        )
                    )

                else:
                    # Handle other difference types
                    differences.append(
                        SchemaDifference(
                            type=diff_type,
                            table="unknown",
                            detail=f"Schema difference: {diff_type}",
                            raw_diff=item,
                        )
                    )

        return differences

    def get_migration_history(self) -> List[Dict[str, str]]:
        """Get list of applied migrations with error handling"""
        try:
            script = ScriptDirectory.from_config(self.alembic_cfg)

            with self.engine.begin() as connection:
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()

            history = []
            if current_rev:
                try:
                    # Try to walk the revisions
                    for rev in script.walk_revisions(current_rev, "base"):
                        history.append(
                            {
                                "revision": rev.revision,
                                "down_revision": rev.down_revision,
                                "message": rev.doc or "No message",
                                "create_date": str(getattr(rev.module, "create_date", "unknown")),
                            }
                        )
                except Exception as walk_error:
                    logger.warning(f"Could not walk full revision history: {walk_error}")
                    # Try to get at least the current revision info
                    try:
                        current_revision = script.get_revision(current_rev)
                        if current_revision:
                            history.append(
                                {
                                    "revision": current_revision.revision,
                                    "down_revision": current_revision.down_revision,
                                    "message": current_revision.doc or "No message",
                                    "create_date": str(getattr(current_revision.module, "create_date", "unknown")),
                                }
                            )
                    except Exception:
                        logger.warning("Could not retrieve current revision info")
                        history.append(
                            {
                                "revision": current_rev,
                                "down_revision": "unknown",
                                "message": "Current revision (history unavailable)",
                                "create_date": "unknown",
                            }
                        )

            return history

        except Exception as e:
            logger.error(f"Error getting migration history: {e}")
            return []

    def validate(self) -> Dict[str, Any]:
        """Run comprehensive database validation with error handling"""
        logger.info("🔍 Starting comprehensive database validation...")

        # Test database connection
        connection_ok = self.test_database_connection()
        if not connection_ok:
            return {"is_valid": False, "connection_ok": False, "error": "Database connection failed"}

        # Get model information
        try:
            model_info = self.get_model_info()
            logger.info(f"📊 Found {model_info['total_models']} registered models")
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            model_info = {"total_models": 0, "models": []}

        # Check migration status
        try:
            migration_status = self.check_migration_status()
        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            migration_status = {"current": "unknown", "head": "unknown", "is_up_to_date": False, "pending_upgrades": True, "error": str(e)}

        # Detect schema differences
        try:
            differences = self.detect_schema_differences()
        except Exception as e:
            logger.error(f"Error detecting schema differences: {e}")
            differences = []

        # Get migration history
        try:
            history = self.get_migration_history()
        except Exception as e:
            logger.error(f"Error getting migration history: {e}")
            history = []

        is_valid = len(differences) == 0 and migration_status.get("is_up_to_date", False)

        return {
            "is_valid": is_valid,
            "connection_ok": connection_ok,
            "migration_status": migration_status,
            "schema_differences": differences,
            "migration_history": history,
            "model_info": model_info,
            "database_config": {
                "host": self.config.DATABASE_HOST,
                "database": self.config.DATABASE_NAME,
                "user": self.config.DATABASE_USER,
            },
            "total_issues": len(differences),
            "validation_timestamp": datetime.utcnow().isoformat(),
        }

    def print_validation_report(self, result: Dict[str, Any]):
        """Print comprehensive validation report"""
        print("\n" + "=" * 80)
        print("🚀 RÖCHLING PRODUCTION API - DATABASE VALIDATION REPORT")
        print("=" * 80)

        # Database connection info
        db_config = result["database_config"]
        print(f"\n📊 Database Information:")
        print(f"  Host:     {db_config['host']}")
        print(f"  Database: {db_config['database']}")
        print(f"  User:     {db_config['user']}")
        print(f"  Status:   {'✅ Connected' if result['connection_ok'] else '❌ Connection Failed'}")

        # Model information
        model_info = result["model_info"]
        print(f"\n📋 Model Information:")
        print(f"  Total Models: {model_info['total_models']}")

        # Show production models separately
        production_models = [m for m in model_info["models"] if m["table_name"].startswith("production_")]
        other_models = [m for m in model_info["models"] if not m["table_name"].startswith("production_")]

        if production_models:
            print(f"  Production Models: {len(production_models)}")
            for model in production_models:
                print(f"    • {model['table_name']} ({model['columns']} columns)")

        if other_models:
            print(f"  Other Models: {len(other_models)}")
            for model in other_models:
                print(f"    • {model['table_name']} ({model['columns']} columns)")

        # Migration status
        migration_status = result["migration_status"]
        print(f"\n🔄 Migration Status:")
        print(f"  Current Revision: {migration_status['current'] or 'None'}")
        print(f"  Head Revision:    {migration_status['head'] or 'None'}")
        print(f"  Up to Date:       {'✅ Yes' if migration_status['is_up_to_date'] else '❌ No'}")

        if not migration_status["is_up_to_date"]:
            print(f"  ⚠️  Database is behind! Run migration to update.")

        # Schema differences
        differences = result["schema_differences"]
        if not differences:
            print("\n✅ No schema drift detected! Models match database perfectly.")
        else:
            print(f"\n❌ Found {len(differences)} schema differences:")

            # Group by type
            by_type = {}
            for diff in differences:
                by_type.setdefault(diff.type, []).append(diff)

            for diff_type, items in by_type.items():
                print(f"\n  {diff_type.upper().replace('_', ' ')} ({len(items)}):")
                for item in items:
                    print(f"    • {item.detail}")

        # Migration history
        history = result["migration_history"]
        if history:
            print(f"\n📜 Recent Migration History ({min(5, len(history))} of {len(history)}):")
            for i, migration in enumerate(history[:5]):
                revision = migration.get("revision", "unknown")[:8]
                message = migration.get("message", "No message")
                print(f"  {i+1}. {revision} - {message}")
        else:
            print(f"\n📜 Migration History: No migration history available")
            if result["migration_status"].get("error"):
                print(f"     Error: {result['migration_status']['error']}")
                print(f"     ⚠️  This may indicate migration files are corrupted or missing")

        # Overall status and recommendations
        print("\n" + "=" * 80)
        if result["is_valid"]:
            print("🎉 DATABASE IS VALID AND UP TO DATE")
            print("\n✨ Your database schema matches your models perfectly!")
        else:
            print("⚠️  VALIDATION FAILED - ACTION REQUIRED")
            print("\n🛠️  Recommended Actions:")

            if not migration_status["is_up_to_date"]:
                print("   1. Upgrade database to latest migration:")
                print("      → alembic upgrade head")
                print("      → python migrate.py (option 2)")

            if differences:
                print("   2. Create new migration for schema changes:")
                print("      → alembic revision --autogenerate -m 'Fix schema differences'")
                print("      → python migrate.py (option 1)")
                print("      → Then run: alembic upgrade head")

            if result["migration_status"].get("error"):
                print("   3. Fix migration history issues:")
                print("      → alembic stamp base  # Reset tracking to base")
                print("      → alembic revision --autogenerate -m 'Capture current schema'")
                print("      → alembic upgrade head  # Apply the migration")

            print("\n⚠️  Production Safety:")
            print("   • Always backup your database before running migrations")
            print("   • Test migrations on staging environment first")
            print("   • Review generated migrations before applying")

        print("=" * 80)
        print(f"Validation completed at: {result['validation_timestamp']}")
        print()


def main():
    """Main validation function"""
    try:
        print("🚀 Initializing Röchling Production API Database Validator...")

        # Check environment
        if not (project_root / "alembic.ini").exists():
            print("❌ Error: alembic.ini not found.")
            print("Make sure you're running this from the project root directory.")
            return 1

        if not (project_root / "src").exists():
            print("❌ Error: src directory not found.")
            print("Make sure you're running this from the project root directory.")
            return 1

        # Initialize validator
        validator = DatabaseValidator()

        # Run validation
        result = validator.validate()

        # Print report
        validator.print_validation_report(result)

        # Return appropriate exit code
        return 0 if result["is_valid"] else 1

    except KeyboardInterrupt:
        print("\n⚠️ Validation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error during validation: {e}")
        logger.exception("Validation failed with exception")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
