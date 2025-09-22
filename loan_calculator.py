#!/usr/bin/env python3
"""
FreeWorld Trucking School Loan Calculator
Bulletproof mathematical validation with extensive edge case handling
"""

import streamlit as st
import base64
import os
import math
from decimal import Decimal, getcontext
from pathlib import Path

# Set high precision for financial calculations
getcontext().prec = 28

def get_base64_of_image(path):
    """Safe image loading with error handling"""
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except (FileNotFoundError, OSError, PermissionError) as e:
        print(f"Image load error for {path}: {e}")
        return None

def get_background_image():
    """Get the highway background image used in agent portal"""
    possible_paths = [
        "data/highway_background.jpg",
        "assets/highway_background.jpg",
        "data/assets/highway_background.jpg",
        "../data/highway_background.jpg"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            encoded = get_base64_of_image(path)
            if encoded:
                return f"data:image/jpeg;base64,{encoded}"

    # Fallback to solid gradient if no image found
    return None

def get_freeworld_logo():
    """Get the FreeWorld wordmark logo"""
    possible_paths = [
        "data/FW-Wordmark-Roots@3x.png",
        "assets/FW-Wordmark-Roots@3x.png",
        "data/assets/FW-Wordmark-Roots@3x.png",
        "../data/FW-Wordmark-Roots@3x.png",
        "data/fw_logo.png",
        "assets/fw_logo.png"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            encoded = get_base64_of_image(path)
            if encoded:
                return encoded

    return ""

def get_round_logo_favicon():
    """Get the round FreeWorld logo for favicon"""
    possible_paths = [
        "assets/FW-Logo-Roots.svg",
        "assets/FW-Logo-Roots@3x.png",
        "assets/FW-Logo-Roots@2x.png",
        "data/FW-Logo-Roots.svg",
        "data/FW-Logo-Roots@3x.png",
        "data/FW-Logo-Roots@2x.png",
        "assets/fw_logo.png",
        "data/fw_logo.png"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            encoded = get_base64_of_image(path)
            if encoded:
                if path.endswith('.svg'):
                    return f"data:image/svg+xml;base64,{encoded}"
                else:
                    return f"data:image/png;base64,{encoded}"

    return ""

def validate_inputs(loan_amount, annual_rate, grace_months, payment_or_term):
    """
    Bulletproof input validation with extensive error checking
    Returns (is_valid, error_message, cleaned_values)
    """
    errors = []

    # Convert and validate loan amount
    try:
        loan_amount = float(loan_amount) if loan_amount else 0
        if loan_amount <= 0:
            errors.append("Loan amount must be greater than $0")
        elif loan_amount > 1000000:  # Reasonable max for trucking school
            errors.append("Loan amount cannot exceed $1,000,000")
    except (ValueError, TypeError):
        errors.append("Loan amount must be a valid number")
        loan_amount = 0

    # Convert and validate interest rate
    try:
        annual_rate = float(annual_rate) if annual_rate else 0
        if annual_rate < 0:
            errors.append("Interest rate cannot be negative")
        elif annual_rate > 100:  # Reasonable max rate
            errors.append("Interest rate cannot exceed 100%")
    except (ValueError, TypeError):
        errors.append("Interest rate must be a valid number")
        annual_rate = 0

    # Convert and validate grace period
    try:
        grace_months = int(grace_months) if grace_months else 0
        if grace_months < 0:
            errors.append("Grace period cannot be negative")
        elif grace_months > 120:  # Reasonable max
            errors.append("Grace period cannot exceed 120 months")
    except (ValueError, TypeError):
        errors.append("Grace period must be a whole number of months")
        grace_months = 0

    # Convert and validate payment/term
    try:
        payment_or_term = float(payment_or_term) if payment_or_term else 0
        if payment_or_term <= 0:
            errors.append("Payment/term must be greater than 0")
    except (ValueError, TypeError):
        errors.append("Payment/term must be a valid number")
        payment_or_term = 0

    return len(errors) == 0, "; ".join(errors), (loan_amount, annual_rate, grace_months, payment_or_term)

def calculate_fixed_payment_loan(loan_amount, annual_rate, grace_months, monthly_payment):
    """
    Calculate time to payoff for fixed payment loan with bulletproof validation
    Returns (total_months, total_paid, error_message)
    """
    # Validate inputs first
    is_valid, error_msg, (loan_amount, annual_rate, grace_months, monthly_payment) = validate_inputs(
        loan_amount, annual_rate, grace_months, monthly_payment
    )

    if not is_valid:
        return None, None, error_msg

    try:
        # Use Decimal for precise financial calculations
        loan_decimal = Decimal(str(loan_amount))
        rate_decimal = Decimal(str(annual_rate))
        grace_decimal = Decimal(str(grace_months))
        payment_decimal = Decimal(str(monthly_payment))

        monthly_rate = rate_decimal / Decimal('100') / Decimal('12')

        if monthly_rate == 0:
            # No interest case
            if payment_decimal <= 0:
                return None, None, "Monthly payment must be greater than $0"

            payment_months = loan_decimal / payment_decimal
            total_months = float(payment_months + grace_decimal)
            total_paid = float(loan_decimal)  # No interest

            if total_months > 1200:  # 100 years max
                return None, None, "Loan term exceeds reasonable limits (100+ years)"

        else:
            # Interest accrues during grace period
            loan_after_grace = loan_decimal * ((Decimal('1') + monthly_rate) ** grace_decimal)

            # Check if payment covers interest
            min_payment = loan_after_grace * monthly_rate
            if payment_decimal <= min_payment:
                return None, None, f"Monthly payment (${payment_decimal:.2f}) must be greater than minimum interest payment (${min_payment:.2f})"

            # Calculate months using loan amortization formula
            # N = -log(1 - (P * r) / PMT) / log(1 + r)
            try:
                numerator = Decimal('1') - (loan_after_grace * monthly_rate) / payment_decimal
                if numerator <= 0:
                    return None, None, "Payment too small - loan will never be paid off"

                payment_months = -Decimal(str(math.log(float(numerator)))) / Decimal(str(math.log(float(Decimal('1') + monthly_rate))))
                total_months = float(payment_months + grace_decimal)
                total_paid = float(payment_decimal * payment_months)

                if total_months > 1200:  # 100 years max
                    return None, None, "Loan term exceeds reasonable limits (100+ years)"

            except (ValueError, ZeroDivisionError, OverflowError) as e:
                return None, None, f"Mathematical error in calculation: {str(e)}"

        return round(total_months, 1), round(total_paid, 2), None

    except Exception as e:
        return None, None, f"Calculation error: {str(e)}"

def calculate_fixed_term_loan(loan_amount, annual_rate, grace_months, term_months):
    """
    Calculate required payment for fixed term loan with bulletproof validation
    Returns (monthly_payment, total_paid, error_message)
    """
    # Validate inputs first
    is_valid, error_msg, (loan_amount, annual_rate, grace_months, term_months) = validate_inputs(
        loan_amount, annual_rate, grace_months, term_months
    )

    if not is_valid:
        return None, None, error_msg

    # Additional validation for term calculation
    if term_months <= grace_months:
        return None, None, f"Total term ({term_months} months) must be greater than grace period ({grace_months} months)"

    try:
        # Use Decimal for precise financial calculations
        loan_decimal = Decimal(str(loan_amount))
        rate_decimal = Decimal(str(annual_rate))
        grace_decimal = Decimal(str(grace_months))
        term_decimal = Decimal(str(term_months))

        payment_months = term_decimal - grace_decimal
        monthly_rate = rate_decimal / Decimal('100') / Decimal('12')

        if monthly_rate == 0:
            # No interest case
            monthly_payment = loan_decimal / payment_months
            total_paid = float(loan_decimal)
        else:
            # Interest accrues during grace period
            loan_after_grace = loan_decimal * ((Decimal('1') + monthly_rate) ** grace_decimal)

            # PMT formula: PMT = P * [r(1+r)^n] / [(1+r)^n - 1]
            try:
                factor = (Decimal('1') + monthly_rate) ** payment_months
                monthly_payment = loan_after_grace * (monthly_rate * factor) / (factor - Decimal('1'))
                total_paid = float(monthly_payment * payment_months)

                if monthly_payment > Decimal('100000'):  # $100k/month max sanity check
                    return None, None, "Required payment exceeds reasonable limits"

            except (ValueError, ZeroDivisionError, OverflowError) as e:
                return None, None, f"Mathematical error in calculation: {str(e)}"

        return round(float(monthly_payment), 2), round(total_paid, 2), None

    except Exception as e:
        return None, None, f"Calculation error: {str(e)}"

def generate_calculator_html():
    """Generate the complete calculator HTML using agent portal pattern"""

    # Get background image and favicon
    bg_image = get_background_image()
    bg_style = f"background-image: url({bg_image});" if bg_image else "background: linear-gradient(135deg, #004751, #593CBC);"
    favicon = get_round_logo_favicon()

    # Add favicon link if available
    favicon_html = f'<link rel="icon" type="image/x-icon" href="{favicon}">' if favicon else ''

    return f"""
    <head>
        <title>FreeWorld Trucking School Loan Calculator - CDL Training Cost Estimator</title>
        {favicon_html}
    </head>
    <style>
    /* FreeWorld Brand Colors */
    :root {{
        --fw-roots: #004751;
        --fw-midnight: #191931;
        --fw-freedom-green: #CDF95C;
        --fw-visionary-violet: #593CBC;
        --fw-horizon-grey: #F4F4F4;
        --fw-card-border: #CCCCCC;
        --fw-card-bg: #FAFAFA;
    }}

    body {{
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background-color: #EAEAEA;
        overflow-x: hidden;
    }}

    .page-container {{
        width: 100%;
        min-height: 100vh;
        position: relative;
        overflow: hidden;
        background-color: white;
    }}

    /* Title page with background */
    .title-page {{
        {bg_style}
        background-size: cover;
        background-position: center;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        text-align: center;
        min-height: 400px;
        padding: 40px 20px 0 20px;
    }}

    .title-page .logo-container {{
        padding-top: 50px;
        margin-bottom: 20px;
    }}

    .title-page .title-block {{
        background-color: var(--fw-roots);
        color: white;
        padding: 20px;
        width: 90%;
        max-width: 300px;
        margin: 20px auto;
        box-sizing: border-box;
        border-radius: 8px;
    }}

    .title-page h1 {{
        font-size: 24px;
        font-weight: bold;
        margin: 0 0 10px 0;
    }}

    .title-page .meta {{
        font-size: 14px;
        color: var(--fw-freedom-green);
    }}

    .title-page .meta p {{
        margin: 5px 0;
    }}

    /* Calculator cards */
    .calculator-container {{
        max-width: 390px;
        margin: 0 auto;
        padding: 0 20px 20px 20px;
    }}

    .calc-card {{
        background: var(--fw-card-bg);
        border: 1px solid var(--fw-card-border);
        border-radius: 12px;
        margin-bottom: 20px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}

    .calc-header h3 {{
        font-size: 18px;
        font-weight: bold;
        color: var(--fw-roots);
        margin: 0 0 10px 0;
    }}

    .calc-description {{
        font-size: 14px;
        color: #666;
        margin-bottom: 20px;
        line-height: 1.4;
    }}

    .form-row {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 16px;
        width: 100%;
        box-sizing: border-box;
    }}

    .form-col {{
        display: flex;
        flex-direction: column;
        min-width: 0;
        box-sizing: border-box;
        position: relative;
    }}

    .form-label {{
        font-size: 14px;
        font-weight: 600;
        color: var(--fw-midnight);
        margin-bottom: 6px;
        height: 20px;
        display: flex;
        align-items: center;
    }}

    .form-input {{
        padding: 12px;
        border: 1px solid var(--fw-card-border);
        border-radius: 8px;
        font-size: 16px;
        background: white;
        color: var(--fw-midnight);
        width: 100%;
        box-sizing: border-box;
        min-width: 0;
    }}

    .form-input:focus {{
        outline: none;
        border-color: var(--fw-roots);
        box-shadow: 0 0 0 2px rgba(0, 71, 81, 0.1);
    }}

    .result-card {{
        background: linear-gradient(135deg, var(--fw-roots), var(--fw-visionary-violet));
        color: white;
        padding: 16px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,71,81,0.2);
    }}

    .result-title {{
        font-size: 14px;
        font-weight: 600;
        opacity: 0.9;
        margin-bottom: 8px;
    }}

    .result-value {{
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 4px;
    }}

    .result-subtitle {{
        font-size: 12px;
        opacity: 0.8;
    }}

    .error-card {{
        background: #dc3545;
        color: white;
        padding: 16px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(220,53,69,0.2);
    }}

    /* Tooltip styles */
    .label-with-help {{
        display: flex;
        align-items: center;
        width: 100%;
        position: relative;
    }}

    .help-icon {{
        position: absolute;
        top: 0;
        right: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        border-radius: 4px;
        background: var(--fw-roots);
        color: white;
        font-size: 10px;
        font-weight: bold;
        cursor: help;
        flex-shrink: 0;
        z-index: 10;
    }}

    .help-icon:hover {{
        background: var(--fw-visionary-violet);
        transform: scale(1.1);
        transition: all 0.2s ease;
    }}

    .tooltip {{
        visibility: hidden;
        opacity: 0;
        position: absolute;
        bottom: 130%;
        right: 0;
        background: var(--fw-midnight);
        color: white;
        text-align: left;
        border-radius: 8px;
        padding: 12px;
        font-size: 13px;
        font-weight: normal;
        line-height: 1.4;
        z-index: 1000;
        width: 280px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: opacity 0.3s, visibility 0.3s;
    }}

    .tooltip::after {{
        content: "";
        position: absolute;
        top: 100%;
        right: 18px;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: var(--fw-midnight) transparent transparent transparent;
    }}

    .help-icon:hover .tooltip {{
        visibility: visible;
        opacity: 1;
    }}

    @media (max-width: 768px) {{
        .form-row {{
            grid-template-columns: 1fr;
            gap: 16px;
        }}

        .tooltip {{
            width: 240px;
            font-size: 12px;
            padding: 10px;
            right: -20px;
        }}

        .help-icon {{
            width: 16px;
            height: 16px;
            font-size: 9px;
        }}
    }}
    .error-text {{
        font-size: 14px;
        font-weight: 600;
    }}

    .footer {{
        text-align: center;
        padding: 30px 20px;
        margin-top: 40px;
        border-top: 1px solid #eee;
    }}

    .footer .company-name {{
        color: var(--fw-midnight);
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 8px;
        font-family: 'Outfit', sans-serif;
    }}

    .footer .contact-info {{
        color: #666;
        font-size: 14px;
        font-family: 'Outfit', sans-serif;
    }}

    .footer a {{
        color: var(--fw-roots);
        text-decoration: none;
        font-weight: 600;
    }}
    </style>

    <div class="page-container">
        <!-- Title page with background -->
        <div class="title-page">
            <div class="logo-container">
                <img src="data:image/png;base64,{get_freeworld_logo()}" alt="FreeWorld" style="height: 60px; width: auto;">
            </div>

            <div class="title-block">
                <h1>Trucking School Loan Calculator</h1>
                <div class="meta">
                    <p>You may be considering a loan to pay for trucking school. But be careful - interest charges that sound reasonable can quickly add up. Use this calculator to understand exactly how much you will have to pay for your school.</p>
                </div>
            </div>
        </div>

        <!-- Calculator cards -->
        <div class="calculator-container">
            <div class="calc-card">
                <div class="calc-header">
                    <h3>Fixed Payment Calculator</h3>
                </div>
                <div class="calc-description">
                    Pay a fixed amount each month. See how long it takes to pay off your loan.
                </div>

                <div class="form-row">
                    <div class="form-col">
                        <label class="form-label">Loan Amount</label>
                        <input type="number" class="form-input" id="loan1" placeholder="3500" step="100" value="3500" min="1" max="1000000">
                    </div>
                    <div class="form-col">
                        <label class="form-label">Interest Rate (%)</label>
                        <input type="number" class="form-input" id="rate1" placeholder="8.5" step="0.1" value="8.5" min="0" max="100">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-col">
                        <label class="form-label">Grace Period (months)</label>
                        <input type="number" class="form-input" id="grace1" placeholder="6" step="1" value="6" min="0" max="120">
                    </div>
                    <div class="form-col">
                        <label class="form-label">Monthly Payment</label>
                        <input type="number" class="form-input" id="payment1" placeholder="500" step="10" value="500" min="1" max="100000">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-col">
                        <div class="result-card" id="result1-months">
                            <div class="result-title">Time to Pay Off</div>
                            <div class="result-value" id="months1">0</div>
                            <div class="result-subtitle">months</div>
                        </div>
                    </div>
                    <div class="form-col">
                        <div class="result-card" id="result1-total">
                            <div class="result-title">Total Paid</div>
                            <div class="result-value" id="total1">$0</div>
                            <div class="result-subtitle">including interest</div>
                        </div>
                    </div>
                </div>

                <div id="error1" style="display: none;">
                    <div class="error-card">
                        <div class="error-text" id="error1-text"></div>
                    </div>
                </div>
            </div>

            <div class="calc-card">
                <div class="calc-header">
                    <h3>Fixed Term Calculator</h3>
                </div>
                <div class="calc-description">
                    Use this section if you want to pay off your loan in a certain amount of time.<br>
                    This will calculate your monthly payment rate in order to pay off your loan.
                </div>

                <div class="form-row">
                    <div class="form-col">
                        <label class="form-label">Loan Amount</label>
                        <input type="number" class="form-input" id="loan2" placeholder="3500" step="100" value="3500" min="1" max="1000000">
                    </div>
                    <div class="form-col">
                        <label class="form-label">Interest Rate (%)</label>
                        <input type="number" class="form-input" id="rate2" placeholder="8.5" step="0.1" value="8.5" min="0" max="100">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-col">
                        <label class="form-label">Grace Period (months)</label>
                        <input type="number" class="form-input" id="grace2" placeholder="6" step="1" value="6" min="0" max="120">
                    </div>
                    <div class="form-col">
                        <label class="form-label">Desired Payoff Time (months)</label>
                        <input type="number" class="form-input" id="term2" placeholder="12" step="1" value="12" min="1" max="1200">
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-col">
                        <div class="result-card" id="result2-payment">
                            <div class="result-title">Monthly Payment</div>
                            <div class="result-value" id="payment2">$0</div>
                            <div class="result-subtitle">per month</div>
                        </div>
                    </div>
                    <div class="form-col">
                        <div class="result-card" id="result2-total">
                            <div class="result-title">Total Paid</div>
                            <div class="result-value" id="total2">$0</div>
                            <div class="result-subtitle">including interest</div>
                        </div>
                    </div>
                </div>

                <div id="error2" style="display: none;">
                    <div class="error-card">
                        <div class="error-text" id="error2-text"></div>
                    </div>
                </div>
            </div>

            <div class="footer">
                <img src="data:image/png;base64,{get_freeworld_logo()}" alt="FreeWorld" style="height: 24px; width: auto; margin-bottom: 8px;">
                <div class="contact-info">
                    For support, call <a href="tel:4086683608">(408) 668-3608</a>
                </div>
            </div>
        </div>
    </div>

    <script>
    // Bulletproof input validation functions
    function validateInputs(loan, rate, grace, paymentOrTerm) {{
        const errors = [];

        // Validate loan amount
        if (!loan || isNaN(loan) || loan <= 0) {{
            errors.push("Loan amount must be greater than $0");
        }} else if (loan > 1000000) {{
            errors.push("Loan amount cannot exceed $1,000,000");
        }}

        // Validate interest rate
        if (isNaN(rate) || rate < 0) {{
            errors.push("Interest rate cannot be negative");
        }} else if (rate > 100) {{
            errors.push("Interest rate cannot exceed 100%");
        }}

        // Validate grace period
        if (isNaN(grace) || grace < 0) {{
            errors.push("Grace period cannot be negative");
        }} else if (grace > 120) {{
            errors.push("Grace period cannot exceed 120 months");
        }}

        // Validate payment/term
        if (!paymentOrTerm || isNaN(paymentOrTerm) || paymentOrTerm <= 0) {{
            errors.push("Payment/term must be greater than 0");
        }}

        return errors;
    }}

    function showError(cardNum, message) {{
        document.getElementById(`error${{cardNum}}`).style.display = 'block';
        document.getElementById(`error${{cardNum}}-text`).textContent = message;

        // Hide result cards
        if (cardNum === 1) {{
            document.getElementById('result1-months').style.display = 'none';
            document.getElementById('result1-total').style.display = 'none';
        }} else {{
            document.getElementById('result2-payment').style.display = 'none';
            document.getElementById('result2-total').style.display = 'none';
        }}
    }}

    function hideError(cardNum) {{
        document.getElementById(`error${{cardNum}}`).style.display = 'none';

        // Show result cards
        if (cardNum === 1) {{
            document.getElementById('result1-months').style.display = 'block';
            document.getElementById('result1-total').style.display = 'block';
        }} else {{
            document.getElementById('result2-payment').style.display = 'block';
            document.getElementById('result2-total').style.display = 'block';
        }}
    }}

    function calculateFixedPayment() {{
        const loan = parseFloat(document.getElementById('loan1').value) || 0;
        const rate = parseFloat(document.getElementById('rate1').value) || 0;
        const grace = parseInt(document.getElementById('grace1').value) || 0;
        const payment = parseFloat(document.getElementById('payment1').value) || 0;

        // Validate inputs
        const errors = validateInputs(loan, rate, grace, payment);
        if (errors.length > 0) {{
            showError(1, errors.join('; '));
            return;
        }}

        try {{
            const monthlyRate = rate / 100 / 12;
            let months, total;

            if (monthlyRate === 0) {{
                // No interest case
                const paymentMonths = loan / payment;
                months = paymentMonths + grace;
                total = loan;
            }} else {{
                // Interest accrues during grace period
                const loanAfterGrace = loan * Math.pow(1 + monthlyRate, grace);
                const minPayment = loanAfterGrace * monthlyRate;

                if (payment <= minPayment) {{
                    showError(1, `Monthly payment ($$${{payment.toFixed(2)}}) must be greater than minimum interest payment ($$${{minPayment.toFixed(2)}})`);
                    return;
                }}

                // Calculate months using loan amortization formula
                const numerator = 1 - (loanAfterGrace * monthlyRate) / payment;
                if (numerator <= 0) {{
                    showError(1, "Payment too small - loan will never be paid off");
                    return;
                }}

                const paymentMonths = -Math.log(numerator) / Math.log(1 + monthlyRate);
                months = paymentMonths + grace;
                total = payment * paymentMonths;

                if (months > 1200) {{
                    showError(1, "Loan term exceeds reasonable limits (100+ years)");
                    return;
                }}
            }}

            hideError(1);
            document.getElementById('months1').textContent = months.toFixed(1);
            document.getElementById('total1').textContent = '$' + total.toLocaleString('en-US', {{maximumFractionDigits: 0}});
        }} catch (e) {{
            showError(1, `Calculation error: ${{e.message}}`);
        }}
    }}

    function calculateFixedTerm() {{
        const loan = parseFloat(document.getElementById('loan2').value) || 0;
        const rate = parseFloat(document.getElementById('rate2').value) || 0;
        const grace = parseInt(document.getElementById('grace2').value) || 0;
        const term = parseInt(document.getElementById('term2').value) || 0;

        // Validate inputs
        const errors = validateInputs(loan, rate, grace, term);
        if (errors.length > 0) {{
            showError(2, errors.join('; '));
            return;
        }}

        // Additional validation for term
        if (term <= grace) {{
            showError(2, `Total term (${{term}} months) must be greater than grace period (${{grace}} months)`);
            return;
        }}

        try {{
            const paymentMonths = term - grace;
            const monthlyRate = rate / 100 / 12;
            let payment, total;

            if (monthlyRate === 0) {{
                // No interest case
                payment = loan / paymentMonths;
                total = loan;
            }} else {{
                // Interest accrues during grace period
                const loanAfterGrace = loan * Math.pow(1 + monthlyRate, grace);

                // PMT formula: PMT = P * [r(1+r)^n] / [(1+r)^n - 1]
                const factor = Math.pow(1 + monthlyRate, paymentMonths);
                payment = loanAfterGrace * (monthlyRate * factor) / (factor - 1);
                total = payment * paymentMonths;

                if (payment > 100000) {{
                    showError(2, "Required payment exceeds reasonable limits");
                    return;
                }}
            }}

            hideError(2);
            document.getElementById('payment2').textContent = '$' + payment.toLocaleString('en-US', {{maximumFractionDigits: 0}});
            document.getElementById('total2').textContent = '$' + total.toLocaleString('en-US', {{maximumFractionDigits: 0}});
        }} catch (e) {{
            showError(2, `Calculation error: ${{e.message}}`);
        }}
    }}

    // Add event listeners with input validation
    ['loan1', 'rate1', 'grace1', 'payment1'].forEach(id => {{
        const element = document.getElementById(id);
        element.addEventListener('input', calculateFixedPayment);
        element.addEventListener('blur', calculateFixedPayment);
    }});

    ['loan2', 'rate2', 'grace2', 'term2'].forEach(id => {{
        const element = document.getElementById(id);
        element.addEventListener('input', calculateFixedTerm);
        element.addEventListener('blur', calculateFixedTerm);
    }});

    // Initial calculations
    calculateFixedPayment();
    calculateFixedTerm();
    </script>
    """

# Streamlit configuration
st.set_page_config(
    page_title="FreeWorld Trucking School Loan Calculator - CDL Training Cost Estimator",
    page_icon="🏫",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def main():
    """Main function for standalone use"""
    # Flush to top styling (EXACT from agent portal)
    st.markdown(
        """
        <style>
          [data-testid="stAppViewContainer"] { padding: 0 !important; }
          .block-container { padding-top: 0 !important; margin-top: 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Generate and display the complete calculator HTML
    calculator_html = generate_calculator_html()
    st.components.v1.html(calculator_html, height=1200, scrolling=True)

if __name__ == "__main__":
    main()