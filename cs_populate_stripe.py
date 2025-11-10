import stripe
import random
from datetime import datetime, timedelta
from faker import Faker

# Faker initialization
fake = Faker()

# Asking user for Stripe API key
stripe.api_key = input("Please enter your Stripe test API key (starts with 'sk_test_'): ").strip()

# Checking validity of the key
if not stripe.api_key.startswith('sk_test_'):
    raise ValueError("Invalid API key. The key must start with 'sk_test_'")

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
    {"interval": "day"},
    {"interval": "week"},
    {"interval": "month"},
    {"interval": "year"},
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

def create_products_and_prices(tax_rates_by_type):
    """Creates products and prices"""
    print("\nCreating products and prices...")
    products_with_prices = []
    
    for i in range(100):
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
                },
                tax_behavior=tax_behavior,
            )
            
            products_with_prices.append({
                "product_id": product.id,
                "price_id": price.id,
                "tax_rates": selected_taxes,
                "tax_behavior": tax_behavior
            })
            
            print(f"✓ Created product {i+1}/100: {product_name[:40]}... ({interval_config['interval']})")
        except Exception as e:
            print(f"✗ Error creating product {i+1}: {e}")
    
    return products_with_prices

def create_customers_with_payment_methods():
    """Creates customers with payment methods using Faker"""
    print("\nCreating customers and payment methods...")
    customers = []
    
    for i in range(100):
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
            
            print(f"✓ Created customer {i+1}/100: {name} with {len(attached_payment_methods)} methods")
        except Exception as e:
            print(f"✗ Error creating customer {i+1}: {e}")
    
    return customers

def get_weighted_random_status():
    """Selects subscription status according to distribution"""
    statuses = list(SUBSCRIPTION_STATUS_DISTRIBUTION.keys())
    weights = list(SUBSCRIPTION_STATUS_DISTRIBUTION.values())
    return random.choices(statuses, weights=weights, k=1)[0]

def create_subscriptions(customers, products_with_prices):
    """Creates subscriptions with different statuses"""
    print("\nCreating subscriptions with different statuses...")
    subscriptions = []
    status_counts = {status: 0 for status in SUBSCRIPTION_STATUS_DISTRIBUTION.keys()}
    
    for i in range(100):
        if i >= len(customers) or i >= len(products_with_prices):
            break
            
        try:
            customer = customers[i]
            product_data = products_with_prices[i]
            
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
                # Add trial period for trialing status
                trial_end = int((datetime.now() + timedelta(days=random.randint(7, 30))).timestamp())
                subscription_params["trial_end"] = trial_end
            elif desired_status == "canceled":
                # Create active and then cancel
                pass  # Will cancel after creation
            elif desired_status == "past_due":
                # For past_due use a card that will decline payment
                subscription_params["payment_behavior"] = "default_incomplete"
            elif desired_status == "unpaid":
                # For unpaid status, special configuration is needed
                subscription_params["payment_behavior"] = "default_incomplete"
            
            subscription = stripe.Subscription.create(**subscription_params)
            
            # Post-processing for specific statuses
            if desired_status == "canceled":
                stripe.Subscription.modify(
                    subscription.id,
                    cancel_at_period_end=True
                )
                # Or cancel immediately
                stripe.Subscription.cancel(subscription.id)
            
            subscriptions.append(subscription.id)
            print(f"✓ Created subscription {i+1}/100 with target status: {desired_status}")
            
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
    
    # Create 10 invoices of each type (50 total)
    for status_type in invoice_statuses:
        for i in range(10):
            if i >= len(customers):
                break
            
            try:
                customer = customers[i]
                
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
                    # Keep as draft
                    pass
                elif status_type == "open":
                    # Finalize (open)
                    stripe.Invoice.finalize_invoice(invoice.id)
                elif status_type == "paid":
                    # Finalize and mark as paid
                    stripe.Invoice.finalize_invoice(invoice.id)
                    stripe.Invoice.pay(invoice.id)
                elif status_type == "void":
                    # Finalize and void
                    stripe.Invoice.finalize_invoice(invoice.id)
                    stripe.Invoice.void_invoice(invoice.id)
                elif status_type == "uncollectible":
                    # Finalize and mark as uncollectible
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
    products_with_prices = create_products_and_prices(tax_rates_by_type)
    
    # 3. Create customers with payment methods
    customers = create_customers_with_payment_methods()
    
    # 4. Create subscriptions with different statuses
    subscriptions = create_subscriptions(customers, products_with_prices)
    
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
