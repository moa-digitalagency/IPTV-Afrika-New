"""GOLDEN API service wrapper"""
import requests
import os
from datetime import datetime
from flask import current_app

class GoldenAPIException(Exception):
    """Custom exception for GOLDEN API errors"""
    pass

class GoldenAPIService:
    """Wrapper for GOLDEN API calls with error handling"""

    TIMEOUT = 10

    @staticmethod
    def get_api_key():
        """Get API key from .env or Flask config"""
        # Priority: Flask config (from .env) > environment variable
        api_key = current_app.config.get('GOLDEN_API_KEY') or os.environ.get('GOLDEN_API_KEY', '')

        if not api_key:
            raise GoldenAPIException("GOLDEN API key not configured in .env. Set GOLDEN_API_KEY environment variable.")
        return api_key

    @staticmethod
    def get_base_url():
        """Get API base URL from .env or Flask config"""
        # Priority: Flask config (from .env) > environment variable > default
        url = current_app.config.get('GOLDEN_API_BASE_URL') or os.environ.get('GOLDEN_API_BASE_URL', 'https://api.goldentv.com')
        return url

    @staticmethod
    def _headers():
        """Get request headers with API key"""
        return {
            'X-API-Key': GoldenAPIService.get_api_key(),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    @staticmethod
    def _extract_data(response):
        """Extract line/data object from API response (handles wrapped responses)"""
        if isinstance(response, dict):
            if 'data' in response:
                data_field = response['data']
                if isinstance(data_field, list) and len(data_field) > 0:
                    return data_field[0]
                elif isinstance(data_field, dict):
                    return data_field
            return response
        return response

    @staticmethod
    def _handle_response(response):
        """Handle API response and raise exceptions on error"""
        try:
            if response.status_code == 401:
                raise GoldenAPIException("Unauthorized: Invalid API key")
            elif response.status_code == 403:
                raise GoldenAPIException("Forbidden: Access denied")
            elif response.status_code == 404:
                raise GoldenAPIException("Not found")
            elif response.status_code == 422:
                # Unprocessable Entity - validation error
                try:
                    error_data = response.json()
                    if 'errors' in error_data:
                        errors = error_data['errors']
                        error_msg = ', '.join([f"{k}: {v}" for k, v in errors.items()])
                        raise GoldenAPIException(f"Validation error: {error_msg}")
                    elif 'message' in error_data:
                        raise GoldenAPIException(f"Validation error: {error_data['message']}")
                except ValueError:
                    raise GoldenAPIException("Validation error (422)")
            elif response.status_code == 429:
                raise GoldenAPIException("Rate limited: Too many requests")
            elif response.status_code >= 500:
                raise GoldenAPIException(f"Server error: {response.status_code}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise GoldenAPIException("Request timeout")
        except requests.exceptions.ConnectionError:
            raise GoldenAPIException("Connection error: Cannot reach GOLDEN API")
        except requests.exceptions.RequestException as e:
            raise GoldenAPIException(f"Request error: {str(e)}")
        except ValueError as e:
            raise GoldenAPIException(f"Invalid JSON response: {str(e)}")

    @staticmethod
    def get_packages():
        """Get available packages from GOLDEN API"""
        try:
            url = f"{GoldenAPIService.get_base_url()}/v1/packages"
            response = requests.get(url, headers=GoldenAPIService._headers(), timeout=GoldenAPIService.TIMEOUT)
            raw_response = GoldenAPIService._handle_response(response)

            # Normalize response: handle both list and dict with 'data' key
            packages_data = raw_response.get('packages', []) if isinstance(raw_response, dict) else []

            if isinstance(packages_data, dict) and 'data' in packages_data:
                packages_list = packages_data['data']
            elif isinstance(packages_data, list):
                packages_list = packages_data
            else:
                packages_list = []

            # Convert package data to standard format with duration_days
            normalized_packages = []
            for pkg in packages_list:
                duration = pkg.get('official_duration', 0)
                duration_unit = pkg.get('official_duration_in', 'days')

                # Convert to days
                if duration_unit == 'years':
                    duration_days = duration * 365
                elif duration_unit == 'months':
                    duration_days = duration * 30
                elif duration_unit == 'hours':
                    duration_days = max(1, duration // 24)  # Convert hours to days, min 1 day
                else:  # days
                    duration_days = duration

                normalized_packages.append({
                    'id': pkg.get('id'),
                    'name': pkg.get('package_name'),
                    'duration_days': duration_days,
                    'is_trial': bool(pkg.get('is_trial', 0)),
                    'max_connections': pkg.get('max_connections', 1),
                    'raw': pkg  # Store original data
                })

            return {'packages': normalized_packages}
        except GoldenAPIException as e:
            print(f"❌ Error fetching packages: {e}")
            raise

    @staticmethod
    def create_line(username, password, package_id):
        """Create a new line"""
        try:
            url = f"{GoldenAPIService.get_base_url()}/v1/lines"
            data = {
                'username': username,
                'password': password,
                'package_id': package_id
            }
            print(f"📝 Sending create line request:")
            print(f"   URL: {url}")
            print(f"   Data: {data}")
            response = requests.post(url, json=data, headers=GoldenAPIService._headers(), timeout=GoldenAPIService.TIMEOUT)
            print(f"   Status: {response.status_code}")
            if response.status_code != 201:
                print(f"   Response: {response.text}")

            result = GoldenAPIService._handle_response(response)
            return GoldenAPIService._extract_data(result)
        except GoldenAPIException as e:
            print(f"❌ Error creating line: {e}")
            raise

    @staticmethod
    def get_line(line_id):
        """Get line details"""
        try:
            url = f"{GoldenAPIService.get_base_url()}/v1/lines/{line_id}"
            response = requests.get(url, headers=GoldenAPIService._headers(), timeout=GoldenAPIService.TIMEOUT)
            result = GoldenAPIService._handle_response(response)
            return GoldenAPIService._extract_data(result)
        except GoldenAPIException as e:
            print(f"❌ Error fetching line {line_id}: {e}")
            raise

    @staticmethod
    def get_all_lines():
        """Get all lines (paginated if needed)"""
        try:
            url = f"{GoldenAPIService.get_base_url()}/v1/lines"
            response = requests.get(url, headers=GoldenAPIService._headers(), timeout=GoldenAPIService.TIMEOUT)
            result = GoldenAPIService._handle_response(response)

            # Extract lines from data if wrapped
            if isinstance(result, dict):
                if 'data' in result:
                    return result['data']  # Return data array/object directly
                return result
            return result
        except GoldenAPIException as e:
            print(f"❌ Error fetching all lines: {e}")
            raise

    @staticmethod
    def extend_line(line_id, days):
        """Extend line expiration"""
        try:
            url = f"{GoldenAPIService.get_base_url()}/v1/lines/{line_id}/extend"
            data = {'days': days}
            response = requests.post(url, json=data, headers=GoldenAPIService._headers(), timeout=GoldenAPIService.TIMEOUT)
            result = GoldenAPIService._handle_response(response)
            return GoldenAPIService._extract_data(result)
        except GoldenAPIException as e:
            print(f"❌ Error extending line {line_id}: {e}")
            raise

    @staticmethod
    def refund_line(line_id):
        """Refund and close a line"""
        try:
            url = f"{GoldenAPIService.get_base_url()}/v1/lines/{line_id}/refund"
            response = requests.post(url, headers=GoldenAPIService._headers(), timeout=GoldenAPIService.TIMEOUT)
            result = GoldenAPIService._handle_response(response)
            return GoldenAPIService._extract_data(result)
        except GoldenAPIException as e:
            print(f"❌ Error refunding line {line_id}: {e}")
            raise

    @staticmethod
    def test_connection():
        """Test GOLDEN API connection"""
        try:
            GoldenAPIService.get_packages()
            return True, "✅ GOLDEN API connection successful"
        except GoldenAPIException as e:
            return False, f"❌ Connection failed: {str(e)}"
