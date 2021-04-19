import pandas as pd
import numpy as np
from statsmodels.regression.linear_model import OLS
from statsmodels.regression.linear_model import RegressionResults
from linearmodels.panel.model import PanelOLS
from statsmodels.discrete.discrete_model import Probit
from statsmodels.discrete.discrete_model import Logit
from statsmodels.sandbox.regression.gmm import IV2SLS
from statsmodels.regression.linear_model import OLSResults  # get_robustcov_results
# from .tobit import *
import statsmodels.api as sm


def convert_to_dummies(categorical_var):
    """
    This function converts a categorical variable to several dummy variables.
    Inputs.
    --------
    categorical_var:1darray of floats, should only consist of categorical values.
    var_name:str, the name of the var.


    Outputs.
    ---------
    dummies:pd.DataFrame, each column is a dummy variable. The column names are
            [var1,var2,var3,...]

    Example use.
    -------------
    data = pd.read_csv("./sample_data/OLS_dataset3.csv")
    dummy_vars = convert_to_dummies(data.year)

    """
    levels = list(set(categorical_var))
    levels.sort()
    dummies = pd.DataFrame()
    for i in range(0, len(levels)):
        dummies[str(levels[i])] = (categorical_var == levels[i]).astype(int)

    return dummies


def convert_to_dummies_list(data, categorical_var_list):
    """
    改进convert_to_dummies方法, 使得可以直接根据传进来的categorical_var_list转化dummies参数
    --------
    data: pd.DataFrame类型, 数据集.
    categorical_var_list: List类型, dummies变量字段列表.
    var_name: str类型, dummies字段名.


    Outputs.
    ---------
    data: pd.DataFrame, 经过处理的数据集, 把dummies变量加入到原数据集中.
    dummies_var_list: List类型, dummies变量字段列表.


    Example use.
    -------------
    data = pd.read_csv("./sample_data/OLS_dataset3.csv")
    dummies_var_list = ["year",...]
    data, dummies_var_list = convert_to_dummies_list(data, dummies_var_list)

    """
    dummies_var_list = []
    for categorical_var in categorical_var_list:
        tmp = data[categorical_var]
        levels = list(set(tmp))
        levels.sort()
        dummies = pd.DataFrame()
        for i in range(0, len(levels)):
            res = (tmp == levels[i])
            dummies[str(levels[i])] = res.astype(int)
        data = pd.concat([data, dummies], axis=1)
        dummies_var = list(dummies.columns)
        dummies_var_list += dummies_var[1:]

    return data, dummies_var_list


def areg(df, y_var, X_vars, absorb_var, add_intercept=True):
    """
    This function replicates areg in STATA.

    Inputs.
    ---------
    df:pd.DataFrame, the data for OLS.
    y_var:str, the column name of the dependent variable
    X_vars:list of str, the list of explanatory variable names （column names in df）
    g_var:str, the name of the column (varible) to be absorbed.
          The g_var column in df should be only contain categorical values (
          df中g_var列应只含有离散值，可以是str,float或者int，比如公司名，公司代码，年份，
          数值不可以是连续变量的值，如温度，股票回报等等。如果数值是连续变量的值，程序包也会执行，
          但模型不具有经济学意义).

    Outputs.
    ---------
    res:obj

    """
    new_df = df.copy()
    # new_df = df.dropna()

    new_df['time_index'] = 1.0
    new_df['entity_index'] = new_df[absorb_var]

    new_df = new_df.set_index(['entity_index', 'time_index'])  # entity first, and then year

    # 因变量
    y = new_df[y_var]

    # 解释变量集合
    if add_intercept:
        new_df['intercept'] = 1.0
        X = new_df[['intercept'] + X_vars]
    else:
        X = new_df[X_vars]

    #  weights: 权重变量,暂时没用; entity_effects: 把g_var转为多个dummy variables,然后将它们加入解释变量集合; time_effects: 忽视time index
    areg = PanelOLS(dependent=y, exog=X, weights=None, entity_effects=True, time_effects=False, singletons=False,
                    drop_absorbed=True)
    res = areg.fit()
    return res


def xtreg(df, y_var, other_X_vars, fix1, fix2=None, add_intercept=True):
    """
    This function replicates xtreg in STATA, for linear fixed effect model.
    至少有一个固定效应变量，至多只能有两个。

    Inputs.
    ---------
    df:pd.DataFrame, the data for OLS.
    y_var:str, the column name of the dependent variable
    other_X_vars:list of str, the list of explanatory variable names （除固定效应变量之外的解释变量列表）
    fix1:str, the column name of the first fix effect variable （第一个固定效应变量名）
    fix2:str or None, the column name of the second fix effect variable (if there is one) （第二个固定效应变量名）

    Outputs.
    ---------
    res:obj

    """
    new_df = df.copy()
    new_df = new_df.dropna()

    if fix2 is None:
        # new_df.dropna(subset=[fix1], inplace=True)
        fix2 = 'time_index'
        fix2_effect = False
        new_df[fix2] = 1.0
    else:
        # new_df.dropna(subset=[fix1, fix2], inplace=True)
        fix2_effect = True

    new_df = new_df.set_index([fix1, fix2])  # entity first, and then year
    y = new_df[y_var]

    if add_intercept:
        new_df['intercept'] = 1.0
        X = new_df[['intercept'] + other_X_vars]
    else:
        X = new_df[other_X_vars]

    xtreg = PanelOLS(dependent=y, exog=X, weights=None, entity_effects=True, time_effects=fix2_effect,
                     other_effects=None, drop_absorbed=True)
    res = xtreg.fit()
    return res


