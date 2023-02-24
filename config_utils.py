"""
@Authors: Tuomas Vanhala, declare constants and helper functions for the model feature construction
@Date: Dec 2022
"""

import QuantLib as ql
from InterestRateSwap import *

###+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Constants

NSIM = 5000 # Number of MC sims
MONTHS_IN_YEAR = 12
YIELD_CURVE_LENGTH_YEARS = 10 # For handling raw data
MAX_PORTFOLIO_LIFETIME_MONTHS = YIELD_CURVE_LENGTH_YEARS * MONTHS_IN_YEAR + 1
PORTFOLIO_COMBINATIONS = 500 # Number of portfolio combinations or None if all possible combinations
# fixed leg payments, floating leg payments, yield curve, weighted deviation from ATM strike, HW1F a, HW1F vola
NBR_FEATURES = 6 # Same for all models

###+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Utils

def calculate_portfolio_fixed_payments_profile(portfolio, portfolio_lifetime_months):
    """
    Helper function to form the fixed payments profile of an IRS portfolio
    ARGS:
        portfolio (list of InterestRateSwap):           portfolio of InterestRateSwap's.
        portfolio_lifetime_months (int):                portfolio lifetime in months.
    """
    portfolio_fixed_payments = [0.0] * portfolio_lifetime_months
    for irs in portfolio:
        fixed_payment = irs.notional * (irs.fair_swap_rate + irs.delta_fair_swap_rate * 0.0001)
        # Append them to portfolio during IRS maturity
        for i in range(irs.forward_start_years * MONTHS_IN_YEAR + irs.fix_freq,
                       irs.forward_start_years * MONTHS_IN_YEAR + irs.tenor_years * MONTHS_IN_YEAR + 1,
                       irs.fix_freq):
            # Take IRS type into account
            if irs.swap_type == ql.VanillaSwap.Payer:
                portfolio_fixed_payments[i] -= fixed_payment
            elif irs.swap_type == ql.VanillaSwap.Receiver:
                portfolio_fixed_payments[i] += fixed_payment
    return portfolio_fixed_payments

def compress_portfolio_floating_leg(portfolio, portfolio_lifetime_months):
    """
    Helper function to represent the floating leg payments profile of an IRS portfolio by using notional
    ARGS:
        portfolio (list of InterestRateSwap):           portfolio of InterestRateSwap's.
        portfolio_lifetime_months (int):                portfolio lifetime in months.
    """
    portfolio_floating_payments = [0.0] * portfolio_lifetime_months
    for irs in portfolio:
        floating_payment = irs.notional
        # Append them to portfolio during IRS maturity
        for i in range(irs.forward_start_years * MONTHS_IN_YEAR + irs.flt_freq,
                       irs.forward_start_years * MONTHS_IN_YEAR + irs.tenor_years * MONTHS_IN_YEAR + 1,
                       irs.flt_freq):
            # Take IRS type into account
            if irs.swap_type == ql.VanillaSwap.Payer:
                portfolio_floating_payments[i] += floating_payment
            elif irs.swap_type == ql.VanillaSwap.Receiver:
                portfolio_floating_payments[i] -= floating_payment
    return portfolio_floating_payments

def get_portfolio_contract_weighted_deviation_from_fair_swap_rate(portfolio, portfolio_lifetime_months):
    """
    Helper function to get the portfolio level deviations during certain moment of portfolio lifetime
    from fair swap rate (ATM strike) weighted by the notionals of the IRS contracts.

    ARGS:
        portfolio (list of InterestRateSwap):                   portfolio of InterestRateSwap's.
    RETURNS:
        portfolio_level_deviations_from_strike (list of float): list as long as portfolio lifetime having
                                                                weighted deviations inside
    """
    portfolio_level_deviations_from_strike = [0.0] * portfolio_lifetime_months
    notionals = sum(irs.notional for irs in portfolio)
    for irs in portfolio:
        weight = irs.notional / notionals
        irs_start = irs.forward_start_years * MONTHS_IN_YEAR
        irs_end = irs.forward_start_years * MONTHS_IN_YEAR + irs.tenor_years * MONTHS_IN_YEAR
        for i in range(irs_start, irs_end + 1):
            portfolio_level_deviations_from_strike[i] += (irs.delta_fair_swap_rate  * 0.0001 * weight)
    return portfolio_level_deviations_from_strike

def convert_swap_type(swap_type):
    if swap_type == 'payer':
        return ql.VanillaSwap.Payer
    elif swap_type == 'receiver':
        return ql.VanillaSwap.Receiver
    else:
        print("Unknown swap type:", swap_type)
        exit()

###+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
