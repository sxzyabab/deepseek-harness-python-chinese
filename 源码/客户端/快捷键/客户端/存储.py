"""显式浏览器与 Desktop 偏好适配器；Desktop 从不回退到浏览器存储。"""
from types import SimpleNamespace as 简易命名空间#存储读写面
from ..协议 import 快捷键持久化#事务协调器

__all__=['快捷键存储键','Web快捷键存储','桌面快捷键存储']#仅中文公开名

快捷键存储键='dsh.keybindings.v1'#浏览器配置文件与同源本地偏好键

def Web快捷键存储(窗口,平台,发布):
    """把 localStorage 与同源外部更新接到共享事务协调器。"""
    本地=窗口.localStorage#同源存储
    def 读():
        """读原文。"""
        return 本地.getItem(快捷键存储键)#可 None
    def 写(原文):
        """整份替换。"""
        本地.setItem(快捷键存储键,原文)#写入
    持久=快捷键持久化(简易命名空间(read=读,write=写),'web',平台,True,发布)#协调器
    def 变更(事件):
        """同源他页写入时重读。"""
        键=事件.key#变更键
        if 键 is None or 键==快捷键存储键:#相关
            持久.读当前()#刷新
    窗口.addEventListener('storage',变更)#监听
    def 获取(定义表):
        """安装目录并读当前。"""
        持久.设定定义(定义表)#目录
        return 持久.读当前()#快照
    def 编辑(编辑,修订):
        """转发编辑。"""
        return 持久.编辑(编辑,修订)#结果
    def 订阅(_监听):
        """Web 侧无推送；返回空拆除。"""
        def 拆除():
            """空拆除。"""
            return None#无事
        return 拆除#拆除器
    def 录制(_活跃):
        """Web 无原生菜单加速器。"""
        return None#完成
    def 拆除():
        """卸监听并停持久化。"""
        窗口.removeEventListener('storage',变更)#卸
        持久.拆除()#停
    return 简易命名空间(#适配器
        get=获取,
        edit=编辑,
        subscribe=订阅,
        recording=录制,
        dispose=拆除,
    )#面结束

def 桌面快捷键存储(窗口):
    """读源作用域 preload 能力；缺桥接为显式配置失败（返回 None）。"""
    桌面=getattr(窗口,'dshDesktop',None)#preload 面
    if 桌面 is None:#无
        return None#缺桥
    return getattr(桌面,'shortcuts',None)#受限 API
