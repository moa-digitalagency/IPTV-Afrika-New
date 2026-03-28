"""Cache synchronization service - syncs GOLDEN API data to local database"""
import time
from datetime import datetime
from config.database import db
from models.line import LineCache, PackageCache
from models.logs import CacheSyncLog
from services.golden_api import GoldenAPIService, GoldenAPIException

class CacheService:
    """Service to synchronize GOLDEN API data with local database cache"""

    @staticmethod
    def sync_packages():
        """Sync packages from GOLDEN API to database"""
        print("\n📦 Syncing packages...")
        start_time = time.time()

        try:
            packages_data = GoldenAPIService.get_packages()
            if not packages_data:
                return 0

            # Handle both list and dict responses
            packages_list = packages_data if isinstance(packages_data, list) else packages_data.get('packages', [])
            synced_count = 0

            for pkg in packages_list:
                golden_id = pkg.get('id')
                if not golden_id:
                    continue

                cache = PackageCache.query.filter_by(golden_id=golden_id).first()

                if not cache:
                    cache = PackageCache(golden_id=golden_id)
                    db.session.add(cache)

                cache.package_name = pkg.get('name', '')
                cache.is_trial = pkg.get('is_trial', False)
                cache.duration_days = pkg.get('duration_days')
                cache.credits_cost = pkg.get('credits_cost')
                cache.cached_at = datetime.utcnow()

                synced_count += 1

            db.session.commit()
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"✅ Synced {synced_count} packages in {duration_ms}ms")
            return synced_count

        except GoldenAPIException as e:
            print(f"❌ Error syncing packages: {e}")
            raise

    @staticmethod
    def sync_lines():
        """
        Sync lines from GOLDEN API to database.

        NOTE: GOLDEN API doesn't support bulk listing all lines.
        This method syncs locally cached lines by refreshing their details from the API.
        New lines are added when created via the POST /v1/lines endpoint.
        """
        print("\n📋 Syncing lines...")
        start_time = time.time()

        try:
            # Get all locally cached lines
            cached_lines = LineCache.query.all()
            synced_count = 0

            if not cached_lines:
                print("ℹ️  No cached lines to sync. Lines are created via POST /v1/lines endpoint.")
                return 0

            # Refresh details for each cached line from GOLDEN API
            for cache in cached_lines:
                try:
                    # Fetch latest data from GOLDEN API for this specific line
                    line_data = GoldenAPIService.get_line(cache.golden_id)
                    if not line_data:
                        continue

                    # Update cache fields with latest data from API
                    cache.username = line_data.get('username', cache.username)
                    cache.password = line_data.get('password', cache.password)
                    cache.full_name = line_data.get('full_name', cache.full_name)
                    cache.email = line_data.get('email', cache.email)
                    cache.phone = line_data.get('phone', cache.phone)
                    cache.package_id = line_data.get('package_id', cache.package_id)
                    cache.package_name = line_data.get('package_name', cache.package_name)
                    cache.is_trial = line_data.get('is_trial', cache.is_trial)

                    # Parse expiration date
                    exp_date_str = line_data.get('exp_date')
                    if exp_date_str:
                        try:
                            if 'T' in exp_date_str:
                                cache.exp_date = datetime.fromisoformat(exp_date_str.replace('Z', '+00:00'))
                            else:
                                cache.exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
                        except ValueError:
                            pass

                    cache.enabled = line_data.get('enabled', cache.enabled)
                    cache.max_connections = line_data.get('max_connections', cache.max_connections)
                    cache.note = line_data.get('note', cache.note)
                    cache.dns_link = line_data.get('dns_link', cache.dns_link)
                    cache.cached_at = datetime.utcnow()
                    synced_count += 1

                except GoldenAPIException as e:
                    print(f"  ⚠️  Could not refresh line {cache.golden_id}: {e}")
                    # Continue with next line
                    continue

            db.session.commit()
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"✅ Synced {synced_count} lines in {duration_ms}ms")
            return synced_count

        except Exception as e:
            print(f"❌ Error syncing lines: {e}")
            raise

    @staticmethod
    def sync_all():
        """Sync all data from GOLDEN API"""
        log = CacheSyncLog(sync_type='all', status='pending')
        db.session.add(log)
        db.session.commit()

        start_time = time.time()

        try:
            print("\n" + "=" * 60)
            print("🔄 Starting complete cache synchronization")
            print("=" * 60)

            # Sync packages first (needed for lines)
            try:
                packages_count = CacheService.sync_packages()
            except GoldenAPIException:
                packages_count = 0

            # Sync lines
            try:
                lines_count = CacheService.sync_lines()
            except GoldenAPIException:
                lines_count = 0

            duration_ms = int((time.time() - start_time) * 1000)
            log.status = 'success'
            log.lines_synced = lines_count
            log.duration_ms = duration_ms
            log.finished_at = datetime.utcnow()
            db.session.commit()

            print("\n" + "=" * 60)
            print(f"✅ Cache synchronization completed in {duration_ms}ms")
            print(f"   • Packages synced: {packages_count}")
            print(f"   • Lines synced: {lines_count}")
            print("=" * 60 + "\n")

            return True, f"Synced {lines_count} lines and {packages_count} packages"

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log.status = 'error'
            log.error_msg = str(e)
            log.duration_ms = duration_ms
            log.finished_at = datetime.utcnow()
            db.session.commit()

            print(f"\n❌ Cache synchronization failed: {e}")
            return False, f"Sync failed: {str(e)}"

    @staticmethod
    def invalidate_line(golden_id):
        """Invalidate cache for a specific line"""
        cache = LineCache.query.filter_by(golden_id=golden_id).first()
        if cache:
            cache.cached_at = datetime.utcfromtimestamp(0)  # Set to epoch to force refresh
            db.session.commit()
            print(f"🔄 Invalidated cache for line {golden_id}")

    @staticmethod
    def invalidate_all_lines():
        """Invalidate cache for all lines"""
        LineCache.query.update({'cached_at': datetime.utcfromtimestamp(0)})
        db.session.commit()
        print("🔄 Invalidated cache for all lines")

    @staticmethod
    def get_cache_status():
        """Get cache synchronization status"""
        latest_log = CacheSyncLog.query.order_by(CacheSyncLog.started_at.desc()).first()

        total_lines = LineCache.query.count()
        total_packages = PackageCache.query.count()
        active_lines = LineCache.query.filter_by(enabled=True).count()
        trial_lines = LineCache.query.filter_by(is_trial=True).count()

        return {
            'total_lines': total_lines,
            'total_packages': total_packages,
            'active_lines': active_lines,
            'trial_lines': trial_lines,
            'last_sync': latest_log.finished_at if latest_log else None,
            'last_sync_status': latest_log.status if latest_log else 'never',
            'last_sync_duration_ms': latest_log.duration_ms if latest_log else None
        }
