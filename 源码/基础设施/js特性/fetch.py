'domonic.webapi.fetch的中文封装。公开名称改成中文，行为按原文转发'
from domonic.webapi.fetch import (#原文公开名称
    FetchedSet,#已请求集合
    Headers,#报文头
    Request,#请求报文
    Response,#响应报文
    fetch,#请求
    fetch_pooled,#请求池化
    fetch_set,#请求集合
    fetch_threaded,#请求线程化
)

__all__=[#模块导出
    '已请求集合',#多次请求的结果
    '报文头',#头表
    '响应数据',#json的类与实例分发
    '响应报文',#响应
    '请求报文',#请求
    '请求',#发出请求
    '请求_逐个',#按顺序取回
    '请求_多线程',#用线程取回
    '请求_线程池',#用线程池取回
]

################################
#已请求集合
################################
class 已请求集合(FetchedSet):
    '多次请求收齐后的结果'
    def __init__(自身,*位置参数,**关键字参数):
        '原文用可变参数收下每一次的结果'
        FetchedSet.__init__(自身,*位置参数,**关键字参数)#可变参数是原文签名

    @property
    def 结果(自身):
        '各次结果'
        return 自身.results#结果

    @结果.setter
    def 结果(自身,值):
        '写入各次结果'
        自身.results=值#结果

    def 追加(自身,结果):
        '再收下一条结果'
        return 自身.append(结果)#追加

    def 当完成(自身,函数):
        '结果已经齐了，把整表交给函数'
        return 自身.oncomplete(函数)#当完成

################################
#报文头
################################
class 报文头(Headers):
    '头名不区分大小写'
    def __init__(自身,初始值=None):
        '用初始值构造头表'
        Headers.__init__(自身,初始值)#初始值

    @property
    def 头部(自身):
        '头名到各值的表'
        return 自身.headers#头部

    @头部.setter
    def 头部(自身,值):
        '写入头表'
        自身.headers=值#头部

    def 追加(自身,名称,值):
        '追加一个值，不覆盖同名头'
        return 自身.append(名称,值)#追加

    def 删除(自身,名称):
        '删去这个名字下的全部值'
        return 自身.delete(名称)#删除

    def 获取(自身,名称,默认=None):
        '同名值合并后返回，没有则返回默认'
        return 自身.get(名称,默认)#获取

    def 获取设置饼干(自身):
        'set-cookie的每个值单独列出'
        return 自身.getSetCookie()#获取设置饼干

    def 具有(自身,名称):
        '是否有这个名字'
        return 自身.has(名称)#具有

    def 设置(自身,名称,值):
        '有同名头则覆盖，否则写下'
        return 自身.set(名称,值)#设置

    def 键(自身):
        '全部头名'
        return 自身.keys()#键

    def 值(自身):
        '全部头值，同名的已合并'
        return 自身.values()#值

    def 条目(自身):
        '头名与合并后的值'
        return 自身.entries()#条目

    def 原始项(自身):
        '头名与每一个原始值，同名不合并'
        return 自身.raw_items()#原始项

    def 逐个(自身,回调,此参数=None):
        '按条目把值、名称和本表交给回调'
        return 自身.forEach(回调,此参数)#逐个

    def 映射(自身,回调,此参数=None):
        '按条目调用回调并收集返回值'
        return 自身.map(回调,此参数)#映射

    def 过滤(自身,回调,此参数=None):
        '留下回调判定为真的条目'
        return 自身.filter(回调,此参数)#过滤

    def 归约(自身,回调,初始值):
        '从初始值起逐条归并'
        return 自身.reduce(回调,初始值)#归约

    def 转字符串(自身):
        '转成字符串'
        return 自身.toString()#转字符串

    def 转对象(自身):
        '转成名字到合并值的字典'
        return 自身.toObject()#转对象

    def 转数据(自身):
        '转成可交给JSON的字典'
        return 自身.toJSON()#转数据

    def 复制(自身):
        '复制一份头部'
        return 自身.copy()#复制

