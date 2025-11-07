import stripe
import random
from datetime import datetime, timedelta
from faker import Faker

# Ініціалізуємо Faker
fake = Faker()

# Встановлюємо API ключ
stripe.api_key = "sk_test_YOUR_TEST_KEY_HERE"

# Тестові картки та банківські рахунки
PAYMENT_METHODS = [
    {"type": "card", "token": "pm_card_visa", "brand": "Visa"},
    {"type": "card", "token": "pm_card_mastercard", "brand": "Mastercard"},
    {"type": "card", "token": "pm_card_amex", "brand": "American Express"},
    {"type": "card", "token": "pm_card_discover", "brand": "Discover"},
    {"type": "card", "token": "pm_card_diners", "brand": "Diners Club"},
    {"type": "card", "token": "pm_card_jcb", "brand": "JCB"},
    {"type": "card", "token": "pm_card_unionpay", "brand": "UnionPay"},
    {"type": "us_bank_account", "token": "pm_usBankAccount", "brand": "US Bank Account"},
]

# Стандартні періоди оплати
BILLING_INTERVALS = [
    {"interval": "day"},
    {"interval": "week"},
    {"interval": "month"},
    {"interval": "year"},
]

# Типи податків
TAX_TYPES = [
    {"display_name": "Sales Tax", "percentage": 7.25, "inclusive": False, "description": "US Sales Tax"},
    {"display_name": "Sales Tax Inclusive", "percentage": 8.5, "inclusive": True, "description": "US Sales Tax (Inclusive)"},
    {"display_name": "VAT", "percentage": 20, "inclusive": False, "description": "UK VAT"},
    {"display_name": "VAT Inclusive", "percentage": 19, "inclusive": True, "description": "Germany VAT (Inclusive)"},
    {"display_name": "GST", "percentage": 5, "inclusive": False, "description": "Canada GST"},
    {"display_name": "GST Inclusive", "percentage": 10, "inclusive": True, "description": "Australia GST (Inclusive)"},
]

# Статуси підписок з вагами (для розподілу)
SUBSCRIPTION_STATUS_DISTRIBUTION = {
    "active": 0.50,           # 50%
    "trialing": 0.15,         # 15%
    "past_due": 0.10,         # 10%
    "canceled": 0.15,         # 15%
    "unpaid": 0.10,           # 10%
}

def create_tax_rates():
    """Створює податкові ставки"""
    print("Створюємо податкові ставки...")
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
            
            # Групуємо податки за типом (inclusive/exclusive)
            if tax["inclusive"]:
                tax_rates_by_type["inclusive"].append(tax_rate.id)
            else:
                tax_rates_by_type["exclusive"].append(tax_rate.id)
                
            print(f"✓ Створено податок: {tax['display_name']}")
        except Exception as e:
            print(f"✗ Помилка при створенні податку {tax['display_name']}: {e}")
    
    return tax_rates_by_type

