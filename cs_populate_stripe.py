import stripe
import random
from datetime import datetime, timedelta
from faker import Faker
import time


# Faker initialization
fake = Faker()


def get_positive_integer(prompt, min_value=0):
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
print("Configure data quantities (enter 0 to skip creation)")
print("=" * 60)
NUM_PRODUCTS = get_positive_integer("How many NEW products to create? (0 to skip): ", min_value=0)
NUM_CUSTOMERS = get_positive_integer("How many NEW customers to create? (0 to skip): ", min_value=0)
NUM_SUBSCRIPTIONS = get_positive_integer("How many NEW subscriptions to create? (min 1): ", min_value=1)
print("=" * 60 + "\n")


# Successful payment methods
PAYMENT_METHODS_SUCCESS = [
    {"type": "card", "token": "pm_card_visa", "brand": "Visa"},
    {"type": "card", "token": "pm_card_mastercard", "brand": "Mastercard"},
    {"type": "card", "token": "pm_card_amex", "brand": "American Express"},
    {"type": "card", "token": "pm_card_discover", "brand": "Discover"},
    {"type": "card", "token": "pm_card_diners", "brand": "Diners Club"},
    {"type": "card", "token": "pm_card_jcb", "brand": "JCB"},
    {"type": "card", "token": "pm_card_unionpay", "brand": "UnionPay"},
    {"type": "us_bank_account", "token": "pm_usBankAccount", "brand": "US Bank Account"},
]


# Failing payment methods
PAYMENT_METHOD_FAILING = {"type": "card", "token": "pm_card_chargeCustomerFail", "brand": "Visa (Will Fail)"}


# Standard billing intervals
BILLING_INTERVALS = [
    {"interval": "day", "interval_count": 1},
    {"interval": "day", "interval_count": 7},
    {"interval": "week", "interval_count": 1},
    {"interval": "week", "interval_count": 2},
    {"interval": "week", "interval_count": 4},
    {"interval": "month", "interval_count": 1},
    {"interval": "month", "interval_count": 2},
    {"interval": "month", "interval_count": 3},
    {"interval": "month", "interval_count": 6},
    {"interval": "year", "interval_count": 1},
    {"interval": "year", "interval_count": 2},
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
    "active": 0.35,           # 35%
    "active_with_end": 0.10,  # 10%
    "trialing": 0.12,         # 12%
    "past_due": 0.08,         # 8%
    "canceled": 0.12,         # 12%
    "unpaid": 0.08,           # 8%
    "paused": 0.10,           # 10%
    "scheduled": 0.05,        # 5%
}


def fetch_existing_customers():
    print("\nFetching existing customers from Stripe...")
    customers = []
    
    try:
        for customer in stripe.Customer.list(limit=100).auto_paging_iter():
            customers.append({
                "id": customer.id,
                "payment_methods": [],
                "type": "normal"
            })
        
        print(f"✓ Found {len(customers)} existing customers")
    except Exception as e:
        print(f"✗ Error fetching customers: {e}")
    
    return customers


def fetch_existing_products_and_prices():
    print("\nFetching existing products and prices from Stripe...")
    products_with_prices = []
    
    try:
        for price in stripe.Price.list(limit=100, active=True, expand=['data.product']).auto_paging_iter():
            if price.recurring:
                products_with_prices.append({
                    "product_id": price.product.id if hasattr(price.product, 'id') else price.product,
                    "price_id": price.id,
                    "tax_rates": [],
                    "tax_behavior": price.tax_behavior or "unspecified"
                })
        
        print(f"✓ Found {len(products_with_prices)} active recurring prices")
    except Exception as e:
        print(f"✗ Error fetching products/prices: {e}")
    
    return products_with_prices


def fetch_existing_tax_rates():
    print("\nFetching existing tax rates from Stripe...")
    tax_rates_by_type = {
        "inclusive": [],
        "exclusive": []
    }
    
    try:
        for tax_rate in stripe.TaxRate.list(limit=100, active=True).auto_paging_iter():
            if tax_rate.inclusive:
                tax_rates_by_type["inclusive"].append(tax_rate.id)
            else:
                tax_rates_by_type["exclusive"].append(tax_rate.id)
        
        total = len(tax_rates_by_type["inclusive"]) + len(tax_rates_by_type["exclusive"])
        print(f"✓ Found {total} existing tax rates")
    except Exception as e:
        print(f"✗ Error fetching tax rates: {e}")
    
    return tax_rates_by_type


