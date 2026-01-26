# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称"米筐科技"）
#
# 除非遵守当前许可，否则不得使用本软件。

import unittest
import pickle
import datetime
import os
from unittest.mock import Mock, patch

from rqalpha.model.instrument import Instrument
from rqalpha.const import INSTRUMENT_TYPE, POSITION_DIRECTION, DEFAULT_ACCOUNT_TYPE, EXCHANGE


class TestInstrument(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """加载测试数据"""
        test_data_path = os.path.join(
            os.path.dirname(__file__), 
            'resources', 
            'test_instruments.pkl'
        )
        with open(test_data_path, 'rb') as f:
            cls.test_data = pickle.load(f)
        
        # 创建模拟的 futures_tick_size_getter
        cls.mock_futures_tick_size_getter = Mock()
        cls.mock_futures_tick_size_getter.return_value = 1.0
        
        # 为每个标的创建测试实例，以 order_book_id 为 key
        cls.instruments = {}
        for data in cls.test_data:
            order_book_id = data.get('order_book_id')
            instrument = Instrument(data, cls.mock_futures_tick_size_getter)
            cls.instruments[order_book_id] = instrument
    
    def test_basic_properties(self):
        """测试基本属性"""
        # 测试股票
        cs_inst = self.instruments['000001.XSHE']
        self.assertEqual(cs_inst.order_book_id, '000001.XSHE')
        self.assertEqual(cs_inst.symbol, '平安银行')
        self.assertEqual(cs_inst.type, INSTRUMENT_TYPE.CS)
        self.assertEqual(cs_inst.exchange, 'XSHE')
        self.assertEqual(cs_inst.round_lot, 100)
        
        # 测试指数
        indx_inst = self.instruments['000001.XSHG']
        self.assertEqual(indx_inst.type, INSTRUMENT_TYPE.INDX)
        self.assertEqual(indx_inst.round_lot, 1)
        
        # 测试期货
        future_inst = self.instruments['A0303']
        self.assertEqual(future_inst.type, INSTRUMENT_TYPE.FUTURE)
        self.assertEqual(future_inst.contract_multiplier, 10.0)
        
    def test_date_properties(self):
        """测试日期相关属性"""
        cs_inst = self.instruments['000001.XSHE']
        
        # 测试上市日期
        self.assertIsInstance(cs_inst.listed_date, datetime.datetime)
        self.assertEqual(cs_inst.listed_date, datetime.datetime(1991, 4, 3))
        
        # 测试退市日期
        self.assertIsInstance(cs_inst.de_listed_date, datetime.datetime)
        
    def test_stock_specific_properties(self):
        """测试股票特有属性"""
        cs_inst = self.instruments['000001.XSHE']
        
        # 测试行业代码
        self.assertEqual(cs_inst.industry_code, 'J66')
        self.assertEqual(cs_inst.industry_name, '货币金融服务')
        
        # 测试板块代码
        self.assertEqual(cs_inst.sector_code, 'Financials')
        self.assertEqual(cs_inst.sector_code_name, '金融')
        
        # 测试板块类型
        self.assertEqual(cs_inst.board_type, 'MainBoard')
        
        # 测试状态
        self.assertEqual(cs_inst.status, 'Active')
        
        # 测试特别处理状态
        self.assertEqual(cs_inst.special_type, 'Normal')
        
        # 测试市场T+N
        self.assertEqual(cs_inst.market_tplus, 1)
        
    def test_future_specific_properties(self):
        """测试期货特有属性"""
        future_inst = self.instruments['A0303']
        
        # 测试合约乘数
        self.assertEqual(future_inst.contract_multiplier, 10.0)
        
        # 测试到期日期
        self.assertEqual(future_inst.maturity_date, datetime.datetime(2003, 3, 14))
        
    def test_round_lot_special_cases(self):
        """测试特殊情况下的交易单位"""
        # 测试科创板股票 - 使用真实数据
        ksh_inst = self.instruments['688001.XSHG']  # 华兴源创，科创板
        # 科创板股票的 round_lot 应该是 1
        self.assertEqual(ksh_inst.round_lot, 1)
        
        # 测试普通主板股票
        mainboard_inst = self.instruments['000001.XSHE']  # 平安银行，主板
        self.assertEqual(mainboard_inst.round_lot, 100)
        
    def test_listing_status_methods(self):
        """测试上市状态相关方法"""
        cs_inst = self.instruments['000001.XSHE']
        
        # 测试在指定日期的状态
        test_date = datetime.datetime(2020, 1, 1)
        
        # 应该已经上市
        self.assertTrue(cs_inst.listed_at(test_date))
        
        # 应该未退市
        self.assertFalse(cs_inst.de_listed_at(test_date))
        
        # 应该在交易
        self.assertTrue(cs_inst.active_at(test_date))
        
        # 测试上市前的日期
        pre_listing_date = datetime.datetime(1990, 1, 1)
        self.assertFalse(cs_inst.listed_at(pre_listing_date))
        self.assertFalse(cs_inst.active_at(pre_listing_date))
        
    def test_trading_hours(self):
        """测试交易时间"""
        cs_inst = self.instruments['000001.XSHE']
        
        trading_hours = cs_inst.trading_hours
        self.assertEqual(len(trading_hours), 2)  # 上午和下午两个时段
        # 验证具体的交易时段
        self.assertEqual(trading_hours[0].start, datetime.time(9, 31))
        self.assertEqual(trading_hours[0].end, datetime.time(11, 30))
        self.assertEqual(trading_hours[1].start, datetime.time(13, 1))
        self.assertEqual(trading_hours[1].end, datetime.time(15, 0))
        
        # 测试连续竞价时间判断
        morning_time = datetime.time(10, 30)  # 上午10:30
        self.assertTrue(cs_inst.during_continuous_auction(morning_time))
        
        afternoon_time = datetime.time(14, 30)  # 下午14:30
        self.assertTrue(cs_inst.during_continuous_auction(afternoon_time))
        
        # 测试非交易时间
        lunch_time = datetime.time(12, 30)  # 午休时间
        self.assertFalse(cs_inst.during_continuous_auction(lunch_time))
        
    def test_call_auction_periods(self):
        """测试集合竞价时段"""
        cs_inst = self.instruments['000001.XSHE']
        
        # 测试开盘集合竞价 (9:25)
        open_auction = datetime.datetime(2020, 1, 1, 9, 25)
        self.assertTrue(cs_inst.during_call_auction(open_auction))
        
        # 测试收盘集合竞价 (14:57)
        close_auction = datetime.datetime(2020, 1, 1, 14, 57)
        self.assertTrue(cs_inst.during_call_auction(close_auction))
        
        # 测试连续竞价时间 (10:30)
        continuous_time = datetime.datetime(2020, 1, 1, 10, 30)
        self.assertFalse(cs_inst.during_call_auction(continuous_time))
        
    def test_account_type(self):
        """测试账户类型"""
        cs_inst = self.instruments['000001.XSHE']
        self.assertEqual(cs_inst.account_type, DEFAULT_ACCOUNT_TYPE.STOCK)
        
        future_inst = self.instruments['A0303']
        self.assertEqual(future_inst.account_type, DEFAULT_ACCOUNT_TYPE.FUTURE)
        
        etf_inst = self.instruments['159001.XSHE']
        self.assertEqual(etf_inst.account_type, DEFAULT_ACCOUNT_TYPE.STOCK)
        
    def test_tick_size(self):
        """测试最小价格变动单位"""
        # 股票
        cs_inst = self.instruments['000001.XSHE']
        self.assertEqual(cs_inst.tick_size(), 0.01)
        
        # 指数
        indx_inst = self.instruments['000001.XSHG']
        self.assertEqual(indx_inst.tick_size(), 0.01)
        
        # ETF
        etf_inst = self.instruments['159001.XSHE']
        self.assertEqual(etf_inst.tick_size(), 0.001)
        
        # LOF
        lof_inst = self.instruments['160105.XSHE']
        self.assertEqual(lof_inst.tick_size(), 0.001)
        
        # 期货
        future_inst = self.instruments['A0303']
        # 应该调用 mock 的 futures_tick_size_getter
        self.assertEqual(future_inst.tick_size(), 1.0)
        self.mock_futures_tick_size_getter.assert_called()
        
    @patch('rqalpha.environment.Environment.get_instance')
    def test_days_from_listed(self, mock_env):
        """测试上市天数计算"""
        mock_trading_dt = datetime.datetime(2020, 1, 1)
        mock_env.return_value.trading_dt = mock_trading_dt
        
        cs_inst = self.instruments['000001.XSHE']
        days = cs_inst.days_from_listed()
        expected_days = (mock_trading_dt.date() - cs_inst.listed_date.date()).days
        self.assertEqual(days, expected_days)
        
    def test_future_continuous_contract_detection(self):
        """测试期货连续合约检测"""
        # 主力连续合约
        self.assertTrue(Instrument.is_future_continuous_contract('A88'))
        self.assertTrue(Instrument.is_future_continuous_contract('IF88'))
        
        # 指数连续合约
        self.assertTrue(Instrument.is_future_continuous_contract('A99'))
        self.assertTrue(Instrument.is_future_continuous_contract('IF99'))
        
        # 普通期货合约
        self.assertFalse(Instrument.is_future_continuous_contract('A2301'))
        self.assertFalse(Instrument.is_future_continuous_contract('IF2301'))
        
        # 非期货代码
        self.assertFalse(Instrument.is_future_continuous_contract('000001.XSHE'))
        
    @patch('rqalpha.environment.Environment.get_instance')
    def test_days_to_expire(self, mock_env):
        """测试到期天数计算"""
        mock_trading_dt = datetime.datetime(2003, 1, 1)
        mock_env.return_value.trading_dt = mock_trading_dt
        
        future_inst = self.instruments['A0303']
        # 对于普通期货合约，应该返回到期天数
        # 但由于测试数据中的期货可能是连续合约，应该返回-1
        days = future_inst.days_to_expire()
        if Instrument.is_future_continuous_contract(future_inst.order_book_id):
            self.assertEqual(days, -1)
        else:
            expected_days = (future_inst.maturity_date.date() - mock_trading_dt.date()).days
            self.assertEqual(days, max(-1, expected_days))
            
    def test_contract_multiplier_validation(self):
        """测试合约乘数验证"""
        # 测试正常的合约乘数 - 使用真实数据
        future_inst = self.instruments['A0303']  # 豆一0303
        self.assertEqual(future_inst.contract_multiplier, 10.0)
        
        # NaN 的合约乘数应该抛出异常 - 需要创建测试数据
        import numpy as np
        nan_data = {
            'order_book_id': 'TEST_NAN',
            'type': 'Future',
            'contract_multiplier': np.nan,
            'symbol': '测试期货NaN'
        }
        with self.assertRaises(RuntimeError) as context:
            Instrument(nan_data, self.mock_futures_tick_size_getter)
        self.assertIn("Contract multiplier", str(context.exception))
            
    def test_date_parsing(self):
        """测试日期解析"""
        # 测试 0000-00-00 日期 - 使用真实数据
        cs_inst = self.instruments['000001.XSHE']  # 平安银行，de_listed_date 为 '0000-00-00'
        self.assertEqual(cs_inst.de_listed_date, Instrument.DEFAULT_DE_LISTED_DATE)
        
        # 测试正常日期解析
        self.assertEqual(cs_inst.listed_date, datetime.datetime(1991, 4, 3))
        
        # 测试 None 日期 - 创建必要的测试数据
        none_date_data = {
            'order_book_id': 'TEST_NONE_DATE',
            'type': 'CS',
            'listed_date': '1991-04-03',
            'de_listed_date': None,
            'symbol': '测试股票None日期'
        }
        inst = Instrument(none_date_data, self.mock_futures_tick_size_getter)
        self.assertEqual(inst.de_listed_date, Instrument.DEFAULT_DE_LISTED_DATE)
        
    def test_missing_attributes(self):
        """测试缺失属性的异常处理"""
        # 创建缺失关键属性的测试数据
        minimal_data = {
            'order_book_id': 'TEST_MINIMAL',
            'type': 'CS',
            'symbol': '最小数据股票'
        }
        inst = Instrument(minimal_data, self.mock_futures_tick_size_getter)
        
        # 访问不存在的股票特有属性应该抛出 AttributeError
        with self.assertRaises(AttributeError) as context:
            _ = inst.sector_code
        self.assertIn("has no attribute 'sector_code'", str(context.exception))
            
        with self.assertRaises(AttributeError) as context:
            _ = inst.industry_code
        self.assertIn("has no attribute 'industry_code'", str(context.exception))
            
        with self.assertRaises(AttributeError) as context:
            _ = inst.board_type
        self.assertIn("has no attribute 'board_type'", str(context.exception))
            
    @patch('rqalpha.environment.Environment.get_instance')    
    def test_calc_cash_occupation(self, mock_env):
        """测试资金占用计算"""
        # 模拟环境和配置
        mock_config = Mock()
        mock_config.base.margin_multiplier = 1.0
        mock_env.return_value.config = mock_config
        
        # 模拟数据代理
        mock_data_proxy = Mock()
        mock_trading_params = Mock()
        mock_trading_params.long_margin_ratio = 0.08
        mock_trading_params.short_margin_ratio = 0.08
        mock_data_proxy.get_futures_trading_parameters.return_value = mock_trading_params
        mock_env.return_value.data_proxy = mock_data_proxy
        
        # 测试股票资金占用
        cs_inst = self.instruments['000001.XSHE']
        cash_occupation = cs_inst.calc_cash_occupation(
            price=10.0, 
            quantity=100, 
            direction=POSITION_DIRECTION.LONG,
            dt=datetime.date(2020, 1, 1)
        )
        self.assertEqual(cash_occupation, 1000.0)  # 10 * 100
        
        # 测试期货资金占用
        future_inst = self.instruments['A0303']
        cash_occupation = future_inst.calc_cash_occupation(
            price=3000.0,
            quantity=1,
            direction=POSITION_DIRECTION.LONG,
            dt=datetime.date(2020, 1, 1)
        )
        expected = 3000.0 * 1 * future_inst.contract_multiplier * 0.08 * 1.0
        self.assertEqual(cash_occupation, expected)
        
    @patch('rqalpha.environment.Environment.get_instance')
    def test_instrument_repr(self, mock_env):
        """测试对象字符串表示"""
        # Mock environment for repr方法中可能访问的属性
        mock_trading_dt = datetime.datetime(2020, 1, 1)
        mock_env.return_value.trading_dt = mock_trading_dt
        
        cs_inst = self.instruments['000001.XSHE']
        repr_str = repr(cs_inst)
        self.assertIsInstance(repr_str, str)
        self.assertTrue(len(repr_str) > 0)
        # 验证包含关键信息
        self.assertIn(cs_inst.order_book_id, repr_str)
        self.assertIn(cs_inst.symbol, repr_str)


if __name__ == '__main__':
    unittest.main()
