"""Host 侧会话日志下载：把逻辑日志与引用附件打成 ZIP。"""
import io,json,re,zipfile#缓冲、JSON、净化、ZIP
from ...内核.会话 import 会话格式版本#当代格式版本
from ...会话.会话格式 import 会话格式日志文件名#规范日志文件名
from ...会话.会话持久化 import 会话持久化未找到错误#缺席

默认会话日志压缩级别=6#缺省 DEFLATE 级别
媒体类型扩展={#光栅媒体扩展
    'image/png':'png','image/jpeg':'jpg','image/webp':'webp','image/gif':'gif',
}#扩展结束
安全段正则=re.compile(r'[^A-Za-z0-9_-]')#会话 id 净化
文件名非法=re.compile(r'[\\/\x00-\x1f\x7f]')#附件名非法码元

def 会话日志导出依赖(上下文):#解析导出服务
    """解析导出所需的持久化、检索与附件服务。"""
    return {#依赖
        'sessionQuery':上下文.获取服务('sessionQuery') if hasattr(上下文,'获取服务') else getattr(上下文,'sessionQuery',None),#检索
        'sessionPersistence':上下文.获取服务('sessionPersistence') if hasattr(上下文,'获取服务') else getattr(上下文,'sessionPersistence',None),#持久化
        'attachments':上下文.获取服务('attachments') if hasattr(上下文,'获取服务') else getattr(上下文,'attachments',None),#附件
        'sessions':getattr(上下文,'sessions',None),#活会话库
    }#结束

def 冲刷活会话日志(依赖,标识,信号=None):#冲刷活会话
    """读前经会话库耐久屏障冲刷一条仍活的会话。"""
    _若已中止(信号)#取消
    会话库=依赖.get('sessions') if isinstance(依赖,dict) else None#会话库
    if 会话库 is None:#无
        return#无活缓冲
    会话=会话库.get(标识)#活会话
    if 会话 is None:#冷或缺席
        return#无需冲刷
    会话库.flush(会话)#耐久屏障
    _若已中止(信号)#再取消

会话日志文件名=会话格式日志文件名(会话格式版本)#当代规范文件名

def 序列化会话日志(头,事件列表):#序列化逻辑日志
    """把头与事件编成规范 JSONL 文本。"""
    行={'type':'session','version':头['version'],'id':头['id'],'createdAt':头['createdAt'],
        'isSeeded':头['isSeeded'],'delegationDepth':头['delegationDepth'] if 'delegationDepth' in 头 else 0}#物理头
    if 'cwd' in 头:#cwd
        行['cwd']=头['cwd']#带上
    if 'parentSession' in 头:#父
        行['parentSession']=头['parentSession']#带上
    if 'origin' in 头:#来源
        行['origin']=头['origin']#带上
    if 'agentPreset' in 头:#预设
        行['agentPreset']=头['agentPreset']#带上
    行列表=[json.dumps(行,ensure_ascii=False,separators=(',',':'),allow_nan=False)]#头行
    for 事件 in 事件列表:#逐事件
        行列表.append(json.dumps(事件,ensure_ascii=False,separators=(',',':'),allow_nan=False))#事件行
    return '\n'.join(行列表)+'\n'#尾换行

def 读会话日志文本(持久化,标识,信号=None):#读完整逻辑日志
    """经读句柄读取并序列化；缺席返回 None。"""
    选项={} if 信号 is None else {'signal':信号}#选项
    try:#打开
        句柄=持久化.打开(标识,'read',选项) if hasattr(持久化,'打开') else 持久化.open(标识,'read',选项)#读句柄
    except 会话持久化未找到错误:#缺席
        return None#无
    try:#读
        结果=句柄.读(0,None,选项) if hasattr(句柄,'读') else 句柄.read(0,None,选项)#全读
        事件=结果['events'] if isinstance(结果,dict) else 结果.events#事件
        头=句柄.header if hasattr(句柄,'header') else 句柄.头#头
        return 序列化会话日志(头,事件)#序列化
    finally:#关闭
        if hasattr(句柄,'关闭'):#中文
            句柄.关闭()#关
        else:#上游
            句柄.close()#关

