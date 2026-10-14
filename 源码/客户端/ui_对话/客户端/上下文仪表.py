import math#圆周

from .统计行 import 上下文占用,格式化令牌#占用与紧凑令牌

__all__=['上下文仪表','半径','周长','读数槽','行配置']#仅中文公开名

半径=5.5#环半径
周长=2*math.pi*半径#周长
读数槽='\u0000'#拆分占位

行配置=[#分解行序
    {'key':'systemTokens','label':'context.system','color':'colorSystem'},#系统
    {'key':'toolsTokens','label':'context.tools','color':'colorTools'},#工具
    {'key':'messageTokens','label':'context.messages','color':'colorMessages'},#消息
]#结束配置

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 分解令牌(分解,键):
    '缺席当 0'
    值=分解[键] if 分解 is not None and 键 in 分解 and 分解[键] is not None else 0#值
    return 值#令牌

class 上下文仪表:
    '压力+容量齐备才渲染；点击开面板'

    def __init__(自身,属性=None):
        '记下 props 与开合'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.已开=False#面板
        自身.画面=None#可反复清空的画面

    def 更新(自身,属性):
        '刷新 props；不可用则关面板'
        自身.属性=属性 if 属性 is not None else {}#新
        用投影=自身.属性['useProjection'] if 'useProjection' in 自身.属性 else None#投影
        压力=用投影('contextPressure') if 用投影 is not None else None#压力
        if 上下文占用(压力) is None and 自身.已开 is True:#不可用
            自身.已开=False#关

    def 切换(自身):
        '翻转面板'
        自身.已开=not 自身.已开#翻

    def 关闭(自身):
        '关面板'
        自身.已开=False#关

    def 渲染(自身):
        '无占用返回 None'
        属性=自身.属性#props
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        用投影=属性['useProjection'] if 'useProjection' in 属性 else None#投影
        压力=用投影('contextPressure') if 用投影 is not None else None#压力
        分解=用投影('contextBreakdown') if 用投影 is not None else None#分解
        占用=上下文占用(压力)#占用
        原译=翻译 if 翻译 is not 恒等翻译 else None#宿主文案
        def 取文案(键,参数=None):
            '属性上的 t 优先，否则用本包中文词典。'
            if 原译 is not None:#宿主
                if 参数 is None:#无参数
                    return 原译(键)#译
                return 原译(键,参数)#带参数
            if 键 not in 对话文案:#词典没有
                return 键#键
            文本=对话文案[键]#词条
            if 参数 is None:#无参数
                return 文本#原文
            for 名 in 参数:#替换占位
                文本=文本.replace('{'+名+'}',str(参数[名]))#替换
            return 文本#译完
        翻译=取文案#词典
        if 占用 is None:#不可用
            return#不画
        百分=占用['percent']#百分
        读数=f'{百分}%'#读数
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('root')#仪表
        def 重画():
            '按面板开合重画。'
            自身.画面.clear()#清空
            with 自身.画面:#仪表
                贴出失败(自身)
                def 点环():
                    '打开或关闭分解。'
                    自身.切换()#翻
                    重画()#重画
                界面.button(翻译('context.aria',{'percent':读数}),on_click=点环)#触发
                界面.linear_progress(value=百分/100).classes('占用')#环的读数
                if 自身.已开 is True:#面板
                    界面.label(翻译('context.used'))#已用
                    界面.label('~'+格式化令牌(占用['usedTokens'])+' / '+格式化令牌(占用['contextWindow']))#数字
                    if 分解 is not None:#分解行
                        for 行 in 行配置:#逐段
                            界面.label(翻译(行['label'])+' ~'+格式化令牌(分解令牌(分解,行['key'])))#行
        重画()#画
