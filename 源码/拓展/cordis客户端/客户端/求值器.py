from ....客户端.模块.客户端.通告 import 取握手窗口
import json#重定向表进页面
import threading#等页面里的异步函数体
from pywebbridge.基础 import undefined as 未定义#process 与 Buffer
from ..异常 import 错误#求值失败


__all__=['动态样式','求值客户端半','是否动态插件','客户端重定向','定时器重定向']


定时器重定向=(
    "browser timer globals are unavailable in dynamic packages. Declare inject: ['timer'] on the returned plugin, "
    "query Client Service.listService for the exact API, and close over that plugin ctx. In React, create timers "
    'from an event handler or React.useEffect and return callback-form disposers from the effect cleanup.'
)
客户端重定向={#被扣全局到教学
    'setTimeout':定时器重定向,
    'setInterval':定时器重定向,
    'clearTimeout':定时器重定向,
    'clearInterval':定时器重定向,
    'fetch':'network belongs to the HOST half: register a handler there with harness.handle(method, fn) and call it here via host.call(method, args).',
    'require':'modules cannot be imported here. React arrives as the `React` closure symbol; everything else goes through ctx services or host.call.',
}


class 动态样式:
    '一个包拥有的 style 标签。卸载时全部摘掉'
    def __init__(自身,插件标识):
        '记下拥有者'
        自身.插件标识=插件标识#data-dyn
        自身.标签={}#编号到元素

    def 插入(自身,样式文本,编号=None):
        '插入一条样式。编号由页面分配时沿用。返回拆除这一条的函数'
        if not isinstance(样式文本,str):#必须是 CSS 字符串
            raise 错误('styles.insert(css) needs a CSS string')
        if 编号 is None:#自己分配
            编号='py-'+str(len(自身.标签)+1)#编号
        文档=取握手窗口().document#当前文档
        标签=文档.createElement('style')#style
        标签.setAttribute('data-dyn',自身.插件标识)#拥有者
        标签.textContent=样式文本#正文
        文档.head.append(标签)#插进 head
        自身.标签[编号]=标签#记账
        def 拆除这一条(当前=编号):
            '摘掉这一条'
            自身.拆除一条(当前)#摘掉
        return 拆除这一条

    @property
    def 数量(自身):
        '还拥有的条数'
        return len(自身.标签)

    def 拆除一条(自身,编号):
        '按编号摘掉一条'
        元素=自身.标签.pop(编号,None)#取出
        if 元素 is not None:#还在
            元素.remove()#摘掉

    def 拆除全部(自身):
        '卸载路径。摘掉还拥有的全部标签'
        for 元素 in list(自身.标签.values()):#逐条
            元素.remove()#摘掉
        自身.标签.clear()#清空


def 是否动态插件(值):
    '函数，或带 apply 的对象，才能挂载'
    if isinstance(值,type) or (callable(值) and not isinstance(值,type)):#函数或类
        return True
    if 值 is None or 值 is 未定义 or isinstance(值,(str,int,float,bool,list,tuple)):#标量或列表
        return False
    if isinstance(值,dict):#字典形态
        return callable(值.get('apply'))
    return callable(getattr(值,'apply',None))#对象形态


class 已求值插件:
    '页面里求值得到的插件。apply 在页面上跑'
    def __init__(自身,编号,助手,描述,门面盒):
        '记下编号、助手和 inject'
        自身.编号=编号#页面表键
        自身._助手=助手#页面助手
        自身._门面盒=门面盒#当前门面
        自身.形态=描述['形态']#函数或对象
        自身.inject=list(描述['注入']) if 描述['形态']=='对象' else []#声明
        if 描述.get('名称'):#有名字
            自身.name=描述['名称']#可选名字

    def apply(自身,门面,配置=None):
        '把这次的门面交给页面，再跑插件的 apply'
        门面.页面助手=自身._助手#组件函数留在页面上，按编号调用
        自身._门面盒['门面']=门面#回调读这一份
        return 自身._助手.跑应用(自身.编号,配置)#页面上的 apply


