"""
Exact replication of your BalanceService logic for wallet analysis.
Uses your proven working patterns from the Telegram bot.
"""

import json
import csv
import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

# Import your exact services
import sys
sys.path.append('.')

# Replicate your exact BalanceService class
import requests

logger = logging.getLogger(__name__)

class BalanceService:
    """Service for checking USDT TRC20 wallet balances - EXACT COPY of your code with API key support."""
    
    def __init__(self):
        # Configuration constants (same as your Slack bot)
        self.API_TIMEOUT = 10  # seconds for API requests
        self.USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Official USDT TRC20 contract
        self.GMT_OFFSET = 7  # GMT+7 timezone offset
        
        # API key from .env
        import os
        from dotenv import load_dotenv
        load_dotenv()
        self.api_key = os.getenv('TRONSCAN_API_KEY')
        
        # Prepare headers
        self.headers = {}
        if self.api_key:
            self.headers['TRON-PRO-API-KEY'] = self.api_key
            logger.info("Using Tronscan API key for requests")
        else:
            logger.warning("No TRONSCAN_API_KEY found in .env file")
    
    def get_usdt_trc20_balance(self, address: str) -> Optional[Decimal]:
        """
        EXACT COPY of your working method WITH API key support.
        Fetches the USDT TRC20 balance for a given Tron address using the Tronscan API.
        """
        url = f"https://apilist.tronscanapi.com/api/account/tokens?address={address}"
        
        try:
            # Use headers if we have an API key
            resp = requests.get(url, headers=self.headers, timeout=self.API_TIMEOUT)
            resp.raise_for_status()

            data = resp.json().get("data", [])
            if not data:
                logger.warning(f"No token data found for address {address}")
                return Decimal('0.0')

            for token in data:
                if token.get("tokenId") == self.USDT_CONTRACT:
                    raw_balance_str = token.get("balance", "0")
                    try:
                        raw_balance = Decimal(raw_balance_str)
                    except Exception as e:
                        logger.error(f"Error converting balance '{raw_balance_str}' for {address}: {e}")
                        return Decimal('0.0')

                    # USDT TRC20 has 6 decimal places (1,000,000 sun per USDT)
                    return raw_balance / Decimal('1000000')
            
            # USDT token not found for this address
            return Decimal('0.0')

        except requests.exceptions.Timeout:
            logger.error(f"Request timed out for address {address}")
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for address {address}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for address {address}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for address {address}: {e}")
        except ValueError as e:
            logger.error(f"Error decoding JSON for address {address}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching balance for address {address}: {e}")
        
        return None
    
    def validate_trc20_address(self, address: str) -> bool:
        """EXACT COPY of your validation method."""
        if not address or not isinstance(address, str):
            return False
        
        # TRC20 addresses start with 'T' and are 34 characters long
        return address.startswith('T') and len(address) == 34
    
    def get_current_gmt_time(self) -> str:
        """EXACT COPY of your time method."""
        gmt_now = datetime.now(timezone(timedelta(hours=self.GMT_OFFSET)))
        return gmt_now.strftime("%Y-%m-%d %H:%M")
    
    def fetch_multiple_balances(self, wallets_to_check: Dict[str, str]) -> Dict[str, Optional[Decimal]]:
        """EXACT COPY of your multiple balance method."""
        balances = {}
        
        for display_name, address in wallets_to_check.items():
            try:
                balance = self.get_usdt_trc20_balance(address)
                balances[display_name] = balance
                
                if balance is not None:
                    logger.info(f"Fetched balance for {display_name}: {balance} USDT")
                else:
                    logger.warning(f"Failed to fetch balance for {display_name}")
                    
            except Exception as e:
                logger.error(f"Error fetching balance for {display_name}: {e}")
                balances[display_name] = None
        
        return balances

# Replicate your exact WalletService class
class WalletService:
    """EXACT COPY of your WalletService."""
    
    def __init__(self, wallets_file: str = "wallets.json"):
        self.wallets_file = wallets_file
    
    def load_wallets(self) -> Dict[str, Any]:
        """EXACT COPY of your load_wallets method."""
        try:
            import os
            if os.path.exists(self.wallets_file):
                with open(self.wallets_file, 'r', encoding='utf-8') as f:
                    wallets = json.load(f)
                    logger.info(f"Loaded {len(wallets)} wallets from {self.wallets_file}")
                    return wallets
            else:
                logger.info(f"Wallets file {self.wallets_file} not found, returning empty dict")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.wallets_file}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading wallets from {self.wallets_file}: {e}")
            return {}