################################
#响应的json
################################
class 响应数据:
    '类上用来构造数据响应，实例上用来读出正文'
    def __get__(自身,实例,所有者):
        '取用位置不同，转到原文json的不同用法'
        if 实例 is None:#类上是构造
            def 构造(数据,初始化=None):
                '用数据构造响应'
                return 所有者.json(数据,初始化)#原文类上的json
            return 构造#交回构造函数
        return 实例.json#原文实例上的json

################################
#响应报文
################################
class 响应报文(Response):
    '一次取回的状态、头部与正文'
    数据=响应数据()#类上构造，实例上读取
    def __init__(自身,网址=None,状态=None,状态文本=None,头部=None,正文=None,*,初始化=None,类型='default',已重定向=False,**关键字参数):
        '参数顺序与原文一致。错误、重定向和数据构造会用英文关键字再进来'
        if 关键字参数:#原文类方法写死了英文参数名
            Response.__init__(自身,**关键字参数)#英文关键字原样转交
            return
        Response.__init__(自身,网址,状态,状态文本,头部,正文,init=初始化,type=类型,redirected=已重定向)#中文参数

    @property
    def 网址(自身):
        '最终网址'
        return 自身.url#网址

    @网址.setter
    def 网址(自身,值):
        '写入网址'
        自身.url=值#网址

    @property
    def 状态(自身):
        '状态码'
        return 自身.status#状态

    @状态.setter
    def 状态(自身,值):
        '写入状态码'
        自身.status=值#状态

    @property
    def 状态文本(自身):
        '状态文本'
        return 自身.statusText#状态文本

    @状态文本.setter
    def 状态文本(自身,值):
        '写入状态文本'
        自身.statusText=值#状态文本

    @property
    def 头部(自身):
        '响应头。这是原文头部，不是报文头类的另一层'
        return 自身.headers#头部

    @头部.setter
    def 头部(自身,值):
        '写入响应头'
        自身.headers=值#头部

    @property
    def 类型(自身):
        '响应类型'
        return 自身.type#类型

    @类型.setter
    def 类型(自身,值):
        '写入响应类型'
        自身.type=值#类型

    @property
    def 已重定向(自身):
        '是否发生过重定向'
        return 自身.redirected#已重定向

    @已重定向.setter
    def 已重定向(自身,值):
        '写入是否重定向'
        自身.redirected=值#已重定向

    @property
    def 正文(自身):
        '正文'
        return 自身.body#正文

    @正文.setter
    def 正文(自身,值):
        '写入正文'
        自身.body=值#正文

    @property
    def 正文已使用(自身):
        '正文是否已经被读过'
        return 自身.bodyUsed#正文已使用

    @正文已使用.setter
    def 正文已使用(自身,值):
        '写入正文是否已使用'
        自身.bodyUsed=值#正文已使用

    @property
    def 成功(自身):
        '状态码是否落在成功范围'
        return 自身.ok#成功

    def 克隆(自身):
        '复制一份。正文已读时原文抛出TypeError。返回的是原文响应'
        return 自身.clone()#克隆

    @classmethod
    def 错误(类):
        '构造一个错误响应'
        return 类.error()#错误

    @classmethod
    def 重定向(类,网址,状态=302):
        '按重定向状态构造响应'
        return 类.redirect(网址,状态)#重定向

    def 数组缓冲(自身):
        '读出正文字节'
        return 自身.arrayBuffer()#数组缓冲

    def 字节(自身):
        '读出正文字节'
        return 自身.bytes()#字节

    def 二进制大对象(自身):
        '读出正文并交给二进制大对象'
        return 自身.blob()#二进制大对象

    def 表单数据(自身):
        '把正文读成表单'
        return 自身.formData()#表单数据

    def 文本(自身):
        '把正文读成文本'
        return 自身.text()#文本