def create_tax_rates():
    print("\nCreating tax rates...")
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
            
            if tax["inclusive"]:
                tax_rates_by_type["inclusive"].append(tax_rate.id)
            else:
                tax_rates_by_type["exclusive"].append(tax_rate.id)
                
            print(f"✓ Created tax rate: {tax['display_name']}")
        except Exception as e:
            print(f"✗ Error creating tax rate {tax['display_name']}: {e}")
    
    return tax_rates_by_type


def create_products_and_prices(tax_rates_by_type, num_products):
    if num_products == 0:
        print("\nSkipping product creation (0 requested)")
        return []
    
    print(f"\nCreating {num_products} NEW products and prices...")
    products_with_prices = []
    
    for i in range(num_products):
        try:
            product_name = fake.catch_phrase()
            product_description = fake.bs()
            
            product = stripe.Product.create(
                name=product_name,
                description=product_description,
            )
            
            interval_config = random.choice(BILLING_INTERVALS)
            tax_behavior = random.choice(["inclusive", "exclusive"])
            
            available_taxes = tax_rates_by_type.get(tax_behavior, [])
            selected_taxes = []
            if available_taxes:
                selected_taxes = random.sample(
                    available_taxes, 
                    k=random.randint(0, min(2, len(available_taxes)))
                )
            
            price = stripe.Price.create(
                product=product.id,
                unit_amount=random.randint(500, 50000),
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
            
            if (i + 1) % 20 == 0:
                time.sleep(1)
                
        except Exception as e:
            print(f"✗ Error creating product {i+1}: {e}")
    
    return products_with_prices


def create_customers_with_payment_methods(num_customers):
    if num_customers == 0:
        print("\nSkipping customer creation (0 requested)")
        return [], []
    
    print(f"\nCreating {num_customers} NEW customers with payment methods...")
    
    # 10% customers will have failing payment method
    num_failing = int(num_customers * 0.10)
    num_normal = num_customers - num_failing
    
    customers_normal = []
    customers_failing = []
    
    # Create normal customers with valid payment methods
    print(f"\n→ Creating {num_normal} customers with VALID payment methods...")
    for i in range(num_normal):
        try:
            name = fake.name()
            email = fake.email()
            phone = fake.msisdn()
            company = fake.company() if random.choice([True, False]) else None
            
            address = {
                "line1": fake.street_address(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "postal_code": fake.postcode(),
                "country": "US"
            }
            
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
            
            # Attach 1-4 valid payment methods
            num_payment_methods = random.randint(1, min(4, len(PAYMENT_METHODS_SUCCESS)))
            selected_methods = random.sample(PAYMENT_METHODS_SUCCESS, k=num_payment_methods)
            
            attached_payment_methods = []
            
            for idx, pm_data in enumerate(selected_methods):
                try:
                    payment_method = stripe.PaymentMethod.attach(
                        pm_data["token"],
                        customer=customer.id,
                    )
                    attached_payment_methods.append(payment_method.id)
                    
                    if idx == 0:
                        stripe.Customer.modify(
                            customer.id,
                            invoice_settings={
                                "default_payment_method": payment_method.id,
                            },
                        )
                except Exception as e:
                    print(f"  ⚠ Failed to attach {pm_data['brand']}: {e}")
            
            customers_normal.append({
                "id": customer.id,
                "payment_methods": attached_payment_methods,
                "type": "normal"
            })
            
            print(f"✓ Created customer {i+1}/{num_normal}: {name} with {len(attached_payment_methods)} methods")
            
            if (i + 1) % 20 == 0:
                time.sleep(1)
                
        except Exception as e:
            print(f"✗ Error creating customer {i+1}: {e}")
    
    # Create customers with FAILING payment method ONLY
    print(f"\n→ Creating {num_failing} customers with FAILING payment method (pm_card_chargeCustomerFail)...")
    for i in range(num_failing):
        try:
            name = fake.name()
            email = fake.email()
            phone = fake.msisdn()
            company = fake.company() if random.choice([True, False]) else None
            
            address = {
                "line1": fake.street_address(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "postal_code": fake.postcode(),
                "country": "US"
            }
            
            customer_params = {
                "name": name,
                "email": email,
                "phone": phone,
                "description": f"Customer from {address['city']}, {address['state']} [FAILING CARD]",
                "address": address,
                "metadata": {"payment_type": "failing_card"}
            }
            
            if company:
                customer_params["metadata"]["company"] = company
            
            customer = stripe.Customer.create(**customer_params)
            
            # Attach ONLY the failing payment method
            try:
                payment_method = stripe.PaymentMethod.attach(
                    PAYMENT_METHOD_FAILING["token"],
                    customer=customer.id,
                )
                
                # Set it as default (and only) payment method
                stripe.Customer.modify(
                    customer.id,
                    invoice_settings={
                        "default_payment_method": payment_method.id,
                    },
                )
                
                customers_failing.append({
                    "id": customer.id,
                    "payment_methods": [payment_method.id],
                    "type": "failing"
                })
                
                print(f"✓ Created FAILING customer {i+1}/{num_failing}: {name} [{PAYMENT_METHOD_FAILING['brand']}]")
                
            except Exception as e:
                print(f"  ⚠ Failed to attach failing card: {e}")
            
            if (i + 1) % 20 == 0:
                time.sleep(1)
                
        except Exception as e:
            print(f"✗ Error creating failing customer {i+1}: {e}")
    
    return customers_normal, customers_failing


def get_weighted_random_status():
    statuses = list(SUBSCRIPTION_STATUS_DISTRIBUTION.keys())
    weights = list(SUBSCRIPTION_STATUS_DISTRIBUTION.values())
    return random.choices(statuses, weights=weights, k=1)[0]


def create_subscriptions(customers_normal, customers_failing, products_with_prices, num_subscriptions):
    print(f"\nCreating {num_subscriptions} NEW subscriptions with different statuses...")
    subscriptions = []
    
    all_customers = customers_normal + customers_failing
    
    if len(all_customers) == 0:
        print("✗ No customers available. Cannot create subscriptions.")
        return subscriptions
    
    if len(products_with_prices) == 0:
        print("✗ No products/prices available. Cannot create subscriptions.")
        return subscriptions
    
    print(f"  Using {len(customers_normal)} normal customers")
    print(f"  Using {len(customers_failing)} failing customers")
    print(f"  Using {len(products_with_prices)} total products/prices")
    
    status_counts = {status: 0 for status in SUBSCRIPTION_STATUS_DISTRIBUTION.keys()}
    
    for i in range(num_subscriptions):
        try:
            # Select customer based on desired status
            desired_status = get_weighted_random_status()
            
            # Use failing customers for past_due status
            if desired_status == "past_due" and customers_failing:
                customer = customers_failing[i % len(customers_failing)]
            else:
                customer = all_customers[i % len(all_customers)]
            
            product_data = random.choice(products_with_prices)
            status_counts[desired_status] += 1
            
            subscription_params = {
                "customer": customer["id"],
                "items": [{"price": product_data["price_id"]}],
            }
            
            if product_data["tax_rates"]:
                subscription_params["default_tax_rates"] = product_data["tax_rates"]
            
            # Configure based on desired status
            if desired_status == "active":
                # Normal active subscription
                pass
            elif desired_status == "active_with_end":
                # Active subscription scheduled to cancel in future
                cancel_at = int((datetime.now() + timedelta(days=random.randint(30, 90))).timestamp())
                subscription_params["cancel_at"] = cancel_at
            elif desired_status == "trialing":
                trial_end = int((datetime.now() + timedelta(days=random.randint(7, 30))).timestamp())
                subscription_params["trial_end"] = trial_end
            elif desired_status == "canceled":
                pass  # Will cancel after creation
            elif desired_status == "past_due":
                subscription_params["payment_behavior"] = "error_if_incomplete"
            elif desired_status == "unpaid":
                subscription_params["payment_behavior"] = "default_incomplete"
            elif desired_status == "paused":
                # Will pause after creation
                pass
            elif desired_status == "scheduled":
                # Subscription that starts in the future
                billing_cycle_anchor = int((datetime.now() + timedelta(days=random.randint(7, 30))).timestamp())
                subscription_params["billing_cycle_anchor"] = billing_cycle_anchor
                subscription_params["trial_end"] = billing_cycle_anchor  # Trial until start date
            
            subscription = stripe.Subscription.create(**subscription_params)
            
            # Post-processing for specific statuses
            if desired_status == "canceled":
                stripe.Subscription.cancel(subscription.id)
            elif desired_status == "paused":
                stripe.Subscription.modify(
                    subscription.id,
                    pause_collection={"behavior": "keep_as_draft"}
                )
            
            subscriptions.append(subscription.id)
            
            # Display different message for special statuses
            if desired_status == "active_with_end":
                cancel_date = datetime.fromtimestamp(subscription_params["cancel_at"]).strftime("%Y-%m-%d")
                print(f"✓ Created subscription {i+1}/{num_subscriptions}: active (ends {cancel_date})")
            elif desired_status == "scheduled":
                start_date = datetime.fromtimestamp(billing_cycle_anchor).strftime("%Y-%m-%d")
                print(f"✓ Created subscription {i+1}/{num_subscriptions}: scheduled (starts {start_date})")
            else:
                print(f"✓ Created subscription {i+1}/{num_subscriptions} with target status: {desired_status}")
            
            if (i + 1) % 20 == 0:
                time.sleep(1)
            
        except Exception as e:
            print(f"✗ Error creating subscription {i+1}: {e}")
    
    print("\n" + "=" * 60)
    print("Subscription status distribution:")
    for status, count in status_counts.items():
        percentage = (count / num_subscriptions * 100) if num_subscriptions > 0 else 0
        print(f"  {status}: {count} ({percentage:.1f}%)")
    print("=" * 60)
    
    return subscriptions


def main():
    print("=" * 60)
    print("Starting Stripe account population")
    print("=" * 60)
    
    # Fetch existing data from Stripe
    existing_customers = fetch_existing_customers()
    existing_products = fetch_existing_products_and_prices()
    
    # Determine if we need to create or fetch tax rates
    has_existing_data = len(existing_customers) > 0 or len(existing_products) > 0
    tax_rates_by_type = {"inclusive": [], "exclusive": []}
    new_tax_rates_created = False
    
    if has_existing_data:
        tax_rates_by_type = fetch_existing_tax_rates()
    elif NUM_PRODUCTS > 0:
        tax_rates_by_type = create_tax_rates()
        new_tax_rates_created = True
    
    # Create new products and prices
    new_products = create_products_and_prices(tax_rates_by_type, NUM_PRODUCTS)
    
    # Create new customers with payment methods (normal and failing)
    new_customers_normal, new_customers_failing = create_customers_with_payment_methods(NUM_CUSTOMERS)
    
    # Combine existing and new data
    all_customers_normal = existing_customers + new_customers_normal
    all_customers_failing = new_customers_failing
    all_products = existing_products + new_products
    
    print("\n" + "=" * 60)
    print("Data summary:")
    print(f"  - Existing customers: {len(existing_customers)}")
    print(f"  - New normal customers: {len(new_customers_normal)}")
    print(f"  - New failing customers: {len(new_customers_failing)}")
    print(f"  - Total customers: {len(all_customers_normal) + len(all_customers_failing)}")
    print(f"  - Existing products/prices: {len(existing_products)}")
    print(f"  - New products/prices: {len(new_products)}")
    print(f"  - Total products/prices: {len(all_products)}")
    total_taxes = len(tax_rates_by_type['inclusive']) + len(tax_rates_by_type['exclusive'])
    if total_taxes > 0:
        tax_source = "new" if new_tax_rates_created else "existing"
        print(f"  - Tax rates ({tax_source}): {total_taxes}")
    print("=" * 60)
    
    # Create subscriptions using ALL data
    subscriptions = create_subscriptions(all_customers_normal, all_customers_failing, all_products, NUM_SUBSCRIPTIONS)
    
    print("\n" + "=" * 60)
    print("Completed!")
    print("=" * 60)
    print(f"Created NEW:")
    if new_tax_rates_created:
        print(f"  - Tax rates: {len(tax_rates_by_type['inclusive']) + len(tax_rates_by_type['exclusive'])}")
    print(f"  - Products with prices: {len(new_products)}")
    print(f"  - Normal customers: {len(new_customers_normal)}")
    print(f"  - Failing customers: {len(new_customers_failing)}")
    print(f"  - Subscriptions: {len(subscriptions)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
