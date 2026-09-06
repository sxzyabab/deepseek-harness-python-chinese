"""Composer 上下文占用环与分解面板。

对齐上游 `ui-conversation/src/client/skeleton/ContextMeter.tsx`。公开面仅中文名。
属性、压力、分解为 dict。
"""
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

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 分解令牌(分解,键):
    """缺席当 0。"""
    值=分解[键] if 分解 is not None and 键 in 分解 and 分解[键] is not None else 0#值
    return 值#令牌

class 上下文仪表:
    """压力+容量齐备才渲染；点击开面板。"""

    def __init__(自身,属性=None):
        """记下 props 与开合。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.已开=False#面板

    def 更新(自身,属性):
        """刷新 props；不可用则关面板。"""
        自身.属性=属性 if 属性 is not None else {}#新
        用投影=自身.属性['useProjection'] if 'useProjection' in 自身.属性 else None#投影
        压力=用投影('contextPressure') if 用投影 is not None else None#压力
        if 上下文占用(压力) is None and 自身.已开 is True:#不可用
            自身.已开=False#关

    def 切换(自身):
        """翻转面板。"""
        自身.已开=not 自身.已开#翻

    def 关闭(自身):
        """关面板。"""
        自身.已开=False#关

    def 渲染(自身):
        """无占用返回 None。"""
        属性=自身.属性#props
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        用投影=属性['useProjection'] if 'useProjection' in 属性 else None#投影
        压力=用投影('contextPressure') if 用投影 is not None else None#压力
        分解=用投影('contextBreakdown') if 用投影 is not None else None#分解
        占用=上下文占用(压力)#占用
        if 占用 is None:#不可用
            return None#空
        百分=占用['percent']#百分
        读数=f'{百分}%'#读数
        拆=翻译('context.aria',{'percent':读数槽}).split(读数槽)#拆
        前=拆[0].strip() if len(拆)>0 else ''#前
        后=拆[1].strip() if len(拆)>1 else ''#后
        分解总=0#总
        if 分解 is not None:#有分解
            分解总=分解令牌(分解,'systemTokens')+分解令牌(分解,'toolsTokens')+分解令牌(分解,'messageTokens')#和
        if 分解 is None or 分解总==0:#无分解比例
            段列表=[{'key':'total','color':None,'width':百分}]#整段
        else:#按比例
            段列表=[{'key':行['key'],'color':行['color'],'width':百分*分解令牌(分解,行['key'])/分解总} for 行 in 行配置]#段
        段列表=[段 for 段 in 段列表 if 段['width']>0]#去零宽
        面板=None#面板
        if 自身.已开 is True:#开
            行列表=None if 分解 is None else [{#行
                'key':行['key'],#键
                'color':行['color'],#色
                'label':翻译(行['label']),#标签
                'tokens':f"~{格式化令牌(分解令牌(分解,行['key']))}",#令牌
            } for 行 in 行配置]#结束行
            面板={#面板
                'aria':翻译('context.used'),#aria
                'before':前,#前
                'percent':读数,#百分
                'after':后,#后
                'figures':f"~{格式化令牌(占用['usedTokens'])} / {格式化令牌(占用['contextWindow'])}",#数字
                'segments':段列表,#段
                'rows':行列表,#行
            }#结束面板
        return {#根
            'className':'root',#类
            'trigger':{#触发
                'aria':翻译('context.aria',{'percent':读数}),#aria
                'expanded':自身.已开,#展开
                'radius':半径,#半径
                'dash':周长*百分/100,#弧长
                'circumference':周长,#周长
                'onClick':自身.切换,#切换
            },#结束触发
            'panel':面板,#面板
        }#结束根