################################
#请求报文
################################
class 请求报文(Request):
    '请求的方法、网址、头部与正文'
    def __init__(自身,网址=None,方法=None,头部=None,正文=None,模式=None,凭据=None,缓存=None,*,初始化=None,重定向=None,引用来源=None,引用来源策略=None,完整性=None,保持活动=None,信号=None,目的地='',优先级=None,双工=None):
        '参数顺序与原文一致，星号后只能用名字传入'
        Request.__init__(自身,网址,方法,头部,正文,模式,凭据,缓存,init=初始化,redirect=重定向,referrer=引用来源,referrerPolicy=引用来源策略,integrity=完整性,keepalive=保持活动,signal=信号,destination=目的地,priority=优先级,duplex=双工)#构造

    @property
    def 网址(自身):
        '请求网址'
        return 自身.url#网址

    @网址.setter
    def 网址(自身,值):
        '写入请求网址'
        自身.url=值#网址

    @property
    def 方法(自身):
        '请求方法'
        return 自身.method#方法

    @方法.setter
    def 方法(自身,值):
        '写入请求方法'
        自身.method=值#方法

    @property
    def 头部(自身):
        '请求头。这是原文头部'
        return 自身.headers#头部

    @头部.setter
    def 头部(自身,值):
        '写入请求头'
        自身.headers=值#头部

    @property
    def 模式(自身):
        '请求模式'
        return 自身.mode#模式

    @模式.setter
    def 模式(自身,值):
        '写入请求模式'
        自身.mode=值#模式

    @property
    def 凭据(自身):
        '凭据策略'
        return 自身.credentials#凭据

    @凭据.setter
    def 凭据(自身,值):
        '写入凭据策略'
        自身.credentials=值#凭据

    @property
    def 缓存(自身):
        '缓存策略'
        return 自身.cache#缓存

    @缓存.setter
    def 缓存(自身,值):
        '写入缓存策略'
        自身.cache=值#缓存

    @property
    def 重定向(自身):
        '重定向策略'
        return 自身.redirect#重定向

    @重定向.setter
    def 重定向(自身,值):
        '写入重定向策略'
        自身.redirect=值#重定向

    @property
    def 引用来源(自身):
        '引用来源'
        return 自身.referrer#引用来源

    @引用来源.setter
    def 引用来源(自身,值):
        '写入引用来源'
        自身.referrer=值#引用来源

    @property
    def 引用来源策略(自身):
        '引用来源策略'
        return 自身.referrerPolicy#引用来源策略

    @引用来源策略.setter
    def 引用来源策略(自身,值):
        '写入引用来源策略'
        自身.referrerPolicy=值#引用来源策略

    @property
    def 完整性(自身):
        '完整性校验'
        return 自身.integrity#完整性

    @完整性.setter
    def 完整性(自身,值):
        '写入完整性校验'
        自身.integrity=值#完整性

    @property
    def 保持活动(自身):
        '是否在页面结束后继续请求'
        return 自身.keepalive#保持活动

    @保持活动.setter
    def 保持活动(自身,值):
        '写入是否保持活动'
        自身.keepalive=值#保持活动

    @property
    def 信号(自身):
        '中止信号'
        return 自身.signal#信号

    @信号.setter
    def 信号(自身,值):
        '写入中止信号'
        自身.signal=值#信号

    @property
    def 目的地(自身):
        '请求目的地'
        return 自身.destination#目的地

    @目的地.setter
    def 目的地(自身,值):
        '写入请求目的地'
        自身.destination=值#目的地

    @property
    def 优先级(自身):
        '请求优先级'
        return 自身.priority#优先级

    @优先级.setter
    def 优先级(自身,值):
        '写入请求优先级'
        自身.priority=值#优先级

    @property
    def 双工(自身):
        '双工模式'
        return 自身.duplex#双工

    @双工.setter
    def 双工(自身,值):
        '写入双工模式'
        自身.duplex=值#双工

    @property
    def 正文(自身):
        '正文'
        return 自身.body#正文

    @正文.setter
    def 正文(自身,值):
        '写入正文'
        自身.body=值#正文

    @property
    def 正文已使用(自身):
        '正文是否已经被读过'
        return 自身.bodyUsed#正文已使用

    @正文已使用.setter
    def 正文已使用(自身,值):
        '写入正文是否已使用'
        自身.bodyUsed=值#正文已使用

    def 克隆(自身):
        '复制一份。正文已读时原文抛出TypeError。返回的是原文请求'
        return 自身.clone()#克隆

    def 数组缓冲(自身):
        '读出正文字节'
        return 自身.arrayBuffer()#数组缓冲

    def 字节(自身):
        '读出正文字节'
        return 自身.bytes()#字节

    def 二进制大对象(自身):
        '读出正文并交给二进制大对象'
        return 自身.blob()#二进制大对象

    def 表单数据(自身):
        '把正文读成表单'
        return 自身.formData()#表单数据

    def 数据(自身):
        '把正文读成数据'
        return 自身.json()#数据

    def 文本(自身):
        '把正文读成文本'
        return 自身.text()#文本

