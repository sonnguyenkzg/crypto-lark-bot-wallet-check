# Crypto Wallet Check Bot Documentation

## Overview
The Crypto Wallet Check Bot is a Lark (Feishu) chatbot designed to help compliance teams validate and track cryptocurrency wallet addresses, specifically TRC20 (TRON) addresses. The bot provides real-time wallet analysis, maintains blacklist and whitelist databases, and generates comprehensive reports for compliance monitoring.

## Core Features

### 1. Single Wallet Check (`/check` or `/c`)
**Purpose**: Instantly verify a wallet address and cross-reference it against internal databases

**Usage**: `/check [vendor_id] [wallet_address]`

**What it provides**:
- Wallet creation date and balance information
- Transaction history (total, incoming, outgoing transactions)
- TRON network red flag status
- Blacklist match detection
- Cross-vendor analysis (identifies if other vendors use the same address)
- Automatic database logging for audit trails

### 2. Blacklist Management
**Purpose**: Maintain and update suspicious wallet addresses

#### Add to Blacklist (`/tagblacklist`)
- **Usage**: `/tagblacklist [address] [tag]` or `/tagblacklist [address] [multi-word tag]`
- **Function**: Flags addresses as suspicious with custom tags (e.g., "Phishing", "Money Laundering")
- **Validation**: Prevents duplicate entries and validates address format

#### Remove from Blacklist (`/removeblacklist`)
- **Usage**: `/removeblacklist [address]`
- **Function**: Removes addresses from the blacklist when they're cleared for use

### 3. Vendor-Address Management
#### Remove Database Entry (`/remove`)
- **Usage**: `/remove [vendor_id] [address]`
- **Function**: Removes specific vendor-address pairs from the whitelist database
- **Use case**: When a vendor stops using a particular address

### 4. Bulk Processing (`/bulk`)
**Purpose**: Process multiple wallet addresses simultaneously for compliance audits

**Usage**: 
```
/bulk
vendor1 address1
vendor2 address2
vendor3 address3
```

**Output**: 
- CSV report containing all wallet analysis data
- Batch compliance status for multiple addresses
- Error reporting for invalid entries

### 5. CSV File Upload
**Purpose**: Process large datasets of vendor-address pairs from spreadsheets

**Process**:
1. Upload CSV file with columns: `vendor_id, address`
2. Bot validates all addresses
3. Generates comprehensive report with compliance status
4. Returns processed CSV with detailed analysis

## Business Benefits

### Compliance & Risk Management
- **Real-time Risk Assessment**: Instant identification of flagged addresses
- **Audit Trail**: Complete logging of all wallet checks and database changes
- **Cross-Reference Analysis**: Detects when multiple vendors share wallet addresses
- **Regulatory Reporting**: Structured data export for compliance reports

### Operational Efficiency
- **Automated Validation**: Reduces manual wallet verification time
- **Batch Processing**: Handle large compliance reviews efficiently
- **Centralized Database**: Single source of truth for wallet status
- **Team Collaboration**: Shared blacklist and whitelist accessible to all team members

### Data Management
- **Structured Storage**: Organized database with timestamped entries
- **Export Capabilities**: CSV reports for external analysis
- **Historical Tracking**: Complete history of wallet analysis and status changes
- **Quality Control**: Automatic address format validation

## Database Structure

The system maintains several databases:

1. **Whitelist Database**: Approved vendor-address relationships
2. **Blacklist Database**: Flagged addresses with risk tags
3. **Check History**: Complete audit log of all wallet verifications
4. **Bulk Processing Records**: Batch operation results
5. **CSV Upload Records**: File processing history

## Supported Commands Summary