求值体='''
const React=React实参
const 重定向表=JSON.parse(重定向文本)
const 陷阱={}
for (const 名字 of Object.keys(重定向表)) {
  陷阱[名字]=function(){
    throw new Error(名字+' is not available in a dynamic client half — '+重定向表[名字])
  }
}
const 标记='[cordis:'+插件标识参数+']'
function 参数文本(参数){
  if (参数 instanceof Error) return 参数.message
  if (typeof 参数==='string') return 参数
  if (参数===undefined) return 'undefined'
  try { return JSON.stringify(参数) } catch (错误) { return '[unserializable console argument]' }
}
const 页面控制台=globalThis.console
function 转发(级别){
  return function(){
    const 参数=Array.prototype.slice.call(arguments)
    页面控制台[级别].apply(页面控制台,[标记].concat(参数))
    if (级别!=='error') return
    记下错误(参数.map(参数文本).join(' ').slice(0,500))
  }
}
const console=new Proxy(页面控制台,{
  get:function(目标,属性){
    if (属性==='log'||属性==='info'||属性==='warn'||属性==='error'||属性==='debug') return 转发(属性)
    const 值=目标[属性]
    return typeof 值==='function'?值.bind(目标):值
  }
})
let 样式序号=0
const styles={
  insert:function(css){
    if (typeof css!=='string') throw new Error('styles.insert(css) needs a CSS string')
    const 编号=String(++样式序号)
    插入样式(编号,css)
    return function(){ 拆除样式(编号) }
  }
}
const host={
  call:function(method,args){
    if (arguments.length<2) args=null
    return 调用宿主(method,args===undefined?null:args)
  }
}
const harness=new Proxy({},{
  get:function(_目标,属性){
    throw new Error('harness.'+String(属性)+' belongs to the HOST half (`code`): register handlers there with harness.handle(method, fn); the browser half calls them via host.call(method, args).')
  }
})
const setTimeout=陷阱.setTimeout
const setInterval=陷阱.setInterval
const clearTimeout=陷阱.clearTimeout
const clearInterval=陷阱.clearInterval
const fetch=陷阱.fetch
const require=陷阱.require
const process=undefined
const Buffer=undefined
const 表={}
const 回调表={}
let 插件序号=0
let 回调序号=0
function 可过(参数){
  return 参数.map(function(项){
    if (typeof 项==='function'){
      const 编号=String(++回调序号)
      回调表[编号]=项
      return {__函数:编号}
    }
    return 项
  })
}
function 描述一份(插件){
  if (typeof 插件==='function') return {形态:'函数',注入:[],名称:''}
  if (插件!==null && typeof 插件==='object' && typeof 插件.apply==='function') {
    return {形态:'对象',注入:Array.isArray(插件.inject)?插件.inject.slice():[],名称:typeof 插件.name==='string'?插件.name:''}
  }
  if (插件===undefined) return {形态:'未定义',注入:[],名称:''}
  return {形态:'其它',注入:[],名称:''}
}
function 建门面(){
  const 槽=new Proxy({},{
    get:function(_目标,属性){
      if (typeof 属性!=='string') return undefined
      return function(){ return 调用门面('slots.'+属性,可过(Array.prototype.slice.call(arguments))) }
    }
  })
  const 主题=new Proxy({},{
    get:function(_目标,属性){
      if (typeof 属性!=='string') return undefined
      return function(){ return 调用门面('theme.'+属性,可过(Array.prototype.slice.call(arguments))) }
    }
  })
  function 服务代理(名字){
    return new Proxy({},{
      get:function(_目标,属性){
        if (typeof 属性!=='string') return undefined
        return function(){ return 调用门面('service.'+名字+'.'+属性,可过(Array.prototype.slice.call(arguments))) }
      }
    })
  }
  return new Proxy({},{
    get:function(_目标,属性){
      if (typeof 属性!=='string') return undefined
      if (属性==='get') return function(名字){ return 调用门面('get',[名字]) }
      if (属性==='slots') return 槽
      if (属性==='theme') return 主题
      const 结果=读取门面(属性)
      if (结果 && 结果.kind==='call') {
        return function(){ return 调用门面(属性,可过(Array.prototype.slice.call(arguments))) }
      }
      if (结果 && 结果.kind==='service') return 服务代理(结果.name)
      if (结果 && 结果.kind==='value') return 结果.value
      return undefined
    },
    set:function(_目标,属性,值){
      写入门面(String(属性),值)
      return true
    },
    has:function(_目标,属性){
      return 询问门面(String(属性))===true
    }
  })
}
const 助手={
  描述:function(编号){ return 表[编号].描述 },
  调用回调:function(编号,参数){
    const 函数=回调表[编号]
    return 函数(参数)
  },
  跑应用:function(编号,配置){
    const 记录=表[编号]
    const 门面=建门面()
    if (typeof 记录.插件==='function') return 记录.插件(门面)
    return 记录.插件.apply(门面,配置)
  }
}
let 跑
try {
  跑=(async () => {
'''


