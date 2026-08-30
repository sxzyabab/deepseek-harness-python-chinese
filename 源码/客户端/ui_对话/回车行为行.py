"""忙碌时 Enter 偏好的通用设置行。

对齐上游 `ui-conversation/src/client/settings/EnterBehaviorRow.tsx`。公开面仅中文名。
"""

__all__=['回车行为行','选项表']#仅中文公开名

选项表=(#忙碌 Enter 选项
    {'id':'queue','label':'settings.enter.queue'},#排队
    {'id':'steer','label':'settings.enter.steer'},#插话
)#选项结束

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 回车行为行:#通用设置行
    """忙碌态纯 Enter 行为选择器。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props
        自身.打开=False#菜单开

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 读行为(自身):#读当前偏好
        """经 useBusyEnter。"""
        用=取字段(自身.属性,'useBusyEnter')#选择器
        if 用 is not None:#有
            return 用(lambda 值:值) or 'queue'#行为
        钩=取字段(自身.属性,'hooks') or {}#hooks
        仓=取字段(钩,'busyEnter')#仓库
        if 仓 is not None and hasattr(仓,'getSnapshot'):#有
            return 仓.getSnapshot()#行为
        return 'queue'#默认

    def 渲染(自身):#结构化视图
        """标题、说明与选择器。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        行为=自身.读行为()#当前
        设=取字段(自身.属性,'setBusyEnter')#写入
        选中标签='settings.enter.queue' if 行为=='queue' else 'settings.enter.steer'#标签键
        return {#视图
            'type':'enter-behavior-row',#类型
            'title':翻译('settings.enter.title'),#标题
            'description':翻译('settings.enter.description'),#说明
            'open':自身.打开,#菜单
            'selectedId':行为,#选中
            'selectedLabel':翻译(选中标签),#选中文案
            'items':[{'id':项['id'],'label':翻译(项['label'])} for 项 in 选项表],#菜单项
            'onToggle':lambda:自身.__setattr__('打开',not 自身.打开),#切换菜单
            'onClose':lambda:自身.__setattr__('打开',False),#关菜单
            'onSelect':(lambda 标识:(自身.__setattr__('打开',False),设(标识) if 设 is not None else None)),#选择
            'cssModule':'回车行为行.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
