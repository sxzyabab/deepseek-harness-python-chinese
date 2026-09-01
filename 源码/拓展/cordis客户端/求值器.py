"""浏览器半闭包求值：符号面、陷阱、样式记账与插件收窄。

对齐上游 `cordis-client-runner/src/client/evaluator.ts`。公开面仅中文名。
无法在本 Python 树执行：上游依赖 `new Function`、浏览器 `document` 与 React 闭包符号；
本模块落盘教学重定向、harness/console 契约、样式记账与插件形态校验。
"""

__all__=[#仅中文公开名
    '定时器重定向','客户端重定向','闭包陷阱','harness陷阱','标记控制台',
    '动态样式','是否动态插件','校验求值返回','错误文本','闭包参数名','说明',
]#公开面结束

说明='求值本体需浏览器 Function/React/DOM；Python 半仅承载契约、陷阱文案与样式记账语义。'#说明

定时器重定向=(#定时器教学
    "browser timer globals are unavailable in dynamic packages. Declare inject: ['timer'] on the returned plugin, "
    'query Client Service.listService for the exact API, and close over that plugin ctx. In React, create timers '
    'from an event handler or React.useEffect and return callback-form disposers from the effect cleanup.'
)#结束

客户端重定向={#被扣全局 → 教学
    'setTimeout':定时器重定向,#超时
    'setInterval':定时器重定向,#间隔
    'clearTimeout':定时器重定向,#清超时
    'clearInterval':定时器重定向,#清间隔
    'fetch':'network belongs to the HOST half: register a handler there with harness.handle(method, fn) and call it here via host.call(method, args).',#网络
    'require':'modules cannot be imported here. React arrives as the `React` closure symbol; everything else goes through ctx services or host.call.',#模块
}#结束

闭包参数名=('React','console','styles','host','harness')#固定座位；其后接陷阱键与 process/Buffer

def 闭包陷阱():#可调用教学陷阱
    """遮蔽闭包不得碰的环境全局。"""
    陷阱={}#名 → 抛
    for 名,重定向 in 客户端重定向.items():#每条
        def 造(名称=名,文=重定向):#绑定
            """抛教学错误。"""
            def 陷(*_位置,**_关键字):#陷阱
                """永不返回。"""
                raise Exception(f'{名称} is not available in a dynamic client half — {文}')#教学
            return 陷#函数
        陷阱[名]=造()#写入
    return 陷阱#表

def harness陷阱():#harness 座位只在宿主侧
    """任意属性访问抛平面拆分教学；对齐 harnessTrap Proxy。"""
    class _座位:#空靶
        """触碰即抛。"""
        def __getattr__(自身,属性):#读任何属性
            """永不返回。"""
            raise Exception(#教学
                f'harness.{属性} belongs to the HOST half (`code`): register handlers there with harness.handle(method, fn); '
                'the browser half calls them via host.call(method, args).'
            )#抛
    return _座位()#实例

def 错误文本(参数):#console 参数串
    """Error 用 message；否则 JSON 或占位。"""
    if isinstance(参数,Exception):#异常
        return str(参数)#消息
    if isinstance(参数,str):#串
        return 参数#原样
    if 参数 is None:#对齐上游 undefined 字面（非 Python repr）
        return 'undefined'#镜像 errorText(undefined)
    try:#JSON
        import json#局部
        return json.dumps(参数,ensure_ascii=False)#序列化
    except Exception:#不可序列化
        return '[unserializable console argument]'#占位

def 标记控制台(插件标识,记下错误=None):#带标记的直通控制台契约
    """返回 log/info/warn/error/debug；error 行额外镜像进加载报告（截 500 字）。"""
    前缀=f'[cordis:{插件标识}]'#前缀
    def 转发(级别):#造一级
        """转发并可选镜像。"""
        def 写(*参数):#写一行
            """契约面：拼文本；真实 console 直通需浏览器。"""
            文=' '.join(错误文本(参) for 参 in 参数)#拼
            if 级别=='error' and callable(记下错误):#镜像
                记下错误(文[:500])#截
            return {'level':级别,'tag':前缀,'text':文}#结构记录
        return 写#函数
    return {#覆盖后的控制台
        'log':转发('log'),#log
        'info':转发('info'),#info
        'warn':转发('warn'),#warn
        'error':转发('error'),#error 另镜像
        'debug':转发('debug'),#debug
    }#结束

class 动态样式:#按包 style 标签记账（语义面，无 DOM）
    """insert/dispose；真实 DOM 挂载需浏览器 `document.createElement('style')`。"""
    def __init__(自身,插件标识):#构造
        """记下所有者。"""
        自身.插件标识=插件标识#id
        自身.标签们=[]#本包仍拥有的 CSS 文本记账（Python 半用字符串代替 HTMLStyleElement）

    def 插入(自身,样式文本):#插入样式
        """需要 CSS 字符串；返回拆除器。"""
        if not isinstance(样式文本,str):#非串
            raise Exception('styles.insert(css) needs a CSS string')#错
        自身.标签们.append(样式文本)#记账
        下标=len(自身.标签们)-1#位置
        def 拆除():#拆除器
            """从记账拿掉。"""
            if 0<=下标<len(自身.标签们):#仍在
                自身.标签们[下标]=None#置空
        return 拆除#拆除器

    @property
    def 数量(自身):#标签数
        """仍拥有的条数。"""
        return sum(1 for t in 自身.标签们 if t is not None)#计数

    def 拆除全部(自身):#卸载路径
        """清空记账。"""
        自身.标签们.clear()#清

def 是否动态插件(值):#是否可挂载
    """函数，或带 apply 的对象。"""
    if callable(值) and not isinstance(值,type):#函数
        return True#是——注意 class 也 callable，上游以 typeof function
    if isinstance(值,dict) and callable(值.get('apply')):#对象带 apply
        return True#是
    if 值 is not None and callable(getattr(值,'apply',None)):#对象属性
        return True#是
    return False#否

def 校验求值返回(返回值):#收窄返回
    """非插件抛教学错误（对齐 evaluateClientHalf 尾校验）。"""
    if 是否动态插件(返回值):#可挂
        return 返回值#原样
    if 返回值 is None:#忘了 return
        raise Exception(#教学
            'client half returned `undefined` — did you forget `return`?\n'
            '  ✓ return (ctx) => { … }\n'
            "  ✓ return { name: '…', inject: ['slots'], apply(ctx) { … } }"
        )#抛
    raise Exception('client half must `return` a plugin: a function, or an object with an `apply(ctx)` method')#形态
