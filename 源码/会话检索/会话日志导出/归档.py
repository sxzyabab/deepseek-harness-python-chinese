'把一条会话的逻辑日志和它引用的附件打成 ZIP'
import io,json,re,zipfile
from ...基础设施.通用工具 import 紧凑json编码#对齐 JSON.stringify
from ...内核.会话 import 会话格式版本#当代格式版本
from ...会话.会话格式 import 会话格式日志文件名#规范日志文件名
from ...会话.会话持久化.异常 import 会话持久化未找到错误#缺席不是失败
from ...客户端.连接.rpc import 中止信号#桥上的取消信号

默认会话日志压缩级别=6#没写压缩级别时用 6
会话日志文件名=会话格式日志文件名(会话格式版本)#当代规范文件名
媒体类型扩展={#光栅媒体的扩展名
    'image/png':'png',
    'image/jpeg':'jpg',
    'image/webp':'webp',
    'image/gif':'gif',
}
安全段正则=re.compile(r'[^A-Za-z0-9_-]')#会话标识里不能进路径的字符
文件名非法=re.compile(r'[\\/\x00-\x1f\x7f]')#附件名里的分隔符和控制符


def 下游取消信号(信号):
    '持久化、检索和附件按 Event.is_set 看取消。桥的信号改交它内部的 Event'
    if 信号 is None:#没有信号
        return None#下游也不看
    if isinstance(信号,中止信号):#桥的 AbortSignal
        return 信号._事件#置位后 is_set 为真
    return 信号#已经是 Event 就原样交


def 若已中止则抛出(信号):
    '信号已中止则抛出。没有信号则继续'
    if 信号 is None:#没有信号
        return#继续
    抛出=getattr(信号,'throwIfAborted',None)#AbortSignal
    if callable(抛出):#有这个方法
        抛出()#已中止则抛
        return#没中止
    if callable(getattr(信号,'is_set',None)) and 信号.is_set():#Event 已置位
        raise Exception('The operation was aborted.')#与没有原因时的中止同一句


def 会话日志导出依赖(上下文):
    '解析导出要的持久化、检索、附件，以及可选的活会话库'
    return {#没挂上的服务是 None
        'sessionQuery':上下文.获取服务('sessionQuery'),#检索
        'sessionPersistence':上下文.获取服务('sessionPersistence'),#持久化
        'attachments':上下文.获取服务('attachments'),#附件
        'sessions':上下文.获取服务('sessions'),#活会话库，可以没有
    }


def 冲刷活会话日志(依赖,标识,信号=None):
    '读逻辑日志之前，把仍在内存里的这一条冲过耐久屏障。冷会话没有可冲的'
    若已中止则抛出(信号)#开始前
    会话库=依赖['sessions']#活会话库
    if 会话库 is None:#没挂
        return#没有内存日志
    会话=会话库.获取(标识)#按标识找
    if 会话 is None:#不在线
        return#冷会话
    会话库.冲洗(会话)#耐久检查点
    若已中止则抛出(信号)#冲完再看


def 序列化会话日志(头,事件列表):
    '把头和事件编成规范 JSONL：一行头，之后每个事件一行，末尾再换行'
    行={#物理头，键序跟当前 v2 头一致
        'type':'session',
        'version':头['version'],
        'id':头['id'],
        'createdAt':头['createdAt'],
    }
    if 'cwd' in 头:#有工作目录才写
        行['cwd']=头['cwd']
    if 'parentSession' in 头:#有父会话才写
        行['parentSession']=头['parentSession']
    行['isSeeded']=头['isSeeded']#是否种子
    if 'origin' in 头:#有来源才写
        行['origin']=头['origin']
    深度=头['delegationDepth'] if 'delegationDepth' in 头 else 0#缺省深度是 0
    if 深度 is None:#显式空也按 0
        深度=0
    行['delegationDepth']=深度#磁盘上必有
    if 'agentPreset' in 头:#有预设才写
        行['agentPreset']=头['agentPreset']
    行列表=[紧凑json编码(行)]#头行
    for 事件 in 事件列表:#按序号
        行列表.append(紧凑json编码(事件))#事件行
    return '\n'.join(行列表)+'\n'#尾换行


def 读会话日志文本(持久化,标识,信号=None):
    '经读句柄读完整逻辑日志并序列化。会话不存在时返回 None，其它失败照样抛'
    下游=下游取消信号(信号)#下游认 Event
    选项={} if 下游 is None else {'signal':下游}#打开和读取都带上
    try:#缺席由打开决定
        句柄=持久化.打开(标识,'read',选项)#读句柄
    except 会话持久化未找到错误:#没有这份日志
        return None#不是损坏
    try:#读完一定关
        结果=句柄.读取事件切片(0,None,选项)#从 0 读到末尾
        return 序列化会话日志(句柄.header,结果['events'])#规范 JSONL
    finally:#句柄必须关
        句柄.关闭()#关


