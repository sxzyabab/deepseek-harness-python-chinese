from ...未实现失败 import 运行时错误
import json
import math
import re

__all__=[
    'promisify','callbackify','inspect','format','isDeepStrictEqual','types',
    'parseArgs','deprecate','TextDecoder','TextEncoder','__esModule','default',
]

def 对象同(左,右):
    """结构相等前的同值判定。"""
    if 左 is 右: return True
    if isinstance(左,float) and isinstance(右,float):
        if math.isnan(左) and math.isnan(右): return True
        if 左==0.0 and 右==0.0: return math.copysign(1.0,左)==math.copysign(1.0,右)
        return 左==右
    if isinstance(左,(int,str,bool)) and type(左) is type(右): return 左==右
    return False

def 承诺化(函数):
    """将错误优先回调函数包装为同步返回结果的函数。"""
    def 包装(*参数):
        """追加错误优先回调并同步交出结果。"""
        结算={'值':None,'错误':None}
        def 回调(错误,值=None):
            """有错记下错误，否则记下值。"""
            if 错误 is not None:
                结算['错误']=错误
            else:
                结算['值']=值
        函数(*参数,回调)
        if 结算['错误'] is not None:
            错误=结算['错误']
            if isinstance(错误,BaseException):
                raise 错误
            raise Exception(检视(错误))
        return 结算['值']
    return 包装

def 回调化(函数):
    """将同步返回结果的函数包装为错误优先回调函数。"""
    def 包装(*参数):
        """末参为回调，前面为实参。"""
        回调=参数[-1]
        其余=参数[:-1]
        try:
            值=函数(*其余)
        except BaseException as 错误:
            回调(错误)
            return
        回调(None,值)
    return 包装

def 检视(值):
    """值的诊断渲染。"""
    if isinstance(值,str): return f"'{值}'"
    if isinstance(值,BaseException):
        栈=getattr(值,'stack',None)
        if 栈 is not None: return 栈
        名=getattr(值,'name',type(值).__name__)
        消息=getattr(值,'message',str(值))
        return f'{名}: {消息}'
    try:
        渲染=json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)
        return 渲染 if 渲染 is not None else str(值)
    except (TypeError,ValueError):#json.dumps 对非法类型或 NaN 失败
        return str(值)

def 格式化(模板,*实参):
    """Node 支持的 `%s`/`%d`/`%j`/`%o` 占位符的 printf 风格格式化。"""
    if not isinstance(模板,str):
        return ' '.join(检视(项) for 项 in (模板,*实参))
    下标=[0]

    def 替换(匹配):
        """替换一个占位符。"""
        记号=匹配.group(0)
        if 记号=='%%': return '%'
        if 下标[0]>=len(实参): return 记号
        值=实参[下标[0]]
        下标[0]+=1
        if 记号 in ('%d','%i','%f'): return str(float(值) if not isinstance(值,(int,float)) else 值)
        if 记号=='%s': return 值 if isinstance(值,str) else 检视(值)
        return 检视(值)

    已替换=re.sub(r'%[sdifjoO%]',替换,模板,count=0)
    剩余=实参[下标[0]:]
    if len(剩余)==0: return 已替换
    return f"{已替换} {' '.join(检视(项) for 项 in 剩余)}"

def 深严格相等(左,右):
    """结构深相等，如 `isDeepStrictEqual` 对普通数据所定义。"""
    if 对象同(左,右): return True
    if not isinstance(左,(dict,list)) or not isinstance(右,(dict,list)): return False
    if isinstance(左,list)!=isinstance(右,list): return False
    if isinstance(左,list):
        if len(左)!=len(右): return False
        return all(深严格相等(甲,乙) for 甲,乙 in zip(左,右))
    左键=list(左.keys())
    右键=list(右.keys())
    if len(左键)!=len(右键): return False
    return all(键 in 右 and 深严格相等(左[键],右[键]) for 键 in 左键)

def 是承诺(值):
    """是否为本宿主 Promise 实例。"""
    if 'Promise' not in globals():
        return False
    return isinstance(值,globals()['Promise'])

def 是日期(值):
    """是否 Date。"""
    if 'Date' not in globals():
        return False
    return isinstance(值,globals()['Date'])

def 是正则(值):
    """是否 RegExp。"""
    if 'RegExp' in globals() and isinstance(值,globals()['RegExp']):
        return True
    return isinstance(值,re.Pattern)

def 是类型化数组(值):
    """Node 只计整数与浮点视图，故 DataView 给出 false。"""
    if 'ArrayBuffer' not in globals():
        return False
    缓冲=globals()['ArrayBuffer']
    是视图=getattr(缓冲,'isView',None)
    if not callable(是视图) or not 是视图(值):
        return False
    if 'DataView' in globals() and isinstance(值,globals()['DataView']):
        return False
    return True

types={
    'isPromise':是承诺,
    'isDate':是日期,
    'isRegExp':是正则,
    'isTypedArray':是类型化数组,
}

def 解析参数(*位置参数,**关键字参数):
    """CLI 参数解析在 worker 主机内无调用方。"""
    raise 运行时错误('web-preview: worker 宿主里没有 node:util.parseArgs')

def 弃用(函数):
    """弃用包装器原样传过函数。"""
    return 函数

promisify=承诺化
callbackify=回调化
inspect=检视
format=格式化
isDeepStrictEqual=深严格相等
parseArgs=解析参数
deprecate=弃用
TextDecoder=globals()['TextDecoder'] if 'TextDecoder' in globals() else None
TextEncoder=globals()['TextEncoder'] if 'TextEncoder' in globals() else None
__esModule=True

default={
    'promisify':承诺化,'callbackify':回调化,'inspect':检视,'format':格式化,
    'isDeepStrictEqual':深严格相等,'types':types,'parseArgs':解析参数,'deprecate':弃用,
    'TextDecoder':TextDecoder,'TextEncoder':TextEncoder,
}