def 收集附件引用(内容,图片表,文件表):#收集内容块附件
    """从已声明 V4 内容数组收集直接附件块。"""
    if not isinstance(内容,list):#非数组
        return#跳过
    for 值 in 内容:#逐块
        if not isinstance(值,dict):#非对象
            continue#跳过
        附件=值.get('attachment')#附件
        if 值.get('type')=='image' and isinstance(附件,dict):#图片
            图片表[str(附件.get('attachmentId'))]=附件#去重
        if 值.get('type')=='file' and isinstance(附件,dict):#文件
            文件表[str(附件.get('attachmentId'))+'\0'+str(附件.get('name'))]=附件#去重

def 收集事件附件引用(事件,图片表,文件表):#收集事件附件
    """只从已声明第一方内容字段与完成助手块收集引用。"""
    if not isinstance(事件,dict):#非对象
        return#跳过
    数据=事件.get('data')#载荷
    if not isinstance(数据,dict):#无载荷
        return#跳过
    类型=事件.get('type')#类型
    if 类型 in ('user/message','tool/ptc-dispatch'):#内容在 data.content
        收集附件引用(数据.get('content'),图片表,文件表)#收集
        return#结束
    if 类型 in ('system/message','developer/message','tool/result','team/message/queued'):#消息内容
        消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}#消息
        收集附件引用(消息.get('content'),图片表,文件表)#收集
        return#结束
    if 类型=='agent/inbox/spliced':#插入消息
        插入=数据.get('inserted')#插入
        if not isinstance(插入,list):#非数组
            return#跳过
        for 消息 in 插入:#逐条
            if isinstance(消息,dict):#对象
                收集附件引用(消息.get('content'),图片表,文件表)#收集
        return#结束
    if 类型=='compaction/summary':#折叠摘要
        收集附件引用(数据.get('summary'),图片表,文件表)#摘要
        收集附件引用(数据.get('rawOutput'),图片表,文件表)#原始输出
        return#结束
    if 类型=='assistant/message':#助手消息
        消息=数据.get('message') if isinstance(数据.get('message'),dict) else {}#消息
        收集附件引用(消息.get('content'),图片表,文件表)#内容
    elif 类型!='assistant/attempt':#其它
        return#不透明
    流=数据.get('stream')#嵌入流
    if isinstance(流,list):#有流
        for 记录 in 流:#逐记录
            if isinstance(记录,dict) and 记录.get('type')=='chunk':#块
                块=记录.get('chunk') if isinstance(记录.get('chunk'),dict) else {}#块
                if 块.get('type')=='block-end':#块结束
                    收集附件引用([块.get('block')],图片表,文件表)#块

def 产物内附件引用(文本):#扫描产物文本
    """从已存产物文本收集去重附件引用。"""
    图片表={}#图片
    文件表={}#文件
    for 行 in 文本.split('\n'):#逐行
        if 行=='':#空
            continue#跳过
        try:#解析
            事件=json.loads(行)#JSON
        except (json.JSONDecodeError,ValueError,TypeError):
            continue#无法引用附件
        收集事件附件引用(事件,图片表,文件表)#收集
    return {'images':图片表,'files':文件表}#去重表

def 安全会话标识段(标识):#安全路径段
    """把未校验会话 id 收成单个 ZIP 路径段。"""
    return 安全段正则.sub('_',str(标识))#净化

def 会话日志zip文件名(会话标识):#归档文件名
    """根会话导出归档文件名。"""
    return f'dsh-session-{安全会话标识段(会话标识)}.zip'#文件名

def 媒体条目路径(引用):#媒体路径
    """内容寻址的媒体 ZIP 路径。"""
    扩展=媒体类型扩展.get(引用.get('mediaType'),'bin')#扩展
    return f"media/{引用.get('attachmentId')}.{扩展}"#路径

def 文件条目路径(引用):#文件路径
    """保留摘要与文件名的 ZIP 路径。"""
    摘要=str(引用.get('attachmentId','')).replace('sha256:','')#去前缀
    名=文件名非法.sub('_',str(引用.get('name','')))#净化名
    安全名='file' if 名 in ('.','..','') else 名#避免点段
    return f'files/{摘要[:2]}/{摘要}/{安全名}'#路径

