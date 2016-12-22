import xlwings as xw
from Calibration.TermStructure import *
import pandas as pd
import numpy as np

@xw.func
@xw.arg('x', doc='swap years.')
@xw.arg('y', doc='swap rates in pencentage points.')
@xw.ret(index = False, header=False)
def Bootstrap_TS(x, y):
    """Returns the annual zero rates"""

    ycrv_swap = ycrv_construct(x,y)
    splf = get_spot_rates(ycrv_swap, Thirty360(), TARGET(), 1+len(y)*12)

    return splf


def Calibrate():
    # Collect calibration data from Excel
    sht = xw.Book.caller().sheets['Main']
    rate_df = pd.DataFrame(sht.range('input_rate').expand().value,
                           columns=['Term','Rate']) #Expandable rate table
    swptn_df = pd.DataFrame(sht.range('input_swptn').expand().value,
                            columns=['Weight','Start','Length','Quote']) #Expandable swaption table
    
    #Not yet implemented below, only assume swap rate and Normal swaptions
    swptn_type = sht.range('type_swptn').value
    swap_type = sht.range('type_rate').value

    #Call yield construct
    ycrv_base = ycrv_construct(rate_df['Term'],rate_df['Rate'])

    #Put swaption data into the required format
    CalibrationData = namedtuple("CalibrationData", 
                             "start, length, volatility")
    data_swaptn = [CalibrationData(swptn_df.Start[i], swptn_df.Length[i], swptn_df.Quote[i]) for i in swptn_df.index]

    #Call calibration algorithm
    alpha, sigma, report = calibrate_hw1f(data_swaptn, swptn_type, ycrv_base)
    param_calibrated = [alpha,sigma]

    #Print results to Excel
    sht.range('result_hw1f').value= param_calibrated
    sht.range('result_error').options(index=False,header = False).value=report

if __name__ == '__main__':
    # Expects the Excel file next to this source file, adjust accordingly.
    xw.Book('HW_Calibration_Black.xlsm').set_mock_caller()
    Calibrate()