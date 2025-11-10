# Stripe Test Account Populator

A Python script to populate a Stripe test account with realistic test data including products, customers, subscriptions, and invoices with various statuses.

## Overview

This script generates comprehensive test data for Stripe development and testing purposes. It creates:
- 100 products with recurring prices
- 100 customers with realistic profile information
- 100 subscriptions with diverse statuses
- 50 standalone invoices with different states
- Multiple payment methods per customer
- Tax rates (Sales Tax, VAT, GST) with inclusive/exclusive options

## Features

- **Realistic Test Data**: Uses the Faker library to generate authentic-looking customer information including names, emails, addresses, and phone numbers
- **Diverse Subscription Statuses**: Creates subscriptions in various states (active, trialing, past_due, canceled, unpaid) with weighted distribution
- **Multiple Billing Intervals**: Supports daily, weekly, monthly, and yearly recurring prices
- **Payment Method Variety**: Attaches multiple payment methods (Visa, Mastercard, Amex, Discover, etc.) to each customer with automatic default selection
- **Invoice Status Diversity**: Generates invoices in all possible states (draft, open, paid, void, uncollectible)
- **Tax Configuration**: Creates both inclusive and exclusive tax rates compatible with Stripe's tax_behavior requirements

## Prerequisites

- Python 3.7 or higher
- Stripe test account with API access
- Test mode API key from your Stripe dashboard

## Installation

1. Clone or download this script

2. Install required dependencies:

```pip install stripe faker```

## Configuration

Replace the API key in the script with your own Stripe test key:

```stripe.api_key = "sk_test_YOUR_TEST_KEY_HERE"```


## Usage

Run the script:

```python cs_stripe_populate.py```


## Data Distribution

### Subscription Statuses
- **Active**: 50% - Fully active recurring subscriptions
- **Trialing**: 15% - Subscriptions in trial period
- **Past Due**: 10% - Subscriptions with failed payments
- **Canceled**: 15% - Canceled subscriptions
- **Unpaid**: 10% - Subscriptions with unpaid invoices

### Invoice Statuses
- **Draft**: 10 invoices - Not yet finalized
- **Open**: 10 invoices - Finalized and awaiting payment
- **Paid**: 10 invoices - Successfully paid
- **Void**: 10 invoices - Voided invoices
- **Uncollectible**: 10 invoices - Marked as uncollectible

### Billing Intervals
Products are created with one of the following recurring intervals:
- Daily
- Weekly
- Monthly
- Yearly

### Tax Rates
The script creates 6 tax rates:
- Sales Tax (7.25%, exclusive)
- Sales Tax Inclusive (8.5%, inclusive)
- VAT (20%, exclusive)
- VAT Inclusive (19%, inclusive)
- GST (5%, exclusive)
- GST Inclusive (10%, inclusive)

## Script Structure

stripe_populator.py
├── create_tax_rates() # Creates tax rates
├── create_products_and_prices() # Generates products with recurring prices
├── create_customers_with_payment_methods() # Creates customers with realistic data
├── create_subscriptions() # Creates subscriptions with various statuses
├── create_standalone_invoices() # Generates invoices in different states
└── main() # Orchestrates the entire process

## Error Handling

The script includes comprehensive error handling:
- Continues execution if individual items fail to create
- Displays warning messages for non-critical errors
- Reports detailed error information for debugging

## Output Summary

Upon completion, the script displays a summary

