# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），
#         您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、
#         本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，
#         否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。

from math import isfinite
from numbers import Real
from typing import AbstractSet, Any, Dict, FrozenSet, Mapping, Optional, Tuple

from rqalpha.environment import Environment
from rqalpha.interface import AbstractMod
from rqalpha.const import INSTRUMENT_TYPE
from rqalpha.utils.exception import patch_user_exc
from rqalpha.utils import INST_TYPE_IN_STOCK_ACCOUNT, RqAttrDict
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_log

from .deciders import (
    CommissionProfile,
    ETFTransactionCostDecider,
    FuturesTransactionCostDecider,
    StockTransactionCostDecider,
)


_PROFILE_FIELDS: FrozenSet[str] = frozenset({"commission_rate", "min_commission"})
_ETF_SUBTYPES: FrozenSet[str] = frozenset({"bond", "money"})


def _to_mapping(value: Any, path: str) -> Mapping[str, Any]:
    if isinstance(value, RqAttrDict):
        value = value.convert_to_dict()
    if not isinstance(value, Mapping):
        raise ValueError("{} must be a mapping".format(path))
    return value


def _validate_keys(
    value: Mapping[str, Any], allowed_keys: AbstractSet[str], path: str
) -> None:
    unknown_keys = set(value) - set(allowed_keys)
    if unknown_keys:
        raise ValueError("unknown {} config field(s): {}".format(path, ", ".join(sorted(unknown_keys))))


def _validate_profile(profile: Any, path: str) -> Dict[str, Optional[float]]:
    profile = _to_mapping(profile, path)
    _validate_keys(profile, _PROFILE_FIELDS, path)
    result: Dict[str, Optional[float]] = {}
    for field in _PROFILE_FIELDS:
        value = profile.get(field)
        if value is None:
            result[field] = None
            continue
        if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or value < 0:
            raise ValueError("{}.{} must be a finite non-negative number or None".format(path, field))
        result[field] = float(value)
    return result


def _overlay_profile(
    base: CommissionProfile, override: Mapping[str, Optional[float]], path: str
) -> CommissionProfile:
    commission_rate = override.get("commission_rate")
    min_commission = override.get("min_commission")
    profile = CommissionProfile(
        commission_rate=base.commission_rate if commission_rate is None else commission_rate,
        min_commission=base.min_commission if min_commission is None else min_commission,
    )
    if profile.commission_rate == 0 and profile.min_commission > 0:
        raise ValueError("{}.min_commission must be 0 when commission_rate is 0".format(path))
    return profile


def _resolve_etf_commission(
    etf_commission: Any, stock_profile: CommissionProfile
) -> Tuple[CommissionProfile, Dict[str, CommissionProfile]]:
    etf_commission = _to_mapping(etf_commission, "etf_commission")
    _validate_keys(etf_commission, {"default", "subtypes"}, "etf_commission")

    default_config = _validate_profile(etf_commission.get("default", {}), "etf_commission.default")
    default_profile = _overlay_profile(stock_profile, default_config, "etf_commission.default")

    subtype_configs = _to_mapping(etf_commission.get("subtypes", {}), "etf_commission.subtypes")
    _validate_keys(subtype_configs, _ETF_SUBTYPES, "etf_commission.subtypes")
    subtype_profiles: Dict[str, CommissionProfile] = {}
    for subtype in _ETF_SUBTYPES:
        config = _validate_profile(
            subtype_configs.get(subtype, {}), "etf_commission.subtypes.{}".format(subtype)
        )
        subtype_profiles[subtype] = _overlay_profile(
            default_profile, config, "etf_commission.subtypes.{}".format(subtype)
        )
    return default_profile, subtype_profiles


class TransactionCostMod(AbstractMod):
    def start_up(self, env: Environment, mod_config: RqAttrDict) -> None:
        stock_commission_multiplier = mod_config.stock_commission_multiplier
        futures_commission_multiplier = mod_config.futures_commission_multiplier

        if stock_commission_multiplier < 0 or mod_config.tax_multiplier < 0:
            raise patch_user_exc(ValueError(_(u"invalid commission multiplier or tax multiplier"
                                              u" value: value range is [0, +∞)")))

        stock_min_commission = mod_config.cn_stock_min_commission
        if stock_min_commission is not None:
            user_log.warning(
                "cn_stock_min_commission is deprecated, use stock_min_commission instead"
            )
        else:
            stock_min_commission = mod_config.stock_min_commission

        stock_profile = CommissionProfile(
            commission_rate=0.0008 * stock_commission_multiplier,
            min_commission=stock_min_commission,
        )
        default_etf_profile, etf_subtype_profiles = _resolve_etf_commission(
            getattr(mod_config, "etf_commission", {}), stock_profile
        )

        for instrument_type in INST_TYPE_IN_STOCK_ACCOUNT:
            if instrument_type in {INSTRUMENT_TYPE.PUBLIC_FUND, INSTRUMENT_TYPE.ETF}:
                continue
            env.set_transaction_cost_decider(instrument_type, StockTransactionCostDecider(
                stock_commission_multiplier, stock_min_commission,
                mod_config.tax_multiplier, mod_config.pit_tax, env.event_bus
            ))

        env.set_transaction_cost_decider(INSTRUMENT_TYPE.ETF, ETFTransactionCostDecider(
            default_etf_profile,
            etf_subtype_profiles,
        ))

        env.set_transaction_cost_decider(INSTRUMENT_TYPE.FUTURE, FuturesTransactionCostDecider(
            futures_commission_multiplier
        ))

    def tear_down(self, code: int, exception: Optional[Exception] = None) -> None:
        pass
