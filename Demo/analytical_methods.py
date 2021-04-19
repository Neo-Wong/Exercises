import os
import time
import uuid
import logging
import pandas as pd

from numpy.linalg import LinAlgError
from statsmodels.tools.sm_exceptions import PerfectSeparationError

from django.conf import settings
from rest_framework.response import Response

from utils.response_code import RespCode, RespMessage, RespData
from utils.serializers import BaseResponse

from .Stata_methods import areg, xtreg, probit, logit, TSLS, TSLS_FIX, convert_to_dummies_list

logger = logging.getLogger('finance')


class CloudAnalysisBase:
    location = settings.SAS_SCRIPT_DIR
    out_dir = settings.CLOUD_OUT_DIR
    analysis_show_name = ""

    def __init__(self, file_path, where_string):
        self.file_path = file_path
        self.where_string = where_string
        self.df = None
        self.return_file = None
        self.out_file_prefix_path = None
        self.out_file = None
        self.out_file_name = None

    def read_csv_file(self):
        """
        判断文件是否存在, 并读取文件数据, 若读取文件有误则返回False.
        :return:
        """
        try:
            file_exist = os.path.isfile(self.file_path)
            if not file_exist:
                print("文件不存在!")
                return False
            self.df = pd.read_csv(self.file_path)
            return True
        except Exception as e:
            print("数据文件有误! 错误:", e)
            return False

    def filter_data(self):
        # 1. 判断文件是否存在, 并读取文件数据.
        read_file_result = self.read_csv_file()
        if not read_file_result:
            return False
        # 2. 根据筛选条件进行分析数据的预筛选
        if self.where_string:
            self.df = self.df.query(self.where_string)
        if self.df.empty:
            print("没有符合筛选条件的数据!!!")
            return False
        return True

    def col_is_na(self, data, check_fields):
        # 检验是否有空列
        for col in check_fields:
            assert False in data[col].isnull().values, "COLUMN_CAN_NOT_BE_NULL"
        return True

    def clean_data(self, fields):
        data_is_ready = self.filter_data()
        assert data_is_ready, "READ_FILE_FAIL"
        assert not self.df.empty, "DATASET_CAN_NOT_BE_EMPTY"
        self.col_is_na(self.df, fields)
        self.df = self.df[fields]
        self.df = self.df.dropna(axis=0, how="all")

    def to_sub_csv(self, res_data):
        self.return_file = {}
        try:
            for title, data in res_data.items():
                try:
                    # print(data)
                    index_list = data.index.names.copy()
                    none_index = index_list.index(None)
                    index_list[none_index] = "Parameters"
                    data.index.set_names(index_list, inplace=True)
                except Exception as e:
                    print(e)
                file_path = "{}_{}.csv".format(self.out_file_prefix_path, title)
                data.to_csv(file_path)
                self.return_file[title] = file_path
            return True
        except Exception as e:
            print(e)
            logger.error("生成csv子结果文件出错, 文件为:{}, 错误为 : {}".format(self.out_file_prefix_path, e))
            # raise Exception(e)
            return False

    def to_sum_csv(self, res_data):
        try:
            full_res = res_data.get(self.analysis_show_name)
            if len(res_data) == 1 and full_res is not None:
                res = pd.concat([full_res])
            else:
                res = pd.concat(res_data, axis=0)
            # print(res)
            # index_list = res.index.names.copy()
            # none_index = index_list.index(None)
            # index_list[none_index] = "Parameters"
            # res.index.set_names(index_list, inplace=True)
            res.to_csv(self.out_file)
            return True
        except Exception as e:
            print(e)
            logger.error("生成csv总结果文件出错, 文件为:{}, 错误为 : {}".format(self.out_file, e))
            # raise Exception(e)
            return False

    def to_res_html(self, res_data):
        self.return_file = {}
        try:
            self.return_file["res_html_table"] = res_data.as_html()
            return True
        except Exception as e:
            print(e)
            logger.error("生成HTML结果时出错, 错误为 : {}".format(e))
            # raise Exception(e)
            return False

    def to_res_csv(self, res_data):
        try:
            csv_string = res_data.as_csv()
            with open(self.out_file, "w") as f:
                f.write(csv_string)
            return True
        except Exception as e:
            print(e)
            logger.error("生成csv结果文件出错, 文件为:{}, 错误为 : {}".format(self.out_file, e))
            # raise Exception(e)
            return False

    def analyse(self):
        return True

    def result(self):
        res = self.analyse()
        if res is True:
            return self.out_file, self.out_file_name, self.return_file

        elif isinstance(res, AssertionError):
            e_str = str(res)
            print(res)
            res_code = getattr(RespCode, e_str)
            res_msg = getattr(RespMessage, e_str)

        elif isinstance(res, ValueError) or isinstance(res, ZeroDivisionError) or isinstance(res, PerfectSeparationError):
            res_code = RespCode.DATASET_MUST_BE_FULL_RANK
            res_msg = RespMessage.DATASET_MUST_BE_FULL_RANK

        elif isinstance(res, LinAlgError):
            e_str = str(res)
            if e_str == "Eigenvalues did not converge":
                res_code = RespCode.EIGENVALUES_DID_NOT_CONVERGE
                res_msg = RespMessage.EIGENVALUES_DID_NOT_CONVERGE
            else:
                res_code = RespCode.DATASET_MUST_BE_FULL_RANK
                res_msg = RespMessage.DATASET_MUST_BE_FULL_RANK

        elif isinstance(res, pd.errors.EmptyDataError):
            e_str = str(res)
            print(res)
            res_code = getattr(RespCode, e_str)
            res_msg = getattr(RespMessage, e_str)
            
        else:
            res_code = RespCode.ANALYSE_ERROR
            res_msg = RespMessage.ANALYSE_ERROR

        response = BaseResponse(res_code, res_msg, res_msg)
        return response