class WalletBalanceChecker:
    """Uses your exact service classes to check wallet balances."""
    
    def __init__(self):
        self.wallet_service = WalletService()
        self.balance_service = BalanceService()
        
        # Create output directory
        self.output_dir = Path("balance_check_output")
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("Initialized with your exact BalanceService and WalletService")
    
    def check_all_wallets(self) -> Dict[str, Any]:
        """Check all wallets using your exact service pattern."""
        # Load wallets using your exact method
        wallet_data = self.wallet_service.load_wallets()
        
        if not wallet_data:
            logger.error("No wallets loaded")
            return {}
        
        logger.info(f"Checking {len(wallet_data)} wallets using your exact BalanceService logic")
        
        # Prepare wallets_to_check in the format your service expects
        wallets_to_check = {}
        for wallet_name, wallet_info in wallet_data.items():
            address = wallet_info.get('address')
            if address and self.balance_service.validate_trc20_address(address):
                wallets_to_check[wallet_name] = address
            else:
                logger.warning(f"Invalid or missing address for wallet: {wallet_name}")
        
        logger.info(f"Valid wallets to check: {len(wallets_to_check)}")
        
        # Use your exact fetch_multiple_balances method
        balances = self.balance_service.fetch_multiple_balances(wallets_to_check)
        
        # Build results in the format similar to your DailyReportService
        results = {
            'check_timestamp': datetime.now().isoformat(),
            'check_time_gmt7': self.balance_service.get_current_gmt_time(),
            'total_wallets': len(wallet_data),
            'valid_wallets': len(wallets_to_check),
            'wallet_results': {},
            'summary': {
                'successful_checks': 0,
                'failed_checks': 0,
                'total_usdt_balance': Decimal('0'),
                'wallets_with_balance': 0
            }
        }
        
        # Process results exactly like your DailyReportService does
        for wallet_name, balance in balances.items():
            wallet_info = wallet_data.get(wallet_name, {})
            
            wallet_result = {
                'wallet_name': wallet_name,
                'company': wallet_info.get('company', 'Unknown'),
                'address': wallet_info.get('address', 'Unknown'),
                'usdt_balance': balance,
                'balance_str': str(balance) if balance is not None else 'Failed',
                'success': balance is not None
            }
            
            results['wallet_results'][wallet_name] = wallet_result
            
            if balance is not None:
                results['summary']['successful_checks'] += 1
                results['summary']['total_usdt_balance'] += balance
                if balance > 0:
                    results['summary']['wallets_with_balance'] += 1
            else:
                results['summary']['failed_checks'] += 1
        
        return results
    
    def save_to_csv(self, results: Dict[str, Any]) -> str:
        """Save results to CSV with detailed information."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = self.output_dir / f"wallet_balances_{timestamp}.csv"
        
        # Prepare CSV data
        csv_rows = []
        
        for wallet_name, wallet_result in results['wallet_results'].items():
            balance = wallet_result['usdt_balance']
            
            csv_row = {
                'wallet_name': wallet_name,
                'company': wallet_result['company'],
                'address': wallet_result['address'],
                'usdt_balance': str(balance) if balance is not None else '0.0',
                'balance_numeric': float(balance) if balance is not None else 0.0,
                'api_success': 'Yes' if wallet_result['success'] else 'No',
                'has_balance': 'Yes' if balance and balance > 0 else 'No',
                'check_time': results['check_time_gmt7'],
                'data_source': 'BalanceService.get_usdt_trc20_balance() - exact copy of your working method',
                'api_endpoint': 'https://apilist.tronscanapi.com/api/account/tokens',
                'usdt_contract': self.balance_service.USDT_CONTRACT,
                'notes': 'Uses your exact working BalanceService logic from Telegram bot'
            }
            
            csv_rows.append(csv_row)
        
        # Sort by company then wallet name
        csv_rows.sort(key=lambda x: (x['company'], x['wallet_name']))
        
        # Write CSV
        if csv_rows:
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = csv_rows[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)
            
            logger.info(f"CSV saved: {csv_filename}")
            return str(csv_filename)
        else:
            logger.error("No data to write to CSV")
            return ""
    
    def print_summary(self, results: Dict[str, Any]) -> None:
        """Print summary in the same format as your DailyReportService."""
        summary = results['summary']
        
        print(f"\n{'='*60}")
        print("WALLET BALANCE CHECK SUMMARY")
        print(f"{'='*60}")
        print(f"Time: {results['check_time_gmt7']} GMT+{self.balance_service.GMT_OFFSET}")
        print(f"Total Wallets: {results['total_wallets']}")
        print(f"Valid Wallets: {results['valid_wallets']}")
        print(f"Successful Checks: {summary['successful_checks']}")
        print(f"Failed Checks: {summary['failed_checks']}")
        print(f"Wallets with Balance: {summary['wallets_with_balance']}")
        print(f"Total USDT Balance: {summary['total_usdt_balance']:.6f} USDT")
        
        # Group by company like your bot does
        companies = {}
        for wallet_result in results['wallet_results'].values():
            company = wallet_result['company']
            if company not in companies:
                companies[company] = {'count': 0, 'usdt_total': Decimal('0')}
            
            companies[company]['count'] += 1
            if wallet_result['usdt_balance']:
                companies[company]['usdt_total'] += wallet_result['usdt_balance']
        
        print(f"\nBY COMPANY:")
        for company, stats in sorted(companies.items()):
            print(f"  {company}: {stats['count']} wallets, {stats['usdt_total']:.6f} USDT")
        
        # Show individual balances like your DailyReportService
        print(f"\nINDIVIDUAL BALANCES:")
        for wallet_name, wallet_result in sorted(results['wallet_results'].items()):
            balance = wallet_result['usdt_balance']
            if balance is not None:
                print(f"  {wallet_name}: {balance:.6f} USDT")
            else:
                print(f"  {wallet_name}: FAILED")

def main():
    """Main function using your exact service patterns."""
    # Configure logging like your code
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Initialize using your exact service classes
        checker = WalletBalanceChecker()
        
        print("Starting wallet balance check using your exact BalanceService logic...")
        print(f"USDT Contract: {checker.balance_service.USDT_CONTRACT}")
        
        # Check all wallets
        results = checker.check_all_wallets()
        
        if not results['wallet_results']:
            print("No wallet results obtained")
            return
        
        # Print summary like your DailyReportService
        checker.print_summary(results)
        
        # Save to CSV
        csv_file = checker.save_to_csv(results)
        if csv_file:
            print(f"\nCSV saved to: {csv_file}")
        
        # Save JSON for detailed analysis
        json_filename = checker.output_dir / f"balance_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Detailed JSON saved to: {json_filename}")
        
        print(f"\nUsing your exact BalanceService.get_usdt_trc20_balance() method")
        print(f"If this fails with 401 errors, the issue is API key requirement at Tronscan")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()