def 收集附件引用(内容,图片表,文件表):
    '从已声明的 V4 内容数组里收集直接的图片块和文件块'
    if not isinstance(内容,list):#不是数组就没有附件块
        return#跳过
    for 值 in 内容:#逐块
        if not isinstance(值,dict):#不是对象
            continue#跳过
        附件=值.get('attachment')#附件引用
        if 值.get('type')=='image' and isinstance(附件,dict):#图片
            图片表[str(附件.get('attachmentId'))]=附件#按标识去重
        if 值.get('type')=='file' and isinstance(附件,dict):#文件
            文件表[str(附件.get('attachmentId'))+'\0'+str(附件.get('name'))]=附件#标识加名字去重


def 安全会话标识段(标识):
    '把会话标识收成一个 ZIP 路径段。斜杠、点段和分隔符都换成下划线'
    return 安全段正则.sub('_',str(标识))#单个路径段


def 会话日志zip文件名(会话标识):
    '根会话这份导出归档的下载文件名'
    return 'dsh-session-'+安全会话标识段(会话标识)+'.zip'#固定前缀


def 会话日志zip条目(依赖,根内容,会话标识,含后代,信号=None):
    '按 ZIP 顺序交出根日志、子会话日志，然后是去重后的图片和文件'
    图片表={}#按附件标识
    文件表={}#按附件标识和存储名
    下游=下游取消信号(信号)#检索和附件认 Event

    def 记下附件(文本):
        '扫描一份已存日志，把附件引用并进上面两张表。解析不了的行没有附件'
        for 行 in 文本.split('\n'):#逐行
            if 行=='':#空行
                continue#跳过
            try:#坏行不能引用附件
                事件=json.loads(行)#一条事件
            except json.JSONDecodeError:#不是 JSON
                continue#日志原文仍会原样导出
            if not isinstance(事件,dict):#不是对象
                continue#不透明
            数据=事件.get('data')#载荷
            if not isinstance(数据,dict):#没有载荷
                continue#不透明
            类型=事件.get('type')#事件类型
            if 类型 in ('user/message','tool/ptc-dispatch'):#内容在 data.content
                收集附件引用(数据.get('content'),图片表,文件表)#收集
                continue#这一行完了
            if 类型 in ('system/message','developer/message','tool/result','team/message/queued'):#内容在消息里
                消息=数据.get('message')#消息
                内容=消息.get('content') if isinstance(消息,dict) else None#消息内容
                收集附件引用(内容,图片表,文件表)#收集
                continue#这一行完了
            if 类型=='agent/inbox/spliced':#插入的消息
                插入=数据.get('inserted')#消息数组
                if isinstance(插入,list):#是数组才看
                    for 消息 in 插入:#逐条
                        if isinstance(消息,dict):#对象
                            收集附件引用(消息.get('content'),图片表,文件表)#收集
                continue#这一行完了
            if 类型=='compaction/summary':#折叠摘要
                收集附件引用(数据.get('summary'),图片表,文件表)#摘要
                收集附件引用(数据.get('rawOutput'),图片表,文件表)#原始输出
                continue#这一行完了
            if 类型=='assistant/message':#助手消息先收正文
                消息=数据.get('message')#消息
                内容=消息.get('content') if isinstance(消息,dict) else None#消息内容
                收集附件引用(内容,图片表,文件表)#正文
            elif 类型!='assistant/attempt':#其余事件不透明
                continue#不看流
            流=数据.get('stream')#嵌入流
            if not isinstance(流,list):#没有流
                continue#完
            for 记录 in 流:#逐段
                if not isinstance(记录,dict) or 记录.get('type')!='chunk':#不是块
                    continue#下一段
                块=记录.get('chunk')#块
                if isinstance(块,dict) and 块.get('type')=='block-end':#块结束才有完整附件
                    收集附件引用([块.get('block')],图片表,文件表)#这一块

    已见={会话标识}#根自己不算子会话

    def 收集(节点列表):
        '按谱系顺序交出子会话日志，并继续往下'
        for 节点 in 节点列表:#谱系顺序
            若已中止则抛出(信号)#每个节点前
            标识=节点['session']['header']['id']#子会话
            if 标识 in 已见:#已经收过
                continue#跳过
            已见.add(标识)#记下
            冲刷活会话日志(依赖,标识,信号)#活的先冲
            文本=读会话日志文本(依赖['sessionPersistence'],标识,信号)#再读
            若已中止则抛出(信号)#读完再看
            if 文本 is None:#没有落盘日志
                raise RuntimeError('subagent "'+str(标识)+'" has no stored log')#不能静默少导
            记下附件(文本)#这一份里的附件
            yield {#子日志条目
                'path':'subagents/'+安全会话标识段(标识)+'/'+会话日志文件名,
                'content':文本,
            }
            yield from 收集(节点['descendants'])#再下一层

    记下附件(根内容)#根日志里的附件
    yield {'path':会话日志文件名,'content':根内容}#根日志在最前
    if 含后代:#要子会话
        谱系=依赖['sessionQuery'].追踪会话谱系(会话标识,下游)#谱系
        若已中止则抛出(信号)#谱系之后
        yield from 收集(谱系['descendants'])#后代
    for 引用 in 图片表.values():#去重后的图片
        若已中止则抛出(信号)#读图前
        已存=依赖['attachments'].读取图像(引用,下游)#校验后的字节
        若已中止则抛出(信号)#读图后
        扩展=媒体类型扩展[引用['mediaType']]#未知类型直接失败
        yield {'path':'media/'+str(引用['attachmentId'])+'.'+扩展,'data':已存['data']}#图片条目
    for 引用 in 文件表.values():#去重后的文件
        若已中止则抛出(信号)#读文件前
        摘要=str(引用['attachmentId'])#存储标识
        if 摘要.startswith('sha256:'):#只去掉前缀
            摘要=摘要[len('sha256:'):]#余下的摘要
        名=文件名非法.sub('_',str(引用['name']))#去掉分隔符
        if 名=='.' or 名=='..' or 名=='':#不能是点段或空名
            名='file'#固定名
        路径='files/'+摘要[:2]+'/'+摘要+'/'+名#摘要目录
        yield {'path':路径,'chunks':依赖['attachments'].读取文件流(引用,下游)}#仍是分块