def 会话日志zip条目(依赖,根内容,会话标识,含后代,信号=None):#ZIP 条目
    """按 ZIP 顺序产出根日志、后代日志与附件。"""
    条目列表=[]#条目
    图片表={}#图片去重
    文件表={}#文件去重
    def 记下附件(文本):#合并引用
        """把一份日志中的附件并入去重表。"""
        引用=产物内附件引用(文本)#扫描
        图片表.update(引用['images'])#图片
        文件表.update(引用['files'])#文件
    记下附件(根内容)#根
    条目列表.append({'path':会话日志文件名,'content':根内容})#根日志
    if 含后代:#含后代
        已见={会话标识}#已见 id
        检索=依赖['sessionQuery']#检索
        谱系=检索.追踪会话谱系(会话标识,信号) if hasattr(检索,'追踪会话谱系') else 检索.traceSession(会话标识,信号)#谱系
        后代=谱系['descendants'] if isinstance(谱系,dict) else getattr(谱系,'descendants',())#后代
        def 收集(节点列表):#递归后代
            """按谱系顺序收集子智能体日志。"""
            for 节点 in 节点列表:#逐节点
                _若已中止(信号)#取消
                会话=节点['session'] if isinstance(节点,dict) else 节点.session#会话记录
                头=会话['header'] if isinstance(会话,dict) else 会话.header#头
                标识=头['id']#id
                if 标识 in 已见:#重复
                    continue#跳过
                已见.add(标识)#记下
                冲刷活会话日志(依赖,标识,信号)#冲刷
                文本=读会话日志文本(依赖['sessionPersistence'],标识,信号)#读
                _若已中止(信号)#再取消
                if 文本 is None:#缺日志
                    raise RuntimeError(f'subagent "{标识}" has no stored log')#失败
                记下附件(文本)#附件
                条目列表.append({'path':f'subagents/{安全会话标识段(标识)}/{会话日志文件名}','content':文本})#子日志
                子代=节点['descendants'] if isinstance(节点,dict) else getattr(节点,'descendants',())#再下
                收集(子代)#递归
        收集(后代)#从根后代起
    附件库=依赖['attachments']#附件库
    for 引用 in 图片表.values():#图片
        _若已中止(信号)#取消
        已存=附件库.readImage(引用,信号) if hasattr(附件库,'readImage') else 附件库.读图片(引用,信号)#读
        数据=已存['data'] if isinstance(已存,dict) else 已存.data#字节
        条目列表.append({'path':媒体条目路径(引用),'data':数据})#图片条目
    for 引用 in 文件表.values():#文件
        _若已中止(信号)#取消
        流=附件库.readFileStream(引用,信号) if hasattr(附件库,'readFileStream') else 附件库.读文件流(引用,信号)#流
        条目列表.append({'path':文件条目路径(引用),'chunks':流})#文件条目
    return 条目列表#条目

def 流式会话日志zip(依赖,根内容,会话标识,含后代,压缩级别,信号=None):#同步 ZIP 字节
    """把导出条目打成一份完整 ZIP 字节缓冲。"""
    缓冲=io.BytesIO()#内存
    with zipfile.ZipFile(缓冲,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=压缩级别) as 归档:#写
        for 条目 in 会话日志zip条目(依赖,根内容,会话标识,含后代,信号):#逐条目
            _若已中止(信号)#取消
            if 'content' in 条目:#文本
                归档.writestr(条目['path'],条目['content'].encode('utf-8'))#写文本
            elif 'data' in 条目:#图片字节
                归档.writestr(条目['path'],bytes(条目['data']))#写字节
            else:#文件流
                块列表=[]#块
                for 块 in 条目['chunks']:#逐块
                    _若已中止(信号)#取消
                    if 块:#非空
                        块列表.append(bytes(块))#记下
                归档.writestr(条目['path'],b''.join(块列表))#写合并
    return 缓冲.getvalue()#ZIP 字节

def _若已中止(信号):#取消
    """已中止则抛出。"""
    if 信号 is None:#无
        return#无事
    if hasattr(信号,'is_set') and 信号.is_set():#Event
        raise InterruptedError('session log export aborted')#取消
    if getattr(信号,'aborted',False):#AbortSignal
        raise InterruptedError('session log export aborted')#取消

__all__=[#公开面
    '默认会话日志压缩级别','会话日志导出依赖','冲刷活会话日志','会话日志文件名',
    '序列化会话日志','读会话日志文本','会话日志zip文件名','会话日志zip条目','流式会话日志zip',
]#结束
