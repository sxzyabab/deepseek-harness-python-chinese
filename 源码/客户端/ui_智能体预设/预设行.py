import importlib.resources as 包资源
from nicegui import ui as 界面
from .异常 import 页面失败文案
from .文案 import 预设展示文案#展示文案
from .预设菜单 import 预设菜单

__all__=['预设行','样式表']#仅中文公开名

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

def 挂到根(原文,根):
    '共享样式只作用在本组件根下'
    return _挂规则(_去注释(原文),根)

样式表=挂到根(_读样式('预设行.module.css'),'预设行根')
界面.add_css(样式表,shared=True)

class 预设行:
    '部署无预设时返回 None。属性与快照都是 dict'
    def __init__(自身,属性):
        '记下 props 并触发 load'
        自身.属性=属性#合成
        自身.打开=False#菜单
        if isinstance(属性,dict) and 'load' in 属性 and 'useAgentPreset' in 属性 and 't' in 属性:
            属性['load']()#拉名册
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '不可写则关菜单'
        自身.属性=属性#最新
        态=自身.状态()#状态
        if 态['writable'] and 态['status']!='unavailable':#仍可用
            return#保留
        自身.打开=False#关

    def 状态(自身):
        '经 useAgentPreset'
        def 恒等(快照):
            '整表'
            return 快照#快照
        return 自身.属性['useAgentPreset'](恒等)#快照

    def 选定(自身,标识):
        '关菜单并 select'
        自身.打开=False#关
        自身.属性['select'](标识)#提交

    def 切换菜单(自身):
        '翻转菜单开闭'
        自身.打开=not 自身.打开#翻转

    def 渲染(自身):
        '产出与上游 JSX 同构的结构化视图'
        态=自身.状态()#状态
        if 态['status']=='unavailable':#无预设
            return None#不渲染
        翻译=自身.属性['t']#翻译
        忙=态['status'] in ('loading','saving')#忙碌
        当前=态['currentValue']#当前
        选中=None#选项
        for 项 in 态['options']:#找
            if 项['id']==当前:#命中
                选中=项
                break
        展示=预设展示文案(选中,翻译) if 选中 is not None else None#展示
        if 当前=='' :#加载中标签
            标签=翻译('loading')#加载
        elif 展示 is not None:#有展示
            标签=展示['name']#名
        else:#回退
            标签=当前#id
        说明=页面失败文案(态['error']) if 态['error'] is not None else None#错误
        if 说明 is None:#无错
            说明=翻译('description')#说明
        def 改开(开):
            '同步菜单开闭'
            自身.打开=bool(开)
        with 界面.row().classes('预设行根 row'):
            with 界面.column().classes('rowText'):
                界面.label(翻译('title')).classes('title')
                界面.label(说明).classes('desc')
            预设菜单({
                't':翻译,
                'options':态['options'],
                'open':自身.打开,
                'onOpenChange':改开,
                'onSelect':自身.选定,
                'selectedId':当前,
                'label':标签,
                'disabled':忙 or not 态['writable'],
                'buttonClassName':'selector',
            }).渲染()

    def __call__(自身,属性=None):
        '对齐 React 组件调用'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()