求值尾='''
})()
} catch (原因) {
  if (原因 instanceof SyntaxError) 失败('语法:'+原因.message)
  else 失败(原因 instanceof Error ? 原因.message : String(原因))
  return 助手
}
跑.then(function(插件){
  const 描述=描述一份(插件)
  if (描述.形态==='未定义' || 描述.形态==='其它') {
    失败(描述.形态)
    return
  }
  const 编号=String(++插件序号)
  表[编号]={插件:插件,描述:描述}
  成功(编号)
}, function(原因){
  失败(原因 instanceof Error ? 原因.message : String(原因))
})
return 助手
'''


def 求值客户端半(插件标识,客户端代码,环境,样式):
    '把浏览器半当成异步函数体求值，返回未套运行器门面的插件'
    窗口=取握手窗口()#当前页
    门面盒={}#跑 apply 时填上
    完成=threading.Event()#异步函数体的门闩
    箱={}#编号或失败
    def 插入样式(编号,样式文本):
        '页面插入样式。编号由页面分配'
        样式.插入(样式文本,编号)#真实标签
    def 拆除样式(编号):
        '页面拆一条样式'
        样式.拆除一条(编号)#摘掉
    def 调用宿主(方法,参数):
        'host.call。参数省略时是 null'
        if 参数 is 未定义:#JSON 里没有 undefined
            参数=None#宿主收到 null
        return 环境['invoke'](方法,参数)
    def 记下错误(文本):
        'console.error 镜像进加载报告'
        环境['noteError'](str(文本))
    def 读取门面(属性):
        '页面 Proxy 的 get'
        门面=门面盒.get('门面')#当前门面
        if 门面 is None:#还没有
            return None
        return 门面.读取(属性)
    def 调用门面(属性,参数):
        '页面 Proxy 的调用'
        门面=门面盒.get('门面')#当前门面
        if 门面 is None:#还没有
            return None
        if 参数 is None:#没带参数
            参数=[]#空
        return 门面.调用(属性,list(参数))
    def 写入门面(属性,值):
        '页面 Proxy 的赋值'
        门面=门面盒.get('门面')#当前门面
        if 门面 is None:#还没有
            return False
        return 门面.写入(属性,值)
    def 询问门面(属性):
        '页面 Proxy 的 has'
        门面=门面盒.get('门面')#当前门面
        if 门面 is None:#还没有
            return False
        return 门面.询问(属性)
    def 成功(编号):
        '插件留在页面上，这里只收编号'
        箱['编号']=编号#编号
        完成.set()#放行
    def 失败(文本):
        '求值或返回值不合法'
        箱['失败']=文本#原因
        完成.set()#放行
    参数名=[
        '重定向文本','插件标识参数','插入样式','拆除样式','调用宿主','记下错误',
        '读取门面','调用门面','写入门面','询问门面','成功','失败','React实参',
    ]
    体=求值体+客户端代码+'\n'+求值尾#闭包体
    try:#构造。插件源码的语法错在这里抛
        工厂=窗口.Function(*参数名,体)#Function
    except SyntaxError as 原因:#浏览器解析失败
        raise 错误(
            'client half failed to parse in this browser: '+str(原因)+'\n'
            'The browser half is plain JavaScript (no JSX, no TypeScript); build elements with React.createElement.'
        ) from 原因
    助手=工厂(#环境
        json.dumps(客户端重定向,ensure_ascii=False),
        插件标识,
        插入样式,拆除样式,调用宿主,记下错误,
        读取门面,调用门面,写入门面,询问门面,
        成功,失败,
        窗口.React,
    )
    完成.wait()#阻塞到插件返回或失败
    if '失败' in 箱:#没有得到插件
        文本=str(箱['失败'])#原因
        if 文本.startswith('语法:'):#运行期才暴露的语法差
            raise 错误(
                'client half failed to parse in this browser: '+文本[len('语法:'):]+'\n'
                'The browser half is plain JavaScript (no JSX, no TypeScript); build elements with React.createElement.'
            )
        if 文本=='未定义':#忘了 return
            raise 错误(
                'client half returned `undefined` — did you forget `return`?\n'
                '  ✓ return (ctx) => { … }\n'
                "  ✓ return { name: '…', inject: ['slots'], apply(ctx) { … } }"
            )
        if 文本=='其它':#不是插件
            raise 错误('client half must `return` a plugin: a function, or an object with an `apply(ctx)` method')
        raise 错误(文本)
    编号=箱['编号']#页面表键
    描述=助手.描述(编号)#形态和 inject
    return 已求值插件(编号,助手,描述,门面盒)
