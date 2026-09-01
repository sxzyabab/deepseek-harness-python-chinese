"""动态包包宿主半求值所用的沙箱（Python 侧：compile 预检 + exec 求值）。

对齐上游 `拓展/cordis-host-runner/src/sandbox.ts` 的公开语义。
Node vm 在 Python 树用 compile/exec 近似；宿主内置巡检符号表保持上游字面量。
"""
import base64#base64 编解码
from .守卫 import 沙箱定义工具,沙箱登记工具#沙箱工具登记

__all__=[#仅中文公开名
    '宿主内置巡检',
    '创建沙箱',
    '语法错误上下文',
    '解析错误消息',
    '预检代码',
    '求值宿主代码',
]#公开面结束

宿主内置巡检=[#内建巡检条目
    {'name':'ctx','description':'Restricted Cordis Context. Prefer ctx.get(name) with an undefined check; use inject for hard dependencies.','signatures':['ctx.get(name: string): unknown | undefined','ctx.on(name: string, listener: Function): () => void','ctx.provide(name: string, value: unknown): () => void','ctx.effect(callback: Function, label?: string): () => void']},#ctx
    {'name':'harness','description':'Host helpers for Package-private Client RPC and model-visible dynamic Tools.','signatures':['harness.handle(method: string, handler: (args: JsonValue) => JsonValue | Promise<JsonValue>): () => void','harness.defineTool(definition: ToolDefinition): ToolDefinition','harness.registerTool(ctx: Context, tool: ToolDefinition): () => void']},#harness
    {'name':'console','description':'Package-tagged Host logging.','signatures':['console.log(...values): void','console.error(...values): void']},#带标记日志
    {'name':'btoa','description':'Encode UTF-8 text as base64.','signatures':['btoa(value: string): string']},#base64 编码
    {'name':'atob','description':'Decode base64 as UTF-8 text.','signatures':['atob(value: string): string']},#base64 解码
    {'name':'TextEncoder','description':'Standard UTF-8 encoder constructor.','signatures':['new TextEncoder()']},#UTF-8 编码器
    {'name':'TextDecoder','description':'Standard text decoder constructor.','signatures':['new TextDecoder(label?: string)']},#文本解码器
]#只读内建表

HOST_BUILTIN_INSPECTION=宿主内置巡检#英文别名，供 tool_cordis 对齐上游导入名

定时器重定向=('Node timers are unavailable. Use the cordis timer service instead: declare inject: [\'timer\'] on your plugin '
    + 'and call ctx.timeout / ctx.interval after querying Host Service.listService for the exact overloads. '
    + 'Those calls are fiber effects, cleaned up automatically when stopped.')#改用 ctx 定时器

节点API重定向={#Node API 重定向
    'require':'Node modules are unavailable. Use the cordis services on ctx instead — e.g. inject: [\'fs\'] for files, [\'web\'] for HTTP, [\'bash\'] for processes; query Service.listService with cordis_inspect_query first.',#改用 ctx 服务
    'setTimeout':定时器重定向,#定时器
    'setInterval':定时器重定向,#间隔
    'setImmediate':定时器重定向,#立即
    'clearTimeout':定时器重定向,#清超时
    'clearInterval':定时器重定向,#清间隔
    'fetch':'Network access goes through the cordis web service: declare inject: [\'web\'] and call ctx.web (query Host Service.listService with cordis_inspect_query for its methods).',#改用 ctx.web
}#重定向结束

def 带标记控制台(标识):#带标记控制台
    """每行都打上包 id。"""
    标签=f'[cordis:{标识}]'#前缀
    def 日志(*参数):#log/info/warn/debug 共用
        """stdout。"""
        print(标签,*参数)#stdout
    def 错误(*参数):#error 走 stderr
        """stderr。"""
        print(标签,*参数,flush=True)#stderr 近似
    return {'log':日志,'info':日志,'warn':日志,'debug':日志,'error':错误}#五级

def 节点API陷阱():#Node API 陷阱
    """调用即抛出重定向。"""
    陷阱={}#名字到陷阱
    for 名,重定向 in 节点API重定向.items():#每条
        def 造陷阱(名称=名,说明=重定向):#闭包绑定
            """陷阱。"""
            def 触发(*_位置参数,**_关键字参数):#调用即抛
                """教学错误。"""
                raise Exception(f'{名称} is not available in the dynamic package sandbox — {说明}')#教学错误
            return 触发#陷阱函数
        陷阱[名]=造陷阱()#写入
    return 陷阱#陷阱表

