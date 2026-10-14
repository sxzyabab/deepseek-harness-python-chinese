from ..树 import 相对时间#树辅助
from nicegui import ui as 界面

__all__=['项目行','会话行','检索结果行','样式表','展示标题','时间标签']#仅中文公开名

样式表='''#对齐 Rows.module.css
.projectRow,.sessionRow{display:flex;align-items:center;border-radius:var(--dsw-radius-md);padding:0 8px;padding-inline-start:calc(8px + var(--dsh-workspace-indent,0px));cursor:pointer;user-select:none;color:var(--dsw-alias-label-primary)}
.projectRow{height:34px;box-sizing:border-box;gap:6px}
.sessionRow{height:32px;gap:0}
.projectRow:hover,.sessionRow:hover,.sessionRow.selected,.searchResultRow:hover,.searchResultRow.selected{background:var(--dsw-alias-interactive-bg-hover)}
.searchResultRow{display:flex;flex-direction:column;align-items:stretch;width:100%;min-height:48px;box-sizing:border-box;border-radius:var(--dsw-radius-lg);padding:4px 8px;background:transparent;cursor:pointer;text-align:left;color:var(--dsw-alias-label-primary)}
.searchResultHeading{display:flex;align-items:center;min-width:0}
.searchResultMeta{display:flex;align-items:center;gap:6px;min-width:0;margin-left:20px}
.searchResultTitle{flex:0 1 auto;min-width:0;margin-left:4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px;line-height:20px}
button.q-btn.title,button.q-btn.searchResultTitle{background:transparent !important;box-shadow:none !important;color:inherit !important;min-height:0;height:auto;padding:0;font-size:14px;line-height:20px;font-weight:400}
.searchResultWorkspace{flex:none;max-width:40%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;line-height:17px;color:var(--dsw-alias-label-tertiary)}
.searchResultSnippet{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;line-height:17px;color:var(--dsw-alias-label-secondary)}
.slot{flex:none;width:16px;height:20px;display:inline-flex;align-items:center;justify-content:center;color:var(--dsw-alias-label-tertiary)}
.title{overflow:hidden;flex:1;min-width:0;text-overflow:ellipsis;white-space:nowrap;font-size:14px;line-height:20px}
.sessionRow .title{margin:0 6px 0 4px}
.rowActions{display:none;align-items:center;gap:4px}
.projectRow:hover .rowActions,.sessionRow:hover .rowActions,.menuOpen .rowActions{display:inline-flex}
.iconButton{display:grid;place-items:center;width:24px;height:24px;border:none;border-radius:999px;background:transparent;cursor:pointer;color:var(--dsw-alias-label-tertiary)}
.time{color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px;flex:none}
.hoverContent{display:flex;flex-direction:column;gap:4px;max-width:280px}
.hoverTitle{font-weight:510}
.hoverPath,.hoverTime{color:var(--dsw-alias-label-tertiary);font-size:12px;word-break:break-all}
.snippet{color:var(--dsw-alias-label-tertiary);font-size:12px;line-height:18px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
'''#样式表结束

样式已登记=False

def 登记样式():
    '同一段行样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表)
    样式已登记=True

def 展示标题(节点,翻译):#行显示标题
    '空白行用本地化新会话标签'
    return 翻译('session.new') if 节点['blank'] else 节点['title']#标题

def 时间标签(更新于,现在,翻译):#紧凑相对时间
    '本地化紧凑相对时间'
    桶=相对时间(更新于,现在)#结构化桶
    if 桶['unit']=='now':#刚刚
        return 翻译('time.now')#刚刚
    return 翻译('time.'+桶['unit'],{'n':桶['n']})#带量级

def 悬停时间标签(更新于,现在,翻译):#悬停相对时间
    '距离套 ago 模板；now 桶保持裸'
    桶=相对时间(更新于,现在)#结构化桶
    if 桶['unit']=='now':#刚刚
        return 翻译('time.now')#刚刚
    return 翻译('time.ago',{'t':翻译('time.'+桶['unit'],{'n':桶['n']})})#ago

def 行状态点(节点):#行状态点状态
    '待处理交互优先于运行；完成提醒再次之'
    待处理=节点['pendingInteraction'] if 'pendingInteraction' in 节点 else None#待处理
    if 待处理 is not None:
        return 'warning'#警告点
    后代数=节点['runningSubagentCount'] if 'runningSubagentCount' in 节点 else 0#后代数
    if 节点['running'] or 后代数>0:#运行中
        return 'ongoing'#进行中
    if 'completed' in 节点 and 节点['completed']:#未读完成
        return 'done'#完成
    return None#空闲无点

