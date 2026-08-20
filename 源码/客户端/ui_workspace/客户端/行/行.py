"""工作区浏览器树行：项目头、会话行、检索行的展示与菜单。

对齐上游 `ui-workspace/src/client/rows/Rows.tsx`。公开面仅中文名。
"""
from ..树 import 取字段,相对时间#树辅助

__all__=['项目行','会话行','检索结果行','样式表','展示标题','时间标签']#仅中文公开名

样式表='''#对齐 Rows.module.css 核心类
.projectRow,.sessionRow,.searchRow{display:flex;align-items:center;gap:8px;min-height:32px;padding:0 8px;border-radius:8px;cursor:pointer}
.projectRow:hover,.sessionRow:hover,.searchRow:hover{background:var(--dsw-alias-interactive-bg-hover)}
.slot{display:inline-flex;width:16px;height:16px;align-items:center;justify-content:center;flex:none}
.title{overflow:hidden;flex:1;min-width:0;text-overflow:ellipsis;white-space:nowrap;font-size:14px;line-height:24px}
.rowActions{display:none;align-items:center;gap:4px}
.projectRow:hover .rowActions,.sessionRow:hover .rowActions,.menuOpen .rowActions{display:inline-flex}
.iconButton{display:grid;place-items:center;width:24px;height:24px;border:none;border-radius:999px;background:transparent;cursor:pointer;color:var(--dsw-alias-label-tertiary)}
.time{color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px;flex:none}
.hoverContent{display:flex;flex-direction:column;gap:4px;max-width:280px}
.hoverTitle{font-weight:510}
.hoverPath,.hoverTime{color:var(--dsw-alias-label-tertiary);font-size:12px;word-break:break-all}
.snippet{color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
'''#样式表结束

def 展示标题(节点,翻译):#行显示标题
    """空白行用本地化新会话标签。"""
    return 翻译('session.new') if 取字段(节点,'blank') else 取字段(节点,'title')#标题

def 时间标签(更新于,现在,翻译):#紧凑相对时间
    """本地化紧凑相对时间。"""
    桶=相对时间(更新于,现在)#结构化桶
    if 取字段(桶,'unit')=='now':#刚刚
        return 翻译('time.now')#刚刚
    return 翻译('time.'+取字段(桶,'unit'),{'n':取字段(桶,'n')})#带量级

def 悬停时间标签(更新于,现在,翻译):#悬停相对时间
    """距离套 ago 模板；now 桶保持裸。"""
    桶=相对时间(更新于,现在)#结构化桶
    if 取字段(桶,'unit')=='now':#刚刚
        return 翻译('time.now')#刚刚
    return 翻译('time.ago',{'t':翻译('time.'+取字段(桶,'unit'),{'n':取字段(桶,'n')})})#ago

def 行状态点(节点):#行状态点状态
    """待处理交互优先于运行；完成提醒再次之。"""
    待处理=取字段(节点,'pendingInteraction')#待处理
    if 待处理 is not None:#有交互
        return 'warning'#警告点
    if 取字段(节点,'running') or 取字段(节点,'runningSubagentCount',0)>0:#运行中
        return 'ongoing'#进行中
    if 取字段(节点,'completed'):#未读完成
        return 'done'#完成
    return None#空闲无点