def create_products_and_prices(tax_rates_by_type):
    """Створює продукти та ціни"""
    print("\nСтворюємо продукти та ціни...")
    products_with_prices = []
    
    for i in range(100):
        try:
            # Генеруємо реалістичні назви продуктів
            product_name = fake.catch_phrase()
            product_description = fake.bs()
            
            # Створюємо продукт
            product = stripe.Product.create(
                name=product_name,
                description=product_description,
            )
            
            # Створюємо ціну для кожного продукту
            interval_config = random.choice(BILLING_INTERVALS)
            
            # Вибираємо tax_behavior
            tax_behavior = random.choice(["inclusive", "exclusive"])
            
            # Вибираємо відповідні податки
            available_taxes = tax_rates_by_type[tax_behavior]
            selected_taxes = []
            if available_taxes:
                selected_taxes = random.sample(
                    available_taxes, 
                    k=random.randint(0, min(2, len(available_taxes)))
                )
            
            price = stripe.Price.create(
                product=product.id,
                unit_amount=random.randint(500, 50000),  # від $5 до $500
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
            
            print(f"✓ Створено продукт {i+1}/100: {product_name[:40]}... ({interval_config['interval']})")
        except Exception as e:
            print(f"✗ Помилка при створенні продукту {i+1}: {e}")
    
    return products_with_prices

def create_customers_with_payment_methods():
    """Створює кастомерів з платіжними методами використовуючи Faker"""
    print("\nСтворюємо кастомерів та платіжні методи...")
    customers = []
    
    for i in range(100):
        try:
            # Генеруємо реалістичні дані кастомера
            name = fake.name()
            email = fake.email()
            phone = fake.phone_number()
            company = fake.company() if random.choice([True, False]) else None
            
            # Створюємо адресу
            address = {
                "line1": fake.street_address(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "postal_code": fake.postcode(),
                "country": "US"
            }
            
            # Створюємо кастомера з реалістичними даними
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
            
            # Додаємо випадкову кількість платіжних методів (1-4)
            num_payment_methods = random.randint(1, 4)
            selected_methods = random.sample(PAYMENT_METHODS, k=num_payment_methods)
            
            attached_payment_methods = []
            
            for idx, pm_data in enumerate(selected_methods):
                try:
                    # Прикріплюємо платіжний метод до кастомера
                    payment_method = stripe.PaymentMethod.attach(
                        pm_data["token"],
                        customer=customer.id,
                    )
                    attached_payment_methods.append(payment_method.id)
                    
                    # Перший метод встановлюємо як default
                    if idx == 0:
                        stripe.Customer.modify(
                            customer.id,
                            invoice_settings={
                                "default_payment_method": payment_method.id,
                            },
                        )
                except Exception as e:
                    print(f"  ⚠ Не вдалось прикріпити {pm_data['brand']}: {e}")
            
            customers.append({
                "id": customer.id,
                "payment_methods": attached_payment_methods
            })
            
            print(f"✓ Створено кастомера {i+1}/100: {name} з {len(attached_payment_methods)} методами")
        except Exception as e:
            print(f"✗ Помилка при створенні кастомера {i+1}: {e}")
    
    return customers

def get_weighted_random_status():
    """Вибирає статус підписки згідно з розподілом"""
    statuses = list(SUBSCRIPTION_STATUS_DISTRIBUTION.keys())
    weights = list(SUBSCRIPTION_STATUS_DISTRIBUTION.values())
    return random.choices(statuses, weights=weights, k=1)[0]

def create_subscriptions(customers, products_with_prices):
    """Створює підписки з різними статусами"""
    print("\nСтворюємо підписки з різними статусами...")
    subscriptions = []
    status_counts = {status: 0 for status in SUBSCRIPTION_STATUS_DISTRIBUTION.keys()}
    
    for i in range(100):
        if i >= len(customers) or i >= len(products_with_prices):
            break
            
        try:
            customer = customers[i]
            product_data = products_with_prices[i]
            
            # Вибираємо статус згідно з розподілом
            desired_status = get_weighted_random_status()
            status_counts[desired_status] += 1
            
            subscription_params = {
                "customer": customer["id"],
                "items": [{"price": product_data["price_id"]}],
            }
            
            # Додаємо податки
            if product_data["tax_rates"]:
                subscription_params["default_tax_rates"] = product_data["tax_rates"]
            
            # Налаштовуємо параметри залежно від бажаного статусу
            if desired_status == "trialing":
                # Додаємо trial period для trialing
                trial_end = int((datetime.now() + timedelta(days=random.randint(7, 30))).timestamp())
                subscription_params["trial_end"] = trial_end
            elif desired_status == "canceled":
                # Створюємо active і потім скасовуємо
                pass  # Скасуємо після створення
            elif desired_status == "past_due":
                # Для past_due використовуємо картку що відхилить платіж
                subscription_params["payment_behavior"] = "default_incomplete"
            elif desired_status == "unpaid":
                # Для unpaid потрібна спеціальна конфігурація
                subscription_params["payment_behavior"] = "default_incomplete"
            
            subscription = stripe.Subscription.create(**subscription_params)
            
            # Post-processing для специфічних статусів
            if desired_status == "canceled":
                stripe.Subscription.modify(
                    subscription.id,
                    cancel_at_period_end=True
                )
                # Або відразу скасовуємо
                stripe.Subscription.cancel(subscription.id)
            
            subscriptions.append(subscription.id)
            print(f"✓ Створено підписку {i+1}/100 з цільовим статусом: {desired_status}")
            
        except Exception as e:
            print(f"✗ Помилка при створенні підписки {i+1}: {e}")
    
    # Виводимо статистику
    print("\nРозподіл статусів підписок:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    return subscriptions

def create_standalone_invoices(customers):
    """Створює окремі інвойси з різними статусами"""
    print("\nСтворюємо окремі інвойси з різними статусами...")
    invoices = []
    
    # Статуси інвойсів: draft, open, paid, uncollectible, void
    invoice_statuses = ["draft", "open", "paid", "void", "uncollectible"]
    
    # Створюємо по 10 інвойсів кожного типу (50 всього)
    for status_type in invoice_statuses:
        for i in range(10):
            if i >= len(customers):
                break
            
            try:
                customer = customers[i]
                
                # Створюємо draft invoice
                invoice = stripe.Invoice.create(
                    customer=customer["id"],
                    collection_method="charge_automatically",
                    description=f"Test invoice - {status_type}",
                )
                
                # Додаємо item до інвойсу
                stripe.InvoiceItem.create(
                    customer=customer["id"],
                    invoice=invoice.id,
                    amount=random.randint(1000, 10000),
                    currency="usd",
                    description=fake.bs(),
                )
                
                # Переводимо в потрібний статус
                if status_type == "draft":
                    # Залишаємо draft
                    pass
                elif status_type == "open":
                    # Фіналізуємо (open)
                    stripe.Invoice.finalize_invoice(invoice.id)
                elif status_type == "paid":
                    # Фіналізуємо і помічаємо як оплачений
                    stripe.Invoice.finalize_invoice(invoice.id)
                    stripe.Invoice.pay(invoice.id)
                elif status_type == "void":
                    # Фіналізуємо і void
                    stripe.Invoice.finalize_invoice(invoice.id)
                    stripe.Invoice.void_invoice(invoice.id)
                elif status_type == "uncollectible":
                    # Фіналізуємо і помічаємо як uncollectible
                    stripe.Invoice.finalize_invoice(invoice.id)
                    stripe.Invoice.mark_uncollectible(invoice.id)
                
                invoices.append(invoice.id)
                print(f"✓ Створено інвойс зі статусом: {status_type}")
                
            except Exception as e:
                print(f"✗ Помилка при створенні інвойсу ({status_type}): {e}")
    
    return invoices

def main():
    """Головна функція"""
    print("=" * 60)
    print("Початок заповнення тестового Stripe акаунту")
    print("=" * 60)
    
    # 1. Створюємо податкові ставки
    tax_rates_by_type = create_tax_rates()
    
    # 2. Створюємо продукти та ціни
    products_with_prices = create_products_and_prices(tax_rates_by_type)
    
    # 3. Створюємо кастомерів з платіжними методами
    customers = create_customers_with_payment_methods()
    
    # 4. Створюємо підписки з різними статусами
    subscriptions = create_subscriptions(customers, products_with_prices)
    
    # 5. Створюємо окремі інвойси з різними статусами
    invoices = create_standalone_invoices(customers)
    
    print("\n" + "=" * 60)
    print("Завершено!")
    print("=" * 60)
    print(f"Створено:")
    print(f"  - Податкових ставок: {len(tax_rates_by_type['inclusive']) + len(tax_rates_by_type['exclusive'])}")
    print(f"  - Продуктів з цінами: {len(products_with_prices)}")
    print(f"  - Кастомерів: {len(customers)}")
    print(f"  - Підписок: {len(subscriptions)}")
    print(f"  - Окремих інвойсів: {len(invoices)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