class MethodStatAnalysis(CloudAnalysisBase):
    """
    描述性统计分析方法
    会生成观测值个数、缺失值个数以及均值、标准差、最小值、第一四分位数、中位数、第三四分位数、最大值
        观测值个数(count)、
        缺失值个数(nmiss)、 数据记录中该字段为空的记录个数
        均值(mean)、
        标准差(std)、
        最小值(min)、
        第一四分位数(q1)、
        中位数(median)、
        第三四分位数(q3)、
        最大值(max)

    Parameters
    ----------
    filename : string
    ('home/user3/files/EVA_BETA20200722151938.csv')
        指定要进行描述性统计的文件,空数据集无法报错，输出结果会是没有任何描述性统计的数值栏位，数据集条数没有任何限制.
    var_list : string
    (['BETA1Year1', 'BETA1Year2'])
        要进行的变量名称,输入的变量串，必须为数值型变量，字符型变量不可能进行描述性统计的计算.
    where_list : string, optional
    ( BETA1Year1>0 and  BETA1Year2<0 or  BETA250D1>=0 and  BETA250D2<=0 or  EndDate ^= 0 and  InstitutionID in ('0') or  LastTradingDate not in ('0') )
        where由用户输入条件筛选，预设为空值可以使用交集，联集.
    group_list : list, optional
    (['BETA250D1', 'BETA250D2'])
        描述应统计文件中 进行分组的变量(该分组变量需要事先给定),可以数值变量、字符变量都可以使用,分组变量，可以留空，如果输入了多个分组变量,则会依序  在每个分组变量下进行描述性统计. The default is [].
    bit : int, optional
    (3)
        四舍五入到小数点位数，建议预设为3，然后让用户自己更改.

    Returns
    -------
    bool
        DESCRIPTION.

    """

    analysis_name = "ts_stat"
    analysis_show_name = "Descriptive Statistics"

    def __init__(self, file_path, var_list=None, group_list=None, where_string=None, accuracy=3):
        super().__init__(file_path, where_string)
        self.var_list = var_list
        self.group_list = group_list
        self.accuracy = accuracy
        self.mid_dir = os.path.join(self.analysis_name, time.strftime('%Y%m%d'))
        self.out_dir = os.path.join(self.out_dir, self.mid_dir)
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        self.out_file_prefix = str(uuid.uuid1())
        self.out_file_prefix_path = os.path.join(self.out_dir, self.out_file_prefix)
        self.out_file_name = "".join([self.out_file_prefix, "_{}.csv".format(self.analysis_name)])
        self.out_file = os.path.join(self.out_dir, self.out_file_name)

    def analyse(self):
        try:
            data_is_ready = self.filter_data()
            # if not data_is_ready:
            #     raise Exception("READ_FILE_FAIL")

            # if False not in self.df[self.group_list].isna().values:
            #     raise Exception("GROUP_VAR_CAN_NOT_BE_NULL")
            assert data_is_ready, "READ_FILE_FAIL"
            # print(self.group_list)
            # print(self.df[self.group_list])
            # print(self.df[self.group_list].isna())
            if self.group_list:
                assert False in self.df[self.group_list].isna().values, "GROUP_VAR_CAN_NOT_BE_NULL"

            # 3. 根据要分析的字段列表以及分组条件列表进行组合分析并进行结果的精度调整
            res_data = {}

            # 若有分组参数和分析参数传入
            if self.group_list and self.var_list:
                # 首先根据分组参数进行分组
                group_data = self.df.groupby(self.group_list)
                # 将分组过后的数据集根据要分析的参数进行拆分
                for var in self.var_list:
                    res_data[var] = group_data[var]
            # 否则直接对整个数据集进行操作
            else:
                if self.var_list:
                    res_data[self.analysis_show_name] = self.df[self.var_list]
                else:
                    res_data[self.analysis_show_name] = self.df

            for label, item in res_data.items():
                res = item.describe()
                res = res if self.group_list else res.T
                if self.group_list:
                    total_count = item.size()
                else:
                    total_count = len(item)
                res['nmiss'] = total_count - res['count']
                res = round(res, self.accuracy)
                res_data[label] = res

            sub_res = self.to_sub_csv(res_data)
            sum_res = self.to_sum_csv(res_data)
            assert sub_res and sum_res, "CAN_NOT_MAKE_RESULT_FILE"
            return True

        except Exception as e:
            print(type(e))
            print(e)
            logger.error("描述性统计分析出错, 错误为 : {}".format(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, repr(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, str(e))
            # return response
            return e

    # def result(self):
    #     return (self.out_file, self.out_file_name, self.return_file)


class MethodCorrAnalysis(CloudAnalysisBase):
    """
    相关性统计分析方法


    Parameters
    ----------
    filename : string
    ('home/user3/files/EVA_BETA20200722151938.csv')
        指定要进行描述性统计的文件,空数据集无法报错，输出结果会是没有任何描述性统计的数值栏位，数据集条数没有任何限制.
    var_list : string
    (['BETA1Year1', 'BETA1Year2'])
        要进行的变量名称,输入的变量串，必须为数值型变量，字符型变量不可能进行描述性统计的计算.
    where_list : string, optional
    ( BETA1Year1>0 and  BETA1Year2<0 or  BETA250D1>=0 and  BETA250D2<=0 or  EndDate ^= 0 and  InstitutionID in ('0') or  LastTradingDate not in ('0') )
        where由用户输入条件筛选，预设为空值可以使用交集，联集.
    group_list : list, optional
    (['BETA250D1', 'BETA250D2'])
        描述应统计文件中 进行分组的变量(该分组变量需要事先给定),可以数值变量、字符变量都可以使用,分组变量，可以留空，如果输入了多个分组变量,则会依序  在每个分组变量下进行描述性统计. The default is [].
    bit : int, optional
    (3)
        四舍五入到小数点位数，建议预设为3，然后让用户自己更改.

    Returns
    -------
    bool
        DESCRIPTION.

    """
    analysis_name = "ts_corr"
    analysis_show_name = "Correlation Coefficient Analysis"

    def __init__(self, file_path, var_list=None, group_list=None, where_string=None, accuracy=3):
        super().__init__(file_path, where_string)
        self.var_list = var_list
        self.group_list = group_list
        self.accuracy = accuracy
        self.mid_dir = os.path.join(self.analysis_name, time.strftime('%Y%m%d'))
        self.out_dir = os.path.join(self.out_dir, self.mid_dir)
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        self.out_file_prefix = str(uuid.uuid1())
        self.out_file_prefix_path = os.path.join(self.out_dir, self.out_file_prefix)
        self.out_file_name = "".join([self.out_file_prefix, "_{}.csv".format(self.analysis_name)])
        self.out_file = os.path.join(self.out_dir, self.out_file_name)

    def analyse(self, methods=None):
        try:
            data_is_ready = self.filter_data()
            # if not data_is_ready:
            #     raise Exception("READ_FILE_FAIL")
            assert data_is_ready, "READ_FILE_FAIL"
            if self.group_list:
                assert False in self.df[self.group_list].isna().values, "GROUP_VAR_CAN_NOT_BE_NULL"

            if not methods:
                methods = [
                    "pearson",
                    "kendall",
                    "spearman",
                ]

            res_data = {}

            if self.group_list:
                # 分组
                for m in methods:
                    res_data[m] = round(self.df.groupby(self.group_list)[self.var_list].corr(m), self.accuracy)
            else:
                # 不分组
                for m in methods:
                    res_data[m] = round(self.df[self.var_list].corr(m), self.accuracy)

            sub_res = self.to_sub_csv(res_data)
            sum_res = self.to_sum_csv(res_data)
            # print(sub_res)
            # print(sum_res)
            assert sub_res and sum_res, "CAN_NOT_MAKE_RESULT_FILE"
            return True

        except Exception as e:
            print(type(e))
            print(e)
            logger.error("相关系数分析出错, 错误为 : {}".format(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, repr(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, str(e))
            # return response.data
            return e

    # def result(self):
    #     return (self.out_file, self.out_file_name, self.return_file)


class MethodOLSRegressionWithDummiesAnalysis(CloudAnalysisBase):
    analysis_name = "ols_reg_with_dum"
    analysis_show_name = "OLS Regression With Dummies"

    def __init__(self, file_path, y_var, x_var_list, absorb_var, dummies_var_list, where_string=None, accuracy=3):
        super().__init__(file_path, where_string)
        self.y_var = y_var
        self.x_var_list = x_var_list
        self.absorb_var = absorb_var
        self.dummies_var_list = dummies_var_list
        self.accuracy = accuracy

        self.mid_dir = os.path.join(self.analysis_name, time.strftime('%Y%m%d'))
        self.out_dir = os.path.join(self.out_dir, self.mid_dir)
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        self.out_file_prefix = str(uuid.uuid1())
        self.out_file_prefix_path = os.path.join(self.out_dir, self.out_file_prefix)
        self.out_file_name = "".join([self.out_file_prefix, "_{}.csv".format(self.analysis_name)])
        self.out_file = os.path.join(self.out_dir, self.out_file_name)

    def analyse(self):
        try:
            fields = [self.y_var, *self.x_var_list, self.absorb_var, *self.dummies_var_list]

            self.clean_data(fields)

            # convert the year column to dummies and append to data
            self.df, dummies_var_list = convert_to_dummies_list(self.df, self.dummies_var_list)
            self.x_var_list = self.x_var_list + dummies_var_list

            add_intercept = True
            res = areg(self.df, y_var=self.y_var, X_vars=self.x_var_list, absorb_var=self.absorb_var,
                       add_intercept=add_intercept)

            res_data = res.summary
            html_res = self.to_res_html(res_data)
            csv_res = self.to_res_csv(res_data)
            assert html_res and csv_res, "CAN_NOT_MAKE_RESULT_FILE"

            # return self.result()
            return True

        except Exception as e:
            print(type(e))
            print(e)
            logger.error("OLS Regression With Dummies回归分析出错, 错误为 : {}".format(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, repr(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, str(e))
            # return response.data
            return e

    # def result(self):
    #     return self.out_file, self.out_file_name, self.return_file


class MethodLinearFixedEffectModelAnalysis(CloudAnalysisBase):
    analysis_name = "lin_fix_eff"
    analysis_show_name = "Linear Fixed Effect Model"

    def __init__(self, file_path, y_var, x_var_list, fix1, fix2=None, where_string=None, accuracy=3):
        super().__init__(file_path, where_string)
        self.y_var = y_var
        self.x_var_list = x_var_list
        self.fix1 = fix1
        self.fix2 = fix2
        self.accuracy = accuracy

        self.mid_dir = os.path.join(self.analysis_name, time.strftime('%Y%m%d'))
        self.out_dir = os.path.join(self.out_dir, self.mid_dir)
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        self.out_file_prefix = str(uuid.uuid1())
        self.out_file_prefix_path = os.path.join(self.out_dir, self.out_file_prefix)
        self.out_file_name = "".join([self.out_file_prefix, "_{}.csv".format(self.analysis_name)])
        self.out_file = os.path.join(self.out_dir, self.out_file_name)

    def analyse(self):
        try:
            fields = [self.y_var, *self.x_var_list, self.fix1]
            if self.fix2:
                fields.append(self.fix2)

            self.clean_data(fields)

            add_intercept = True
            res = xtreg(self.df, y_var=self.y_var, other_X_vars=self.x_var_list, fix1=self.fix1, fix2=self.fix2,
                        add_intercept=add_intercept)

            res_data = res.summary
            html_res = self.to_res_html(res_data)
            csv_res = self.to_res_csv(res_data)
            assert html_res and csv_res, "CAN_NOT_MAKE_RESULT_FILE"

            # return self.result()
            return True

        except Exception as e:
            print(type(e))
            print(e)
            logger.error("Linear Fixed Effect Model回归分析出错, 错误为 : {}".format(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, repr(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, str(e))
            # return response.data
            return e


class MethodProbitModelWithDummiesAnalysis(CloudAnalysisBase):
    analysis_name = "probit_with_dum"
    analysis_show_name = "Probit Model With Dummies"

    def __init__(self, file_path, y_var, x_var_list, dummies_var_list, where_string=None, accuracy=3):
        super().__init__(file_path, where_string)
        self.y_var = y_var
        self.x_var_list = x_var_list
        self.dummies_var_list = dummies_var_list
        self.accuracy = accuracy

        self.mid_dir = os.path.join(self.analysis_name, time.strftime('%Y%m%d'))
        self.out_dir = os.path.join(self.out_dir, self.mid_dir)
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        self.out_file_prefix = str(uuid.uuid1())
        self.out_file_prefix_path = os.path.join(self.out_dir, self.out_file_prefix)
        self.out_file_name = "".join([self.out_file_prefix, "_{}.csv".format(self.analysis_name)])
        self.out_file = os.path.join(self.out_dir, self.out_file_name)

    def analyse(self):
        try:
            fields = [self.y_var, *self.x_var_list, *self.dummies_var_list]

            self.clean_data(fields)

            # convert the year column to dummies and append to data
            self.df, dummies_var_list = convert_to_dummies_list(self.df, self.dummies_var_list)

            self.x_var_list = self.x_var_list + dummies_var_list
            add_intercept = True
            res = probit(self.df, y_var=self.y_var, X_vars=self.x_var_list, add_intercept=add_intercept)

            res_data = res.summary()
            html_res = self.to_res_html(res_data)
            csv_res = self.to_res_csv(res_data)
            assert html_res and csv_res, "CAN_NOT_MAKE_RESULT_FILE"

            # return self.result()
            return True

        except Exception as e:
            print(type(e))
            print(e)
            logger.error("Probit Model With Dummies回归分析出错, 错误为 : {}".format(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, repr(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, str(e))
            # return response.data
            return e


class MethodLogitModelWithDummiesAnalysis(CloudAnalysisBase):
    analysis_name = "logit_with_dum"
    analysis_show_name = "Logit Model With Dummies"

    def __init__(self, file_path, y_var, x_var_list, dummies_var_list, where_string=None, accuracy=3):
        super().__init__(file_path, where_string)
        self.y_var = y_var
        self.x_var_list = x_var_list
        self.dummies_var_list = dummies_var_list
        self.accuracy = accuracy

        self.mid_dir = os.path.join(self.analysis_name, time.strftime('%Y%m%d'))
        self.out_dir = os.path.join(self.out_dir, self.mid_dir)
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        self.out_file_prefix = str(uuid.uuid1())
        self.out_file_prefix_path = os.path.join(self.out_dir, self.out_file_prefix)
        self.out_file_name = "".join([self.out_file_prefix, "_{}.csv".format(self.analysis_name)])
        self.out_file = os.path.join(self.out_dir, self.out_file_name)

    def analyse(self):
        try:
            fields = [self.y_var, *self.x_var_list, *self.dummies_var_list]

            self.clean_data(fields)

            # convert the year column to dummies and append to data
            self.df, dummies_var_list = convert_to_dummies_list(self.df, self.dummies_var_list)

            self.x_var_list = self.x_var_list + dummies_var_list
            add_intercept = True
            res = logit(self.df, y_var=self.y_var, X_vars=self.x_var_list, add_intercept=add_intercept)

            res_data = res.summary()
            html_res = self.to_res_html(res_data)
            csv_res = self.to_res_csv(res_data)
            assert html_res and csv_res, "CAN_NOT_MAKE_RESULT_FILE"

            # return self.result()
            return True

        except Exception as e:
            print(type(e))
            print(e)
            logger.error("Logit Model With Dummies回归分析出错, 错误为 : {}".format(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, repr(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, str(e))
            # return response.data
            return e


class MethodTobitModelWithDummiesAnalysis(CloudAnalysisBase):
    pass


class MethodTwoStatgeLinearRegressionsWithDummiesAnalysis(CloudAnalysisBase):
    analysis_name = "ts_lin_reg_with_dum"
    analysis_show_name = "Two Statge Linear Regressions With Dummies"

    def __init__(self, file_path, y_var, x_var_list, first_y, IV_list, dummies_var_list, where_string=None, accuracy=3):
        super().__init__(file_path, where_string)
        self.y_var = y_var
        self.x_var_list = x_var_list
        self.first_y = first_y
        self.IV_list = IV_list
        self.dummies_var_list = dummies_var_list
        self.accuracy = accuracy

        self.mid_dir = os.path.join(self.analysis_name, time.strftime('%Y%m%d'))
        self.out_dir = os.path.join(self.out_dir, self.mid_dir)
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        self.out_file_prefix = str(uuid.uuid1())
        self.out_file_prefix_path = os.path.join(self.out_dir, self.out_file_prefix)
        self.out_file_name = "".join([self.out_file_prefix, "_{}.csv".format(self.analysis_name)])
        self.out_file = os.path.join(self.out_dir, self.out_file_name)

    def analyse(self):
        try:
            fields = [self.y_var, *self.x_var_list, self.first_y, *self.IV_list, *self.dummies_var_list]

            self.clean_data(fields)

            # convert the year column to dummies and append to data
            self.df, dummies_var_list = convert_to_dummies_list(self.df, self.dummies_var_list)

            self.x_var_list = self.x_var_list + dummies_var_list
            add_intercept = True
            res = TSLS(self.df, y_var=self.y_var, firsts_y=self.first_y, X_vars=self.x_var_list, IV=self.IV_list,
                       add_intercept=add_intercept)

            res_data = res.summary()
            html_res = self.to_res_html(res_data)
            csv_res = self.to_res_csv(res_data)
            assert html_res and csv_res, "CAN_NOT_MAKE_RESULT_FILE"

            # return self.result()
            return True

        except Exception as e:
            print(type(e))
            print(e)
            logger.error("Two Statge Linear Regressions With Dummies回归分析出错, 错误为 : {}".format(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, repr(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, str(e))
            # return response.data
            return e


class MethodTwoStatgeFixedEffectModelAnalysis(CloudAnalysisBase):
    analysis_name = "ts_fix_eff"
    analysis_show_name = "Two Statge Fixed Effect Model"

    def __init__(self, file_path, y_var, x_var_list, first_y, IV_list, fix1, fix2, where_string=None, accuracy=3):
        super().__init__(file_path, where_string)
        self.y_var = y_var
        self.x_var_list = x_var_list
        self.first_y = first_y
        self.IV_list = IV_list
        self.fix1 = fix1
        self.fix2 = fix2
        self.accuracy = accuracy

        self.mid_dir = os.path.join(self.analysis_name, time.strftime('%Y%m%d'))
        self.out_dir = os.path.join(self.out_dir, self.mid_dir)
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)
        self.out_file_prefix = str(uuid.uuid1())
        self.out_file_prefix_path = os.path.join(self.out_dir, self.out_file_prefix)
        self.out_file_name = "".join([self.out_file_prefix, "_{}.csv".format(self.analysis_name)])
        self.out_file = os.path.join(self.out_dir, self.out_file_name)

    def analyse(self):
        try:
            fields = [self.y_var, *self.x_var_list, self.first_y, *self.IV_list, self.fix1]
            if self.fix2:
                fields.append(self.fix2)

            self.clean_data(fields)

            add_intercept = False
            res = TSLS_FIX(self.df, y_var=self.y_var, first_y=self.first_y, X_vars=self.x_var_list, IV=self.IV_list,
                           fix1=self.fix1, fix2=self.fix2, add_intercept=add_intercept)

            res_data = res.summary()
            html_res = self.to_res_html(res_data)
            csv_res = self.to_res_csv(res_data)
            assert html_res and csv_res, "CAN_NOT_MAKE_RESULT_FILE"

            # return self.result()
            return True

        except Exception as e:
            print(type(e))
            print(e)
            logger.error("Two Statge Fixed Effect Model回归分析出错, 错误为 : {}".format(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, repr(e))
            # response = BaseResponse(RespCode.ERROR, RespMessage.ERROR, str(e))
            # return response.data
            return e
