"""
Wallet analyzer with TRC20 transfer debugging to identify why transfers show 0.
Built from proven working balance checker logic.
"""

import json
import csv
import logging
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path
import requests
import time
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BalanceService:
    """Service for checking USDT TRC20 wallet balances - EXACT COPY from working balance checker."""
    
    def __init__(self):
        # Configuration constants (same as your Slack bot)
        self.API_TIMEOUT = 10  # seconds for API requests
        self.USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Official USDT TRC20 contract
        self.GMT_OFFSET = 7  # GMT+7 timezone offset
        
        # API key from .env
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

class WalletService:
    """EXACT COPY of your WalletService."""
    
    def __init__(self, wallets_file: str = "wallets.json"):
        self.wallets_file = wallets_file
    
    def load_wallets(self) -> Dict[str, Any]:
        """EXACT COPY of your load_wallets method."""
        try:
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

class AdditionalDataService:
    """Additional data fetching using the same API approach as BalanceService with debugging."""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('TRONSCAN_API_KEY')
        self.headers = {}
        if self.api_key:
            self.headers['TRON-PRO-API-KEY'] = self.api_key
        
        self.API_TIMEOUT = 10
        self.GMT_OFFSET = 7
        self.BASE_URL = "https://apilist.tronscanapi.com/api"
        self.USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Add USDT contract here
    
    def get_account_info(self, address: str) -> Optional[Dict]:
        """Get basic account info using same pattern as BalanceService."""
        url = f"{self.BASE_URL}/account?address={address}"
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=self.API_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Error fetching account info for {address}: {e}")
            return None
    
    def get_transaction_history(self, address: str, limit: int = 20) -> Optional[Dict]:
        """Get transaction history using same pattern."""
        url = f"{self.BASE_URL}/transaction"
        params = {
            'sort': 'timestamp',
            'count': 'true',
            'limit': limit,
            'start': 0,
            'address': address
        }
        
        try:
            resp = requests.get(url, params=params, headers=self.headers, timeout=self.API_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Error fetching transaction history for {address}: {e}")
            return None
    
    def debug_trc20_transfers(self, address: str) -> None:
        """Debug what the TRC20 transfers API returns using correct parameters."""
        url = f"{self.BASE_URL}/token_trc20/transfers"
        
        # Test both approaches
        test_cases = [
            {
                'name': 'Current approach (address param - gets all transfers)',
                'params': {'limit': 5, 'start': 0, 'address': address}
            },
            {
                'name': 'Fixed approach (relatedAddress param - gets wallet-specific transfers)', 
                'params': {'limit': 20, 'start': 0, 'relatedAddress': address}
            },
            {
                'name': 'Fixed + USDT filter (relatedAddress + trc20Id)',
                'params': {'limit': 20, 'start': 0, 'relatedAddress': address, 'trc20Id': self.USDT_CONTRACT}
            }
        ]
        
        print(f"\n=== TESTING TRC20 TRANSFER APPROACHES FOR {address} ===")
        
        for test_case in test_cases:
            print(f"\n--- {test_case['name']} ---")
            print(f"Params: {test_case['params']}")
            
            try:
                resp = requests.get(url, params=test_case['params'], headers=self.headers, timeout=self.API_TIMEOUT)
                print(f"Status: {resp.status_code}")
                
                if resp.status_code == 200:
                    data = resp.json()
                    if 'token_transfers' in data:
                        transfers = data['token_transfers']
                        print(f"Found: {len(transfers)} transfers")
                        
                        # Check how many actually involve this wallet
                        relevant = 0
                        wallet_lower = address.lower()
                        
                        for transfer in transfers:
                            to_addr = transfer.get('to_address', '').lower()
                            from_addr = transfer.get('from_address', '').lower()
                            
                            if to_addr == wallet_lower:
                                relevant += 1
                                print(f"  INCOMING: from {transfer.get('from_address', '')} amount {transfer.get('quant', '')}")
                            elif from_addr == wallet_lower:
                                relevant += 1
                                print(f"  OUTGOING: to {transfer.get('to_address', '')} amount {transfer.get('quant', '')}")
                        
                        print(f"Relevant to this wallet: {relevant}/{len(transfers)}")
                        
                        if relevant == 0 and transfers:
                            print(f"Sample transfer (not related): {transfers[0]['from_address']} -> {transfers[0]['to_address']}")
                    else:
                        print("No token_transfers in response")
                else:
                    print(f"Error: {resp.text}")
                    
            except Exception as e:
                print(f"Request failed: {e}")
        
        print("="*80)
    
    def get_trc20_transfers(self, address: str, limit: int = 50) -> Optional[Dict]:
        """Get TRC20 transfer history specific to the wallet address."""
        
        # The correct parameter is 'relatedAddress' to get transfers for a specific wallet
        url = f"{self.BASE_URL}/token_trc20/transfers"
        params = {
            'limit': limit,
            'start': 0,
            'relatedAddress': address,  # This gets transfers TO or FROM the specific address
            'trc20Id': self.USDT_CONTRACT  # Filter for USDT only
        }
        
        try:
            logger.info(f"Getting TRC20 transfers for address: {address}")
            resp = requests.get(url, params=params, headers=self.headers, timeout=self.API_TIMEOUT)
            resp.raise_for_status()
            
            data = resp.json()
            
            # Check if we got wallet-specific data
            if 'token_transfers' in data:
                transfers = data['token_transfers']
                logger.info(f"Found {len(transfers)} transfers for address {address}")
                
                # Verify these transfers actually involve our address
                relevant_transfers = 0
                for transfer in transfers[:5]:  # Check first 5
                    to_addr = transfer.get('to_address', '').lower()
                    from_addr = transfer.get('from_address', '').lower()
                    if to_addr == address.lower() or from_addr == address.lower():
                        relevant_transfers += 1
                
                logger.info(f"Verified {relevant_transfers} transfers actually involve this address")
                return data
            else:
                logger.warning(f"No token_transfers found for {address}")
                return None
                        
        except Exception as e:
            logger.error(f"Failed to get TRC20 transfers for {address}: {e}")
            
            # Fallback: try without trc20Id filter
            try:
                params_fallback = {
                    'limit': limit,
                    'start': 0,
                    'relatedAddress': address
                }
                logger.info(f"Trying fallback without trc20Id filter")
                resp = requests.get(url, params=params_fallback, headers=self.headers, timeout=self.API_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except Exception as e2:
                logger.error(f"Fallback also failed: {e2}")
                return None
    
    def count_trc20_transfers(self, trc20_data: Optional[Dict], wallet_address: str) -> Dict[str, int]:
        """Count TRC20 transfers with multiple response structure support."""
        if not trc20_data:
            return {
                'trc20_transfers_in': 0,
                'trc20_transfers_out': 0,
                'total_trc20_transfers': 0,
                'data_available': False,
                'error': 'No TRC20 data received'
            }
        
        # Handle different response structures
        transfers = None
        if 'token_transfers' in trc20_data:
            transfers = trc20_data['token_transfers']
        elif 'data' in trc20_data:
            transfers = trc20_data['data']
        
        if not transfers:
            return {
                'trc20_transfers_in': 0,
                'trc20_transfers_out': 0,
                'total_trc20_transfers': 0,
                'data_available': False,
                'error': 'No transfers found in response'
            }
        
        transfers_in = 0
        transfers_out = 0
        wallet_lower = wallet_address.lower()
        
        for transfer in transfers:
            to_addr = transfer.get('to_address', '').lower()
            from_addr = transfer.get('from_address', '').lower()
            
            # Also try alternative field names
            if not to_addr:
                to_addr = transfer.get('toAddress', '').lower()
            if not from_addr:
                from_addr = transfer.get('fromAddress', '').lower()
            
            if to_addr == wallet_lower:
                transfers_in += 1
            elif from_addr == wallet_lower:
                transfers_out += 1
        
        return {
            'trc20_transfers_in': transfers_in,
            'trc20_transfers_out': transfers_out,
            'total_trc20_transfers': transfers_in + transfers_out,
            'data_available': True,
            'transfers_found': len(transfers)
        }
    
    def find_creation_date(self, transaction_data: Optional[Dict]) -> Optional[str]:
        """Find wallet creation date from first transaction."""
        if not transaction_data or 'data' not in transaction_data:
            return None
        
        transactions = transaction_data.get('data', [])
        if not transactions:
            return None
        
        # Find oldest transaction
        oldest_tx = min(transactions, key=lambda tx: tx.get('timestamp', float('inf')))
        oldest_timestamp = oldest_tx.get('timestamp')
        
        if not oldest_timestamp:
            return None
        
        # Convert to GMT+7
        gmt_time = datetime.fromtimestamp(oldest_timestamp / 1000, 
                                        timezone(timedelta(hours=self.GMT_OFFSET)))
        
        return gmt_time.strftime('%Y-%m-%d')

class WalletAnalyzer:
    """Wallet analyzer with TRC20 transfer debugging."""
    
    def __init__(self):
        self.wallet_service = WalletService()
        self.balance_service = BalanceService()
        self.additional_service = AdditionalDataService()
        
        # Create output directories
        self.output_dir = Path("wallet_analysis_output")
        self.raw_data_dir = self.output_dir / "raw_data"
        self.summaries_dir = self.output_dir / "summaries"
        
        self.output_dir.mkdir(exist_ok=True)
        self.raw_data_dir.mkdir(exist_ok=True)
        self.summaries_dir.mkdir(exist_ok=True)
        
        logger.info("Initialized wallet analyzer with TRC20 transfer debugging")
    
    def analyze_single_wallet(self, wallet_id: str, wallet_info: Dict) -> Dict[str, Any]:
        """Analyze single wallet with TRC20 transfer debugging."""
        address = wallet_info.get('address')
        
        if not address:
            logger.error(f"No address found for wallet: {wallet_id}")
            return None
        
        if not self.balance_service.validate_trc20_address(address):
            logger.error(f"Invalid TRC20 address for {wallet_id}: {address}")
            return None
        
        logger.info(f"Analyzing wallet: {wallet_id} ({address})")
        
        # Use the working balance service
        usdt_balance = self.balance_service.get_usdt_trc20_balance(address)
        
        # Get additional data using same API pattern
        account_info = self.additional_service.get_account_info(address)
        transaction_history = self.additional_service.get_transaction_history(address)
        creation_date = self.additional_service.find_creation_date(transaction_history)
        
        # Debug TRC20 transfers for first few wallets
        if wallet_id in list(self.wallet_service.load_wallets().keys())[:3]:  # Debug first 3 wallets
            self.additional_service.debug_trc20_transfers(address)
        
        # Get TRC20 transfers with multiple endpoint attempts
        trc20_transfers = self.additional_service.get_trc20_transfers(address)
        transfer_counts = self.additional_service.count_trc20_transfers(trc20_transfers, address)
        
        # Build analysis result
        analysis_data = {
            'wallet_id': wallet_id,
            'wallet_info': wallet_info,
            'address': address,
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_time_gmt7': self.balance_service.get_current_gmt_time(),
            'raw_data': {
                'account_info': account_info,
                'transaction_history': transaction_history,
                'trc20_transfers': trc20_transfers
            },
            'summary': {
                'wallet_id': wallet_id,
                'company': wallet_info.get('company', 'Unknown'),
                'wallet_name': wallet_info.get('wallet', wallet_info.get('name', 'Unknown')),
                'address': address,
                'analysis_time': self.balance_service.get_current_gmt_time(),
                'usdt_balance': str(usdt_balance) if usdt_balance is not None else '0.0',
                'usdt_balance_decimal': usdt_balance,
                'creation_date': creation_date or 'Unknown',
                
                # TRC20 transfer counts (what the bot requirements ask for)
                'trc20_transfers_in': transfer_counts['trc20_transfers_in'],
                'trc20_transfers_out': transfer_counts['trc20_transfers_out'],
                'total_trc20_transfers': transfer_counts['total_trc20_transfers'],
                'trc20_debug_info': {
                    'data_available': transfer_counts['data_available'],
                    'transfers_found': transfer_counts.get('transfers_found', 0),
                    'error': transfer_counts.get('error', None)
                },
                
                'api_success': {
                    'usdt_balance': usdt_balance is not None,
                    'account_info': account_info is not None,
                    'transaction_history': transaction_history is not None,
                    'trc20_transfers': transfer_counts['data_available']
                }
            }
        }
        
        # Add account info to summary if available (general transactions)
        if account_info:
            analysis_data['summary']['trx_balance'] = f"{account_info.get('balance', 0) / 1_000_000:.6f}"
            analysis_data['summary']['total_transactions'] = account_info.get('totalTransactionCount', 0)
            analysis_data['summary']['transactions_in'] = account_info.get('transactions_in', 0)
            analysis_data['summary']['transactions_out'] = account_info.get('transactions_out', 0)
        else:
            analysis_data['summary']['trx_balance'] = '0.0'
            analysis_data['summary']['total_transactions'] = 0
            analysis_data['summary']['transactions_in'] = 0
            analysis_data['summary']['transactions_out'] = 0
        
        return analysis_data
    
    def save_wallet_data(self, wallet_id: str, analysis_data: Dict) -> None:
        """Save wallet data to files."""
        # Save raw data
        raw_filename = self.raw_data_dir / f"{wallet_id}_raw_data.json"
        with open(raw_filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False, default=str)
        
        # Save summary
        summary_filename = self.summaries_dir / f"{wallet_id}_summary.json"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump({
                'wallet_id': wallet_id,
                'summary': analysis_data['summary']
            }, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Saved data for {wallet_id}")
    
    def analyze_all_wallets(self) -> Dict[str, Dict]:
        """Analyze all wallets using working balance service with TRC20 debugging."""
        # Load wallets using proven working method
        wallet_data = self.wallet_service.load_wallets()
        
        if not wallet_data:
            logger.error("No wallets loaded")
            return {}
        
        logger.info(f"Starting analysis of {len(wallet_data)} wallets with TRC20 transfer debugging")
        
        all_results = {}
        successful_analyses = 0
        failed_analyses = 0
        
        for wallet_id, wallet_info in wallet_data.items():
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing wallet {successful_analyses + failed_analyses + 1}/{len(wallet_data)}: {wallet_id}")
                logger.info(f"{'='*60}")
                
                analysis_result = self.analyze_single_wallet(wallet_id, wallet_info)
                
                if analysis_result:
                    all_results[wallet_id] = analysis_result
                    self.save_wallet_data(wallet_id, analysis_result)
                    successful_analyses += 1
                    
                    # Log balance and transfer info
                    summary = analysis_result['summary']
                    usdt_balance = summary['usdt_balance_decimal']
                    trc20_in = summary['trc20_transfers_in']
                    trc20_out = summary['trc20_transfers_out']
                    
                    balance_str = f"{usdt_balance} USDT" if usdt_balance and usdt_balance > 0 else "No USDT"
                    transfer_str = f"TRC20 transfers: {trc20_in} in, {trc20_out} out"
                    
                    logger.info(f"✅ {wallet_id}: {balance_str}, {transfer_str}")
                    
                    # Log debug info if available
                    debug_info = summary.get('trc20_debug_info', {})
                    if debug_info.get('error'):
                        logger.warning(f"   TRC20 Error: {debug_info['error']}")
                    elif debug_info.get('transfers_found'):
                        logger.info(f"   Found {debug_info['transfers_found']} raw transfers")
                else:
                    failed_analyses += 1
                    logger.error(f"❌ Failed to analyze: {wallet_id}")
                
                # Small delay to be nice to API
                time.sleep(0.3)
                
            except Exception as e:
                failed_analyses += 1
                logger.error(f"Error analyzing {wallet_id}: {e}")
        
        logger.info(f"\n🏁 Analysis completed!")
        logger.info(f"✅ Successful: {successful_analyses}")
        logger.info(f"❌ Failed: {failed_analyses}")
        
        return all_results
    
    def create_master_summary(self, all_results: Dict[str, Dict]) -> Dict:
        """Create master summary with TRC20 transfer statistics."""
        master_summary = {
            'analysis_overview': {
                'total_wallets': len(all_results),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_time_gmt7': self.balance_service.get_current_gmt_time()
            },
            'companies': {},
            'wallet_summaries': [],
            'totals': {
                'total_usdt_balance': Decimal('0'),
                'wallets_with_usdt': 0,
                'successful_balance_checks': 0,
                'successful_trc20_transfer_checks': 0,
                'total_trc20_transfers_in': 0,
                'total_trc20_transfers_out': 0
            }
        }
        
        company_stats = {}
        
        for wallet_id, result in all_results.items():
            summary = result['summary']
            company = summary.get('company', 'Unknown')
            
            # Company statistics
            if company not in company_stats:
                company_stats[company] = {
                    'wallet_count': 0,
                    'total_usdt': Decimal('0'),
                    'total_trc20_transfers': 0,
                    'wallets': []
                }
            
            company_stats[company]['wallet_count'] += 1
            company_stats[company]['wallets'].append(wallet_id)
            
            # Add to wallet summaries
            usdt_balance = summary.get('usdt_balance_decimal')
            trc20_in = summary.get('trc20_transfers_in', 0)
            trc20_out = summary.get('trc20_transfers_out', 0)
            
            master_summary['wallet_summaries'].append({
                'wallet_id': wallet_id,
                'company': company,
                'wallet_name': summary.get('wallet_name', ''),
                'address': summary.get('address', ''),
                'usdt_balance': str(usdt_balance) if usdt_balance is not None else '0.0',
                'creation_date': summary.get('creation_date', 'Unknown'),
                'trx_balance': summary.get('trx_balance', '0.0'),
                'total_transactions': summary.get('total_transactions', 0),
                'trc20_transfers_in': trc20_in,
                'trc20_transfers_out': trc20_out,
                'total_trc20_transfers': trc20_in + trc20_out,
                'api_success': summary.get('api_success', {}).get('usdt_balance', False),
                'trc20_api_success': summary.get('api_success', {}).get('trc20_transfers', False)
            })
            
            # Aggregate statistics
            if usdt_balance is not None:
                master_summary['totals']['successful_balance_checks'] += 1
                master_summary['totals']['total_usdt_balance'] += usdt_balance
                company_stats[company]['total_usdt'] += usdt_balance
                
                if usdt_balance > 0:
                    master_summary['totals']['wallets_with_usdt'] += 1
            
            if summary.get('api_success', {}).get('trc20_transfers', False):
                master_summary['totals']['successful_trc20_transfer_checks'] += 1
                master_summary['totals']['total_trc20_transfers_in'] += trc20_in
                master_summary['totals']['total_trc20_transfers_out'] += trc20_out
                company_stats[company]['total_trc20_transfers'] += trc20_in + trc20_out
        
        master_summary['companies'] = company_stats
        return master_summary

def main():
    """Main function with TRC20 transfer debugging."""
    try:
        # Initialize analyzer
        analyzer = WalletAnalyzer()
        
        # Analyze all wallets
        all_results = analyzer.analyze_all_wallets()
        
        # Create master summary
        master_summary = analyzer.create_master_summary(all_results)
        
        # Save master summary
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        master_summary_file = analyzer.output_dir / f"master_summary_{timestamp}.json"
        
        with open(master_summary_file, 'w', encoding='utf-8') as f:
            json.dump(master_summary, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Master summary saved to: {master_summary_file}")
        
        # Print overview
        print(f"\n{'='*80}")
        print("WALLET ANALYSIS OVERVIEW WITH TRC20 DEBUGGING")
        print(f"{'='*80}")
        overview = master_summary['analysis_overview']
        print(f"Total Wallets: {overview['total_wallets']}")
        print(f"Analysis Time: {overview['analysis_time_gmt7']} GMT+7")
        
        print(f"\n{'='*80}")
        print("BALANCE & TRANSFER SUMMARY")
        print(f"{'='*80}")
        totals = master_summary['totals']
        print(f"Successful Balance Checks: {totals['successful_balance_checks']}")
        print(f"Successful TRC20 Transfer Checks: {totals['successful_trc20_transfer_checks']}")
        print(f"Total USDT Balance: {totals['total_usdt_balance']} USDT")
        print(f"Wallets with USDT: {totals['wallets_with_usdt']}")
        print(f"Total TRC20 Transfers In: {totals['total_trc20_transfers_in']}")
        print(f"Total TRC20 Transfers Out: {totals['total_trc20_transfers_out']}")
        
        print(f"\n{'='*80}")
        print("BY COMPANY")
        print(f"{'='*80}")
        for company, data in master_summary['companies'].items():
            print(f"{company}: {data['wallet_count']} wallets, {data['total_usdt']} USDT, {data['total_trc20_transfers']} TRC20 transfers")
        
        print(f"\nAnalysis complete with TRC20 transfer debugging!")
        print(f"Check debug output above for TRC20 transfer API details.")
        print(f"Check {analyzer.output_dir} for detailed results.")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()