class 项目行:#工作区头行
    '文件夹 + 标题；悬停露出 chevron 与新建'
    def __init__(自身,分组,切换,创建,动作=None,翻译=None):#分组与回调
        '记下分组与回调'
        自身.分组=分组#分组节点
        自身.切换=切换#展开切换
        自身.创建=创建#新建会话
        自身.动作=动作#重命名/删除
        自身.翻译=翻译#文案
        自身.菜单开=False#菜单开关

    def 渲染(自身):#结构树
        '返回项目头行结构树'
        组=自身.分组#分组
        标签=自身.翻译('group.ungrouped') if 组['workspaceId'] is None else 组['label']#标签
        登记样式()
        with 界面.row().classes('projectRow'):
            界面.icon('folder').classes('slot')
            界面.button(标签, on_click=自身.切换).props('flat no-caps align=left').classes('title')
            if isinstance(自身.动作,dict):
                def 开菜单():
                    '打开工作区菜单'
                    自身.处理动作('menu')
                菜单钮=界面.button(自身.翻译('actions.workspace.aria',{'name':标签}), on_click=开菜单)
                with 菜单钮:
                    with 界面.menu():
                        if callable(自身.动作.get('rename')):
                            界面.menu_item(自身.翻译('rename'), on_click=自身.动作['rename'])
                        if callable(自身.动作.get('delete')):
                            界面.menu_item(自身.翻译('delete.workspace'), on_click=自身.动作['delete'])
            界面.button(自身.翻译('actions.newSession.aria',{'name':标签}), on_click=自身.创建)

    def 处理动作(自身,动作):#分发
        '切换、新建或菜单'
        if 动作=='toggle':#展开
            自身.切换()#回调
            return#已处理
        if 动作=='create':#新建
            自身.创建()#回调
            return#已处理
        if 动作=='menu':#菜单
            自身.菜单开=not 自身.菜单开#翻转

class 会话行:#会话树行
    '状态点 + 标题 + 相对时间 + 行菜单'
    def __init__(自身,节点,选中,动作,翻译,现在):#节点与回调
        '记下会话行事实'
        自身.节点=节点#会话节点
        自身.选中=选中#打开会话
        自身.动作=动作#重命名/分叉/归档
        自身.翻译=翻译#文案
        自身.现在=现在#当前时刻
        自身.菜单开=False#菜单

    def 渲染(自身):#结构树
        '返回会话行结构树'
        节点=自身.节点#节点
        标题=展示标题(节点,自身.翻译)#标题
        点=行状态点(节点)#状态点
        登记样式()
        with 界面.row().classes('sessionRow'):
            with 界面.element('span').classes('slot'):
                if 点:
                    界面.icon('error' if 点=='error' else 'circle')
            界面.button(标题, on_click=自身.选中).props('flat no-caps align=left').classes('title')
            if not 节点['blank']:
                界面.label(时间标签(节点['updatedAt'],自身.现在,自身.翻译)).classes('time')
            if isinstance(自身.动作,dict) and not 节点['blank']:
                def 开菜单():
                    '打开行菜单'
                    自身.处理动作('menu')
                菜单钮=界面.button(自身.翻译('actions.session.aria',{'name':标题}), on_click=开菜单)
                with 菜单钮:
                    with 界面.menu():
                        if callable(自身.动作.get('rename')):
                            界面.menu_item(自身.翻译('rename'), on_click=自身.动作['rename'])
                        if callable(自身.动作.get('fork')):
                            界面.menu_item(自身.翻译('menu.fork'), on_click=自身.动作['fork'])
                        if callable(自身.动作.get('archive')):
                            界面.menu_item(自身.翻译('menu.archiveSession'), on_click=自身.动作['archive'])

    def 处理动作(自身,动作):#分发
        '打开或菜单'
        if 动作=='open':#打开
            自身.选中()#回调
            return#已处理
        if 动作=='menu':#菜单
            自身.菜单开=not 自身.菜单开#翻转

class 检索结果行:#检索扁平行
    '标题 + 工作区 + 可选片段'
    def __init__(自身,节点,选中,翻译):#结果节点
        '记下检索行'
        自身.节点=节点#检索节点
        自身.选中=选中#打开
        自身.翻译=翻译#文案

    def 渲染(自身):#结构树
        '返回检索行结构树'
        节点=自身.节点#节点
        点=行状态点(节点)#状态点
        登记样式()
        with 界面.column().classes('searchResultRow'):
            with 界面.row().classes('searchResultHeading'):
                if 点:
                    界面.icon('error' if 点=='error' else 'circle').classes('slot')
                界面.button(节点['title'], on_click=自身.选中).props('flat no-caps align=left').classes('searchResultTitle')
            with 界面.row().classes('searchResultMeta'):
                if isinstance(节点['workspace'],str) and 节点['workspace']!='':
                    界面.label(节点['workspace']).classes('searchResultWorkspace')
                if 'snippet' in 节点 and isinstance(节点['snippet'],str) and 节点['snippet']!='':
                    界面.label(节点['snippet']).classes('searchResultSnippet')

    def 处理动作(自身,动作):#分发
        '打开会话'
        if 动作=='open':#打开
            自身.选中()#回调
