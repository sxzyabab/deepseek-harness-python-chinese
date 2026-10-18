from ...依赖 import cordis as Cordis#平台种子里的 cordis
from .. import 存储 as 客户端存储#平台种子里的存储
from .. import ui_槽位 as 界面槽位#平台种子里的槽位
from .. import ui_基础界面组件 as 界面基础#平台种子里的基础界面
from .. import ui_停靠套件 as 停靠套件#平台种子里的停靠套件


def 静态模块表():
    '构建启动时交给模块加载器的静态表。键是平台说明符'
    return {#已有 Python 包的那几条。react、zod、react-virtual 没有对应包
        '@deepseek-ai/cordis':Cordis,#cordis
        '@deepseek-ai/dsh-client-store':客户端存储,#存储
        '@deepseek-ai/dsh-client-ui-slots':界面槽位,#槽位
        '@deepseek-ai/dsh-client-ui-primitives':界面基础,#基础界面
        '@deepseek-ai/dsh-client-ui-dockkit':停靠套件,#停靠套件
    }#表结束
