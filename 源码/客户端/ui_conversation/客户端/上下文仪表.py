"""Composer 上下文占用环与分解面板。

对齐上游 `ui-conversation/src/client/skeleton/ContextMeter.tsx`。公开面仅中文名。
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

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 上下文仪表:#占用环
    """压力+容量齐备才渲染；点击开面板。"""

    def __init__(自身,属性=None):#记下
        """记下 props 与开合。"""
        自身.属性=属性 or {}#合成
        自身.已开=False#面板

    def 更新(自身,属性):#刷新
        """刷新 props；不可用则关面板。"""
        自身.属性=属性 or {}#新
        用投影=取字段(自身.属性,'useProjection')#投影
        压力=用投影('contextPressure') if callable(用投影) else None#压力
        if 上下文占用(压力) is None and 自身.已开:#不可用
            自身.已开=False#关

    def 切换(自身):#开合
        """翻转面板。"""
        自身.已开=not 自身.已开#翻

    def 关闭(自身):#关
        """关面板。"""
        自身.已开=False#关

    def 渲染(自身):#结构
        """无占用返回 None。"""
        属性=自身.属性#props
        翻译=取字段(属性,'t',lambda 键,**_:键)#文案
        用投影=取字段(属性,'useProjection')#投影
        压力=用投影('contextPressure') if callable(用投影) else None#压力
        分解=用投影('contextBreakdown') if callable(用投影) else None#分解
        占用=上下文占用(压力)#占用
        if 占用 is None:#不可用
            return None#空
        百分=占用['percent']#百分
        读数=f'{百分}%'#读数
        拆=翻译('context.aria',{'percent':读数槽}).split(读数槽)#拆
        前=(拆[0].strip() if 拆 else '')#前
        后=(拆[1].strip() if len(拆)>1 else '')#后
        分解总=0#总
        if 分解 is not None:#有分解
            分解总=(取字段(分解,'systemTokens') or 0)+(取字段(分解,'toolsTokens') or 0)+(取字段(分解,'messageTokens') or 0)#和
        if 分解 is None or 分解总==0:#无分解比例
            段们=[{'key':'total','color':None,'width':百分}]#整段
        else:#按比例
            段们=[{'key':行['key'],'color':行['color'],'width':百分*取字段(分解,行['key'])/分解总} for 行 in 行配置]#段
        段们=[段 for 段 in 段们 if 段['width']>0]#去零宽
        面板=None#面板
        if 自身.已开:#开
            面板={#面板
                'aria':翻译('context.used'),#aria
                'before':前,#前
                'percent':读数,#百分
                'after':后,#后
                'figures':f"~{格式化令牌(占用['usedTokens'])} / {格式化令牌(占用['contextWindow'])}",#数字
                'segments':段们,#段
                'rows':None if 分解 is None else [{#行
                    'key':行['key'],#键
                    'color':行['color'],#色
                    'label':翻译(行['label']),#标签
                    'tokens':f"~{格式化令牌(取字段(分解,行['key']))}",#令牌
                } for 行 in 行配置],#结束行
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
