import stripe
import random
from datetime import datetime, timedelta
from faker import Faker
import time


# Faker initialization
fake = Faker()


def get_positive_integer(prompt, min_value=1):
    """Gets positive integer input from user with validation"""
    while True:
        try:
            value = int(input(prompt))
            if value >= min_value:
                return value
            else:
                print(f"Please enter a number >= {min_value}")
        except ValueError:
            print("That's not a valid integer. Please try again.")


# Asking user for Stripe API key
stripe.api_key = input("Please enter your Stripe test API key (starts with 'sk_test_'): ").strip()


# Checking validity of the key
if not stripe.api_key.startswith('sk_test_'):
    raise ValueError("Invalid API key. The key must start with 'sk_test_'")


# Get quantities from user
print("\n" + "=" * 60)
print("Configure data quantities")
print("=" * 60)
NUM_PRODUCTS = get_positive_integer("How many products to create? (min 1): ", min_value=1)
NUM_CUSTOMERS = get_positive_integer("How many customers to create? (min 1): ", min_value=1)
NUM_SUBSCRIPTIONS = get_positive_integer("How many subscriptions to create? (min 1): ", min_value=1)
print("=" * 60 + "\n")


# Test payment methods tokens (Stripe test tokens)
PAYMENT_METHODS = [
    {"type": "card", "token": "pm_card_visa", "brand": "Visa"},
    {"type": "card", "token": "pm_card_mastercard", "brand": "Mastercard"},
    {"type": "card", "token": "pm_card_amex", "brand": "American Express"},
    {"type": "card", "token": "pm_card_discover", "brand": "Discover"},
    {"type": "card", "token": "pm_card_diners", "brand": "Diners Club"},
    {"type": "card", "token": "pm_card_jcb", "brand": "JCB"},
    {"type": "card", "token": "pm_card_unionpay", "brand": "UnionPay"},
    {"type": "us_bank_account", "token": "pm_usBankAccount", "brand": "US Bank Account"}
]


# Standard billing intervals
BILLING_INTERVALS = [
    {"interval": "day", "interval_count": 1},      # Daily
    {"interval": "day", "interval_count": 7},      # Every 7 days
    {"interval": "week", "interval_count": 1},     # Weekly
    {"interval": "week", "interval_count": 2},     # Every 2 weeks
    {"interval": "week", "interval_count": 4},     # Every 4 weeks
    {"interval": "month", "interval_count": 1},    # Monthly
    {"interval": "month", "interval_count": 2},    # Every 2 months
    {"interval": "month", "interval_count": 3},    # Every 3 months
    {"interval": "month", "interval_count": 6},    # Every 6 months
    {"interval": "year", "interval_count": 1},     # Yearly
    {"interval": "year", "interval_count": 2},     # Every 2 years
]


# Tax types to create
TAX_TYPES = [
    {"display_name": "Sales Tax", "percentage": 7.25, "inclusive": False, "description": "US Sales Tax"},
    {"display_name": "Sales Tax Inclusive", "percentage": 8.5, "inclusive": True, "description": "US Sales Tax (Inclusive)"},
    {"display_name": "VAT", "percentage": 20, "inclusive": False, "description": "UK VAT"},
    {"display_name": "VAT Inclusive", "percentage": 19, "inclusive": True, "description": "Germany VAT (Inclusive)"},
    {"display_name": "GST", "percentage": 5, "inclusive": False, "description": "Canada GST"},
    {"display_name": "GST Inclusive", "percentage": 10, "inclusive": True, "description": "Australia GST (Inclusive)"},
]


# Subscription status distribution
SUBSCRIPTION_STATUS_DISTRIBUTION = {
    "active": 0.50,           # 50%
    "trialing": 0.15,         # 15%
    "past_due": 0.10,         # 10%
    "canceled": 0.15,         # 15%
    "unpaid": 0.10,           # 10%
}


def create_tax_rates():
    """Creates tax rates"""
    print("Creating tax rates...")
    tax_rates_by_type = {
        "inclusive": [],
        "exclusive": []
    }
    
    for tax in TAX_TYPES:
        try:
            tax_rate = stripe.TaxRate.create(
                display_name=tax["display_name"],
                description=tax["description"],
                percentage=tax["percentage"],
                inclusive=tax["inclusive"],
            )
            
            # Tax grouping by type (inclusive/exclusive)
            if tax["inclusive"]:
                tax_rates_by_type["inclusive"].append(tax_rate.id)
            else:
                tax_rates_by_type["exclusive"].append(tax_rate.id)
                
            print(f"✓ Created tax rate: {tax['display_name']}")
        except Exception as e:
            print(f"✗ Error creating tax rate {tax['display_name']}: {e}")
    
    return tax_rates_by_type


