"""检查器后端使用的、与界域无关的 JavaScript 值描述。

对齐上游 `shared/cdp/remote-object.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '运行时远程对象类型','运行时远程对象子类型',
    '运行时属性预览','运行时对象预览','运行时远程对象描述符',
    '运行时后端对象引用','运行时远程对象',
]#公开面结束

运行时远程对象类型=(#远程对象类型
    'object','function','undefined','string','number','boolean','symbol','bigint',
)#类型结束

运行时远程对象子类型=(#远程对象子类型
    'array','null','node','regexp','date','map','set','weakmap','weakset',#集合类
    'iterator','generator','error','proxy','promise','typedarray',#异步与缓冲
    'arraybuffer','dataview','webassemblymemory','wasmvalue',#缓冲与Wasm
)#子类型结束

class 运行时属性预览:#属性预览
    """DevTools 内联渲染的浅属性。"""
    def __init__(自身,name,type,value=None,valuePreview=None,subtype=None):#构造
        """保存属性预览字段。"""
        自身.name=name#属性名
        自身.type=type#值类型或访问器
        自身.value=value#展示字符串
        自身.valuePreview=valuePreview#嵌套预览
        自身.subtype=subtype#子类型

class 运行时对象预览:#对象预览
    """从不携带活对象引用的浅对象渲染。"""
    def __init__(自身,type,overflow,properties,subtype=None,description=None):#构造
        """保存对象预览字段。"""
        自身.type=type#值类型
        自身.subtype=subtype#子类型
        自身.description=description#描述
        自身.overflow=overflow#是否溢出
        自身.properties=tuple(properties)#属性预览

class 运行时远程对象描述符:#远程对象描述符
    """一个 JavaScript 值的与引擎无关的描述。"""
    def __init__(自身,type,subtype=None,className=None,value=None,unserializableValue=None,description=None,preview=None):#构造
        """保存远程对象描述符字段。"""
        自身.type=type#值类型
        自身.subtype=subtype#子类型
        自身.className=className#类名
        自身.value=value#可序列化值
        自身.unserializableValue=unserializableValue#不可序列化字面量
        自身.description=description#描述
        自身.preview=preview#预览

class 运行时后端对象引用:#后端对象引用
    """一个界域会话中后端拥有的、对保留对象的引用。"""
    def __init__(自身,handle):#构造
        """保存后端句柄。"""
        自身.handle=handle#后端句柄

class 运行时远程对象:#远程对象
    """与界域无关的值，加上可选的后端与 Cordis 身份。"""
    def __init__(自身,descriptor,object=None,semanticReference=None):#构造
        """保存远程对象字段。"""
        自身.descriptor=descriptor#值描述符
        自身.object=object#后端引用
        自身.semanticReference=semanticReference#Cordis语义引用
