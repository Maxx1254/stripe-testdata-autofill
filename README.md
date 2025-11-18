# Stripe Test Account Populator

A Python script to populate a Stripe test account with realistic test data including products, customers, subscriptions, and invoices with various statuses.

## Overview

This script generates comprehensive test data for Stripe development and testing purposes. It creates:
- User defined number of products with recurring prices
- User defined number of customers with realistic profile information
- User defined number of subscriptions with diverse statuses
- 15 standalone invoices with different states
- Multiple payment methods per customer
- Tax rates (Sales Tax, VAT, GST) with inclusive/exclusive options

## Features

- **Realistic Test Data**: Uses the Faker library to generate authentic-looking customer information including names, emails, addresses, and phone numbers
- **Diverse Subscription Statuses**: Creates subscriptions in various states (active, trialing, past_due, canceled, unpaid) with weighted distribution
- **Multiple Billing Intervals**: Supports daily, weekly, monthly, yearly and custom set recurring prices
- **Payment Method Variety**: Attaches 1-4 payment methods per customer including:
  - Standard cards (Visa, Mastercard, Amex, Discover, Diners Club, JCB, UnionPay)
  - US Bank Account
  - Automatically sets first payment method as default
- **Invoice Status Diversity**: Generates invoices in all possible states (draft, open, paid, void, uncollectible)
- **Tax Configuration**: Creates both inclusive and exclusive tax rates compatible with Stripe's tax_behavior requirements

## Prerequisites

- Python 3.7 or higher
- Stripe test account with API access
- Test mode API key from your Stripe dashboard

## Installation

1. Clone or download this script

2. Install required dependencies:

```bash
pip install stripe faker
```

## Usage

1. Run the script with Python:

```bash
python cs_populate_stripe.py
```

2. When prompted, enter your Stripe test API key (starts with `sk_test_`).

The script will validate the API key format before proceeding with data creation.

For security, the API key is not stored in the code and must be provided each time you run the script.

3. After the key has been entered, you need to enter the required amount of products, customers and subscriptions.

## Data Distribution

### Subscription Statuses
- **Active**: 50% - Fully active recurring subscriptions
- **Trialing**: 15% - Subscriptions in trial period
- **Past Due**: 10% - Subscriptions with failed payments
- **Canceled**: 15% - Canceled subscriptions
- **Unpaid**: 10% - Subscriptions with unpaid invoices

### Payment Methods
The script uses Stripe's test payment method tokens, including:
- Standard Payment Cards:
  - Visa (`pm_card_visa`)
  - Mastercard (`pm_card_mastercard`)
  - American Express (`pm_card_amex`)
  - Discover (`pm_card_discover`)
  - Diners Club (`pm_card_diners`)
  - JCB (`pm_card_jcb`)
  - UnionPay (`pm_card_unionpay`)
- Alternative Payment Methods:
  - US Bank Account (`pm_usBankAccount`)

Each customer gets 1-4 randomly selected payment methods, with the first one set as the default payment method.

### Invoice Statuses
- **Draft**: 3 invoices - Not yet finalized
- **Open**: 3 invoices - Finalized and awaiting payment
- **Paid**: 3 invoices - Successfully paid
- **Void**: 3 invoices - Voided invoices
- **Uncollectible**: 3 invoices - Marked as uncollectible

### Billing Intervals
Products are created with one of the following recurring intervals:
- Daily
- Every 7 days
- Weekly
- Every 2 weeks
- Every 4 weeks
- Monthly
- Every 2 months
- Every 3 months
- Every 6 months
- Yearly
- Every 2 years

### Tax Rates
The script creates 6 tax rates:
- Sales Tax (7.25%, exclusive)
- Sales Tax Inclusive (8.5%, inclusive)
- VAT (20%, exclusive)
- VAT Inclusive (19%, inclusive)
- GST (5%, exclusive)
- GST Inclusive (10%, inclusive)

## Error Handling

The script includes comprehensive error handling:
- Continues execution if individual items fail to create
- Displays warning messages for non-critical errors
- Reports detailed error information for debugging

## Output Summary

Upon completion, the script displays a summary

