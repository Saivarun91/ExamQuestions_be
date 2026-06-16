CURRENCY_SYMBOLS = {
    'INR': '₹',
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
}


def normalize_currency(currency):
    return (currency or 'INR').upper().strip()


def get_currency_symbol(currency):
    code = normalize_currency(currency)
    return CURRENCY_SYMBOLS.get(code, f'{code} ')


def resolve_payment_currency(requested_currency, course_currency=None):
    """User-selected currency always takes priority over course default."""
    if requested_currency:
        currency = normalize_currency(requested_currency)
        if currency in ('INR', 'USD'):
            return currency
    currency = normalize_currency(course_currency)
    if currency not in ('INR', 'USD'):
        currency = 'INR'
    return currency


def to_smallest_unit(amount, currency='INR'):
    """Convert major currency unit to smallest unit (paise/cents)."""
    code = normalize_currency(currency)
    smallest = int(round(float(amount) * 100))

    if code == 'USD':
        min_smallest = 50
        min_amount = 0.50
    else:
        min_smallest = 100
        min_amount = 1.0

    if smallest < min_smallest:
        return min_smallest, min_amount
    return smallest, float(amount)


def format_min_purchase_message(currency, min_purchase):
    symbol = get_currency_symbol(currency)
    return f"Minimum purchase amount of {symbol}{min_purchase} required for this coupon"
