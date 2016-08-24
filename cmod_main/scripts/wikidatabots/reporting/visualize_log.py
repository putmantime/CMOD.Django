__author__ = 'andra'

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


log_dataframe = pd.read_csv('/tmp/WD_bot_run-2016-01-03_20:29.log', quotechar="\"", skipinitialspace=True, header=None)
print(log_dataframe)
print(log_dataframe.columns)
print(log_dataframe[0])
output = log_dataframe[6].plot()
fig = output.get_figure()
fig.savefig('/tmp/figure2.pdf')