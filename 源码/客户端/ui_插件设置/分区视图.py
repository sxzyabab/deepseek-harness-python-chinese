import importlib.resources as 包资源
from nicegui import ui as 界面
from .异常 import 页面失败文案

__all__=['插件设置分区']#仅中文公开名

def _读样式(文件名):
    '读当前包内样式。失败时异常文案只有样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath(文件名).read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None

def _去注释(原文):
    '去掉块注释，避免注释里的花括号打断规则'
    出=[]
    下标=0
    长度=len(原文)
    while 下标<长度:
        if 原文.startswith('/*',下标):
            止=原文.find('*/',下标+2)
            if 止<0:
                break
            下标=止+2
            continue
        出.append(原文[下标])
        下标+=1
    return ''.join(出)

def _前缀一片(片,根):
    '同一元素与后代都能命中'
    片=片.strip()
    if 片=='':
        return ''
    return '.'+根+' '+片+', .'+根+片

def _前缀选择器(选择器,根):
    '逗号分隔的每一段都挂上根'
    条=[]
    for 片 in 选择器.split(','):
        已=_前缀一片(片,根)
        if 已!='':
            条.append(已)
    return ', '.join(条)

def _挂规则(文,根):
    '普通规则挂根；媒体查询递归；关键帧保持原样'
    出=[]
    下标=0
    长度=len(文)
    while 下标<长度:
        while 下标<长度 and 文[下标].isspace():
            下标+=1
        if 下标>=长度:
            break
        起=下标
        while 下标<长度 and 文[下标]!='{':
            下标+=1
        if 下标>=长度:
            break
        选择器=文[起:下标].strip()
        下标+=1
        深度=1
        体起=下标
        while 下标<长度 and 深度>0:
            if 文[下标]=='{':
                深度+=1
            elif 文[下标]=='}':
                深度-=1
            下标+=1
        体=文[体起:下标-1]
        if 选择器.startswith('@keyframes') or 选择器.startswith('@font-face'):
            出.append(选择器+'{'+体+'}')
        elif 选择器.startswith('@media') or 选择器.startswith('@container') or 选择器.startswith('@supports'):
            出.append(选择器+'{'+_挂规则(体,根)+'}')
        elif 选择器!='':
            出.append(_前缀选择器(选择器,根)+'{'+体+'}')
    return '\n'.join(出)

界面.add_css(_挂规则(_去注释(_读样式('插件设置分区.module.css')),'插件设置分区根'),shared=True)

def _键名(事件):
    '从界面事件取出键名'
    参数=事件.args if hasattr(事件,'args') else None#事件参数
    if isinstance(参数,dict) and 'key' in 参数:
        return 参数['key']#键
    return None#没有

