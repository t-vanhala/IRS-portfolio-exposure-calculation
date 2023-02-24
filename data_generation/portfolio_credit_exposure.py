"""
@Authors: Tuomas Vanhala, functions valuate_irs and portfolio_exposure
based on https://github.com/frodiie/Credit-Exposure-Prediction-GRU
@Date: Nov 2022
"""

import pandas as pd
import numpy as np
import QuantLib as ql
import random
from itertools import combinations
"""
Import functions for short rate paths and corresponding zero-coupon bond prices
from https://github.com/frodiie/Credit-Exposure-Prediction-GRU
"""
from credit_exposure import short_rate, zcb_price
from config_utils import *

def valuate_irs(irs_type, short_rates: np.ndarray, T: int, zero_rates, fwd_rates, 
                gridpoints: np.ndarray, nsim: int, param_a: float, param_vola: float, 
                delta_strike: float, flt_freq: int, fix_freq: int, notional: int):
        """
        Function based on the code in https://github.com/frodiie/Credit-Exposure-Prediction-GRU
        with slight modifications by adding a possibility to valuate also payer swaps.
        ARGS:
            irs_type (ql.VanillaSwap.Type):   type of the swap: payer or receiver.
            short_rates (np.ndarray):         short rate paths matrix.
            T (int):                          time to maturity (years).
            zero_rates (list):                short rates at t=0.
            fwd_rates (list):                 forward rates at t=0.
            gridpoints (pd.Series):           gridpoints [0, T] (years).
            nsim (int):                       nbr of MC simulations.
            param_a (float):                  HW1F param mean reversion.
            param_vola (float):               HW1F param volatility.
            delta_strike (float):             difference from fair rate in bps.
            flt_freq (int):                   floating payment frequency (months).
            fix_freq (int):                   fixed payment frequency (months).
            notional (int):                   notional principal (M USD).
        """
        tenor_flt = [i for i in range(0, MONTHS_IN_YEAR*T+1, flt_freq)]
        tenor_fix = [i for i in range(0, MONTHS_IN_YEAR*T+1, fix_freq)]
        # Check which leg has payments more often and select it as a base
        tenor_idx = tenor_flt if len(tenor_flt) >= len(tenor_fix) else tenor_fix
        nbr_payments = len(tenor_idx) - 1

        zcb_prices = [
            zcb_price(short_rates, i, zero_rates, fwd_rates, gridpoints, nsim,
                      param_a, param_vola) 
            for i in tenor_idx
        ]
        #generate_plot(zcb_prices[-1], "Zero-coupon bond prices", "Zero-coupon bond price", MONTHS_IN_YEAR*T+1)
        libor_rates = [
            1 / (zcb_prices[i+1][tenor_idx[i],:]) 
            for i in range(len(zcb_prices)-1)
        ]

        all_fix = 0.0
        all_fixed_payments = list(filter((tenor_idx[0]).__lt__, tenor_fix))
        for i in [tenor_idx.index(i) for i in all_fixed_payments]:
            all_fix += (fix_freq / 12.0) * zcb_prices[i][0,:]
        all_floating = 1 - zcb_prices[-1][0,:]
        R = (all_floating / all_fix) + delta_strike * 0.0001
        realized_R = np.mean(R - delta_strike * 0.0001)
        #print("Fair swap rate for the IRS was", realized_R)
        V = np.empty(shape=(0, nsim))
        for j in range(0, nbr_payments):
            # Valuate the IRS based on the payments left
            outstand_fix = list(filter((tenor_idx[j]).__lt__, tenor_fix))
            outstand_ind_fix = [tenor_idx.index(i) for i in outstand_fix]
            outstand_flt = list(filter((tenor_idx[j]).__lt__, tenor_flt))
            outstand_ind_flt = [tenor_idx.index(i) for i in outstand_flt]
            l = outstand_ind_flt[0]
            fix_leg = sum(R * (fix_freq / 12.0) * zcb_prices[l][tenor_idx[j]:tenor_idx[j+1], :] for l in outstand_ind_fix)
            lib = libor_rates[l-1]
            flt_leg = lib * zcb_prices[l][tenor_idx[j]:tenor_idx[j+1], :] - zcb_prices[-1][tenor_idx[j]:tenor_idx[j+1], :]
            if irs_type == ql.VanillaSwap.Payer:
                V_t = notional * (fix_leg - flt_leg)
            elif irs_type == ql.VanillaSwap.Receiver:
                V_t = notional * (flt_leg - fix_leg)
            else:
                print("IRS type not specified")
                exit()
            V = np.append(V, V_t, axis=0)
        final_price = np.zeros((1, nsim))
        V = np.append(V, final_price, axis=0)
        return V, realized_R

