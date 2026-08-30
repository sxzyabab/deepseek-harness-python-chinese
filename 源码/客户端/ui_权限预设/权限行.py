"""权限偏好行：新会话默认预设选择器。



对齐上游 `ui-permission-presets/src/client/PermissionRow.tsx`。公开面仅中文名。

"""

from .展示 import 完全访问预设#完全访问键



__all__=['权限行']#仅中文公开名



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺省#缺席

    return getattr(对象,键,缺省)#属性



class 权限行:#通用设置行组件

    """新会话权限默认选择器；宿主无权限设置时返回 None。"""

    def __init__(自身,属性):#按合成 props 构造

        """记下 props；首次加载描述符。"""

        自身.属性=属性#合成 props

        自身.打开=False#菜单

        自身.确认完全访问=False#风险确认

        自身.已知晓=False#知晓勾选

        加载=取字段(属性,'load')#加载

        if 加载 is not None:#有

            加载()#拉描述符



    def 更新(自身,属性):#props 变更

        """刷新；不可写则关菜单。"""

        自身.属性=属性#最新

        状态=自身.状态()#当前状态

        if 取字段(状态,'writable') and 取字段(状态,'status')!='unavailable':#仍可用

            return#保留菜单

        自身.打开=False#关

        自身.已知晓=False#清

        自身.确认完全访问=False#清



    def 状态(自身):#读设置行快照

        """经 usePermission 选择器。"""

        用权限=取字段(自身.属性,'usePermission')#选择器

        if 用权限 is None:#无

            return {'status':'unavailable','options':[],'currentValue':'','writable':False,'error':None}#不可用

        return 用权限(lambda 快照:快照) or {}#快照



    def 选定(自身,标识):#选定一个预设

        """完全访问先走确认闸。"""

        自身.打开=False#关菜单

        状态=自身.状态()#当前

        if 标识==取字段(状态,'currentValue'):#未变

            return#跳过

        if 标识==完全访问预设:#完全访问

            自身.已知晓=False#重置知晓

            自身.确认完全访问=True#打开确认

            return#等确认

        选择=取字段(自身.属性,'select')#写入

        if 选择 is not None:#有

            选择(标识)#持久化



    def 确认启用完全访问(自身):#确认闸通过

        """写入完全访问。"""

        自身.确认完全访问=False#关确认

        选择=取字段(自身.属性,'select')#写入

        if 选择 is not None:#有

            选择(完全访问预设)#持久化



    def 视图(自身):#读视图模型

        """不可用返回 None。"""

        状态=自身.状态()#快照

        if 取字段(状态,'status')=='unavailable':#不可用

            return None#不渲染

        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案

        选项=取字段(状态,'options') or []#选项

        当前=取字段(状态,'currentValue')#当前值

        选中=None#选中项

        for 项 in 选项:#找标签

            if 取字段(项,'id')==当前:#命中

                选中=项#记下

                break#找到

        忙碌=取字段(状态,'status') in ('loading','saving') or 自身.确认完全访问#忙碌

        标签=取字段(选中,'label')#标签

        if 标签 is None:#无选中

            标签=翻译('loading') if 忙碌 else 翻译('unavailable')#回退

        return {#视图

            'title':翻译('title'),#标题

            'description':取字段(状态,'error') or 翻译('description'),#说明或错误

            'label':标签,#选择器标签

            'options':选项,#选项

            'currentValue':当前,#当前

            'open':自身.打开,#菜单

            'busy':忙碌,#忙碌

            'writable':取字段(状态,'writable'),#可写

            'confirmingFullAccess':自身.确认完全访问,#确认闸

            'acknowledged':自身.已知晓,#知晓

            'confirm':{#确认文案

                'title':翻译('confirm.title'),#标题

                'description':翻译('confirm.description'),#说明

                'acknowledge':翻译('confirm.acknowledge'),#知晓

                'cancel':翻译('confirm.cancel'),#取消

                'enable':翻译('confirm.enable'),#启用

            },#确认结束

        }#视图结束



    def __call__(自身,属性=None):#组件调用形

        """对齐 React 组件调用；返回视图或 None。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.视图()#视图