class 插件设置分区:#插件设置分区组件
    '本地化页签围绕功能自有页面。空页签由本分区写回退句'
    def __init__(自身,属性):#构造
        '记下 props 与本地页签状态。槽位只调用构造，键齐了就画。'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成 props
        自身.活动标识=None#当前页签
        自身.已访问=set()#已挂载过的页签
        if 't' in 自身.属性 and 'renderSlot' in 自身.属性:
            自身.渲染()#键齐才画

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 选页签(自身,标识):#切换活动页签
        '记下当前页签'
        自身.活动标识=标识#选中

    def 读页签(自身):#读页签行
        '经 useTabs；旧注入仍可读 hooks.tabs'
        用=自身.属性['useTabs'] if 'useTabs' in 自身.属性 else None#选择器
        if callable(用):#已绑定
            快照=用(lambda 值:值)#整表
            return 快照 if 快照 is not None else []#行
        钩=自身.属性['hooks'] if 'hooks' in 自身.属性 and isinstance(自身.属性['hooks'],dict) else {}#旧面
        存储=钩['tabs'] if 'tabs' in 钩 else None#源
        if 存储 is not None and hasattr(存储,'getSnapshot'):#对象源
            快照=存储.getSnapshot()#快照
            return 快照 if 快照 is not None else []#行
        return []#无

    def _安放(自身,界面):
        '复用分区根，避免页签切换再叠一层'
        旧=getattr(自身,'根',None)
        if 旧 is not None:
            try:
                旧.clear()
                return 旧
            except Exception as 错误:
                自身.根=None
                自身.画面失败=页面失败文案(错误)
        自身.根=界面.column().classes('插件设置分区根 section')
        return 自身.根

    def _画页(自身,渲染槽,标识):
        '只画这一页；槽空则面板里什么都不加'
        if 标识 is None:
            return
        with 界面.column().classes('panel'):
            渲染槽('settings.plugins.tab',{},{'only':标识})#页自己画

    def 渲染(自身):#结构化视图
        '标题、导语、页签与面板。没有页签时由本分区写空态'
        if 't' not in 自身.属性 or 'renderSlot' not in 自身.属性:#槽位还没齐
            return#不画
        翻译=自身.属性['t']#文案
        渲染槽=自身.属性['renderSlot']#槽渲染
        行表=自身.读页签()#页签
        if not isinstance(行表,list):#缺快照
            行表=[]#当空
        活动=自身.活动标识#请求
        if not any(('id' in 行 and 行['id']==活动) for 行 in 行表):#请求消失
            活动=行表[0]['id'] if len(行表)>0 and 'id' in 行表[0] else None#退回首行
        if 活动 is not None:
            自身.已访问.add(活动)#记访问
            自身.活动标识=活动
        with 自身._安放(界面):
            失败句=getattr(自身,'画面失败',None)
            if isinstance(失败句,str) and 失败句!='':
                自身.画面失败=None
                界面.label(失败句)
            界面.label(翻译('title')).classes('heading')
            界面.label(翻译('intro')).classes('intro')
            if len(行表)==0:#空槽回退写在画槽的主人里
                界面.label(翻译('empty')).classes('empty')
            elif len(行表)==1:#单页不画页签条
                标识=行表[0]['id'] if 'id' in 行表[0] else None
                自身._画页(渲染槽,标识)
            else:
                条=界面.row().classes('tabs')
                条.props('role=tablist aria-label="'+str(翻译('tabs')).replace('"','')+'"')
                with 条:
                    for 序号,行 in enumerate(行表):#每行
                        标识=行['id'] if 'id' in 行 else None#id
                        文=行['label'] if 'label' in 行 and isinstance(行['label'],str) else ''#标签
                        def 点页(钉=标识):
                            '切换并保留已访问页'
                            自身.选页签(钉)
                            if 钉 is not None:
                                自身.已访问.add(钉)
                            自身.渲染()
                        def 按键(事件,下标=序号,行们=list(行表)):
                            '左右与首尾移动页签'
                            键=_键名(事件)#键
                            总数=len(行们)#页数
                            if 键=='ArrowRight':
                                下一=(下标+1)%总数
                            elif 键=='ArrowLeft':
                                下一=(下标-1+总数)%总数
                            elif 键=='Home':
                                下一=0
                            elif 键=='End':
                                下一=总数-1
                            else:
                                return
                            下一标识=行们[下一]['id'] if 'id' in 行们[下一] else None#下一页
                            if 下一标识 is None:
                                return
                            自身.选页签(下一标识)
                            自身.已访问.add(下一标识)
                            自身.渲染()
                        钮=界面.button(文, on_click=点页).props('flat no-caps type=button role=tab').classes('tab')
                        钮.props('aria-selected='+('true' if 标识==活动 else 'false'))
                        if 标识==活动:
                            钮.props('data-active=true tabindex=0')
                        else:
                            钮.props('tabindex=-1')
                        钮.on('keydown',按键)
                for 行 in 行表:#已访问的页留着，只显当前
                    标识=行['id'] if 'id' in 行 else None
                    if 标识 is None or 标识 not in 自身.已访问:
                        continue
                    面板=界面.column().classes('panel')
                    面板.set_visibility(标识==活动)
                    with 面板:
                        渲染槽('settings.plugins.tab',{},{'only':标识})#页自己画

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()
