"""
CSV analyzer for the working balance checker output.
Converts wallet analysis output to comprehensive CSV format.
"""

import json
import csv
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OutputAnalyzer:
    """Analyze wallet analysis output and create consolidated CSV."""
    
    def __init__(self, output_dir: str = "wallet_analysis_output"):
        self.output_dir = Path(output_dir)
        self.summaries_dir = self.output_dir / "summaries"
        self.raw_data_dir = self.output_dir / "raw_data"
        
        # Check if directories exist
        if not self.output_dir.exists():
            raise FileNotFoundError(f"Output directory not found: {self.output_dir}")
        
        if not self.summaries_dir.exists():
            logger.warning(f"Summaries directory not found: {self.summaries_dir}")
        
        if not self.raw_data_dir.exists():
            logger.warning(f"Raw data directory not found: {self.raw_data_dir}")
    
    def load_summary_files(self) -> Dict[str, Dict]:
        """Load all summary files from the working analyzer."""
        summaries = {}
        
        if not self.summaries_dir.exists():
            logger.error("No summaries directory found")
            return summaries
        
        summary_files = list(self.summaries_dir.glob("*_summary.json"))
        logger.info(f"Found {len(summary_files)} summary files")
        
        for file_path in summary_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    wallet_id = data.get('wallet_id')
                    if wallet_id:
                        summaries[wallet_id] = data
                        logger.debug(f"Loaded summary for: {wallet_id}")
                    else:
                        logger.warning(f"No wallet_id found in {file_path}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        logger.info(f"Successfully loaded {len(summaries)} wallet summaries")
        return summaries
    
    def create_csv_row(self, wallet_id: str, summary_data: Dict) -> Dict[str, Any]:
        """Create a single CSV row for a wallet using working analyzer output."""
        summary = summary_data.get('summary', {})
        
        # Basic info from working analyzer
        row = {
            'wallet_id': wallet_id,
            'company': summary.get('company', 'Unknown'),
            'wallet_name': summary.get('wallet_name', 'Unknown'),
            'address': summary.get('address', 'Unknown'),
            'analysis_time': summary.get('analysis_time', 'Unknown'),
        }
        
        # Creation date
        row['creation_date'] = summary.get('creation_date', 'Unknown')
        row['creation_date_notes'] = (
            "Derived from timestamp of first transaction via Tronscan transaction history API with API key"
            if summary.get('creation_date', 'Unknown') != 'Unknown'
            else "Unknown - No transaction history available or API failed"
        )
        
        # USDT Balance (from working balance service)
        usdt_balance = summary.get('usdt_balance', '0.0')
        row['usdt_balance'] = usdt_balance
        
        # API success status
        api_success = summary.get('api_success', {})
        usdt_api_success = api_success.get('usdt_balance', False)
        
        if usdt_api_success and float(usdt_balance) > 0:
            row['usdt_balance_notes'] = f"From working BalanceService.get_usdt_trc20_balance() method with TRON-PRO-API-KEY, USDT contract TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t, converted from sun (÷1,000,000)"
        elif usdt_api_success and float(usdt_balance) == 0:
            row['usdt_balance_notes'] = "API call successful but no USDT tokens found for this address"
        else:
            row['usdt_balance_notes'] = "API call failed - check API key or network connectivity"
        
        # TRX Balance
        trx_balance = summary.get('trx_balance', '0.0')
        row['trx_balance'] = trx_balance
        if float(trx_balance) > 0:
            row['trx_balance_notes'] = "From Tronscan account API 'balance' field, converted from sun to TRX (÷1,000,000)"
        else:
            row['trx_balance_notes'] = "0.0 - Either empty wallet or account API call failed"
        
        # Transaction counts
        row['total_transactions'] = summary.get('total_transactions', 0)
        row['transactions_in'] = summary.get('transactions_in', 0)
        row['transactions_out'] = summary.get('transactions_out', 0)
        
        # TRC20 Transfer counts (what the bot requirements ask for)
        row['trc20_transfers_in'] = summary.get('trc20_transfers_in', 0)
        row['trc20_transfers_out'] = summary.get('trc20_transfers_out', 0)
        row['total_trc20_transfers'] = summary.get('total_trc20_transfers', 0)
        
        account_api_success = api_success.get('account_info', False)
        trc20_api_success = api_success.get('trc20_transfers', False)
        
        if account_api_success:
            row['transaction_counts_notes'] = "General Tron transactions from account API: totalTransactionCount, transactions_in, transactions_out"
        else:
            row['transaction_counts_notes'] = "Not available - Account info API call failed"
            
        if trc20_api_success:
            row['trc20_transfers_notes'] = "TRC20 token transfers from token_trc20/transfers API: counted by matching to_address/from_address with wallet"
        else:
            row['trc20_transfers_notes'] = "Not available - TRC20 transfers API call failed (may require API key)"
        
        # API Success Summary
        row['usdt_api_success'] = 'Yes' if usdt_api_success else 'No'
        row['account_api_success'] = 'Yes' if account_api_success else 'No'
        row['transaction_history_api_success'] = 'Yes' if api_success.get('transaction_history', False) else 'No'
        row['trc20_transfers_api_success'] = 'Yes' if trc20_api_success else 'No'
        
        # Wallet Status
        if usdt_api_success:
            if float(usdt_balance) > 0:
                row['wallet_status'] = 'Has USDT Balance'
            elif float(trx_balance) > 0 or row['total_transactions'] > 0:
                row['wallet_status'] = 'Active (No USDT)'
            else:
                row['wallet_status'] = 'Empty/Inactive'
        else:
            row['wallet_status'] = 'API Failed'
        
        # Data Source Documentation
        row['data_source'] = 'Working BalanceService and WalletService with TRON-PRO-API-KEY authentication'
        row['api_endpoints_used'] = 'account/tokens (USDT), account (TRX/transactions), transaction (history)'
        row['usdt_contract'] = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'
        
        # Analysis Notes
        notes = []
        if not usdt_api_success:
            notes.append("USDT balance check failed - verify API key")
        if summary.get('creation_date') == 'Unknown':
            notes.append("Could not determine wallet creation date")
        if float(usdt_balance) == 0 and float(trx_balance) == 0 and row['total_transactions'] == 0:
            notes.append("Wallet appears completely empty or all APIs failed")
        
        row['analysis_notes'] = "; ".join(notes) if notes else "All data retrieved successfully"
        
        return row
    
    def analyze_and_create_csv(self) -> str:
        """Main function to analyze output files and create CSV."""
        logger.info("Starting analysis of wallet analyzer output files...")
        
        # Load all summary data
        summaries = self.load_summary_files()
        
        if not summaries:
            raise ValueError("No summary files found to analyze")
        
        # Prepare CSV data
        csv_rows = []
        
        for wallet_id, summary_data in summaries.items():
            logger.info(f"Processing wallet: {wallet_id}")
            
            # Create CSV row
            csv_row = self.create_csv_row(wallet_id, summary_data)
            csv_rows.append(csv_row)
        
        # Sort by company then wallet_id
        csv_rows.sort(key=lambda x: (x['company'], x['wallet_id']))
        
        # Generate CSV filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = self.output_dir / f"wallet_analysis_consolidated_{timestamp}.csv"
        
        # Write CSV
        if csv_rows:
            fieldnames = csv_rows[0].keys()
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)
            
            logger.info(f"CSV created successfully: {csv_filename}")
            logger.info(f"Total wallets processed: {len(csv_rows)}")
            
            # Print summary statistics
            self.print_csv_summary(csv_rows)
            
            return str(csv_filename)
        else:
            raise ValueError("No data to write to CSV")
    
    def print_csv_summary(self, csv_rows: List[Dict]) -> None:
        """Print summary statistics about the CSV data."""
        print(f"\n{'='*80}")
        print("CSV ANALYSIS SUMMARY")
        print(f"{'='*80}")
        
        total_wallets = len(csv_rows)
        print(f"Total Wallets: {total_wallets}")
        
        # Company breakdown
        companies = {}
        for row in csv_rows:
            company = row['company']
            companies[company] = companies.get(company, 0) + 1
        
        print(f"\nCOMPANIES:")
        for company, count in sorted(companies.items()):
            print(f"  {company}: {count} wallets")
        
        # API Success Statistics
        usdt_success = sum(1 for row in csv_rows if row['usdt_api_success'] == 'Yes')
        account_success = sum(1 for row in csv_rows if row['account_api_success'] == 'Yes')
        
        print(f"\nAPI SUCCESS RATES:")
        print(f"  USDT Balance API: {usdt_success}/{total_wallets} ({usdt_success/total_wallets*100:.1f}%)")
        print(f"  Account Info API: {account_success}/{total_wallets} ({account_success/total_wallets*100:.1f}%)")
        
        # Balance statistics (only for successful API calls)
        successful_usdt_rows = [row for row in csv_rows if row['usdt_api_success'] == 'Yes']
        if successful_usdt_rows:
            total_usdt = sum(float(row['usdt_balance']) for row in successful_usdt_rows)
            wallets_with_usdt = sum(1 for row in successful_usdt_rows if float(row['usdt_balance']) > 0)
            
            print(f"\nBALANCE SUMMARY (from successful API calls):")
            print(f"  Total USDT Balance: {total_usdt:.6f} USDT")
            print(f"  Wallets with USDT: {wallets_with_usdt}")
            print(f"  Average USDT per wallet: {total_usdt/len(successful_usdt_rows):.6f} USDT")
        
        # Wallet Status Breakdown
        status_counts = {}
        for row in csv_rows:
            status = row['wallet_status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"\nWALLET STATUS:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count} wallets")
        
        # Show any problematic wallets
        failed_wallets = [row for row in csv_rows if row['usdt_api_success'] == 'No']
        if failed_wallets:
            print(f"\nWALLETS WITH FAILED USDT API CALLS:")
            for row in failed_wallets[:10]:  # Show first 10
                print(f"  {row['wallet_id']}: {row['analysis_notes']}")
            if len(failed_wallets) > 10:
                print(f"  ... and {len(failed_wallets) - 10} more")
        
        print(f"\nCSV contains detailed notes explaining data sources and any issues encountered.")

def main():
    """Main execution function."""
    try:
        # Initialize analyzer
        analyzer = OutputAnalyzer("wallet_analysis_output")
        
        # Create CSV
        csv_file = analyzer.analyze_and_create_csv()
        
        print(f"\nSUCCESS!")
        print(f"Consolidated CSV created: {csv_file}")
        print(f"\nThe CSV includes:")
        print(f"   • All wallet data from working balance checker")
        print(f"   • Detailed notes explaining data sources and API calls")
        print(f"   • API success/failure status for each endpoint")
        print(f"   • Company groupings and balance analysis")
        print(f"   • Wallet status classification")
        print(f"\nOpen the CSV file to see all your wallet analysis results!")
        
    except FileNotFoundError as e:
        logger.error(f"Directory not found: {e}")
        print(f"\nMake sure you've run the wallet analyzer first to generate output files!")
    except ValueError as e:
        logger.error(f"Data error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()