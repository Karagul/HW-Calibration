from QuantLib import *
import datetime
import numpy as np
import matplotlib.pyplot as plt
from pandas import DataFrame
from collections import namedtuple
import math

# global data
# Here enter the Yield Curve reference Data
calendar = TARGET()
todaysDate = Date(30,9,2016);
Settings.instance().evaluationDate = todaysDate
settlementDate = Date(30,9,2016);

# build rate helpers
fixedLegFrequency = Annual
fixedLegTenor = Period(1,Years)
fixedLegAdjustment = Unadjusted
fixedLegDayCounter = Thirty360()
floatingLegFrequency = Semiannual
floatingLegTenor = Period(6,Months)
floatingLegAdjustment = ModifiedFollowing

def ycrv_construct(
    swap_yrs, swap_rates):
    swap_maturities = [Period(int(y),Years) for y in swap_yrs]
    swapHelpers = [ SwapRateHelper(QuoteHandle(SimpleQuote(r/100)),
                                   m, calendar,
                                   fixedLegFrequency, fixedLegAdjustment,
                                   fixedLegDayCounter, Euribor6M())
                   for r,m in list(zip(swap_rates, swap_maturities)) ]
    return PiecewiseLinearForward(settlementDate, swapHelpers,
                                            Thirty360())

def get_spot_rates(
        yieldcurve, day_count,
        calendar=TARGET(), months=481):
    spots = []
    tenors = []
    ref_date = yieldcurve.referenceDate()
    calc_date = ref_date
    for month in range(0, months):
        yrs = month/12.0
        d = calendar.advance(ref_date, Period(month, Months))
        compounding = Compounded
        freq = Annual
        zero_rate = yieldcurve.zeroRate(yrs, compounding, freq)
        tenors.append(yrs)
        eq_rate = zero_rate.equivalentRate(
            day_count,compounding,freq,calc_date,d).rate()
        spots.append(100*eq_rate)
    return DataFrame(list(zip(tenors, spots)), 
                     columns=["Maturities","Curve"], 
                     index=['']*len(tenors))

def create_swaption_helpers(data, quote_type, index, term_structure, engine):
    swaptions = []
    fixed_leg_tenor = Period(6, Months)
    fixed_leg_daycounter = Actual360()
    floating_leg_daycounter = Actual360()
    for d in data:
        vol_handle = QuoteHandle(SimpleQuote(d.volatility)) 
        if quote_type == 'Normal':
            helper = SwaptionHelper(Period(int(d.start), Years),
                                    Period(int(d.length), Years),
                                    vol_handle,
                                    index,
                                    fixed_leg_tenor,
                                    fixed_leg_daycounter,
                                    floating_leg_daycounter,
                                    term_structure,
                                    CalibrationHelper.RelativePriceError,
                                    nullDouble(),
                                    1.0,
                                    Normal,
                                    0.0
                                    )
        else:
            helper = SwaptionHelper(Period(int(d.start), Years),
                                    Period(int(d.length), Years),
                                    vol_handle,
                                    index,
                                    fixed_leg_tenor,
                                    fixed_leg_daycounter,
                                    floating_leg_daycounter,
                                    term_structure,
                                    CalibrationHelper.RelativePriceError,
                                    nullDouble(),
                                    1.0,
                                    ShiftedLognormal,
                                    0.0
                                    )
        helper.setPricingEngine(engine)
        swaptions.append(helper)
    return swaptions


def calibrate_hw1f(swaption_quotes, swaption_type, termstructure):

    # calibrate procedure
    ycrv = YieldTermStructureHandle(termstructure)
    index = Euribor1Y(ycrv)
    model = HullWhite(ycrv)
    engine = JamshidianSwaptionEngine(model)
    swaptions = create_swaption_helpers(swaption_quotes, swaption_type, index, ycrv, engine)

    optimization_method = LevenbergMarquardt(1.0e-8,1.0e-8,1.0e-8)
    end_criteria = EndCriteria(10000, 100, 1e-6, 1e-8, 1e-8)
    model.calibrate(swaptions, optimization_method, end_criteria)

    a, sigma = model.params()

    return a, sigma