def create_products_and_prices(tax_rates_by_type, num_products):
    """Creates products and prices"""
    print(f"\nCreating {num_products} products and prices...")
    products_with_prices = []
    
    for i in range(num_products):
        try:
            # Realistic product names generation
            product_name = fake.catch_phrase()
            product_description = fake.bs()
            
            # Product creation
            product = stripe.Product.create(
                name=product_name,
                description=product_description,
            )
            
            # Price creation for each product
            interval_config = random.choice(BILLING_INTERVALS)
            
            # Tax behavior selection
            tax_behavior = random.choice(["inclusive", "exclusive"])
            
            # Corresponding tax rates selection
            available_taxes = tax_rates_by_type[tax_behavior]
            selected_taxes = []
            if available_taxes:
                selected_taxes = random.sample(
                    available_taxes, 
                    k=random.randint(0, min(2, len(available_taxes)))
                )
            
            price = stripe.Price.create(
                product=product.id,
                unit_amount=random.randint(500, 50000),  # from $5 to $500
                currency="usd",
                recurring={
                    "interval": interval_config["interval"],
                    "interval_count": interval_config["interval_count"],
                },
                tax_behavior=tax_behavior,
            )
            
            products_with_prices.append({
                "product_id": product.id,
                "price_id": price.id,
                "tax_rates": selected_taxes,
                "tax_behavior": tax_behavior
            })
            
            if interval_config["interval_count"] == 1:
                interval_display = interval_config["interval"]
            else:
                interval_display = f"every {interval_config['interval_count']} {interval_config['interval']}s"
            
            print(f"✓ Created product {i+1}/{num_products}: {product_name[:40]}... ({interval_display})")
            
            # Rate limiting
            if (i + 1) % 20 == 0:
                time.sleep(1)
                
        except Exception as e:
            print(f"✗ Error creating product {i+1}: {e}")
    
    return products_with_prices


