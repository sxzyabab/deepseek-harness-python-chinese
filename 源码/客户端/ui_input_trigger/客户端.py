"""斜杠触发插件浏览器半边。

对齐上游 `ui-input-trigger/src/client/index.ts`。公开面仅中文名。
挂触发服务，并把菜单视图挂进 input.overlay。
"""
from .文案 import 命名空间,中文,英文#词典
from .菜单视图 import 菜单视图#菜单组件
from .服务 import 触发服务#根服务
from .控制器 import 触发控制器#每会话控制器
from .探测 import 检测触发#纯核心探测
from .菜单归约 import 菜单关闭,铺分组,菜单归约,精确匹配#纯核心归约

__all__=['注入','应用','菜单视图','触发服务','触发控制器','检测触发','菜单关闭','铺分组','菜单归约','精确匹配','命名空间','中文','英文']#仅中文公开名

注入=['sessions','locale']#会话与文案

def 应用(上下文):#安装斜杠触发浏览器半边
    """登记词典与触发服务，并把菜单视图挂进 input.overlay。"""
    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-input-trigger: menu dictionaries')#词典
    上下文.plugin(触发服务)#挂 ctx.inputTriggers
    def 挂菜单(作用域):#等槽位、inputTriggers、会话
        """登记 slash-menu 叠层条目。"""
        触发=作用域.inputTriggers#触发服务
        会话们=作用域.sessions#会话
        def 登记():#登记菜单
            """候选菜单视图。"""
            def 注入面(会话标识):#按会话解析
                """菜单状态与点选/关闭。"""
                作用域会话=会话们.scope(会话标识)#作用域
                if 作用域会话 is None:#无
                    raise Exception('ui-input-trigger: session "'+str(会话标识)+'" resolved no scope')#失败
                控制器=触发.sessionOf(作用域会话)#该会话控制器
                return {#注入面
                    'menu':控制器.menu,#菜单仓
                    'onPick':lambda 来源,下标:控制器.pick(来源,下标),#点选
                    'onDismiss':lambda:控制器.dismiss(),#关闭
                }#结束
            return 作用域.slots.register({#登记
                'name':'conversation.input.overlay',#叠层槽
                'id':'slash-menu',#条目 id
                'order':0,#顺序
                'locale':命名空间,#词表
                'inject':注入面,#注入
            },菜单视图)#组件
        作用域.slots.inject('conversation.input.overlay',登记)#等槽
    上下文.inject(['slots','inputTriggers','sessions'],挂菜单)#注入