class 项目行:#工作区头行
    """文件夹 + 标题；悬停露出 chevron 与新建。"""
    def __init__(自身,分组,切换,创建,动作=None,翻译=None):#分组与回调
        """记下分组与回调。"""
        自身.分组=分组#分组节点
        自身.切换=切换#展开切换
        自身.创建=创建#新建会话
        自身.动作=动作#重命名/删除
        自身.翻译=翻译#文案
        自身.菜单开=False#菜单开关

    def 渲染(自身):#结构树
        """返回项目头行结构树。"""
        组=自身.分组#分组
        标签=自身.翻译('group.ungrouped') if 取字段(组,'workspaceId') is None else 取字段(组,'label')#标签
        return {#行
            'type':'div','class':'projectRow','role':'treeitem','aria-expanded':取字段(组,'expanded'),'onClick':'toggle',#行
            'children':[#子
                {'type':'span','class':'slot folder'},#文件夹槽
                {'type':'span','class':'title','children':[标签]},#标题
                {'type':'span','class':'rowActions','children':[#动作
                    {'type':'button','class':'iconButton','aria-label':自身.翻译('actions.workspace.aria',{'name':标签}),'onClick':'menu'} if 自身.动作 else None,#菜单
                    {'type':'button','class':'iconButton','aria-label':自身.翻译('actions.newSession.aria',{'name':标签}),'onClick':'create'},#新建
                ]},#动作结束
            ],#子结束
        }#行结束

    def 处理动作(自身,动作):#分发
        """切换、新建或菜单。"""
        if 动作=='toggle':#展开
            自身.切换()#回调
            return#已处理
        if 动作=='create':#新建
            自身.创建()#回调
            return#已处理
        if 动作=='menu':#菜单
            自身.菜单开=not 自身.菜单开#翻转

class 会话行:#会话树行
    """状态点 + 标题 + 相对时间 + 行菜单。"""
    def __init__(自身,节点,选中,动作,翻译,现在):#节点与回调
        """记下会话行事实。"""
        自身.节点=节点#会话节点
        自身.选中=选中#打开会话
        自身.动作=动作#重命名/分叉/归档
        自身.翻译=翻译#文案
        自身.现在=现在#当前时刻
        自身.菜单开=False#菜单

    def 渲染(自身):#结构树
        """返回会话行结构树。"""
        节点=自身.节点#节点
        标题=展示标题(节点,自身.翻译)#标题
        点=行状态点(节点)#状态点
        return {#行
            'type':'div','class':'sessionRow','onClick':'open',#行
            'children':[#子
                {'type':'span','class':'slot','children':[{'type':'StateDot','state':点}] if 点 else []},#状态槽
                {'type':'span','class':'title','children':[标题]},#标题
                {'type':'span','class':'time','children':[时间标签(取字段(节点,'updatedAt'),自身.现在,自身.翻译)]} if not 取字段(节点,'blank') else None,#时间
                {'type':'span','class':'rowActions','children':[{'type':'button','class':'iconButton','aria-label':自身.翻译('actions.session.aria',{'name':标题}),'onClick':'menu'}]} if 自身.动作 and not 取字段(节点,'blank') else None,#菜单
            ],#子结束
        }#行结束

    def 处理动作(自身,动作):#分发
        """打开或菜单。"""
        if 动作=='open':#打开
            自身.选中()#回调
            return#已处理
        if 动作=='menu':#菜单
            自身.菜单开=not 自身.菜单开#翻转

class 检索结果行:#检索扁平行
    """标题 + 工作区 + 可选片段。"""
    def __init__(自身,节点,选中,翻译):#结果节点
        """记下检索行。"""
        自身.节点=节点#检索节点
        自身.选中=选中#打开
        自身.翻译=翻译#文案

    def 渲染(自身):#结构树
        """返回检索行结构树。"""
        节点=自身.节点#节点
        点=行状态点(节点)#状态点
        子=[{'type':'span','class':'slot','children':[{'type':'StateDot','state':点}] if 点 else []},{'type':'span','class':'title','children':[取字段(节点,'title')]},{'type':'span','class':'time','children':[取字段(节点,'workspace')]}]#基础
        if 取字段(节点,'snippet') is not None:#有片段
            子.append({'type':'div','class':'snippet','children':[取字段(节点,'snippet')]})#片段
        return {'type':'div','class':'searchRow','onClick':'open','children':子}#行

    def 处理动作(自身,动作):#分发
        """打开会话。"""
        if 动作=='open':#打开
            自身.选中()#回调