class 响应容量门:
    '同步生成器在交出下一块之前检查取消。调用方来取，才算拉开了容量'
    def __init__(自身):
        '还没有挂起的生产者'
        自身._待放=None#放开回调

    def 等待(自身,信号):
        '取消则抛出。下一次拉取由生成器的调用方决定'
        若已中止则抛出(信号)#已中止就不要再写

    def 已拉取(自身):
        '消费方取走一块后放开生产者'
        待放=自身._待放#当前等待
        自身._待放=None#清掉
        if callable(待放):#真有人在等
            待放()#放开


def 流式会话日志zip(依赖,根内容,会话标识,含后代,压缩级别,信号):
    '把导出条目打成一份 ZIP。中途失败不交出截断归档'
    门=响应容量门()#每写一条之前看取消

    def 生成():
        '全部条目成功后才交出字节。失败时缓冲作废'
        缓冲=io.BytesIO()#一份归档
        归档=zipfile.ZipFile(缓冲,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=压缩级别)#DEFLATE
        try:#失败也要关上归档
            for 条目 in 会话日志zip条目(依赖,根内容,会话标识,含后代,信号):#ZIP 顺序
                门.等待(信号)#下一条之前
                if 'content' in 条目:#日志文本
                    归档.writestr(条目['path'],条目['content'].encode('utf-8'))#整段编码
                elif 'data' in 条目:#图片字节
                    归档.writestr(条目['path'],bytes(条目['data']))#已有上限的图片
                else:#文件按块写，不把整份留在一张表里
                    目标=归档.open(条目['path'],'w')#这一条
                    try:#写完或失败都关条目
                        for 块 in 条目['chunks']:#逐块
                            门.等待(信号)#下一块之前
                            if 块 is not None and len(块)>0:#空块跳过
                                目标.write(bytes(块))#写入
                    finally:#条目必须关
                        目标.close()#关这一条
        finally:#中央目录在关闭时写完
            归档.close()#关归档
        门.等待(信号)#交出前再看一次
        数据=缓冲.getvalue()#完整 ZIP
        门.已拉取()#调用方拿走这一块
        yield 数据#只在成功时交出

    return 生成()#调用方来迭代


__all__=[#与上游具名导出一致
    '默认会话日志压缩级别','会话日志导出依赖','冲刷活会话日志','会话日志文件名',
    '序列化会话日志','读会话日志文本','会话日志zip文件名','会话日志zip条目',
    '流式会话日志zip',
]
