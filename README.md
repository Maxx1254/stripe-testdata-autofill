# Stripe Test Account Populator

A Python script to populate a Stripe test account with realistic test data including products, customers, subscriptions with various statuses, and support for both new and existing accounts.

## Overview

This script generates comprehensive test data for Stripe development and testing purposes. It can work with both empty and existing Stripe accounts, automatically detecting and reusing existing data. It creates:
- User-defined number of products with recurring prices
- User-defined number of customers with realistic profile information
- User-defined number of subscriptions with diverse statuses
- Multiple payment methods per customer
- Tax rates (Sales Tax, VAT, GST) with inclusive/exclusive options
- Customers with failing payment methods for testing error scenarios

## Features

- **Works with Existing Accounts**: Automatically detects and reuses existing customers, products, and tax rates
- **Flexible Data Creation**: Create 0 or more of any entity type - useful for adding subscriptions to existing accounts
- **Realistic Test Data**: Uses the Faker library to generate authentic-looking customer information including names, emails, addresses, and phone numbers
- **Diverse Subscription Statuses**: Creates subscriptions in various states with weighted distribution:
  - Active (35%)
  - Active with scheduled cancellation (10%)
  - Trialing (12%)
  - Past due (8%)
  - Canceled (12%)
  - Unpaid (8%)
  - Paused (10%)
  - Scheduled to start in future (5%)
- **Multiple Billing Intervals**: Supports daily, weekly, monthly, yearly and custom recurring periods
- **Payment Method Variety**: Attaches 1-4 payment methods per customer including:
  - Standard cards (Visa, Mastercard, Amex, Discover, Diners Club, JCB, UnionPay)
  - US Bank Account
  - Failing payment method for testing error scenarios
  - Automatically sets first payment method as default
- **Tax Configuration**: Creates both inclusive and exclusive tax rates compatible with Stripe's tax_behavior requirements
- **Smart Tax Rate Management**: Reuses existing tax rates if account already has data, prevents duplicates

## Prerequisites

- Python 3.7 or higher
- Stripe test account with API access
- Test mode API key from your Stripe dashboard

## Installation

1. Clone or download this script

2. Install required dependencies:

```pip install stripe faker```

## Usage

1. Run the script with Python:

```python stripe_populator.py```

2. When prompted, enter your Stripe test API key (starts with `sk_test_`).

The script will validate the API key format before proceeding with data creation.

For security, the API key is not stored in the code and must be provided each time you run the script.

3. Configure the quantities to create:
   - **Products**: Enter number of new products to create (0 to skip)
   - **Customers**: Enter number of new customers to create (0 to skip)
   - **Subscriptions**: Enter number of new subscriptions to create (minimum 1)

**Note**: You can enter `0` for products and customers to only add subscriptions to an existing account.

## Data Distribution

### Subscription Statuses

The script creates subscriptions with the following distribution:

| Status | Percentage | Description |
|--------|-----------|-------------|
| **Active** | 35% | Fully active recurring subscriptions |
| **Active with end date** | 10% | Active subscriptions scheduled to cancel in 30-90 days |
| **Trialing** | 12% | Subscriptions in trial period (7-30 days) |
| **Past Due** | 8% | Subscriptions with failed payments (uses failing payment method) |
| **Canceled** | 12% | Canceled subscriptions |
| **Unpaid** | 8% | Subscriptions with unpaid invoices |
| **Paused** | 10% | Paused subscriptions (drafts kept) |
| **Scheduled** | 5% | Subscriptions scheduled to start 7-30 days in future |

### Customer Types

The script creates two types of customers:

1. **Normal Customers (90%)**: Have 1-4 valid payment methods attached
2. **Failing Customers (10%)**: Have only `pm_card_chargeCustomerFail` payment method, used for testing payment failures and past_due scenarios

### Payment Methods

The script uses Stripe's test payment method tokens:

**Standard Payment Cards:**
- Visa (`pm_card_visa`)
- Mastercard (`pm_card_mastercard`)
- American Express (`pm_card_amex`)
- Discover (`pm_card_discover`)
- Diners Club (`pm_card_diners`)
- JCB (`pm_card_jcb`)
- UnionPay (`pm_card_unionpay`)

**Alternative Payment Methods:**
- US Bank Account (`pm_usBankAccount`)

**Test Failing Payment:**
- Visa (Will Fail) (`pm_card_chargeCustomerFail`) - Used exclusively for testing payment failures

Each normal customer gets 1-4 randomly selected valid payment methods, with the first one set as the default payment method. Failing customers get only the failing payment method.

### Billing Intervals

Products are created with one of the following recurring intervals:
- Daily
- Every 7 days
- Weekly
- Every 2 weeks
- Every 4 weeks
- Monthly
- Every 2 months
- Every 3 months (quarterly)
- Every 6 months (semi-annually)
- Yearly
- Every 2 years (biannually)

### Tax Rates

The script creates 6 tax rates (or reuses existing ones if account has data):
- Sales Tax (7.25%, exclusive)
- Sales Tax Inclusive (8.5%, inclusive)
- VAT (20%, exclusive)
- VAT Inclusive (19%, inclusive)
- GST (5%, exclusive)
- GST Inclusive (10%, inclusive)

Each product is randomly assigned 0-2 tax rates matching its tax behavior (inclusive/exclusive).

## How It Works

1. **Detection Phase**: Script checks for existing customers, products, and tax rates in your Stripe account
2. **Tax Rate Management**: 
   - If existing data found → reuses existing tax rates
   - If empty account + creating products → creates new tax rates
   - Otherwise → skips tax rate creation
3. **Data Creation**: Creates new products, customers, and subscriptions as specified
4. **Data Combination**: Combines existing and new data for subscription creation
5. **Summary**: Displays detailed summary of existing vs. new data created

## Error Handling

The script includes comprehensive error handling:
- Continues execution if individual items fail to create
- Displays warning messages for non-critical errors (e.g., payment method attachment failures)
- Reports detailed error information for debugging
- Validates API key format before starting
- Handles edge cases like insufficient data for subscriptions

## Use Cases

- **Initial Setup**: Populate an empty test account with comprehensive data
- **Add Subscriptions**: Add more subscriptions to existing test account (set products and customers to 0)
- **Expand Data**: Add more products/customers to existing account
- **Test Payment Failures**: Use customers with failing payment methods to test error handling
- **Test Subscription Lifecycle**: Test all subscription statuses and transitions
- **Tax Testing**: Test inclusive and exclusive tax calculations

## Limitations

- Designed for test mode only (requires `sk_test_` API keys)
- Does not create coupons, discounts, or promotion codes
- Does not create webhook endpoints
- Does not simulate actual payment flows (uses test tokens)
- Subscription status distribution is approximate due to random selection

## Rate Limiting

The script includes automatic rate limiting:
- Pauses for 1 second after every 20 items created
- Prevents hitting Stripe API rate limits during bulk operations

## Security

- API keys are never stored in the code
- Script validates API key format before use
- Only works with test mode API keys (prevents accidental production use)

## Troubleshooting

**"Sample larger than population or is negative"**
- The script tries to attach more payment methods than available
- This is automatically handled with `min()` function in the latest version

**"list indices must be integers or slices, not str"**
- Check that `PAYMENT_METHOD_FAILING` is a dictionary, not a list
- Should be: `{"type": "card", ...}` not `[{"type": "card", ...}]`

**Subscriptions not getting past_due status**
- This is expected - past_due requires actual payment failure attempts
- The script creates subscriptions with failing payment methods that will become past_due on first charge attempt

## License

This script is provided as-is for development and testing purposes.