| Command | Purpose | Example |
|---------|---------|---------|
| `/help` | Display available commands | `/help` |
| `/check` or `/c` | Single wallet verification | `/c vendor123 TXXXxxxxx...` |
| `/tagblacklist` | Add address to blacklist | `/tagblacklist TXXXxxxxx... [Suspicious Activity]` |
| `/removeblacklist` | Remove from blacklist | `/removeblacklist TXXXxxxxx...` |
| `/remove` | Remove vendor-address pair | `/remove vendor123 TXXXxxxxx...` |
| `/bulk` | Batch processing | `/bulk` followed by vendor-address pairs |
| **CSV Upload** | File-based batch processing | Upload CSV file directly |

## Wallet Check Response Format

When checking a wallet, the bot returns structured information:

```
🔍 WALLET CHECK RESULTS
◆ Commands: /c vendor123 TXXXxxxxx...
◆ Vendor: vendor123
◆ Address: TXXXxxxxx...

🔍 Database Check
◆ Match with Blacklist: NO ✅ / YES ❌❌
◆ Match with Other Vendors: NO / YES
  - [Other vendor matches if found]

🔍 Wallet Check
◆ Wallet Creation Date: YYYY-MM-DD
◆ Wallet Balance: X.XX USDT
◆ TronScan RedTag: [Status]
◆ Summary:
  - Transactions Total: XXX
  - Transactions In: XXX
  - Transactions Out: XXX
```

## System Architecture

### Platform Components
The bot operates as a cloud-based service that connects multiple business systems:

- **Communication Layer**: Lark (Feishu) workspace integration for team messaging
- **Data Processing Engine**: n8n workflow automation platform for business logic
- **Database Storage**: Google Sheets for transparent, accessible data management
- **External Data Sources**: TRON blockchain network APIs for real-time wallet information

### Data Flow Architecture
1. **User Input**: Commands received through Lark chat interface
2. **Validation Layer**: Address format and parameter checking
3. **Data Retrieval**: Real-time blockchain data fetching from TRON network
4. **Database Operations**: Cross-referencing internal blacklist and whitelist databases
5. **Report Generation**: Automated CSV creation and file delivery
6. **Response Delivery**: Formatted results sent back to Lark chat

### Infrastructure Benefits
- **Cloud-Based**: No local installation or maintenance required
- **Scalable**: Handles individual requests or bulk processing seamlessly  
- **Transparent**: Database stored in familiar Google Sheets format
- **Accessible**: Team members can view and audit data directly
- **Reliable**: Automated error handling and retry mechanisms
- **Audit-Ready**: Complete activity logging for compliance reviews

### Integration Details

- **Platform**: Lark (Feishu) messaging platform
- **Automation Engine**: n8n workflow platform
- **Blockchain**: TRON network (TRC20 addresses)
- **Data Sources**: TronGrid API, TronScan API
- **Storage**: Google Sheets integration for database management
- **Output**: Interactive messages and CSV file generation

## Security & Validation

- **Address Validation**: Automatic TRC20 address format verification (starts with 'T', 34 characters)
- **Duplicate Prevention**: Prevents duplicate blacklist entries
- **Error Handling**: Comprehensive error reporting for invalid inputs
- **Access Control**: Team-based access through Lark workspace permissions
- **Rate Limiting**: Built-in delays between API calls to respect service limits

## Error Handling

The bot provides clear error messages for:
- Invalid TRC20 address format
- Missing command parameters
- Duplicate blacklist entries
- Non-existent database records
- API connection issues
- File format validation errors

## Best Practices

### For Compliance Teams
- Use `/check` for real-time verification during vendor onboarding
- Regularly review and update blacklist entries with `/tagblacklist`
- Use bulk processing for periodic compliance audits
- Export CSV reports for regulatory documentation

### For Database Management
- Use descriptive tags when blacklisting addresses
- Remove outdated entries when vendor relationships end
- Maintain regular backups of the database sheets
- Monitor the audit trail for compliance reporting

This bot streamlines cryptocurrency compliance operations by providing instant wallet analysis, maintaining organized databases, and generating detailed reports for regulatory and internal audit purposes.