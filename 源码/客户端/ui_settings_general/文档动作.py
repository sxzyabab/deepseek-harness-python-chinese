"""打开本地设置文档的页眉动作。

对齐上游 `ui-settings-general/src/client/SettingsDocumentAction.tsx`。公开面仅中文名。
"""

__all__=['文档动作','样式表']#仅中文公开名

样式表='''#对齐 SettingsDocumentAction.module.css
.action{display:flex;min-width:0;align-items:center;gap:8px}
.error{max-width:180px;overflow:hidden;color:var(--dsw-alias-state-error-primary);font-size:12px;line-height:18px;text-overflow:ellipsis;white-space:nowrap}
'''#样式表结束

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 文档动作:#打开配置文件动作
    """元数据确认有文档后才渲染。"""
    def __init__(自身,属性):#构造
        """记下 props 并触发首读。"""
        自身.属性=属性#合成 props
        控制器=取字段(属性,'controller')#文档仓库
        if 控制器 is not None:#有
            控制器.load()#首读

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 读状态(自身):#读快照
        """经 useSnapshot 选择器。"""
        用快照=取字段(自身.属性,'useSnapshot')#选择器
        if 用快照 is not None:#有
            return 用快照(lambda 快照:快照) or {}#快照
        控制器=取字段(自身.属性,'controller')#仓库
        if 控制器 is None:#无
            return {'status':'idle','opening':False,'error':None}#默认
        return 控制器.store.getSnapshot()#直接读

    def 渲染(自身):#结构化视图
        """未就绪返回 None。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        状态=自身.读状态()#状态
        if 取字段(状态,'status')!='ready':#未就绪
            return None#不渲染
        控制器=取字段(自身.属性,'controller')#仓库
        return {#视图
            'type':'settings-document-action',#类型
            'error':None if 取字段(状态,'error') is None else 翻译('openDocument.error'),#错误文案
            'opening':bool(取字段(状态,'opening')),#打开中
            'label':翻译('openDocument'),#按钮文案
            'onOpen':(lambda:控制器.open()) if 控制器 is not None else None,#打开
            'css':样式表,#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
