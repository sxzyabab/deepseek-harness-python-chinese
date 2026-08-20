"""无版本号、结构化克隆线路协议，连接同发行的宿主与工人代码。宿主把入站流量当敌对，因为模型代码可以伪造父端口消息；工人信任宿主应答。"""

class 工人启动数据:#宿主在spawn时经workerData交给工人的启动载荷
    """工人启动数据字段约定（运行时为dict）。"""
    代码='code'#已剥类型（纯JS）或Python程序体
    命名空间们='namespaces'#要物化的绑定命名空间；函数本身留在宿主侧
    最大输出字节='maxOutputBytes'#外层序列化日志加上完成值或失败诊断的硬上限

工人启动数据字段=('code','namespaces','maxOutputBytes')#程序体、命名空间声明、外层输出字节上限

# 命名空间声明项约定：
# { global: str, names: list[str], errorClass?: { name: str, memberNameProperty: str } }

class 调用消息:#工人→宿主：一次桥接的绑定调用
    """绑定调用消息字段约定。"""
    类型='type'#消息标签，取值'call'
    编号='id'#工人签发的相关id；宿主对每个id至多应答一次，重复则忽略
    全局='global'#调用所针对的命名空间全局名
    名字='name'#命名空间内的函数名
    实参='args'#单一实参，扁平无损JSON线路值

调用消息字段=('type','id','global','name','args')#标签call、相关id、全局名、函数名、编码实参

class 日志消息:#工人→宿主：捕获的文本，急切流式发送
    """日志消息字段约定。"""
    类型='type'#消息标签，取值'log'
    文本='text'#捕获的文本

日志消息字段=('type','text')#标签log与捕获文本

class 输出超限消息:#工人→宿主：工人侧捕获或完成值计量已超过外层上限
    """输出超限消息字段约定。"""
    类型='type'#消息标签，取值'output-limit'

输出超限消息字段=('type',)#标签output-limit

class 完成消息:#工人→宿主：程序已结算；日志不在此携带
    """完成消息字段约定。error携带程序异常、无效完成或输出溢出；value仅在干净完成且产出了值时出现。"""
    类型='type'#消息标签，取值'done'
    值='value'#可选的完成值线路编码
    错误='error'#可选的失败字段{kind,message}

完成消息字段=('type','value','error')#标签done、可选完成值线路编码、可选失败字段

class 工人到宿主类型:#工人发出的全部消息标签
    """工人→宿主联合标签（线路值就是标签字符串）。"""
    调用='call'#绑定调用
    日志='log'#捕获文本
    输出超限='output-limit'#工人侧触顶
    完成='done'#程序已结算

工人到宿主类型元组=('call','log','output-limit','done')#工人→宿主联合标签元组

class 应答消息:#宿主→工人：对一条调用消息的应答
    """宿主应答字段约定：成功带回无损JSON，失败带回错误说明。"""
    类型='type'#消息标签，取值'reply'
    编号='id'#相关调用id
    成功='ok'#成败布尔
    值='value'#成功时可选无损JSON线路值
    消息='message'#失败时可选错误说明

应答消息字段=('type','id','ok','value','message')#标签reply、相关id、成败、可选值、可选说明

# 完成消息.error.kind 合法取值：'exception' | 'invalid-output' | 'output-limit'
完成失败种类=('exception','invalid-output','output-limit')#done.error.kind封闭联合
