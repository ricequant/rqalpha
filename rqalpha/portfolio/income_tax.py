import datetime

from rqalpha.interface import AbstractIncomeTaxCalculator
from rqalpha.environment import Environment
from rqalpha.const import SIDE
from rqalpha.model.trade import Trade
from rqalpha.core.events import EVENT


class CapitalGainsTaxCalculator(AbstractIncomeTaxCalculator):
    """
    计算 `金融商品转让增值税` + `附加税`，具体计算逻辑和公式如下：
    定义: 
        K: 年度可抵余额，K <= 0，每年年初重置为 0；
        R: 月初为 0，当月所有的卖出交易中，卖出价扣除买入价（成本价）后加总的总额
    """
    # FIXME: 开空仓的时候应该怎么计算
    def __init__(self, env: Environment):
        self._K = self._R = 0
        self._env = env
        env.event_bus.add_listener(EVENT.BEFORE_TRADING, self._on_before_trading)

    def calc(self, trading_dt: datetime.date) -> float:
        """
        每月月底进行缴纳税额计算:
        1) R + K > 0: 
            a. tax = ((R + K) * 3%)[增值税] + ((R + K) * 3% * (3.5% + 1.5% + 1%))[附加税]
            b. set R = K = 0
        2) R + K <= 0:
            K = K + R then set R = 0
        3) 特别说明：
            为了方便计算，此处将「增值税」和 「附加税」的费率统一为配置中的 base.capital_gain_tax_rate，用户可以进行自定义
        """
        if not self._is_end_of_month(trading_dt):
            return 0
        taxable_amount = self._R + self._K
        if taxable_amount > 0:
            tax = taxable_amount * self._env.config.base.capital_gain_tax_rate
            self._K = self._R = 0
            return tax
        else:
            self._K = taxable_amount
            self._R = 0
            return 0

    def _is_end_of_month(self, trading_dt: datetime.date) -> bool:
        next_trading_date = self._env.data_proxy.get_next_trading_date(trading_dt)
        return next_trading_date.month != trading_dt.month
    
    def _is_start_of_year(self, trading_dt: datetime.date) -> bool:
        if trading_dt.month != 1: # 减少交易日获取
            return False
        prev_trading_date = self._env.data_proxy.get_previous_trading_date(trading_dt)
        return prev_trading_date.year != trading_dt.year

    def on_trade(self, trade: Trade):
        # 每有一笔卖出交易，则需要更新 self._R
        if trade.side != SIDE.SELL:
            return
        avg_price = self._env.portfolio.get_position(trade.order_book_id, trade.position_direction).avg_price
        self._R += (trade.last_price - avg_price) * trade.last_quantity

    def _on_before_trading(self, event):
        """
        每年年初将 K 重置为 0
        """
        if self._is_start_of_year(event.trading_dt.date()):
            self._K = 0


class DividendTaxCalculator(AbstractIncomeTaxCalculator):
    def calc(self, trading_dt):
        raise NotImplementedError