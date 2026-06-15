from datetime import date

from rqalpha.core.events import EVENT


class CapitalGainsTaxMixin:
    """
    计算 `金融商品转让增值税` + `附加税`，具体计算逻辑和公式如下：
    定义:
        annual_deductible_balance: 年度可抵余额 <= 0，每年年初重置为 0；
        monthly_realized_pnl: 月初为 0，当月所有的卖出交易中，卖出价扣除买入价（成本价）后加总的总额
    """
    def __init__(self):
        self._annual_deductible_balance = 0
        self._monthly_realized_pnl = 0
        self._env.event_bus.add_listener(EVENT.BEFORE_TRADING, self._on_before_trading)

    def _on_before_trading(self, event):
        """
        每年年初将 K 重置为 0
        """
        self._trading_dt = event.trading_dt
        if self._is_start_of_year():
            self._annual_deductible_balance = 0

    def calc_capital_gains_tax(self) -> float:
        """
        每月月底进行缴纳税额计算 (tax_basis = annual_deductible_balance + monthly_realized_pnl):
        1) tax_basis > 0:
            a. tax = (tax_basis * 3%)[增值税] + (tax_basis * 3% * (3.5% + 1.5% + 1%))[附加税]
            b. set annual_deductible_balance = monthly_realized_pnl = 0
        2) tax_basis <= 0:
            annual_deductible_balance = tax_basis then set monthly_realized_pnl = 0
        3) 特别说明：
            为了方便计算，此处将「增值税」和 「附加税」的费率统一为配置中的 base.capital_gain_tax_rate，用户可以进行自定义
        """
        if not self._is_end_of_month():
            return 0
        tax_basis = self._annual_deductible_balance + self._monthly_realized_pnl
        if tax_basis > 0:
            tax = tax_basis * self._env.config.base.capital_gain_tax_rate
            self._monthly_realized_pnl = self._annual_deductible_balance = 0
            return tax
        else:
            self._annual_deductible_balance = tax_basis
            self._monthly_realized_pnl = 0
            return 0

    def _is_end_of_month(self) -> bool:
        next_trading_date = self._env.data_proxy.get_next_trading_date(self._trading_dt)
        return next_trading_date.month != self._trading_dt.month

    def _is_start_of_year(self) -> bool:
        if self._trading_dt.month != 1: # 减少交易日获取
            return False
        prev_trading_date = self._env.data_proxy.get_previous_trading_date(self._trading_dt)
        return prev_trading_date.year != self._trading_dt.year

    def _add_monthly_realized_pnl(self, delta_amount: float) -> None:
        self._monthly_realized_pnl += delta_amount
