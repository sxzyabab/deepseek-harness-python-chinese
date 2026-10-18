'全应用一条删除结果横幅。pending 不弹'
from ...模块.客户端.通告 import 取握手窗口
from ...ui_基础界面组件.吐司 import 处理吐司
from ...ui_基础界面组件.icons import 图标警告16
from .管理文案 import 管理中文

__all__=['删除提示']

class 删除提示:
    '删成了用成功横幅，没确认用警告。没有通知就什么都不画'
    def __new__(类,属性=None):
        '读当前通知'
        窗口=属性['window'] if isinstance(属性,dict) and 'window' in 属性 else 取握手窗口()
        用=属性.get('useToast')
        if not callable(用):
            return None
        def 原样(当前):
            '横幅状态原样拿出来'
            return 当前
        通知=用(原样)
        if 通知 is None:
            return None
        关掉=属性.get('dismiss')
        if 通知.get('kind')=='deleted':
            return 处理吐司(窗口,{'text':管理中文['toast.deleted'],'tone':'success','onDone':关掉,'window':窗口})
        图=图标警告16({'window':窗口})
        return 处理吐司(窗口,{'text':管理中文['toast.deleteFailed'],'icon':图,'onDone':关掉,'window':窗口})
