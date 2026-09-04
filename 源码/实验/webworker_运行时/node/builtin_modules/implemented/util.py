"""worker 侧的 `node:util`：harness 代码实际导入的成员。Node 的 inspect 输出
仅用于诊断，故 JSON 形态渲染足够；`promisify` 严格遵循 Node 的错误优先
回调约定，因为 zlib 风格 API 在模块作用域用它包装。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/util.ts`。
公开面中文名；Node 面经别名与 default 暴露英文名。
"""
import json#诊断序列化
import math#Object.is 的 NaN/+0/-0
import re#占位符替换

__all__=[#中文公开名与Node英文挂名
    '承诺化','回调化','检视','格式化','深严格相等','解析参数','弃用',
    'promisify','callbackify','inspect','format','isDeepStrictEqual','types',
    'parseArgs','deprecate','TextDecoder','TextEncoder','__esModule','default',
]#公开结束

def 对象同(左,右):#对齐 Object.is
    """结构相等前的同值判定。"""
    if 左 is 右: return True#同引用
    if isinstance(左,float) and isinstance(右,float):#浮点特殊
        if math.isnan(左) and math.isnan(右): return True#NaN
        if 左==0.0 and 右==0.0: return math.copysign(1.0,左)==math.copysign(1.0,右)#+0/-0
        return 左==右#其余浮点
    if isinstance(左,(int,str,bool)) and type(左) is type(右): return 左==右#原始同值
    return False#其余否

def 承诺化(函数):#回调转Promise
    """将错误优先回调函数包装为返回 promise 的函数。"""
    承诺类=globals()['Promise']#Promise构造器

    def 包装(*参数):#返回包装器
        """追加错误优先回调并返回 Promise。"""
        def 执行(兑现,拒绝):#Promise体
            """桥接回调。"""
            def 回调(错误,值=None):#错误优先回调
                """有错拒绝，否则兑现。"""
                if 错误 is not None:#有错
                    拒绝(错误 if isinstance(错误,BaseException) else Exception(检视(错误)))#拒绝
                else:#成功
                    兑现(值)#兑现
            函数(*参数,回调)#追加回调
        return 承诺类(执行)#返回Promise
    return 包装#交回

def 回调化(函数):#Promise转回调
    """将返回 promise 的函数包装为错误优先回调函数。"""
    def 包装(*参数):#返回包装器
        """末参为回调，前面为实参。"""
        回调=参数[-1]#末参回调
        其余=参数[:-1]#前面实参
        def 成功(值):#兑现
            """回调成功。"""
            回调(None,值)#成功
        def 失败(错误):#拒绝
            """回调失败。"""
            回调(错误)#失败
        函数(*其余).then(成功,失败)#桥接
    return 包装#交回

def 检视(值):#诊断渲染
    """值的诊断渲染。"""
    if isinstance(值,str): return f"'{值}'"#字符串加引号
    if isinstance(值,BaseException):#错误
        栈=getattr(值,'stack',None)#栈
        if 栈 is not None: return 栈#错误栈
        名=getattr(值,'name',type(值).__name__)#错误名
        消息=getattr(值,'message',str(值))#消息
        return f'{名}: {消息}'#名与消息
    try:#尝试JSON
        渲染=json.dumps(值)#序列化
        return 渲染 if 渲染 is not None else str(值)#空则String
    except Exception:#不可序列化
        return str(值)#兜底String

def 格式化(模板,*实参):#printf格式化
    """Node 支持的 `%s`/`%d`/`%j`/`%o` 占位符的 printf 风格格式化。"""
    if not isinstance(模板,str):#非串
        return ' '.join(检视(项) for 项 in (模板,*实参))#拼接
    下标=[0]#已消费实参下标

    def 替换(匹配):#替换占位符
        """替换一个占位符。"""
        记号=匹配.group(0)#记号
        if 记号=='%%': return '%'#转义百分号
        if 下标[0]>=len(实参): return 记号#实参不足保留
        值=实参[下标[0]]#取下一实参
        下标[0]+=1#推进
        if 记号 in ('%d','%i','%f'): return str(float(值) if not isinstance(值,(int,float)) else 值)#数值
        if 记号=='%s': return 值 if isinstance(值,str) else 检视(值)#字符串
        return 检视(值)#其余用检视

    已替换=re.sub(r'%[sdifjoO%]',替换,模板)#替换占位符
    剩余=实参[下标[0]:]#剩余实参
    if len(剩余)==0: return 已替换#无剩余
    return f"{已替换} {' '.join(检视(项) for 项 in 剩余)}"#拼剩余

