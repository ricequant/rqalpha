# -*- coding: utf-8 -*-
# 版权所有 2019 深圳米筐科技有限公司（下称“米筐科技”）
#
# 除非遵守当前许可，否则不得使用本软件。
#
#     * 非商业用途（非商业用途指个人出于非商业目的使用本软件，或者高校、研究所等非营利机构出于教育、科研等目的使用本软件）：
#         遵守 Apache License 2.0（下称“Apache 2.0 许可”），您可以在以下位置获得 Apache 2.0 许可的副本：http://www.apache.org/licenses/LICENSE-2.0。
#         除非法律有要求或以书面形式达成协议，否则本软件分发时需保持当前许可“原样”不变，且不得附加任何条件。
#
#     * 商业用途（商业用途指个人出于任何商业目的使用本软件，或者法人或其他组织出于任何目的使用本软件）：
#         未经米筐科技授权，任何个人不得出于任何商业目的使用本软件（包括但不限于向第三方提供、销售、出租、出借、转让本软件、本软件的衍生产品、引用或借鉴了本软件功能或源代码的产品或服务），任何法人或其他组织不得出于任何目的使用本软件，否则米筐科技有权追究相应的知识产权侵权责任。
#         在此前提下，对本软件的使用同样需要遵守 Apache 2.0 许可，Apache 2.0 许可与本许可冲突之处，以本许可为准。
#         详细的授权流程，请联系 public@ricequant.com 获取。
import sys
from setuptools import find_packages, setup
import versioneer

requirements = [
    'requests',
    'numpy',
    'pandas >=1.0.5',
    'python-dateutil',
    'six',
    'logbook',
    'click >=7.0.0',
    'jsonpickle',
    'simplejson',
    'PyYAML',
    'tabulate',
    'rqrisk >=1.0.0',
    'h5py',
    'matplotlib >=2.2.0',
    "openpyxl"
]

if sys.version_info < (3, 5):
    requirements.append('typing')

if sys.version_info.major == 2 and sys.version_info.minor == 7:
    requirements.extend([
        "enum34",
        "fastcache",
        "funcsigs",
        "backports.tempfile",
    ])

setup(
    name='rqalpha',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='Ricequant Algorithm Trading System',
    packages=find_packages(exclude=[]),
    author='ricequant',
    author_email='public@ricequant.com',
    license='Apache License v2',
    include_package_date=True,
    package_data={
        'rqalpha': ['*.yml',
                    'examples/*.*', 'examples/data_source/*.*', 'examples/extend_api/*.*',
                    'resource/*.*', 'utils/translations/zh_Hans_CN/LC_MESSAGES/*',
                    "mod/rqalpha_mod_sys_analyser/report/templates/*.xlsx",
                    ],
    },
    url='https://github.com/ricequant/rqalpha',
    install_requires=requirements,
    extra_requires={
        'profiler': ["line_profiler"],
    },
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "rqalpha = rqalpha.__main__:entry_point"
        ]
    },
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires=">=3.6"
)
