import importlib.resources as 包资源
import re as 正则
from nicegui import ui as 界面
from .异常 import 计划错误,去掉敏感,页面失败文案#本包异常

def _读样式():
    '读同目录计划模式样式。打不开时只报样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath('计划模式控件.module.css').read_text(encoding='utf-8')
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

def _挂(原文,根):
    '类选择器只作用在计划芯片根下，避免盖到别的芯片'
    文=_去注释(原文)
    def 换(匹配):
        选择器=匹配.group(1).strip()
        体=匹配.group(2)
        if 选择器.startswith('@'):
            return 选择器+'{'+体+'}'
        条=[]
        for 片 in 选择器.split(','):
            片=片.strip()
            if 片=='':
                continue
            条.append('.'+根+' '+片)
            条.append('.'+根+片)
        if len(条)==0:
            return ''
        return ', '.join(条)+'{'+体+'}'
    return 正则.sub(r'([^{]+)\{([^}]*)\}',换,文)

样式表=_挂(_读样式(),'计划芯片根')
界面.add_css(样式表,shared=True)

def 腾出根(自身,隐藏=None):
    '清空仍挂着的根。父级已拆掉时丢掉根，并返回要显示的失败句。'
    旧=getattr(自身,'根',None)
    if 旧 is None:
        return None
    try:
        旧.clear()
        if 隐藏 is True:
            旧.set_visibility(False)
        elif 隐藏 is False:
            旧.set_visibility(True)
    except Exception as 错误:
        自身.根=None
        return 页面失败文案(错误)
    return None

def 标出失败(文案):
    '失败句非空时写在当前页面上'
    if isinstance(文案,str) and 文案!='':
        界面.label(文案)

__all__=['计划芯片','计划错误']#仅中文公开名

def 默认翻译(键,_缺省=None):#无文案席回退
    '无文案席时回退为键本身'
    return 键#原样

class 计划芯片:#composer 计划席位组件
    '只在有效目标为计划模式时渲染；点击执行 /plan off'
    def __init__(自身,属性):#按合成 props 构造
        '记下 props'
        自身.属性=属性#合成 props
        自身.离开中=False#正在退出
        自身.错误=None#失败行
        自身.存活=True#实例存活
        if isinstance(自身.属性,dict) and 'useProjection' in 自身.属性 and 'exitPlanMode' in 自身.属性:
            自身.渲染()#槽位只调用构造，键齐了就画

    def 更新(自身,属性):#props 变更
        '刷新合成 props'
        自身.属性=属性#最新

    def 卸载(自身):#卸载
        '标死'
        自身.存活=False#死

    def 关闭计划(自身):#执行 /plan off
        '无 leaving/locked 守卫：两者会禁用按钮。exitPlanMode 返回任务'
        自身.离开中=True#离开中
        自身.错误=None
        退出=自身.属性['exitPlanMode'] if 'exitPlanMode' in 自身.属性 else None#退出动作
        try:#执行
            失败=退出().等待() if 退出 is not None else None#结算任务
        except Exception as 原因:#回调拒绝；契约未定
            if not 自身.存活:#已死
                raise
            自身.离开中=False
            自身.错误=页面失败文案(原因)
            return
        if not 自身.存活:#已死
            return#丢弃
        自身.离开中=False
        if isinstance(失败,str) and 失败!='':
            文=去掉敏感(失败)
            自身.错误=文 if 文!='' else '退出失败'
        else:
            自身.错误=失败

    def 视图(自身):#读视图模型
        '投影缺席或非目标则 None'
        用投影=自身.属性['useProjection'] if 'useProjection' in 自身.属性 else None#投影选择器
        if 用投影 is None:#无
            return None#不渲染
        计划=用投影('plan')#plan 投影
        if 计划 is None:#缺席
            return None#不渲染
        进行中=计划['pending'] if 'pending' in 计划 else None#待定翻转
        活动=计划['active'] if 'active' in 计划 else None#当前活动
        目标=(not 活动) if 进行中 else 活动#有效目标
        if not 目标:#非计划模式
            return None#不渲染
        翻译=自身.属性['t'] if 't' in 自身.属性 else 默认翻译#文案
        锁定=自身.属性['locked'] if 'locked' in 自身.属性 else None#锁定
        return {#视图
            'aria':翻译('chip.on.aria'),#无障碍名
            'title':翻译('chip.on.title'),#悬停
            'disabled':锁定 is True or 自身.离开中,#禁用
            'error':自身.错误,#失败行
            'leaving':自身.离开中,#离开中
        }#视图结束

    def 渲染(自身):
        '计划模式芯片；点击执行退出'
        视=自身.视图()
        if 视 is None:
            清除失败=腾出根(自身,隐藏=True)
            标出失败(清除失败)
            return
        清除失败=腾出根(自身,隐藏=False)
        if getattr(自身,'根',None) is None:
            自身.根=界面.row().classes('计划芯片根 wrap')
        翻译=自身.属性['t'] if 't' in 自身.属性 else 默认翻译
        def 点关():
            '退出计划模式'
            自身.关闭计划()
            自身.渲染()
        with 自身.根:
            标出失败(清除失败)
            钮=界面.button(翻译('chip.label'),on_click=点关).props('flat no-caps').classes('chip')
            钮.tooltip(视['title'])
            if 视['disabled'] is True:
                钮.disable()
            错误=视['error']
            if isinstance(错误,str) and 错误!='':
                界面.label(翻译('chip.exitFailed')).classes('error').tooltip(错误)

    def __call__(自身,属性=None):#组件调用形
        '组件调用形'
        if 属性 is not None:
            自身.更新(属性)#刷新
        return 自身.渲染()