################################
#请求函数
################################
def 请求(输入,初始化=None,**关键字参数):
    '取回资源。返回原文期约，兑现值是原文响应'
    return fetch(输入,初始化,**关键字参数)#请求

def 请求_逐个(网址,回调函数=None,错误处理器=None,**关键字参数):
    '按顺序取回多个网址'
    return fetch_set(网址,回调函数,错误处理器,**关键字参数)#请求集合

def 请求_多线程(网址,回调函数=None,错误处理器=None,**关键字参数):
    '用线程同时取回多个网址'
    return fetch_threaded(网址,回调函数,错误处理器,**关键字参数)#请求并行

def 请求_线程池(网址,回调函数=None,错误处理器=None,**关键字参数):
    '用线程池取回多个网址'
    return fetch_pooled(网址,回调函数,错误处理器,**关键字参数)#请求池化

词元={#英到中，按词元而不是整个名字
    'Fetched':'已请求',
    'Set':'集合',#名词。getSetCookie里的Set是动词，方法名用设置
    'set':'设置',
    'Headers':'报文头',
    'Request':'请求报文',
    'Response':'响应报文',
    'fetch':'请求',
    'pooled':'池化',
    'threaded':'线程化',
    'append':'追加',
    'delete':'删除',
    'get':'获取',
    'Cookie':'饼干',
    'has':'具有',
    'keys':'键',
    'values':'值',
    'entries':'条目',
    'raw':'原始',
    'items':'项',
    'for':'逐',
    'Each':'个',
    'map':'映射',
    'filter':'过滤',
    'reduce':'归约',
    'to':'转',
    'String':'字符串',
    'Object':'对象',
    'JSON':'数据',
    'json':'数据',
    'copy':'复制',
    'init':'初始化',
    'name':'名称',
    'value':'值',
    'default':'默认',
    'callback':'回调',
    'this':'此',
    'Arg':'参数',
    'initial':'初始',
    'Value':'值',
    'array':'数组',
    'Buffer':'缓冲',
    'bytes':'字节',
    'blob':'二进制大对象',
    'form':'表单',
    'Data':'数据',
    'text':'文本',
    'Text':'文本',
    'body':'正文',
    'Used':'已使用',
    'url':'网址',
    'urls':'网址',
    'status':'状态',
    'ok':'成功',
    'type':'类型',
    'redirected':'已重定向',
    'redirect':'重定向',
    'clone':'克隆',
    'error':'错误',
    'method':'方法',
    'mode':'模式',
    'credentials':'凭据',
    'cache':'缓存',
    'referrer':'引用来源',
    'Policy':'策略',
    'integrity':'完整性',
    'keepalive':'保持活动',
    'signal':'信号',
    'destination':'目的地',
    'priority':'优先级',
    'duplex':'双工',
    'results':'结果',
    'oncomplete':'当完成',
    'function':'函数',
    'handler':'处理器',
    'input':'输入',
}
