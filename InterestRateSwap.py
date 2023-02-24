"""
@Authors: Tuomas Vanhala, helper class for an individual interest rate swap
@Date: Dec 2022
"""

class InterestRateSwap:
    """
    Class to describe single IRS contract
    ARGS:
        swap_type (ql.VanillaSwap.Type):    type of the IRS contract: payer or receiver
        base_swap_id (int):                 unique identifier for the base swaps used in data generation
        notional (int):                     notional in millions (USD)
        forward_start_years (int):          in years if forward starting, or 0
        tenor_years (int):                  maturity of the contract
        delta_fair_swap_rate (float):       difference to the fair rate (or to ATM strike) in bps
        flt_freq (int):                     frequency of the floating payments in months
        fix_freq (int):                     frequency of the fixed payments in months
        reference_rate (str):               name of the underlying reference rate
    """
    def __init__(self, swap_type, base_swap_id, notional: int, forward_start_years: int, tenor_years: int,
                 delta_fair_swap_rate: float, flt_freq: int, fix_freq: int, reference_rate = 'LIBOR'):
        self.swap_type = swap_type
        self.base_swap_id = base_swap_id
        self.notional = notional
        self.forward_start_years = forward_start_years
        self.tenor_years = tenor_years
        self.delta_fair_swap_rate = delta_fair_swap_rate
        self.flt_freq = flt_freq
        self.fix_freq = fix_freq
        self.reference_rate = reference_rate
        self.fair_swap_rate = None
