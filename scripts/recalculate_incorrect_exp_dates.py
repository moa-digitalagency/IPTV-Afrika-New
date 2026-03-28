"""
Recalculate exp_dates for lines where the duration doesn't match their package duration
Runs on app startup to ensure exp_dates are accurate after package duration changes
"""
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.line import LineCache, PackageCache


def recalculate_incorrect_exp_dates():
    """Fix exp_dates that don't match their package duration"""
    with app.app_context():
        lines = LineCache.query.all()
        now = datetime.utcnow()

        if not lines:
            print("✓ No lines to check")
            return

        print(f"🔄 Checking {len(lines)} lines for incorrect exp_dates...")
        recalculated = 0

        for line in lines:
            if not line.created_at or not line.exp_date:
                continue

            # Get expected duration from package
            pkg = PackageCache.query.filter_by(golden_id=line.package_id).first()
            if not pkg or not pkg.duration_days or pkg.duration_days <= 0:
                continue

            # Calculate what the exp_date SHOULD be
            expected_exp_date = line.created_at + timedelta(days=pkg.duration_days)

            # If it doesn't match, fix it
            if line.exp_date != expected_exp_date:
                old_date = line.exp_date.strftime("%d/%m/%Y %H:%M")
                new_date = expected_exp_date.strftime("%d/%m/%Y %H:%M")
                print(f"  ✓ {line.username}: {pkg.package_name} → {old_date} → {new_date}")
                line.exp_date = expected_exp_date
                recalculated += 1

        if recalculated > 0:
            db.session.commit()

        print(f"✅ Fixed {recalculated} lines")

        # Show updated stats
        testers_active = LineCache.query.filter(
            LineCache.is_trial == True,
            LineCache.enabled == True,
            LineCache.exp_date > now
        ).count()

        subs_active = LineCache.query.filter(
            LineCache.is_trial == False,
            LineCache.enabled == True,
            LineCache.exp_date > now
        ).count()

        print(f"\n📊 Distribution after recalculation:")
        print(f"   Testeurs actifs: {testers_active}")
        print(f"   Abonnés actifs: {subs_active}")


if __name__ == '__main__':
    recalculate_incorrect_exp_dates()