def create_customers_with_payment_methods(num_customers):
    """Creates customers with payment methods using Faker"""
    print(f"\nCreating {num_customers} customers and payment methods...")
    customers = []
    
    for i in range(num_customers):
        try:
            # Generate realistic customer data
            name = fake.name()
            email = fake.email()
            phone = fake.msisdn()
            company = fake.company() if random.choice([True, False]) else None
            
            # Create address
            address = {
                "line1": fake.street_address(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "postal_code": fake.postcode(),
                "country": "US"
            }
            
            # Create customer with realistic data
            customer_params = {
                "name": name,
                "email": email,
                "phone": phone,
                "description": f"Customer from {address['city']}, {address['state']}",
                "address": address,
            }
            
            if company:
                customer_params["metadata"] = {"company": company}
            
            customer = stripe.Customer.create(**customer_params)
            
            # Add random number of payment methods (1-4)
            num_payment_methods = random.randint(1, 4)
            selected_methods = random.sample(PAYMENT_METHODS, k=num_payment_methods)
            
            attached_payment_methods = []
            
            for idx, pm_data in enumerate(selected_methods):
                try:
                    # Attach payment method to customer
                    payment_method = stripe.PaymentMethod.attach(
                        pm_data["token"],
                        customer=customer.id,
                    )
                    attached_payment_methods.append(payment_method.id)
                    
                    # Set first method as default
                    if idx == 0:
                        stripe.Customer.modify(
                            customer.id,
                            invoice_settings={
                                "default_payment_method": payment_method.id,
                            },
                        )
                except Exception as e:
                    print(f"  ⚠ Failed to attach {pm_data['brand']}: {e}")
            
            customers.append({
                "id": customer.id,
                "payment_methods": attached_payment_methods
            })
            
            print(f"✓ Created customer {i+1}/{num_customers}: {name} with {len(attached_payment_methods)} methods")
            
            # Rate limiting
            if (i + 1) % 20 == 0:
                time.sleep(1)
                
        except Exception as e:
            print(f"✗ Error creating customer {i+1}: {e}")
    
    return customers


def get_weighted_random_status():
    """Selects subscription status according to distribution"""
    statuses = list(SUBSCRIPTION_STATUS_DISTRIBUTION.keys())
    weights = list(SUBSCRIPTION_STATUS_DISTRIBUTION.values())
    return random.choices(statuses, weights=weights, k=1)[0]


def create_subscriptions(customers, products_with_prices, num_subscriptions):
    """Creates subscriptions with different statuses"""
    print(f"\nCreating {num_subscriptions} subscriptions with different statuses...")
    subscriptions = []
    status_counts = {status: 0 for status in SUBSCRIPTION_STATUS_DISTRIBUTION.keys()}
    
    # Check we have enough customers
    if len(customers) < num_subscriptions:
        print(f"⚠ Warning: Only {len(customers)} customers available for {num_subscriptions} subscriptions")
        print(f"  Some customers will have multiple subscriptions")
    
    for i in range(num_subscriptions):
        try:
            # Select customer (cycle through if needed)
            customer = customers[i % len(customers)]
            
            # Select random product from available products
            product_data = random.choice(products_with_prices)
            
            # Select status according to distribution
            desired_status = get_weighted_random_status()
            status_counts[desired_status] += 1
            
            subscription_params = {
                "customer": customer["id"],
                "items": [{"price": product_data["price_id"]}],
            }
            
            # Add taxes
            if product_data["tax_rates"]:
                subscription_params["default_tax_rates"] = product_data["tax_rates"]
            
            # Configure parameters based on desired status
            if desired_status == "trialing":
                trial_end = int((datetime.now() + timedelta(days=random.randint(7, 30))).timestamp())
                subscription_params["trial_end"] = trial_end
            elif desired_status == "canceled":
                pass
            elif desired_status == "past_due":
                subscription_params["payment_behavior"] = "default_incomplete"
            elif desired_status == "unpaid":
                subscription_params["payment_behavior"] = "default_incomplete"
            
            subscription = stripe.Subscription.create(**subscription_params)
            
            # Post-processing for specific statuses
            if desired_status == "canceled":
                stripe.Subscription.cancel(subscription.id)
            
            subscriptions.append(subscription.id)
            print(f"✓ Created subscription {i+1}/{num_subscriptions} with target status: {desired_status}")
            
            # Rate limiting
            if (i + 1) % 20 == 0:
                time.sleep(1)
            
        except Exception as e:
            print(f"✗ Error creating subscription {i+1}: {e}")
    
    # Output statistics
    print("\nSubscription status distribution:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    return subscriptions


def create_standalone_invoices(customers):
    """Creates standalone invoices with different statuses"""
    print("\nCreating standalone invoices with different statuses...")
    invoices = []
    
    # Invoice statuses: draft, open, paid, uncollectible, void
    invoice_statuses = ["draft", "open", "paid", "void", "uncollectible"]
    
    # Create 3 invoices of each type (15 total)
    for status_type in invoice_statuses:
        for i in range(3):
            if i >= len(customers):
                break
            
            try:
                customer = customers[i % len(customers)]
                
                # Create draft invoice
                invoice = stripe.Invoice.create(
                    customer=customer["id"],
                    collection_method="charge_automatically",
                    description=f"Test invoice - {status_type}",
                )
                
                # Add item to invoice
                stripe.InvoiceItem.create(
                    customer=customer["id"],
                    invoice=invoice.id,
                    amount=random.randint(1000, 10000),
                    currency="usd",
                    description=fake.bs(),
                )
                
                # Change to desired status
                if status_type == "draft":
                    pass
                elif status_type == "open":
                    stripe.Invoice.finalize_invoice(invoice.id)
                elif status_type == "paid":
                    stripe.Invoice.finalize_invoice(invoice.id)
                    stripe.Invoice.pay(invoice.id)
                elif status_type == "void":
                    stripe.Invoice.finalize_invoice(invoice.id)
                    stripe.Invoice.void_invoice(invoice.id)
                elif status_type == "uncollectible":
                    stripe.Invoice.finalize_invoice(invoice.id)
                    stripe.Invoice.mark_uncollectible(invoice.id)
                
                invoices.append(invoice.id)
                print(f"✓ Created invoice with status: {status_type}")
                
            except Exception as e:
                print(f"✗ Error creating invoice ({status_type}): {e}")
    
    return invoices


def main():
    """Main function"""
    print("=" * 60)
    print("Starting test Stripe account population")
    print("=" * 60)
    
    # 1. Create tax rates
    tax_rates_by_type = create_tax_rates()
    
    # 2. Create products and prices
    products_with_prices = create_products_and_prices(tax_rates_by_type, NUM_PRODUCTS)
    
    # 3. Create customers with payment methods
    customers = create_customers_with_payment_methods(NUM_CUSTOMERS)
    
    # 4. Create subscriptions with different statuses
    subscriptions = create_subscriptions(customers, products_with_prices, NUM_SUBSCRIPTIONS)
    
    # 5. Create standalone invoices with different statuses
    invoices = create_standalone_invoices(customers)
    
    print("\n" + "=" * 60)
    print("Completed!")
    print("=" * 60)
    print(f"Created:")
    print(f"  - Tax rates: {len(tax_rates_by_type['inclusive']) + len(tax_rates_by_type['exclusive'])}")
    print(f"  - Products with prices: {len(products_with_prices)}")
    print(f"  - Customers: {len(customers)}")
    print(f"  - Subscriptions: {len(subscriptions)}")
    print(f"  - Standalone invoices: {len(invoices)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
