# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from rqalpha.const import COMMISSION_TYPE, MARGIN_TYPE


CN_FUTURE_INFO = {
    "SM": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 3.0
        }
    },
    "SR": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 3.0
        }
    },
    "JD": {
        "hedge": {
            "short_margin_ratio": 0.08,
            "close_commission_today_ratio": 0.00015,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 0.00015,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.08,
            "open_commission_ratio": 0.00015
        },
        "speculation": {
            "short_margin_ratio": 0.08,
            "close_commission_today_ratio": 0.00015,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 0.00015,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.08,
            "open_commission_ratio": 0.00015
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.00015,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 0.00015,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 0.00015
        }
    },
    "T": {
        "hedge": {
            "short_margin_ratio": 0.02,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.02,
            "open_commission_ratio": 3.0
        },
        "speculation": {
            "short_margin_ratio": 0.02,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.02,
            "open_commission_ratio": 3.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.02,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.02,
            "open_commission_ratio": 3.0
        }
    },
    "P": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.5
        }
    },
    "BB": {
        "hedge": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 5e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 0.0001,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 0.0001
        },
        "speculation": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 5e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 0.0001,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 0.0001
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 5e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 0.0001,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 0.0001
        }
    },
    "RM": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 1.5
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 1.5
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.5,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 1.5
        }
    },
    "RS": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 2.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 2.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 2.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.0
        }
    },
    "J": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 3e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 6e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 6e-05
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 3e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 6e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 6e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 3e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 6e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 6e-05
        }
    },
    "RI": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 2.5,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 2.5,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 2.5,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.5
        }
    },
    "ER": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 2.5,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 2.5,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 2.5,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.5
        }
    },
    "L": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.0
        }
    },
    "PP": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 2.5e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 5e-05
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 2.5e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 5e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 2.5e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 5e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 5e-05
        }
    },
    "SN": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 3.0
        }
    },
    "I": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 3e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 6e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 6e-05
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 3e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 6e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 6e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 3e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 6e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 6e-05
        }
    },
    "TA": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 3.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 3.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 3.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 3.0
        }
    },
    "AL": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 3.0
        }
    },
    "ZC": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 4.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 4.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 4.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 4.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 4.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 4.0
        }
    },
    "TC": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 4.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 4.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 4.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 4.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 4.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 4.0
        }
    },
    "LR": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 3.0
        }
    },
    "RU": {
        "hedge": {
            "short_margin_ratio": 0.08,
            "close_commission_today_ratio": 4.5e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4.5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.08,
            "open_commission_ratio": 4.5e-05
        },
        "speculation": {
            "short_margin_ratio": 0.08,
            "close_commission_today_ratio": 4.5e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4.5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.08,
            "open_commission_ratio": 4.5e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 4.5e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4.5e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 4.5e-05
        }
    },
    "M": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 1.5
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 1.5
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.5,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 1.5
        }
    },
    "TF": {
        "hedge": {
            "short_margin_ratio": 0.012,
            "close_commission_today_ratio": 3.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.012,
            "open_commission_ratio": 3.0
        },
        "speculation": {
            "short_margin_ratio": 0.012,
            "close_commission_today_ratio": 3.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.012,
            "open_commission_ratio": 3.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.012,
            "close_commission_today_ratio": 3.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.012,
            "open_commission_ratio": 3.0
        }
    },
    "MA": {
        "hedge": {
            "short_margin_ratio": 0.07,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.4,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.07,
            "open_commission_ratio": 1.4
        },
        "speculation": {
            "short_margin_ratio": 0.07,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.4,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.07,
            "open_commission_ratio": 1.4
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.4,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 1.4
        }
    },
    "ME": {
        "hedge": {
            "short_margin_ratio": 0.07,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.4,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.07,
            "open_commission_ratio": 1.4
        },
        "speculation": {
            "short_margin_ratio": 0.07,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.4,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.07,
            "open_commission_ratio": 1.4
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.4,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 1.4
        }
    },
    "WR": {
        "hedge": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 4e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 4e-05
        },
        "speculation": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 4e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 4e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 4e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 4e-05
        }
    },
    "RB": {
        "hedge": {
            "short_margin_ratio": 0.06,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4.5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.06,
            "open_commission_ratio": 4.5e-05
        },
        "speculation": {
            "short_margin_ratio": 0.06,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4.5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.06,
            "open_commission_ratio": 4.5e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4.5e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 4.5e-05
        }
    },
    "C": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.2,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 1.2
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.2,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 1.2
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.2,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 1.2
        }
    },
    "JR": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 3.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 3.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 3.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 3.0
        }
    },
    "SF": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 3.0
        }
    },
    "OI": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.5
        }
    },
    "RO": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.5
        }
    },
    "CF": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 4.3,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 4.3
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 4.3,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 4.3
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 4.3,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 4.3
        }
    },
    "BU": {
        "hedge": {
            "short_margin_ratio": 0.07,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 3e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.07,
            "open_commission_ratio": 3e-05
        },
        "speculation": {
            "short_margin_ratio": 0.07,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 3e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.07,
            "open_commission_ratio": 3e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 3e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 3e-05
        }
    },
    "JM": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 3e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 6e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 6e-05
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 3e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 6e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 6e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 3e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 6e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 6e-05
        }
    },
    "IH": {
        "hedge": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 0.000115,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2.5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 2.5e-05
        },
        "speculation": {
            "short_margin_ratio": 0.4,
            "close_commission_today_ratio": 0.0023,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2.3e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.4,
            "open_commission_ratio": 2.3e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 0.000115,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2.5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 2.5e-05
        }
    },
    "FG": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 3.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 3.0
        }
    },
    "PM": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 5.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 5.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 5.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 5.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 5.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 5.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 5.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 5.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 5.0
        }
    },
    "FB": {
        "hedge": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 5e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 0.0001,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 0.0001
        },
        "speculation": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 5e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 0.0001,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 0.0001
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 5e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 0.0001,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 0.0001
        }
    },
    "CS": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 1.5
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 1.5
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 1.5,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 1.5
        }
    },
    "B": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 2.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 2.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 2.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.0
        }
    },
    "IC": {
        "hedge": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 0.000115,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2.5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 2.5e-05
        },
        "speculation": {
            "short_margin_ratio": 0.4,
            "close_commission_today_ratio": 0.0023,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2.3e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.4,
            "open_commission_ratio": 2.3e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 0.000115,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2.5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 2.5e-05
        }
    },
    "WH": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.5
        }
    },
    "WS": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.5
        }
    },
    "FU": {
        "hedge": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 2e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 2e-05
        },
        "speculation": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 2e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 2e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 2e-05,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2e-05
        }
    },
    "AU": {
        "hedge": {
            "short_margin_ratio": 0.06,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 10.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.06,
            "open_commission_ratio": 10.0
        },
        "speculation": {
            "short_margin_ratio": 0.06,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 10.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.06,
            "open_commission_ratio": 10.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 10.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 10.0
        }
    },
    "CU": {
        "hedge": {
            "short_margin_ratio": 0.08,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2.5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.08,
            "open_commission_ratio": 2.5e-05
        },
        "speculation": {
            "short_margin_ratio": 0.08,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2.5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.08,
            "open_commission_ratio": 2.5e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2.5e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.5e-05
        }
    },
    "V": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.0
        }
    },
    "Y": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.5
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.5,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.5
        }
    },
    "AG": {
        "hedge": {
            "short_margin_ratio": 0.08,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.08,
            "open_commission_ratio": 5e-05
        },
        "speculation": {
            "short_margin_ratio": 0.08,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.08,
            "open_commission_ratio": 5e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 5e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 5e-05
        }
    },
    "PB": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 4e-05
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 4e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 4e-05
        }
    },
    "IF": {
        "hedge": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 0.000115,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2.5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 2.5e-05
        },
        "speculation": {
            "short_margin_ratio": 0.4,
            "close_commission_today_ratio": 0.0023,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2.3e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.4,
            "open_commission_ratio": 2.3e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.2,
            "close_commission_today_ratio": 0.000115,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 2.5e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.2,
            "open_commission_ratio": 2.5e-05
        }
    },
    "A": {
        "hedge": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.0
        },
        "speculation": {
            "short_margin_ratio": 0.05,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.05,
            "open_commission_ratio": 2.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 2.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 2.0
        }
    },
    "NI": {
        "hedge": {
            "short_margin_ratio": 0.07,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 6.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.07,
            "open_commission_ratio": 6.0
        },
        "speculation": {
            "short_margin_ratio": 0.07,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 6.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.07,
            "open_commission_ratio": 6.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 6.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 6.0
        }
    },
    "HC": {
        "hedge": {
            "short_margin_ratio": 0.06,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.06,
            "open_commission_ratio": 4e-05
        },
        "speculation": {
            "short_margin_ratio": 0.06,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4e-05,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.06,
            "open_commission_ratio": 4e-05
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_MONEY,
            "close_commission_ratio": 4e-05,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 4e-05
        }
    },
    "ZN": {
        "hedge": {
            "short_margin_ratio": 0.06,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.06,
            "open_commission_ratio": 3.0
        },
        "speculation": {
            "short_margin_ratio": 0.06,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": MARGIN_TYPE.BY_MONEY,
            "long_margin_ratio": 0.06,
            "open_commission_ratio": 3.0
        },
        "arbitrage": {
            "short_margin_ratio": 0.0,
            "close_commission_today_ratio": 0.0,
            "commission_type": COMMISSION_TYPE.BY_VOLUME,
            "close_commission_ratio": 3.0,
            "margin_type": None,
            "long_margin_ratio": 0.0,
            "open_commission_ratio": 3.0
        }
    }
}

