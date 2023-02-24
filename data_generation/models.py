"""
@Authors: Tuomas Vanhala, MongoDB table declarations
@Date: Dec 2022
"""
import uuid
from typing import List
from pydantic import BaseModel, Field

class CustomisableInterestRateSwap(BaseModel):
    """
    To present a base IRS object
    ARGS:
        _id:                        unique identifier for the IRS
        swap_type:                  type of the IRS contract: 'payer' or 'receiver'
        notional:                   notional in millions (USD)
        reference_rate:             name of the underlying reference rate
    """
    _id: str = Field(..., alias='_id')
    swap_type: str
    notional: int
    reference_rate: str

    class Config:
        orm_mode = True
        copy_on_model_validation = False

class YieldCurve(BaseModel):
    """
    To store yield curves
    ARGS:
        _id:                        unique identifier for the yield curve: use 'own' ids to keep track of stored yield curves
        yield_curve:                exposure profile in a list in monthly time grid
    """
    _id: str = Field(..., alias='_id')
    yield_curve: List[float] = []

    class Config:
        orm_mode = True
        copy_on_model_validation = False

class ValuatedInterestRateSwap(BaseModel):
    """
    To store priced IRS for which the fair swap rate and the exposure profile with a certain yield curve are calculated.
    ARGS:
        irs_ref:                    reference to a certain CustomisableInterestRateSwap
        fair_swap_rate:             fair swap rate or the ATM strike
        final_notional:             final notional, having it here enables scaling the exposure profile
        final_forward_start_years:  forward start of the contract in years
        final_tenor_years:          maturity of the contract in years
        final_delta_fair_swap_rate: difference to the fair swap or ATM strike rate in bps
        final_flt_freq:             floating payment frequency in months
        final_fix_freq:             fixed payment frequency in months
    """
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    irs_ref: str
    fair_swap_rate: float
    final_notional: float
    forward_start_years: int
    tenor_years: int
    delta_fair_swap_rate: int
    flt_freq: int
    fix_freq: int

    class Config:
        orm_mode = True
        copy_on_model_validation = False

class Portfolio(BaseModel):
    """
    To portfolio exposure profile.
    ARGS:
        valuated_swaps_ref:         references to ValuatedInterestRateSwap in the portfolio
        exposure_profile:           exposure profile of the portfolio in monthly time grid
    """
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    valuated_swaps_ref: List[str]
    exposure_profile: List[float]

    class Config:
        orm_mode = True
        copy_on_model_validation = False

class MarketScenario(BaseModel):
    """
    Table to combine portfolios to a certain market scenario (HW1F params and yield curve), where the
    valuation happened.
    ARGS:
        HW1F_a:                     Hull-White One-Factor model param alpha
        HW1F_vola:                  Hull-White One-Factor model param volatility
        yield_curve_ref             reference to YieldCurve used for valuating the swaps in the portfolio
        portfolios_ref              references to the portfolios valuated in the certain market scenario
    """
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    HW1F_a: float
    HW1F_vola: float
    yield_curve_ref: str
    portfolios_ref: List[str]

    class Config:
        orm_mode = True
        copy_on_model_validation = False

class Loss(BaseModel):
    """
    To store losses.
    """
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    model: str
    save_timestamp: str
    loss_name: str
    loss: List[float]

    class Config:
        orm_mode = True
        copy_on_model_validation = False

class Error(BaseModel):
    """
    To help in error analysis.
    """
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    model: str
    save_timestamp: str
    mae: float
    portfolio_notional_diff: float
    market_scenario_ref: str
    portfolio_ref: str

    class Config:
        orm_mode = True
        copy_on_model_validation = False
