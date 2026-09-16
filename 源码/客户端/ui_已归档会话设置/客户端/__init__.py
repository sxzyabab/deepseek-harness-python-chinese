from .文案 import 命名空间,中文,英文#词表
from .已归档会话分区 import 已归档会话分区#页组件

__all__=['注入','应用','已归档会话分区','命名空间','中文','英文']#仅中文公开名

注入=['slots','locale','uiWorkspace']#槽、文案、工作区

def 应用(上下文):#贡献已归档会话页
    """把已归档会话分区登记进设置。"""
    def 登记词典():#登记中英文案
        """把词表写进 locale。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词典,'ui-settings-unarchive-sessions: dictionaries')#词典
    翻译=上下文.locale.bind(命名空间)#绑定
    def 注入面():#取消归档
        """只暴露 unarchive。"""
        def 取消归档(会话标识):#恢复
            """调用工作区命令。"""
            return 上下文.uiWorkspace.unarchiveSession(会话标识)#写入
        return {'unarchive':取消归档}#注入
    def 页签标签():#导航文案
        """分区导航标签。"""
        return 翻译('nav')#标签
    def 登记分区():#登记 settings.section
        """登记已归档会话分区。"""
        return 上下文.slots.register({#席位
            'name':'settings.section',#槽名
            'id':'archived-sessions',#分区 id
            'order':25,#顺序
            'label':页签标签,#标签
            'locale':命名空间,#文案
            'inject':注入面,#注入
        },已归档会话分区)#组件
    上下文.slots.inject('settings.section',登记分区)#等槽

inject=注入#框架槽
apply=应用#框架槽
