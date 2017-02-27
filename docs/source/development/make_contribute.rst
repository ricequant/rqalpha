.. _development-make-contribute:

==================
如何贡献代码
==================

.. _Ricequant: https://www.ricequant.com/algorithms
.. _RQAlpha Github: https://github.com/ricequant/rqalpha
.. _master 分支: https://github.com/ricequant/rqalpha
.. _develop 分支: https://github.com/ricequant/rqalpha/tree/develop
.. _How to Contribute to an Open Source Project on GitHub: https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github

RQAlpha 是一个持续更新和维护的项目，它支持 `Ricequant`_ 平台的策略回测、实盘交易，因此合并代码是一件非常严谨的事情，这并不意味着我们不希望接受来自开源社区的贡献，反之，我们更愿意拥抱开源，加快产品的迭代、功能的完善、问题的修复。如果您愿意加入进来，共同维护和开发 RQAlpha，请阅读以下文档，希望以下内容可以解答您的疑惑，给您带来帮助。

RQAlpha 所有的开发工作都将会在 `RQAlpha Github`_ 上进行，无论是 团队成员还是个人贡献者都需要以同样的方式进行代码提交。

.. _development-make-contribute-branch-management:

分支管理
--------------------------

`master 分支`_ 为最新稳定版本，只有团队成员在发布新版本时才会将充分测试的 `develop 分支`_ 合并到 `master 分支`_ 中。

`develop 分支`_ 为最新开发版本，提交代码需要保证通过所有的测试。

如果是修复bug，需要额外创建 `bug/xxx` 分支来进行代码提交，测试通过后提交 pull request 并等待 team member 的 merge check.

如果是增加feature, 需要额外创建 `feature/xxx` 分支来进行代码提交，并完善文档和测试脚本，测试通过后提交 pull request 并等待 team member 的 merge check.

Bugs
--------------------------

如果您在使用的过程中发现了Bug, 请通过 `https://github.com/ricequant/rqalpha/issues` 来提交并描述相关的问题，您也可以在这里查看其它的issue，通过解决这些issue来贡献代码。

Pull Request
--------------------------

如果您是第一次通过 `Pull Request` 提交代码， 您可以参考 `How to Contribute to an Open Source Project on GitHub`_ 来了解 Contribute Workflow.

我们会认真审核您的 `Pull Request`, 并给出如下三种回应:

*   `Merge Pull Request` : 合并您的代码进入 `develop 分支`_
*   `Pending` : 如果发现有一些地方还需要完善，我们会给出具体的完善建议，并等待您的进一步提交。
*   `Won't Merge` : 如果发现您的 `Pull Request` 不适合合并，我们会给出具体的解释，并关闭相应的issue。

Contribute Workflow
--------------------------

在提交 `Pull Request` 前，请确保您是按照如下流程进行代码的开发和测试的:

1.  Fork `RQAlpha Github`_
2.  基于 `develop 分支`_ 创建新的分支，分支命名需要遵循 :ref:`development-make-contribute-branch-management` 中的命名规则。
3.  如果您修改了代码，请保证通过测试。
4.  如果您修改了API, 请保证文档也同时更新。
5.  如果您增加了新的功能，请保证增加测试代码，

Development Workflow
--------------------------

To Be Continued

Style Guide
--------------------------

PEP8

License
--------------------------

Apache License 2.0