def portfolio_exposure(available_swaps: list, portfolio_combinations: int, observed_dates: list, observed_yield_curve: list,
                       nsim: int, max_tenor_years: int, param_a: float, param_vola: float):
    """
    ARGS:
        available_swaps (list of InterestRateSwap):     portfolio of InterestRateSwap's.
        portfolio_combinations (int):                   number of different portfolio combinations to create
        observed_dates (list of dates):                 list of dates when the yield curve has been observed.
        observed_yield_curve (yield curve in a list):   list containing the observed yield curve.
        nsim (int):                                     nbr of MC simulations.
        max_tenor_years (int):                          max length for the portfolio in years.
        param_a (float):                                HW1F param mean reversion.
        param_vola (float):                             HW1F param volatility.
    """
    ###+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Interpolate the yield curve for the portfolio life time

    dates = pd.Series(observed_dates)
    start_date = pd.Timestamp(dates[0])
    end_date = start_date + pd.DateOffset(years=max_tenor_years)
    all_dates_pd = pd.DateOffset(days=start_date.day-1) + \
        pd.Series(pd.date_range(start_date - pd.DateOffset(days=start_date.day),
        end_date, freq='MS').tolist())
    all_dates = all_dates_pd.apply(ql.Date().from_date)
    obs_dates = dates.apply(ql.Date().from_date)
    gridpoints = (all_dates_pd - start_date) / np.timedelta64(1, 'Y')
    curve = ql.CubicZeroCurve(obs_dates, observed_yield_curve, ql.ActualActual(), ql.TARGET())
    curve_handle = ql.YieldTermStructureHandle(curve)
    curve.enableExtrapolation()

    # Create Hull-White process with params
    hw_process = ql.HullWhiteProcess(curve_handle, param_a, param_vola)

    max_tenor_in_months = MONTHS_IN_YEAR * max_tenor_years + 1
    nbr_gridpoints = max_tenor_in_months

    rng = ql.GaussianRandomSequenceGenerator(
        ql.UniformRandomSequenceGenerator(nbr_gridpoints - 1, ql.UniformRandomGenerator()))
    seq = ql.GaussianPathGenerator(hw_process, max_tenor_years, nbr_gridpoints - 1, rng, False)

    ###+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Generate short rate paths
    short_rates = short_rate(nsim, seq, nbr_gridpoints)

    ###+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Form portfolios: Let's form N different portfolios from available_swaps

    portfolios = []
    # Uncomment if only one portfolio is wanted
    #portfolios = [random.sample(available_swaps, 3)]
    # portfolios.extend(list(x) for x in combinations(available_swaps, 5))
    # portfolios.extend(list(x) for x in combinations(available_swaps, 4))
    portfolios.extend(list(x) for x in combinations(available_swaps, 3))
    portfolios.extend(list(x) for x in combinations(available_swaps, 2))
    random.shuffle(portfolios)
    # Use all possible combinations if None
    if portfolio_combinations is not None:
        portfolios = random.sample(portfolios, portfolio_combinations)

    ###+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # Do swap pricing under each short rate path

    day_counter = ql.ActualActual()
    zero_rates = [
        curve.zeroRate(date, day_counter, ql.Continuous).rate()
        for date in all_dates
    ]
    fwd_rates = [
        curve.forwardRate(date, date + ql.Period('1d'), day_counter, ql.Simple).rate()
        for date in all_dates
    ]

    # Valuate each available swap
    swap_npvs = {} # base_swap_id as a dict key
    for irs in available_swaps:

        """
        Customise the IRS here: Set possible ranges for values and choose randomly from there.
        available_swaps is taken with deepcopy, so it can be directly modified.
        """
        irs.forward_start_years = random.randrange(0, 7 + 1)
        """
        Supposing fwd start is picked from an uniformal dist., the prob. for a certain number is 0.14.
        Thus, IRS tenor 10 years is possible only in 14% of cases, that's why duplicate tenors 5, 7 and 10 in the list.
        """
        irs_lengths = [3, 5, 5, 7, 7, 7, 10, 10, 10, 10]
        filtered_irs_lengths = list(filter(lambda irs_length:
            irs_length < YIELD_CURVE_LENGTH_YEARS + 1 - irs.forward_start_years, irs_lengths))
        irs.tenor_years = random.choice(filtered_irs_lengths)
        irs.delta_fair_swap_rate = random.randrange(-5, 5 + 1)
        irs.flt_freq = random.choice([3, 6])
        irs.fix_freq = random.choice([3, 6])

        # Adjust rates for IRS lifetime (end adjustment is not needed because of the indexing from start in the 'valuate_irs' function)
        start_adj = irs.forward_start_years * MONTHS_IN_YEAR
        adj_short_rates = short_rates[start_adj:]
        adj_zero_rates = zero_rates[start_adj:]
        adj_fwd_rates = fwd_rates[start_adj:]
        adj_gridpoints = gridpoints[:len(gridpoints) -
            (max_tenor_years - irs.tenor_years - irs.forward_start_years) * MONTHS_IN_YEAR - start_adj]

        irs_values, fair_swap_rate = valuate_irs(irs.swap_type, adj_short_rates, irs.tenor_years, adj_zero_rates,
                                                    adj_fwd_rates, adj_gridpoints, nsim, param_a, param_vola, irs.delta_fair_swap_rate,
                                                    irs.flt_freq, irs.fix_freq, irs.notional)
        # Save fair rate
        irs.fair_swap_rate = fair_swap_rate

        # Pad to have length of maximum swap length (forward start + tenor) in the portfolio
        irs_values_padded = irs_values
        if (irs_values.shape[0] != nbr_gridpoints):
            # Padding is needed
            irs_values_padded = np.pad(irs_values_padded,
                [(start_adj, nbr_gridpoints - irs_values_padded.shape[0] - start_adj), (0, 0)], 'constant')

        # Scale notional and thus also the IRS values
        scaled_notional = random.randrange(1, 5 + 1) # from 1 to 5 million USD
        irs_values_padded = irs_values_padded * scaled_notional

        # Store padded IRS values and scaled notional to dict
        swap_npvs[irs.base_swap_id] = [irs_values_padded, scaled_notional]

    # Then get portfolio exposures
    portfolios_and_exposures = []
    for portfolio in portfolios:
        npv_paths = np.zeros((nbr_gridpoints, nsim))
        for irs in portfolio:
            irs_values_padded = swap_npvs[irs.base_swap_id][0]
            irs.notional = swap_npvs[irs.base_swap_id][1]
            npv_paths = np.add(npv_paths, irs_values_padded)

        # Floor to zero (comes directly from the exposure calculation)
        exposure_paths = np.maximum(npv_paths, 0)

        # Exposure is the mean of the values in different MC sims per a time point
        portfolio_exposure_profile = np.mean(exposure_paths, axis = 1)

        portfolios_and_exposures.append([portfolio, portfolio_exposure_profile])

    return zero_rates, portfolios_and_exposures
