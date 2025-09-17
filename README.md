# Harness Helpers

A collection of Python utilities for interacting with the Harness CI/CD platform API. These tools help analyze configurations, count resources, and manage your Harness environment more effectively.

## 🚀 Features

- **Configuration Analysis**: Compare default vs customer configurations
- **Pipeline Management**: Count and analyze pipelines across organizations
- **Support Image Configuration**: Retrieve and analyze execution configurations
- **API Integration**: Seamless integration with Harness NextGen APIs

## 📋 Prerequisites

- Python 3.6 or higher
- `requests` library
- Valid Harness API token with appropriate permissions
- Harness account ID

## 🛠 Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd harnessHelpers
```

2. Install required dependencies:
```bash
pip install requests
```

3. Set up environment variables:
```bash
export HARNESS_API_TOKEN="your_harness_api_token_here"
export HARNESS_ACCT_ID="your_harness_account_id_here"
```

## 🔧 Scripts Overview

### 1. Configuration Comparison Tool
**File**: `compareDefaultvsCustomerConfigHarness.py`

Compares your organization's custom configuration against Harness default settings to identify overrides and customizations.

**Usage**:
```bash
python compareDefaultvsCustomerConfigHarness.py
```

**Features**:
- ✅ Identifies overridden values
- ➕ Shows customer-only settings
- ➖ Displays default-only settings
- 📊 Provides comprehensive summary statistics

### 2. Pipeline Counter by Organization
**File**: `pipelinesByOrg.py`

Analyzes and counts pipelines across all organizations in your Harness account.

**Usage**:
```bash
python pipelinesByOrg.py
```

**Features**:
- 📈 Pipeline count per organization
- 📊 Percentage distribution analysis
- 🏆 Identifies organizations with most pipelines
- 📋 Detailed project-level breakdown

### 3. Customer Configuration Retriever
**File**: `getHarnessSupportImagesCustomerConfig.py`

Retrieves customer-specific execution configuration overrides.

**Usage**:
```bash
python getHarnessSupportImagesCustomerConfig.py
```

### 4. Default Configuration Retriever
**File**: `getHarnessSupportImagesDefaultConfig.py`

Retrieves the default Harness execution configuration.

**Usage**:
```bash
python getHarnessSupportImagesDefaultConfig.py
```

## 🔑 Authentication Setup

### Getting Your API Token

1. Log into your Harness account
2. Navigate to **Account Settings** → **Access Control** → **API Keys**
3. Create a new Personal Access Token or Service Account token
4. Copy the token and set it as an environment variable

### Finding Your Account ID

Your Account ID can be found in:
- The URL when logged into Harness (e.g., `https://app.harness.io/ng/account/{ACCOUNT_ID}/...`)
- Account Settings in the Harness UI

## 📊 Sample Output

### Configuration Comparison
```
===============================================================================
HARNESS CONFIGURATION COMPARISON
===============================================================================
🔍 COMPARISON RESULTS:
Customer config has overrides. Analyzing differences...

🔄 OVERRIDDEN VALUES:
--------------------------------------------------
Key: resources.limits.memory
  Default:  1Gi
  Customer: 2Gi

➕ CUSTOMER-ONLY SETTINGS:
--------------------------------------------------
Key: customSettings.timeout
  Value: 300s

==================================================
SUMMARY:
  🔄 Overridden values: 3
  ➕ Customer-only settings: 2
  ➖ Default-only settings: 15
  ✅ Unchanged values: 45
```

### Pipeline Count Analysis
```
==================================================
📊 PIPELINE COUNT SUMMARY
==================================================
Production Org                 |    45 pipelines ( 60.0%)
Development Org               |    20 pipelines ( 26.7%)
Testing Org                   |    10 pipelines ( 13.3%)
--------------------------------------------------
TOTAL                         |    75 pipelines
==================================================

📈 Average pipelines per organization: 25.0
🏆 Organization with most pipelines: Production Org (45 pipelines)
```

## 🔧 Configuration

The scripts use the following environment variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `HARNESS_API_TOKEN` | Your Harness API token | ✅ Yes |
| `HARNESS_ACCT_ID` | Your Harness account ID | ✅ Yes |

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify your API token is valid and has proper permissions
   - Ensure the account ID matches your Harness instance

2. **Network Timeouts**
   - Check your internet connection
   - Verify Harness instance URL is accessible

3. **Missing Configurations**
   - Some organizations may not have custom configurations (this is normal)
   - Empty responses indicate default settings are in use

### API Permissions Required

Your API token needs the following permissions:
- Read access to Organizations
- Read access to Projects
- Read access to Pipelines
- Read access to Execution Configurations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your Harness API permissions
3. Review the Harness API documentation
4. Open an issue in this repository

## 🔗 Useful Links

- [Harness Documentation](https://docs.harness.io/)
- [Harness API Reference](https://apidocs.harness.io/)
- [Harness Community](https://community.harness.io/)

---

**Made with ❤️ for the Harness community**