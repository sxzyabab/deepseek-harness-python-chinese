"""后台任务列表插件的浏览器半边：贡献一条会话头动作，渲染本会话的 `ctx.jobs` 记录。

数据全部经 `jobsBySession` 列表镜像到达，因此本插件不发 RPC，
除弹出层可见性外不持有自有状态。

对齐上游 `ui-jobs/src/client/index.ts`。公开面仅中文名。
上游 `export type { JobListActionProps }` 属任务列表动作叶（本波跳过 tsx）；
上游 LocaleNamespaceMap 合并：`'job'` → 任务文案键（见文案叶）。
"""
from .文案 import 命名空间,中文,英文#词典：命名空间与中英文案
from ..任务列表动作 import 任务列表动作#头动作组件（客户端/任务列表动作 为空硬缺口，用包根厚叶）

__all__=['注入','应用','任务列表动作']#仅中文公开名；对齐 inject/apply，并再导出登记用组件

注入=['sessions','slots','locale']#会话、槽位与文案

def 应用(上下文):#安装后台任务列表浏览器半边
    """登记词表与头动作。

    @param 上下文 - 客户端根上下文。
    """
    def 登记词典():#登记中英文案
        """登记本插件词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记 zh/en
    上下文.effect(登记词典,'ui-job: dictionaries')#词典生命周期
    def 登记头动作():#登记任务列表动作
        """等会话头动作槽出现再登记。"""
        return 上下文.slots.register({#登记任务列表动作
            'name':'conversation.session.header.actions',#会话头动作槽名
            'id':'job-list',#条目 id
            # 排在子智能体目录之后：会话谱系先读，进程工作后读。
            'order':20,#头动作顺序
            'locale':命名空间,#文案命名空间
        },任务列表动作)#任务列表动作组件
    上下文.slots.inject('conversation.session.header.actions',登记头动作)#等槽出现