def 深严格相等(左,右):#深相等
    """结构深相等，如 `isDeepStrictEqual` 对普通数据所定义。"""
    if 对象同(左,右): return True#同引用或同值
    if not isinstance(左,(dict,list)) or not isinstance(右,(dict,list)): return False#非对象
    if isinstance(左,list)!=isinstance(右,list): return False#数组性不一致
    if isinstance(左,list):#列表按索引
        if len(左)!=len(右): return False#长度不同
        return all(深严格相等(甲,乙) for 甲,乙 in zip(左,右))#逐项
    左键=list(左.keys())#左键
    右键=list(右.keys())#右键
    if len(左键)!=len(右键): return False#键数不同
    return all(键 in 右 and 深严格相等(左[键],右[键]) for 键 in 左键)#逐键

def 是承诺(值):#Promise实例或thenable
    """是否 Promise 或 thenable。"""
    承诺类=globals().get('Promise')#Promise类
    if 承诺类 is not None and isinstance(值,承诺类): return True#Promise实例
    return 值 is not None and (isinstance(值,dict) or hasattr(值,'then')) and callable(getattr(值,'then',None))#或thenable

def 是日期(值):#Date
    """是否 Date。"""
    日期类=globals().get('Date')#Date类
    return 日期类 is not None and isinstance(值,日期类)#Date

def 是正则(值):#RegExp
    """是否 RegExp。"""
    正则类=globals().get('RegExp')#RegExp类
    if 正则类 is not None and isinstance(值,正则类): return True#RegExp
    return isinstance(值,re.Pattern)#Python Pattern

def 是类型化数组(值):#TypedArray
    """Node 只计整数与浮点视图，故 DataView 给出 false。"""
    缓冲=globals().get('ArrayBuffer')#ArrayBuffer
    数据视图=globals().get('DataView')#DataView
    if 缓冲 is None: return False#无ArrayBuffer
    是视图=getattr(缓冲,'isView',None)#isView
    if not callable(是视图) or not 是视图(值): return False#非视图
    if 数据视图 is not None and isinstance(值,数据视图): return False#排除DataView
    return True#TypedArray

types={#类型谓词集
    'isPromise':是承诺,#Promise
    'isDate':是日期,#Date
    'isRegExp':是正则,#RegExp
    'isTypedArray':是类型化数组,#TypedArray
}#types结束

def 解析参数(*位置参数,**关键字参数):#不可用
    """CLI 参数解析在 worker 主机内无调用方。"""
    raise Exception('web-preview: node:util.parseArgs is not available in the worker host')#抛错

def 弃用(函数):#弃用包装透传
    """弃用包装器原样传过函数。"""
    return 函数#原样返回

promisify=承诺化#Node面
callbackify=回调化#Node面
inspect=检视#Node面
format=格式化#Node面
isDeepStrictEqual=深严格相等#Node面
parseArgs=解析参数#Node面
deprecate=弃用#Node面
TextDecoder=globals().get('TextDecoder')#DOM TextDecoder
TextEncoder=globals().get('TextEncoder')#DOM TextEncoder
__esModule=True#CJS互操作

default={#默认导出
    'promisify':承诺化,'callbackify':回调化,'inspect':检视,'format':格式化,#工具
    'isDeepStrictEqual':深严格相等,'types':types,'parseArgs':解析参数,'deprecate':弃用,#其余
    'TextDecoder':TextDecoder,'TextEncoder':TextEncoder,#编解码器
}#默认导出结束
