"""
Migration script: Calculate missing exp_date values for lines in database
Runs on app startup to ensure all lines have expiration dates
"""
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.line import LineCache, PackageCache


def migrate_missing_exp_dates():
    """Calculate exp_date for all lines that have NULL exp_date"""
    with app.app_context():
        # Find all lines with NULL exp_date
        lines_without_exp = LineCache.query.filter(LineCache.exp_date == None).all()

        if not lines_without_exp:
            print("✓ All lines have exp_date set")
            return

        print(f"🔄 Migrating {len(lines_without_exp)} lines with missing exp_date...")

        migrated = 0
        for line in lines_without_exp:
            # Try to get duration from package
            package = PackageCache.query.filter_by(golden_id=line.package_id).first()

            duration_days = None
            if package and package.duration_days and package.duration_days > 0:
                duration_days = package.duration_days
                source = "package_duration"
            else:
                # Default: 7 days for testers, 30 days for subscribers
                duration_days = 7 if line.is_trial else 30
                source = "default"

            # Calculate expiration from created_at or now
            base_date = line.created_at if line.created_at else datetime.utcnow()
            line.exp_date = base_date + timedelta(days=duration_days)

            print(f"  ✓ {line.username}: +{duration_days}j ({source}) → {line.exp_date.strftime('%d/%m/%Y %H:%M')}")
            migrated += 1

        db.session.commit()
        print(f"✅ Migrated {migrated} lines")

        # Show updated stats
        from sqlalchemy import func
        now = datetime.utcnow()

        testers_active = LineCache.query.filter(
            LineCache.is_trial == True,
            LineCache.enabled == True,
            LineCache.exp_date > now
        ).count()

        testers_expired = LineCache.query.filter(
            LineCache.is_trial == True,
            LineCache.exp_date < now,
            LineCache.enabled == True
        ).count()

        subs_active = LineCache.query.filter(
            LineCache.is_trial == False,
            LineCache.enabled == True,
            LineCache.exp_date > now
        ).count()

        subs_expired = LineCache.query.filter(
            LineCache.is_trial == False,
            LineCache.exp_date < now,
            LineCache.enabled == True
        ).count()

        print(f"\n📊 Lines distribution:")
        print(f"  Testeurs actifs: {testers_active}")
        print(f"  Testeurs expirés: {testers_expired}")
        print(f"  Abonnés actifs: {subs_active}")
        print(f"  Abonnés expirés: {subs_expired}")


if __name__ == '__main__':
    migrate_missing_exp_dates()