def probit(df, y_var, X_vars, add_intercept=True):
    """
    This function replicates probit in STATA, for probit model.
    至少有一个固定效应变量，至多只能有两个。
    被解释变量y为0-1变量时，模型才有意义

    Inputs.
    ---------
    df:pd.DataFrame, the data for OLS.
    y_var:str, the column name of the dependent variable, 被解释变量y应为0-1变量
    X_vars:list of str, the list of explanatory variable names

    Outputs.
    ---------
    res:obj

    """
    new_df = df.copy()
    new_df = new_df.dropna()
    y = new_df[y_var]

    if add_intercept:
        new_df['intercept'] = 1.0
        X = new_df[['intercept'] + X_vars]
    else:
        X = new_df[X_vars]

    probit_mod = Probit(endog=y, exog=X, check_rank=True, missing="drop")
    res = probit_mod.fit(start_params=None, method='newton', maxiter=35, full_output=1, disp=1, callback=None)

    return res


def logit(df, y_var, X_vars, add_intercept=True):
    """
    This function replicates probit in STATA, for probit model.
    至少有一个固定效应变量，至多只能有两个。
    y变量应为0-1变量。

    Inputs.
    ---------
    df:pd.DataFrame, the data for OLS.
    y_var:str, the column name of the dependent variable
    X_vars:list of str, the list of explanatory variable names

    Outputs.
    ---------
    res:obj

    """
    new_df = df.copy()
    new_df = new_df.dropna()
    y = new_df[y_var]

    if add_intercept:
        new_df['intercept'] = 1.0
        X = new_df[['intercept'] + X_vars]
    else:
        X = new_df[X_vars]

    logit_mod = Logit(endog=y, exog=X, check_rank=True, missing="drop")
    res = logit_mod.fit(start_params=None, method='newton', maxiter=35, full_output=1, disp=1, callback=None)

    return res


def TSLS(df, y_var, firsts_y, X_vars, IV, add_intercept=True):
    """
    This function replicates probit in STATA, for probit model.
    至少有一个固定效应变量，至多只能有两个。

    Inputs.
    ---------
    df:pd.DataFrame, the data for OLS.
    y_var:str, the column name of the dependent variable
    firsts_y:str, the column name of the first-stage y
    X_vars:list of str, the list of explanatory variable names
    IV:list str, the list of instrument variable names

    Outputs.
    ---------
    res:obj

    """
    new_df = df.copy()
    new_df = new_df.dropna()
    y = new_df[y_var]

    if add_intercept:
        new_df['intercept'] = 1.0
        x = ['intercept'] + [firsts_y] + X_vars
        # new_df.dropna(subset=temp, inplace=True)
        X = new_df[x]
        #         X = new_df[['intercept'] + [firsts_y] + X_vars]
        X_vars = ['intercept'] + X_vars
    else:
        x = [firsts_y] + X_vars
        # new_df.dropna(subset=temp, inplace=True)
        X = new_df[x]
        # X = new_df[[firsts_y] + X_vars]

    # IV and all x that is not explained by the IV
    TSLS_mod = IV2SLS(endog=y, exog=X, instrument=new_df[X_vars + IV])
    res = TSLS_mod.fit()

    return res


def demean(dat):
    return dat - np.mean(dat, axis=0)


def TSLS_FIX(df, y_var, first_y, X_vars, IV, fix1, fix2=None, add_intercept=True):
    """
    This function replicates probit in STATA, for probit model.
    至少有一个固定效应变量，至多只能有两个。

    Inputs.
    ---------
    df:pd.DataFrame, the data for OLS.
    y_var:str, the column name of the dependent variable
    first_y:str, the column name of the first-stage y
    X_vars:list of str, the list of explanatory variable names
    IV:list str, the list of instrument variable names
    fix1:str, the column name of the first fix effect variable
    fix2:str, the column name of the second fix effect variable

    Outputs.
    ---------
    res:obj

    """
    new_df = df.copy()
    new_df = new_df.dropna()

    if fix2 is None:
        #         data.dropna(subset=[fix1], inplace=True)
        fix2 = 'time_index'
        #         new_df = new_df[[y_var] + [first_y] + X_vars + IV + [fix1]]
        new_df = new_df.groupby(fix1).apply(demean)
    else:
        #         data.dropna(subset=[fix1,fix2], inplace=True)
        #         new_df = new_df[[y_var] + [first_y] + X_vars + IV + [fix1, fix2]]
        new_df = new_df.groupby([fix1, fix2]).apply(demean)

    y = new_df[y_var]

    if add_intercept:
        new_df['intercept'] = 1.0
        X = new_df[['intercept'] + [first_y] + X_vars]
        X_vars = ['intercept'] + X_vars
    else:
        X = new_df[[first_y] + X_vars]

    # IV and all x that is not explained by the IV
    TSLS_mod = IV2SLS(endog=y, exog=X, instrument=new_df[X_vars + IV])

    res = TSLS_mod.fit()
    return res
