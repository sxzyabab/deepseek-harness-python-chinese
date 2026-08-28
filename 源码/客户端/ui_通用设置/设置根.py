"""设置壳根：侧栏底触发器 + 居中模态面板与分区导航。

对齐上游 `ui-settings-general/src/client/SettingsRoot.tsx`。公开面仅中文名。
"""

__all__=['设置根','导航图标','样式表']#仅中文公开名

样式表=None#样式原文落在 设置根.module.css

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 导航图标(分区标识):#按分区 id 选导航字形键
    """未知 id 退回 settings 齿轮。"""
    if 分区标识=='models':#模型
        return 'data'#数据图标
    if 分区标识=='agent-presets':#智能体预设
        return 'agent-preset'#预设图标
    if 分区标识=='plugins':#插件
        return 'personalization'#个性化图标
    return 'settings'#默认齿轮

class 设置根:#设置外壳根组件
    """触发器 + 面板；引导步骤协调。"""
    def __init__(自身,属性):#构造
        """记下 props 与本地查看状态。"""
        自身.属性=属性#合成 props
        自身.打开=False#模态是否打开
        自身.活动标识=None#当前分区 id
        自身.已完成引导=set()#已完成引导步骤

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 关闭(自身):#关闭面板
        """清打开与活动分区。"""
        自身.打开=False#关
        自身.活动标识=None#清

    def 打开分区(自身,标识):#打开到指定分区
        """设活动 id 并打开。"""
        自身.活动标识=标识#分区
        自身.打开=True#开

    def 完成引导步骤(自身,标识):#完成本步
        """记入已完成集合。"""
        自身.已完成引导.add(标识)#记入

    def 读分区行(自身):#读导航行
        """经 useSections。"""
        用分区=取字段(自身.属性,'useSections')#选择器
        if 用分区 is None:#无
            return []#空
        return 用分区(lambda 快照:快照) or []#行

    def 读引导步骤(自身):#读引导步骤
        """经 useOnboardingSteps。"""
        用引导=取字段(自身.属性,'useOnboardingSteps')#选择器
        if 用引导 is None:#无
            return []#空
        return 用引导(lambda 快照:快照) or []#步骤

    def 引导是否活跃(自身):#空 Hero 事实是否激活
        """ready 且当前会话 blank 或无当前。"""
        用会话=取字段(自身.属性,'useSessions')#选择器
        if 用会话 is None:#无
            return False#不激活
        def 选(状态):#选引导活跃
            """投影空 Hero 事实。"""
            if 取字段(状态,'phase')!='ready':#未就绪
                return False#不
            当前=取字段(状态,'current')#当前会话
            if 当前 is None:#无当前
                return True#活跃
            表=取字段(状态,'byId') or {}#表
            项=表.get(当前) if isinstance(表,dict) else 取字段(表,当前)#项
            return 取字段(项,'blank') is True#blank 则活跃
        return bool(用会话(选))#选

    def 渲染面板(自身,行表,渲染槽):#模态面板
        """遮罩 + 导航 + 内容列。"""
        活动=自身.活动标识#请求的活动
        活动行=None#命中行
        for 行 in 行表:#找
            if 取字段(行,'id')==活动:#命中
                活动行=行#记下
                break#找到
        if 活动行 is None and len(行表)>0:#请求 id 已消失
            活动=取字段(行表[0],'id')#退回首行
        else:#有命中或空
            活动=取字段(活动行,'id') if 活动行 is not None else None#活动 id
        导航=[]#导航按钮
        for 行 in 行表:#每行
            标识=取字段(行,'id')#id
            导航.append({#导航单元
                'id':标识,#分区
                'label':取字段(行,'label'),#标签
                'active':标识==活动,#是否当前
                'icon':导航图标(标识),#图标键
                'onSelect':(lambda 某=标识:自身.打开分区(某)),#选中
            })#单元结束
        分区面=None#分区内容
        if 活动 is not None and 渲染槽 is not None:#有活动
            分区面=渲染槽('settings.section',{'close':自身.关闭},{'only':活动})#仅该分区
        return {#面板视图
            'type':'settings-panel',#类型
            'navTitle':渲染槽('settings.header',{}) if 渲染槽 is not None else None,#标题席
            'nav':导航,#导航
            'actions':渲染槽('settings.action',{}) if 渲染槽 is not None else None,#动作席
            'closeLabel':渲染槽('settings.close',{}) if 渲染槽 is not None else None,#关闭标签
            'onClose':自身.关闭,#关闭
            'section':分区面,#分区
        }#面板结束

    def 渲染(自身):#结构化视图
        """触发器 + 可选面板 + 可选引导步骤。"""
        宽=bool(取字段(自身.属性,'wide'))#宽轨
        渲染槽=取字段(自身.属性,'renderSlot')#槽渲染
        行表=自身.读分区行()#导航行
        引导活跃=自身.引导是否活跃()#空 Hero
        if not 引导活跃:#非引导期
            自身.已完成引导=set()#清已完成
        引导步骤表=自身.读引导步骤()#步骤
        当前引导=None#待挂步骤
        if 引导活跃:#引导期
            for 步 in 引导步骤表:#找未完成
                if 取字段(步,'id') not in 自身.已完成引导:#未完成
                    当前引导=步#记下
                    break#找到
        引导面=None#引导渲染
        if 当前引导 is not None and 渲染槽 is not None:#有步骤
            步标识=取字段(当前引导,'id')#id
            引导面=渲染槽('settings.onboarding',{#主人份额
                'stepId':步标识,#步骤
                'complete':lambda 某=步标识:自身.完成引导步骤(某),#完成
                'openSection':自身.打开分区,#打开分区
            },{'only':步标识})#仅该步
        return {#根视图
            'type':'settings-root',#类型
            'wide':宽,#宽轨
            'open':自身.打开,#面板开
            'trigger':渲染槽('settings.trigger',{'wide':宽}) if 渲染槽 is not None else None,#触发器
            'onOpen':lambda:自身.__setattr__('打开',True),#打开
            'panel':自身.渲染面板(行表,渲染槽) if 自身.打开 else None,#面板
            'onboarding':引导面,#引导
            'cssModule':'设置根.module.css',#样式模块名
        }#根结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