def 创建沙箱(标识,harness额外=None):#创建沙箱
    """带标记控制台、harness 登记助手、编码原语、Node API 陷阱。"""
    if harness额外 is None:#默认空
        harness额外={}#空
    def btoa(串):#UTF-8 → base64
        """编码。"""
        return base64.b64encode(串.encode('utf-8')).decode('ascii')#编码
    def atob(串):#base64 → UTF-8
        """解码。"""
        return base64.b64decode(串.encode('ascii')).decode('utf-8')#解码
    沙箱={#沙箱全局
        **节点API陷阱(),#Node API 陷阱
        'console':带标记控制台(标识),#带标记控制台
        'harness':{'defineTool':沙箱定义工具,'registerTool':沙箱登记工具,**harness额外},#登记助手
        'btoa':btoa,#UTF-8 → base64
        'atob':atob,#base64 → UTF-8
    }#sandbox结束
    return 沙箱#交给求值

def 是否语法错误(错误):#是否语法错误
    """按 name / 类型判断。"""
    return isinstance(错误,SyntaxError) or (isinstance(错误,Exception) and getattr(错误,'__class__',None).__name__=='SyntaxError')#按类型

def 语法错误上下文(错误):#语法错误上下文
    """栈前缀，含 SyntaxError 那一行。"""
    栈=getattr(错误,'stack',None) or ''#栈
    if not 栈 and isinstance(错误,SyntaxError):#Python SyntaxError
        return f'SyntaxError: {错误.msg}\n{(错误.text or "").rstrip()}'#消息与出错行
    行们=栈.split('\n')#按行拆栈
    消息下标=next((序号 for 序号,行 in enumerate(行们) if 行.startswith('SyntaxError')),-1)#消息行
    if 消息下标==-1:#没有前奏
        return str(错误)#没有前奏
    return '\n'.join(行们[:消息下标+1])#含消息行的前缀

def 解析错误消息(半边,上下文):#解析失败教学
    """面向模型的错误消息。"""
    出错行=(上下文.split('\n')+[ ''])[1] if '\n' in 上下文 else ''#出错源码行
    if r'\bas\b' in 出错行 or ' as ' in 出错行:#像类型断言
        return (f'dynamic package `{半边}` failed to parse:\n{上下文}\n'
            + 'The sandbox runs plain JavaScript, not TypeScript. Remove type annotations:\n'
            + "  ✗ { type: 'text' as const, text: x }\n"
            + "  ✓ { type: 'text', text: x }")#去掉注解
    return (f'dynamic package `{半边}` failed to parse:\n{上下文}\n'
        + 'Note: it runs as the BODY of an async function (line numbers are offset by the 1-line wrapper). '
        + 'Check bracket balance — ending the returned plugin object with `});` closes a call that was never opened; '
        + 'a plain `return { … }` ends with `}` (an optional `;`), never `)`.')#括号平衡提示

def 预检代码(代码,半边):#定义时预检
    """解析一半源码但不运行：教学启发式对齐上游 vm Script 预检。"""
    if not isinstance(代码,str):#必须是字符串
        raise Exception(f'dynamic package `{半边}` failed to parse:\nexpected a string function body')#非法
    上下文=f'SyntaxError: Unexpected token\n{代码.splitlines()[0] if 代码.splitlines() else ""}'#合成上下文
    出错行=(代码.splitlines() or [''])[0]#出错源码行近似取首行
    if ' as ' in 代码:#像类型断言（整份粗检；上游只看出错行）
        for 行 in 代码.splitlines():#找含 as 的行
            if ' as ' in 行:#命中
                上下文=f'SyntaxError: Unexpected identifier\n{行}'#用该行
                break#找到
        raise Exception(解析错误消息(半边,上下文))#教学错误
    开=代码.count('{')+代码.count('(')+代码.count('[')#开括号
    闭=代码.count('}')+代码.count(')')+代码.count(']')#闭括号
    if 开!=闭:#括号不平衡
        raise Exception(解析错误消息(半边,f'SyntaxError: Unexpected end of input\n{出错行}'))#教学错误

def 求值宿主代码(沙箱,代码,标识,超时毫秒):#求值宿主半
    """把宿主半当作函数体在沙箱里求值；返回代码 return 的任何东西。"""
    try:#跑包装后的函数
        包装=f'def __cordis_host_main__():\n'+'\n'.join('    '+行 for 行 in 代码.splitlines() or [''])+'\n'#缩进为函数体
        局部={}#局部命名空间
        执行全局=dict(沙箱)#沙箱全局
        exec(compile(包装,f'cordis-dyn-{标识}.js','exec'),执行全局,局部)#编译执行定义
        return 局部['__cordis_host_main__']()#调用并返回
    except SyntaxError as 错误:#语法错误
        raise Exception(解析错误消息('code.host',语法错误上下文(错误))) from 错误#教学错误
