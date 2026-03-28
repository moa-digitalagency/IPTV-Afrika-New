#!/usr/bin/env python3
"""
Populate database with test data from GOLDEN API.
Since GOLDEN API doesn't support listing all lines, we search by trying IDs.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from config.database import db
from models.line import LineCache, PackageCache
from services.golden_api import GoldenAPIService, GoldenAPIException
from datetime import datetime, timedelta

def populate_packages():
    """Populate packages from GOLDEN API"""
    print("\n📦 Fetching packages from GOLDEN API...")
    try:
        packages_data = GoldenAPIService.get_packages()
        packages = packages_data.get('packages', [])
        
        for pkg in packages:
            golden_id = pkg.get('id')
            if not golden_id:
                continue
            
            cache = PackageCache.query.filter_by(golden_id=golden_id).first()
            if not cache:
                cache = PackageCache(golden_id=golden_id)
                db.session.add(cache)
            
            cache.package_name = pkg.get('name', '')
            cache.is_trial = pkg.get('is_trial', False)
            cache.duration_days = pkg.get('duration_days', 30)
            cache.credits_cost = pkg.get('credits_cost')
            cache.cached_at = datetime.utcnow()
        
        db.session.commit()
        print(f"✅ Synced {len(packages)} packages")
        return packages
    except Exception as e:
        print(f"❌ Error fetching packages: {e}")
        return []

def find_lines_by_id_range(start=1, end=50):
    """Try to fetch lines by searching for IDs in a range"""
    print(f"\n🔍 Searching for lines (IDs {start}-{end})...")
    found_count = 0
    
    for line_id in range(start, end + 1):
        try:
            line_data = GoldenAPIService.get_line(line_id)
            if not line_data:
                continue
            
            golden_id = line_data.get('id')
            if not golden_id:
                continue
            
            # Check if already cached
            cache = LineCache.query.filter_by(golden_id=golden_id).first()
            if not cache:
                cache = LineCache(golden_id=golden_id)
                db.session.add(cache)
            
            cache.username = line_data.get('username', f'user_{golden_id}')
            cache.password = line_data.get('password', 'password123')
            cache.full_name = line_data.get('full_name')
            cache.email = line_data.get('email')
            cache.phone = line_data.get('phone')
            cache.package_id = line_data.get('package_id')
            cache.package_name = line_data.get('package_name', 'Test Package')
            cache.is_trial = line_data.get('is_trial', True)
            cache.enabled = line_data.get('enabled', True)
            cache.max_connections = line_data.get('max_connections', 1)
            cache.dns_link = line_data.get('dns_link')
            cache.note = line_data.get('note')
            
            # Parse expiration date
            exp_date_str = line_data.get('exp_date')
            if exp_date_str:
                try:
                    if 'T' in exp_date_str:
                        cache.exp_date = datetime.fromisoformat(exp_date_str.replace('Z', '+00:00'))
                    else:
                        cache.exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
                except:
                    cache.exp_date = datetime.utcnow() + timedelta(days=30)
            else:
                cache.exp_date = datetime.utcnow() + timedelta(days=30)
            
            if not cache.created_at:
                cache.created_at = datetime.utcnow()
            
            cache.cached_at = datetime.utcnow()
            found_count += 1
            print(f"   ✓ Found line {golden_id}: {cache.username}")
            
        except GoldenAPIException:
            # Line doesn't exist, continue
            continue
        except Exception as e:
            print(f"   ⚠️  Error fetching line {line_id}: {e}")
            continue
    
    db.session.commit()
    print(f"✅ Found and cached {found_count} lines")
    return found_count

def main():
    with app.app_context():
        db.create_all()
        
        print("=" * 70)
        print("📥 Populating Database with GOLDEN API Data")
        print("=" * 70)
        
        # Fetch packages
        populate_packages()
        
        # Try to find lines (search by ID range)
        print("\n⚠️  Note: GOLDEN API doesn't support listing all lines.")
        print("   Searching by ID range (1-100)...")
        found = find_lines_by_id_range(1, 100)
        
        # Check final status
        from models.line import LineCache
        total_lines = LineCache.query.count()
        total_packages = PackageCache.query.count()
        
        print("\n" + "=" * 70)
        print("📊 Database Status")
        print("=" * 70)
        print(f"   Packages: {total_packages}")
        print(f"   Lines: {total_lines}")
        
        if total_lines == 0:
            print("\n💡 No lines found. To add lines:")
            print("   1. Use admin panel: /app/lines/create")
            print("   2. API endpoint: POST /v1/lines with username, password, package_id")
        else:
            print(f"\n✅ Data ready! Found {total_lines} lines to manage.")

if __name__ == '__main__':
    main()
