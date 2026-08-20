"""插件设置分区与可配置页签、插件卡片壳。

对齐上游 PluginsSettingsSection / ConfigurablePluginsTab / PluginCard。公开面仅中文名。
"""

__all__=['插件设置分区','可配置插件页签','插件卡片']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 插件设置分区:#插件设置分区组件
    """本地化页签围绕功能自有页面。"""
    def __init__(自身,属性):#构造
        """记下 props 与本地页签状态。"""
        自身.属性=属性#合成 props
        自身.活动标识=None#当前页签
        自身.已访问=set()#已挂载过的页签

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 读页签(自身):#读页签行
        """经 useTabs。"""
        用页签=取字段(自身.属性,'useTabs')#选择器
        if 用页签 is None:#无
            return []#空
        return 用页签(lambda 快照:快照) or []#行

    def 渲染(自身):#结构化视图
        """标题、导语、页签与面板。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        渲染槽=取字段(自身.属性,'renderSlot')#槽渲染
        行表=自身.读页签()#页签
        活动=自身.活动标识#请求
        if not any(取字段(行,'id')==活动 for 行 in 行表):#请求消失
            活动=取字段(行表[0],'id') if len(行表)>0 else None#退回首行
        if 活动 is not None:#有活动
            自身.已访问.add(活动)#记访问
        页签面=[]#页签按钮
        for 行 in 行表:#每行
            标识=取字段(行,'id')#id
            页签面.append({#页签
                'id':标识,#id
                'label':取字段(行,'label'),#标签
                'selected':标识==活动,#选中
                'onSelect':(lambda 某=标识:自身.__setattr__('活动标识',某)),#选中
            })#页签结束
        面板=[]#已访问面板
        for 行 in 行表:#每行
            标识=取字段(行,'id')#id
            if 标识!=活动 and 标识 not in 自身.已访问:#未访问且非当前
                continue#跳过
            面板.append({#面板
                'id':标识,#id
                'hidden':标识!=活动,#隐藏非当前
                'content':渲染槽('settings.plugins.tab',{},{'only':标识}) if 渲染槽 is not None else None,#内容
            })#面板结束
        return {#视图
            'type':'plugins-settings-section',#类型
            'title':翻译('title'),#标题
            'intro':翻译('intro'),#导语
            'empty':翻译('empty') if len(行表)==0 else None,#空态
            'tabsLabel':翻译('tabs'),#页签组无障碍
            'tabs':页签面,#页签
            'panels':面板,#面板
            'cssModule':'插件设置分区.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

class 可配置插件页签:#可配置插件页签
    """渲染可编辑设置卡片列表。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """无卡片则空态。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        渲染槽=取字段(自身.属性,'renderSlot')#槽渲染
        卡片数=取字段(自身.属性,'cardCount',0) or 0#卡片数
        if 卡片数==0:#空
            return {'type':'configurable-plugins-tab','empty':翻译('empty')}#空态
        return {#有卡片
            'type':'configurable-plugins-tab',#类型
            'cards':渲染槽('settings.plugin.item',{}) if 渲染槽 is not None else None,#卡片
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

class 插件卡片:#插件卡片壳
    """页眉展开控件与保存脚。"""
    def __init__(自身,属性):#构造
        """记下 props。"""
        自身.属性=属性#合成 props
        自身.展开=False#披露状态

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 渲染(自身):#结构化视图
        """命名空间不可用则不渲染。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        状态=取字段(自身.属性,'state') or {}#表单外壳
        if not 取字段(状态,'available'):#不可用
            return None#不渲染
        标题键=取字段(自身.属性,'titleKey')#标题键
        说明键=取字段(自身.属性,'descriptionKey')#说明键
        标题=翻译(标题键)#标题
        脏=bool(取字段(状态,'dirty'))#脏
        阻塞=not 脏 or bool(取字段(状态,'invalid')) or bool(取字段(状态,'saving'))#保存阻塞
        return {#视图
            'type':'plugin-card',#类型
            'open':自身.展开,#展开
            'title':标题,#标题
            'description':翻译(说明键),#说明
            'unsaved':翻译('unsaved') if 脏 else None,#未保存徽章
            'expandLabel':f"{翻译('collapse' if 自身.展开 else 'expand')}: {标题}",#无障碍
            'onToggle':lambda:自身.__setattr__('展开',not 自身.展开),#切换
            'readOnly':翻译('readOnly') if not 取字段(状态,'writable') else None,#只读
            'failed':翻译('saveFailed') if 取字段(状态,'failed') else None,#失败
            'discardLabel':翻译('discard'),#放弃
            'saveLabel':翻译('saving' if 取字段(状态,'saving') else 'save'),#保存
            'discardDisabled':not 脏 or bool(取字段(状态,'saving')),#放弃禁用
            'saveDisabled':阻塞,#保存禁用
            'onDiscard':取字段(自身.属性,'onDiscard'),#放弃
            'onSave':取字段(自身.属性,'onSave'),#保存
            'children':取字段(自身.属性,'children'),#控件
            'cssModule':'插件卡片.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
