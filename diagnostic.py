"""
Diagnostic tool to check individual wallet balances and API responses.
Uses the exact same logic as your existing BalanceService.
"""

import json
import requests
import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WalletDiagnostic:
    """Diagnostic tool using your exact BalanceService logic."""
    
    def __init__(self):
        # Same constants as your BalanceService
        self.API_TIMEOUT = 10
        self.USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
        self.GMT_OFFSET = 7
        self.BASE_URL = "https://apilist.tronscanapi.com/api"
    
    def validate_trc20_address(self, address: str) -> bool:
        """Validate TRC20 address (same as your code)."""
        if not address or not isinstance(address, str):
            return False
        return address.startswith('T') and len(address) == 34
    
    def get_current_gmt_time(self) -> str:
        """Get current GMT+7 time (same as your code)."""
        gmt_now = datetime.now(timezone(timedelta(hours=self.GMT_OFFSET)))
        return gmt_now.strftime("%Y-%m-%d %H:%M:%S")
    
    def get_usdt_balance_detailed(self, address: str) -> dict:
        """
        Get USDT balance with detailed diagnostic info.
        Uses your exact BalanceService logic but returns more details.
        """
        result = {
            'address': address,
            'usdt_balance': None,
            'api_success': False,
            'tokens_found': 0,
            'usdt_token_found': False,
            'raw_tokens': [],
            'error': None,
            'response_data': None
        }
        
        url = f"{self.BASE_URL}/account/tokens?address={address}"
        
        try:
            logger.info(f"Checking address: {address}")
            resp = requests.get(url, timeout=self.API_TIMEOUT)
            resp.raise_for_status()
            
            json_data = resp.json()
            result['response_data'] = json_data
            result['api_success'] = True
            
            data = json_data.get("data", [])
            result['tokens_found'] = len(data)
            
            if not data:
                logger.warning(f"No token data found for address {address}")
                result['usdt_balance'] = Decimal('0.0')
                return result
            
            # Store all tokens for diagnostic
            for token in data:
                token_info = {
                    'tokenId': token.get("tokenId", ""),
                    'tokenName': token.get("tokenName", ""),
                    'tokenAbbr': token.get("tokenAbbr", ""),
                    'balance': token.get("balance", "0")
                }
                result['raw_tokens'].append(token_info)
            
            # Look for USDT specifically
            for token in data:
                if token.get("tokenId") == self.USDT_CONTRACT:
                    result['usdt_token_found'] = True
                    raw_balance_str = token.get("balance", "0")
                    try:
                        raw_balance = Decimal(raw_balance_str)
                        result['usdt_balance'] = raw_balance / Decimal('1000000')
                        logger.info(f"Found USDT: {raw_balance_str} sun = {result['usdt_balance']} USDT")
                        return result
                    except Exception as e:
                        result['error'] = f"Error converting balance '{raw_balance_str}': {e}"
                        logger.error(result['error'])
                        result['usdt_balance'] = Decimal('0.0')
                        return result
            
            # USDT token not found
            result['usdt_balance'] = Decimal('0.0')
            logger.info(f"USDT token not found for {address}")
            return result
            
        except requests.exceptions.Timeout:
            result['error'] = "Request timeout"
            logger.error(f"Request timed out for address {address}")
        except requests.exceptions.HTTPError as e:
            result['error'] = f"HTTP error {e.response.status_code}"
            logger.error(f"HTTP error {e.response.status_code} for address {address}")
        except requests.exceptions.ConnectionError:
            result['error'] = "Connection error"
            logger.error(f"Connection error for address {address}")
        except requests.exceptions.RequestException as e:
            result['error'] = f"Request error: {e}"
            logger.error(f"Request error for address {address}: {e}")
        except ValueError as e:
            result['error'] = f"JSON decode error: {e}"
            logger.error(f"Error decoding JSON for address {address}: {e}")
        except Exception as e:
            result['error'] = f"Unexpected error: {e}"
            logger.error(f"Unexpected error fetching balance for address {address}: {e}")
        
        return result
    
    def check_account_info(self, address: str) -> dict:
        """Get basic account info for additional context."""
        url = f"{self.BASE_URL}/account?address={address}"
        
        try:
            resp = requests.get(url, timeout=self.API_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            
            return {
                'success': True,
                'balance_trx': data.get('balance', 0) / 1_000_000,  # Convert sun to TRX
                'total_transactions': data.get('totalTransactionCount', 0),
                'transactions_in': data.get('transactions_in', 0),
                'transactions_out': data.get('transactions_out', 0),
                'latest_operation_time': data.get('latest_operation_time', 0)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def load_and_check_wallets(self) -> dict:
        """Load wallets.json and check each one."""
        try:
            with open('wallets.json', 'r', encoding='utf-8') as f:
                wallets = json.load(f)
        except FileNotFoundError:
            logger.error("wallets.json not found")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in wallets.json: {e}")
            return {}
        
        logger.info(f"Loaded {len(wallets)} wallets from wallets.json")
        
        results = {}
        
        for wallet_id, wallet_info in wallets.items():
            address = wallet_info.get('address')
            
            if not address:
                logger.error(f"No address found for wallet: {wallet_id}")
                continue
            
            if not self.validate_trc20_address(address):
                logger.error(f"Invalid TRC20 address for {wallet_id}: {address}")
                continue
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Checking wallet: {wallet_id}")
            logger.info(f"Address: {address}")
            logger.info(f"Company: {wallet_info.get('company', 'Unknown')}")
            
            # Get USDT balance details
            usdt_result = self.get_usdt_balance_detailed(address)
            
            # Get account info
            account_info = self.check_account_info(address)
            
            results[wallet_id] = {
                'wallet_info': wallet_info,
                'usdt_details': usdt_result,
                'account_info': account_info,
                'check_time': self.get_current_gmt_time()
            }
            
            # Print summary for this wallet
            print(f"\n🔍 WALLET: {wallet_id}")
            print(f"   Address: {address}")
            print(f"   Company: {wallet_info.get('company', 'Unknown')}")
            
            if usdt_result['api_success']:
                print(f"   ✅ API Success: Found {usdt_result['tokens_found']} tokens")
                print(f"   💰 USDT Balance: {usdt_result['usdt_balance']} USDT")
                print(f"   🔍 USDT Token Found: {usdt_result['usdt_token_found']}")
                
                if usdt_result['raw_tokens']:
                    print(f"   📋 All Tokens Found:")
                    for token in usdt_result['raw_tokens']:
                        symbol = token.get('tokenAbbr', 'Unknown')
                        balance = token.get('balance', '0')
                        print(f"      - {symbol}: {balance}")
            else:
                print(f"   ❌ API Failed: {usdt_result['error']}")
            
            if account_info['success']:
                print(f"   🏦 TRX Balance: {account_info['balance_trx']:.6f} TRX")
                print(f"   📊 Total Transactions: {account_info['total_transactions']}")
            else:
                print(f"   ❌ Account Info Failed: {account_info['error']}")
        
        return results
    
    def generate_summary_report(self, results: dict) -> None:
        """Generate summary report of all wallets."""
        if not results:
            print("\n❌ No results to summarize")
            return
        
        print(f"\n{'='*80}")
        print("📊 SUMMARY REPORT")
        print(f"{'='*80}")
        
        total_wallets = len(results)
        successful_api_calls = sum(1 for r in results.values() if r['usdt_details']['api_success'])
        wallets_with_usdt = sum(1 for r in results.values() 
                               if r['usdt_details']['usdt_balance'] and r['usdt_details']['usdt_balance'] > 0)
        wallets_with_tokens = sum(1 for r in results.values() 
                                 if r['usdt_details']['tokens_found'] > 0)
        
        total_usdt = sum(r['usdt_details']['usdt_balance'] or Decimal('0') for r in results.values())
        
        print(f"Total Wallets Checked: {total_wallets}")
        print(f"Successful API Calls: {successful_api_calls}")
        print(f"Wallets with Any Tokens: {wallets_with_tokens}")
        print(f"Wallets with USDT Balance: {wallets_with_usdt}")
        print(f"Total USDT Balance: {total_usdt:.6f} USDT")
        
        # Group by company
        companies = {}
        for wallet_id, result in results.items():
            company = result['wallet_info'].get('company', 'Unknown')
            if company not in companies:
                companies[company] = {'count': 0, 'usdt_total': Decimal('0')}
            
            companies[company]['count'] += 1
            if result['usdt_details']['usdt_balance']:
                companies[company]['usdt_total'] += result['usdt_details']['usdt_balance']
        
        print(f"\n🏢 BY COMPANY:")
        for company, stats in sorted(companies.items()):
            print(f"  {company}: {stats['count']} wallets, {stats['usdt_total']:.6f} USDT")
        
        # Show wallets with issues
        failed_wallets = [wallet_id for wallet_id, result in results.items() 
                         if not result['usdt_details']['api_success']]
        
        if failed_wallets:
            print(f"\n❌ FAILED API CALLS:")
            for wallet_id in failed_wallets:
                error = results[wallet_id]['usdt_details']['error']
                print(f"  {wallet_id}: {error}")
    
    def save_detailed_report(self, results: dict) -> str:
        """Save detailed diagnostic report to JSON."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"wallet_diagnostic_{timestamp}.json"
        
        # Convert Decimal to string for JSON serialization
        json_results = {}
        for wallet_id, result in results.items():
            json_result = result.copy()
            if result['usdt_details']['usdt_balance']:
                json_result['usdt_details']['usdt_balance'] = str(result['usdt_details']['usdt_balance'])
            json_results[wallet_id] = json_result
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Detailed report saved to: {filename}")
        return filename

def main():
    """Main diagnostic function."""
    diagnostic = WalletDiagnostic()
    
    print("🔍 Starting wallet balance diagnostic...")
    print("Using the exact same logic as your BalanceService")
    print(f"USDT Contract: {diagnostic.USDT_CONTRACT}")
    print(f"Current Time: {diagnostic.get_current_gmt_time()}")
    
    # Check all wallets
    results = diagnostic.load_and_check_wallets()
    
    # Generate summary
    diagnostic.generate_summary_report(results)
    
    # Save detailed report
    if results:
        filename = diagnostic.save_detailed_report(results)
        print(f"\n💾 Detailed diagnostic saved to: {filename}")
    
    print(f"\n✅ Diagnostic complete!")

if __name__ == "__main__":
    main()