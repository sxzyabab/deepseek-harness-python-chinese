"""后台任务列表插件的浏览器半边。

贡献一条会话头动作，渲染本会话的 ctx.jobs 记录。数据全部经 jobsBySession 列表镜像到达。

对齐上游 `ui-jobs/src/client/index.ts`。公开面仅中文名。
"""
from .文案 import 命名空间,中文,英文#词典
from .任务列表动作 import 任务列表动作#任务列表动作组件

__all__=['注入','应用','任务列表动作']#仅中文公开名

注入=['sessions','slots','locale']#会话、槽位与文案

def 应用(上下文):#安装后台任务列表浏览器半边
    """登记词表与头动作。"""
    def 登记词典():#登记中英文案
        """登记本插件词典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.effect(登记词典,'ui-job: dictionaries')#词典生命周期
    def 登记头动作():#登记任务列表动作
        """等会话头动作槽出现再登记。"""
        return 上下文.slots.register({#登记任务列表动作
            'name':'conversation.session.header.actions',#会话头动作槽名
            'id':'job-list',#条目 id
            'order':20,#头动作顺序
            'locale':命名空间,#文案命名空间
        },任务列表动作)#任务列表动作组件
    上下文.slots.inject('conversation.session.header.actions',登记头动作)#等槽出现
