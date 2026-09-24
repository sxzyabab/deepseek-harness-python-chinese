"""JSONL 会话产物的耐久整代发布（对齐 generation.ts；迁移校验进程内完成）。"""
import hashlib#摘要
import os#路径与 fs
import secrets#随机令牌
import sys#平台
import time#让出近似
from ...内核.会话 import 会话,会话标识#Session 重开
from ...模型后端.llm import 块组装器,展开助手流#嵌入流回放
from ...工具.值 import 深相等json#深相等
from ..会话格式 import 会话格式错误#格式错误
from ..会话格式目录 import 会话格式目录,会话格式不支持迁移错误#格式目录
from ..会话格式目录.消息投影 import 当前会话消息投影表#当代消息投影
from ..会话持久化.存储契约 import 校验已存事件#已存事件校验
from .格式 import 代次日志文件名,日志后缀,扫描日志#格式辅助
from .zstd编解码 import (#zstd 公开面
    压缩zstd帧,#压缩帧
    创建zstd帧解码器,#帧解码器
    解压zstd前缀,#前缀解压
    扫描zstd帧,#帧扫描
)#zstd
from .win32 import 发布新文件win32,是否eexist as win32是否eexist#Win32 发布

迁移解码让出间隔秒=0.5#迁移解码让出间隔
迁移工作块字节=1024*1024#迁移工作块
迁移写块字节=4*1024*1024#迁移写块

class 代次源变更错误(Exception):#源变更
    """历史源在解码与迁移遍之后发生了变更。"""
    def __init__(自身,路径):#构造
        """记下修订已变的历史代。"""
        自身.path=路径#路径
        自身.name='JsonlGenerationSourceChangedError'#错误名
        super().__init__(f'historical session generation changed during migration: "{路径}"')#消息

class 代次不支持迁移错误(Exception):#不支持迁移
    """历史产物完好，但格式边拒绝其内容。"""
    def __init__(自身,来自版本,原因):#构造
        """记下源版本与格式边拒绝。"""
        自身.fromVersion=来自版本#源版本
        自身.reason=原因#原因
        自身.name='JsonlGenerationUnsupportedMigrationError'#错误名
        super().__init__(str(原因))#消息
        自身.__cause__=原因#cause

class 代次目标冲突错误(Exception):#目标冲突
    """当代文件名已指向不同或非法字节。"""
    def __init__(自身,路径,原因):#构造
        """记下阻止独占发布的目标。"""
        自身.path=路径#路径
        自身.reason=原因#原因
        自身.name='JsonlGenerationTargetConflictError'#错误名
        super().__init__(f'current session generation already exists at "{路径}": {原因}')#消息
        自身.__cause__=原因#cause

def 物理身份(状态):#从 os.stat_result 造身份
    """与精确代字节一并捕获的 stat 身份。"""
    return {#物理身份
        'dev':状态.st_dev,#设备
        'ino':状态.st_ino,#inode
        'size':状态.st_size,#大小
        'mtimeNs':getattr(状态,'st_mtime_ns',int(状态.st_mtime*1e9)),#mtime
        'ctimeNs':getattr(状态,'st_ctime_ns',int(状态.st_ctime*1e9)),#ctime
    }#结束

def 身份串(值):#身份字符串
    """冒号拼接物理身份字段。"""
    return ':'.join([str(值['dev']),str(值['ino']),str(值['size']),str(值['mtimeNs']),str(值['ctimeNs'])])#拼接

def 是否eexist(错误):#是否 EEXIST
    """文件系统冲突是否表示目标已存在。"""
    if win32是否eexist(错误):#Win32
        return True
    if getattr(错误,'errno',None)==getattr(os,'EEXIST',17):#POSIX
        return True
    return isinstance(错误,FileExistsError)#FileExistsError

def 读稳定jsonl文件(路径,信号=None):#读稳定修订
    """以单次重试读取稳定修订；持续写者重叠时返回已提交预读前缀。"""
    _若已中止(信号)#取消
    之前=物理身份(os.stat(路径))#读前
    尝试=0#尝试计数
    while True:#直至稳定或取前缀
        _若已中止(信号)#取消
        with open(路径,'rb') as 文件:#读
            字节=文件.read()#字节
        _若已中止(信号)#取消
        之后=物理身份(os.stat(路径))#读后
        if 身份串(之前)==身份串(之后):#稳定
            return {'bytes':字节,'identity':之后}#快照
        if 尝试==1:#第二次仍不稳
            return {'bytes':字节[:之前['size']],'identity':之前}#预读前缀
        之前=之后#重试
        尝试+=1#递增

def _若已中止(信号):#取消检查
    """已中止则抛出。"""
    if 信号 is None:#无信号
        return#无事
    if 信号.is_set():#已中止
        raise InterruptedError('session migration preparation aborted')#包装

def _已存版本(头):#取已存版本
    """解析版本判别式，不校验版本特定字段。"""
    if not isinstance(头,dict) or isinstance(头,list):#非对象
        raise Error('corrupt session log: first line is not a JSON object')#损坏
    版本=头.get('version')#version
    if not isinstance(版本,int) or isinstance(版本,bool) or 版本<0:#非法
        raise Error('corrupt session log: header version is not a non-negative safe integer')#损坏
    return 版本#返回

def _解析json(文本,主题):#解析 JSON
    """解析 JSON 文本。"""
    import json#JSON
    try:
        return json.loads(文本)
    except (json.JSONDecodeError,TypeError,ValueError) as 错误:
        raise Error(f'corrupt session log: {主题} is not valid JSON') from 错误#包装

def _断言独立头帧(明文):#断言独立头帧
    """第一帧须恰好一行头记录。"""
    if len(明文)==0 or 明文.find(b'\n')!=len(明文)-1:#非恰好一行
        raise Error('corrupt Zstandard session log: first frame is not exactly one header line')#损坏

def _断言代次路径(源路径,源版本,当代路径,当代版本,压缩):#断言路径
    """断言源与当代文件名/目录，返回后缀。"""
    期望源=代次日志文件名(源版本,压缩)#期望源名
    期望当代=代次日志文件名(当代版本,压缩)#期望当代名
    if os.path.basename(源路径)!=期望源:#源名不符
        raise Error(f'resolved JSONL source path must end with "{期望源}": {源路径}')#错误
    if os.path.basename(当代路径)!=期望当代:#当代名不符
        raise Error(f'current JSONL generation path must end with "{期望当代}": {当代路径}')#错误
    if os.path.dirname(源路径)!=os.path.dirname(当代路径):#目录不一致
        raise Error('source and current JSONL generations must share one Session directory')#错误
    return 日志后缀(压缩)#后缀

def _同步目录(路径):#同步目录项
    """POSIX 下 fsync 父目录；Windows 跳过（写穿命名空间另担）。"""
    if sys.platform=='win32':#Windows
        return#跳过（MoveFileEx WRITE_THROUGH / 注明缺口）
    标志=os.O_RDONLY#只读
    if hasattr(os,'O_DIRECTORY'):#目录标志
        标志|=os.O_DIRECTORY#目录
    描述符=os.open(路径,标志)#打开目录
    try:#fsync
        os.fsync(描述符)#同步
    finally:#关闭
        os.close(描述符)#关闭

class 迁移中jsonl行:#迁移行解析
    """仅保留跨帧记录碎片的增量 JSONL 解析器。"""
    def __init__(自身,恢复器):#构造
        """持有格式恢复器。"""
        自身.恢复器=恢复器#恢复器
        自身.碎片=[]#碎片
        自身.碎片字节=0#碎片字节
        自身.行下标=0#行下标
        自身.问题=None#延迟错误

    def 写入(自身,块):#写入块
        """消费明文字节。"""
        行起点=0#行起点
        while True:#找换行
            换行=块.find(b'\n',行起点)#换行
            if 换行<0:#无
                break
            片段=块[行起点:换行]#本行
            行=片段#默认
            if len(自身.碎片)>0:#有碎片
                if len(片段)>0:#非空
                    自身.碎片.append(片段)#并入
                行=b''.join(自身.碎片)#拼行
                自身.碎片=[]#清空
                自身.碎片字节=0#重置
            自身._消费(行)#消费
            行起点=换行+1#推进
        if 行起点<len(块):#未完成行
            片段=bytes(块[行起点:])#复制
            自身.碎片.append(片段)#压入
            自身.碎片字节+=len(片段)#累加

    def 断言完整帧落在记录边界(自身):#断言记录边界
        """拒绝完整帧留下的记录碎片。"""
        if len(自身.碎片)>0:#尚有碎片
            raise Error('corrupt Zstandard session log: complete frame contains a torn JSONL record')#撕裂

    def 完成(自身):
        """完成恢复器。"""
        return 自身.恢复器.finish()#产物

    def _消费(自身,行):#消费一行
        """解析并喂入恢复器。"""
        下标=自身.行下标#行号
        自身.行下标+=1#递增
        try:#解析
            已解析=_解析json(行.decode('utf-8'),f'row {下标+1}')#JSON
        except (UnicodeDecodeError,Error) as 错误:
            if 自身.问题 is None:#首错
                自身.问题=错误
            return#跳过
        if 自身.问题 is not None:#恢复模式
            if isinstance(已解析,dict) and 已解析.get('type')=='turn/end':#遇 turn/end
                raise 自身.问题#抛首错
            return#继续跳过
        自身.恢复器.decodeRow(已解析)#解码

def _流式解码迁移(字节,压缩,源版本,格式适配,校验历史头=None,信号=None):#流式解码
    """解码历史代为格式产物。"""
    _若已中止(信号)#取消
    if 压缩=='none':#明文
        头末=字节.find(b'\n')#头换行
        if 头末<0:#无头
            raise Error('empty or header-less session log')#损坏
        解析器=_启动迁移流(字节[:头末+1],源版本,格式适配,校验历史头)
        _若已中止(信号)#取消
        体末=字节.rfind(b'\n')#体末
        if 体末>头末:#有体
            _消费迁移字节(解析器,[字节[头末+1:体末+1]],信号)#消费
        return 解析器.完成()#完成
    扫描=扫描zstd帧(字节)#扫描帧
    帧列表=扫描['frames']#完整帧
    撕裂=扫描.get('tornStart')#撕裂起点
    if len(帧列表)==0:#无帧
        raise Error('empty or header-less Zstandard session log')#损坏
    解码器=创建zstd帧解码器()#解码器
    try:#解码
        产出=解码器.解码(字节,帧列表)#迭代
        try:#首帧
            首=next(产出)#头帧
        except StopIteration:#无产出
            raise Error('empty or header-less Zstandard session log')#损坏
        _断言独立头帧(首)#断言头
        解析器=_启动迁移流(首,源版本,格式适配,校验历史头)
        _若已中止(信号)#取消
        _消费迁移字节(解析器,产出,信号)#其余帧
        解析器.断言完整帧落在记录边界()#记录边界
        if 撕裂 is not None:#有撕裂尾
            恢复=b''#恢复明文
            try:#解压前缀
                恢复=解压zstd前缀(字节[撕裂:])#前缀
            except Exception:
                _若已中止(信号)#优先中止
            _若已中止(信号)#取消
            换行=恢复.rfind(b'\n')#最后换行
            if 换行>=0:#有完整行
                _消费迁移字节(解析器,[恢复[:换行+1]],信号)#消费
        return 解析器.完成()#完成
    finally:#清理
        解码器.关闭()#关闭

def _启动迁移流(头记录,源版本,格式适配,校验历史头):#启动迁移流
    """解析头并创建行解析器。"""
    值=_解析json(头记录[:-1].decode('utf-8'),'header line')#头
    版本=_已存版本(值)#版本
    if 版本!=源版本:#错配
        raise Error(f'resolved JSONL source filename identifies v{源版本}, but its header identifies v{版本}')#错误
    if 校验历史头 is not None:#可选校验
        校验历史头(值)#校验
    恢复器=格式适配['createRestore'](值)#创建恢复
    return 迁移中jsonl行(恢复器)#解析器

def _消费迁移字节(解析器,块序列,信号=None):#消费迁移字节
    """按工作块喂入并周期性让出。"""
    _若已中止(信号)#取消
    截止=time.monotonic()+迁移解码让出间隔秒#让出截止
    for 字节 in 块序列:#每块
        偏移=0#偏移
        while 偏移<len(字节):#切块
            解析器.写入(字节[偏移:偏移+迁移工作块字节])#喂入
            偏移+=迁移工作块字节#推进
            if time.monotonic()<截止:#未到
                continue#继续
            time.sleep(0)#让出
            _若已中止(信号)#取消
            截止=time.monotonic()+迁移解码让出间隔秒#重武装

def _解码当代代(字节,压缩):#解码当代代
    """严格解码完整当代代。"""
    if 压缩=='none':#明文
        结果=扫描日志(字节,'strict')#严格扫描
        if 结果.get('committedBytes',len(字节))!=len(字节):#有撕裂
            raise Error('current session generation has a torn physical tail')#拒绝
        return 结果#返回
    扫描=扫描zstd帧(字节)#扫描
    if len(扫描['frames'])==0:#无帧
        raise Error('empty or header-less Zstandard session log')#损坏
    if 扫描.get('tornStart') is not None:#当代不允许撕裂
        raise Error('current session generation has a torn physical tail')#拒绝
    解码器=创建zstd帧解码器()#解码器
    try:#解码
        明文块=list(解码器.解码(字节,扫描['frames']))#全部明文
        if len(明文块)==0:#无
            raise Error('empty or header-less Zstandard session log')#损坏
        _断言独立头帧(明文块[0])#头帧
        合并=b''.join(明文块)#拼接
        结果=扫描日志(合并,'strict')#严格
        if 结果.get('committedBytes',len(合并))!=len(合并):#撕裂
            raise Error('current session generation has a torn physical tail')#拒绝
        return 结果#返回
    finally:#清理
        解码器.关闭()#关闭

def 校验jsonl当代代(路径,压缩,期望标识,期望事件数,期望前缀=None):#校验当代代
    """读取并校验一份完整当代代（或仅校验已迁移前缀）。"""
    之前=物理身份(os.stat(路径))#读前
    with open(路径,'rb') as 文件:#读
        字节=文件.read()#字节
    之后=物理身份(os.stat(路径))#读后
    if 期望前缀 is not None:#仅前缀
        if len(字节)<期望前缀['bytes']:#过短
            raise Error('target bytes are shorter than the migrated generation')#错误
        摘要=hashlib.sha256(字节[:期望前缀['bytes']]).hexdigest()#摘要
        if 摘要!=期望前缀['digest']:#不符
            raise Error('target bytes do not begin with the migrated generation')#错误
        return {'identity':之后,'bytes':期望前缀['bytes'],'digest':摘要}#前缀身份
    if 身份串(之前)!=身份串(之后):#变更
        raise Error('current session generation changed during verification')#错误
    代=_解码当代代(字节,压缩)#解码
    校验已存事件(代['meta'],list(代['events']),{'kind':'jsonl','path':路径})#校验事件
    if 代['meta']['id']!=期望标识:#id 不符
        raise Error(f'current session generation contains id "{代["meta"]["id"]}", expected "{期望标识}"')#错误
    if len(代['events'])!=期望事件数:#事件数不符
        raise Error(f'current session generation contains {len(代["events"])} events, expected {期望事件数}')#错误
    会话.从恢复(会话标识(代['meta']['id']),代['events'],代['meta'],代.get('inheritedEventCount',0),'detached',当前会话消息投影表)#重开校验
    断言当代助手流(代['events'])#断言嵌入流
    return {#已校验
        'identity':之后,#身份
        'bytes':len(字节),#字节数
        'digest':hashlib.sha256(字节).hexdigest(),#全文摘要
    }#返回

def 断言当代助手流(事件列表):#断言当代助手流
    """仅在隔离当代校验内完整回放嵌入流（对齐 assertCurrentAssistantStreams）。"""
    for 下标,事件 in enumerate(事件列表):#逐事件
        if 事件.get('type')!='assistant/message' and 事件.get('type')!='assistant/attempt':#非助手
            continue#跳过
        组装器=块组装器()#块组装器
        数据=事件.get('data') or {}#载荷
        try:#尝试展开
            带时=展开助手流(数据.get('stream') or [])#展开嵌入流
            for 成员 in 带时:#逐成员
                组装器.推入(成员['chunk'])#推入块
        except BaseException as 错误:#展开失败
            raise Error(f'seed {事件.get("type")} at index {下标} has an invalid embedded stream') from 错误#无效流
        if 事件.get('type')=='assistant/attempt' or len(带时)==0:#attempt 或空流
            continue#跳过内容比对
        内容=组装器.中断块列表() if 数据.get('interrupted') is True else 组装器.块列表()#期望内容
        消息=数据.get('message') or {}#消息
        if not 深相等json(消息.get('content'),内容):#内容不符
            raise Error(f'seed assistant/message at index {下标} content disagrees with its embedded stream')#内容冲突
        if not 深相等json(数据.get('usage'),组装器.用量):#用量不符
            raise Error(f'seed assistant/message at index {下标} usage disagrees with its embedded stream')#用量冲突
        来源=消息.get('source') or {}#来源
        if not 深相等json(来源.get('replayState'),组装器.回放状态):#回放状态不符
            raise Error(f'seed assistant/message at index {下标} replay state disagrees with its embedded stream')#回放冲突

def _写已同步临时(当代路径,后缀,压缩,产物,格式适配,信号=None):#写已同步临时
    """直接编码进已同步暂存。"""
    _若已中止(信号)#取消
    目录=os.path.dirname(当代路径)#目录
    while True:#直至唯一名
        路径=os.path.join(目录,f'session.migration.{secrets.token_hex(8)}{后缀}.tmp')#临时
        try:#独占创建
            描述符=os.open(路径,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)#wx
            break#成功
        except FileExistsError:#名冲突
            continue#重试
    哈希=hashlib.sha256()#摘要
    字节数=0#已写
    失败=None
    try:#写出
        def 写块(块):#写并哈希
            """写一块。"""
            nonlocal 字节数#累加
            if isinstance(块,str):#文本
                块=块.encode('utf-8')#转字节
            os.write(描述符,块)#写
            哈希.update(块)#哈希
            字节数+=len(块)#累加
        头值=格式适配['encodeHeader'](产物['header'],产物.get('inheritedEventCount',0))#编码头
        import json#JSON
        头行=(json.dumps(头值,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')#头行
        写块(压缩zstd帧(头行) if 压缩=='zstd' else 头行)#写头
        事件列表=产物.get('events') or []#事件
        if len(事件列表)>0:#有事件
            行缓冲=[]#行
            缓冲字节=0#缓冲大小
            for 值 in 事件列表:#逐事件
                行=json.dumps(格式适配['encodeEvent'](值),ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n'#行
                行字节=len(行.encode('utf-8'))#行字节
                if 缓冲字节>0 and 缓冲字节+行字节>迁移工作块字节:#超块
                    明文=''.join(行缓冲).encode('utf-8')#明文
                    写块(压缩zstd帧(明文) if 压缩=='zstd' else 明文)#写出
                    time.sleep(0)#让出
                    _若已中止(信号)#取消
                    行缓冲=[]#清空
                    缓冲字节=0#重置
                行缓冲.append(行)#追加
                缓冲字节+=行字节#累加
            if 缓冲字节>0:#尾部
                明文=''.join(行缓冲).encode('utf-8')#明文
                写块(压缩zstd帧(明文) if 压缩=='zstd' else 明文)#写出
        _若已中止(信号)#取消
        os.fsync(描述符)#同步文件
    except BaseException as 错误:#写失败
        失败=错误#记录
    try:#关闭
        os.close(描述符)#关闭
    except BaseException as 关闭错误:#关闭失败
        失败=关闭错误 if 失败 is None else ExceptionGroup('failed to write and close migration stage', [失败,关闭错误])#聚合
    if 失败 is not None:#有失败
        try:#清理
            os.remove(路径)#删临时
        except BaseException as 清理:#清理失败
            raise ExceptionGroup(f'failed to clean migration temporary "{路径}"', [失败,清理])#聚合
        raise 失败#抛出
    return {'path':路径,'bytes':字节数,'digest':哈希.hexdigest()}#暂存

def _独占发布当代(暂存,当代路径):
    """Win32 写穿移动或 POSIX 硬链接+目录 fsync。"""
    if sys.platform=='win32':
        try:
            发布新文件win32(暂存,当代路径)
            return True
        except OSError as 错误:
            if 是否eexist(错误):
                return False
            raise
    try:
        os.link(暂存,当代路径)
    except OSError as 错误:
        if 是否eexist(错误):
            return False
        raise
    _同步目录(os.path.dirname(当代路径))
    return True

def _发布已准备迁移(选项,后缀,产物,源身份):#发布已准备迁移
    """编码、校验并独占发布一次。"""
    time.sleep(0)#让出
    源路径=选项['sourcePath']#源
    当代路径=选项['currentPath']#当代
    压缩=选项['compression']#压缩
    校验文件=选项['verifyCurrentFile']#校验
    事件数=len(产物.get('events') or [])#事件数
    暂存=_写已同步临时(当代路径,后缀,压缩,产物,选项['format'],None)#写暂存
    try:#发布
        已校验=校验文件(暂存['path'],压缩,产物['header']['id'],事件数)#校验暂存
        if 已校验['bytes']!=暂存['bytes'] or 已校验['digest']!=暂存['digest']:#变更
            raise Error('staged session generation changed during verification')#错误
        校验相关=选项.get('validateRelatedSources')#相关源
        if 校验相关 is not None:#发布前再核
            校验相关()#核
        发布前=物理身份(os.stat(源路径))#源 stat
        if 身份串(发布前)!=身份串(源身份):#源已变
            raise 代次源变更错误(源路径)#错误
        已发布=_独占发布当代(暂存['path'],当代路径)#独占发布
        if 已发布 and sys.platform=='win32':#Win32 暂存已迁走
            暂存={'path':'','bytes':暂存['bytes'],'digest':暂存['digest']}#清空路径
        if 已发布:#本进程成功
            if 暂存['path']!='':#仍有暂存
                try:#删多余
                    os.remove(暂存['path'])#删除
                except OSError:#忽略
                    pass#已提交
                暂存={'path':'','bytes':暂存['bytes'],'digest':暂存['digest']}#清空
            return 物理身份(os.stat(当代路径))#当代身份
        #他人已发布：校验赢家前缀
        def 检查赢家():#检查
            """校验竞争胜者。"""
            候选=校验文件(当代路径,压缩,产物['header']['id'],事件数,暂存)#前缀
            if 候选['bytes']!=暂存['bytes'] or 候选['digest']!=暂存['digest']:#不符
                raise Error('target bytes differ from the migrated generation')#错误
            return 候选#返回
        try:#检查目标
            赢家=检查赢家()#赢家
        except OSError:#errno
            raise#保留
        except Exception as 错误:#冲突
            raise 代次目标冲突错误(当代路径,错误 if isinstance(错误,Exception) else Error(str(错误)))#包装
        if 暂存['path']!='':#清暂存
            try:#删除
                os.remove(暂存['path'])#删
            except OSError:#忽略
                pass#忽略
        return 赢家['identity']#身份
    except BaseException as 错误:
        if 暂存.get('path'):#有暂存
            try:#清理
                os.remove(暂存['path'])#删
            except BaseException as 清理:#清理失败
                raise ExceptionGroup(f'failed to clean migration temporary "{暂存["path"]}"', [错误,清理])#聚合
        raise#抛出

def 准备jsonl迁移(选项):#准备迁移
    """解码并迁移一份历史代，不写其后继；返回可幂等 publish。"""
    源路径=选项['sourcePath']#源
    源版本=选项['sourceVersion']#源版本
    当代路径=选项['currentPath']#当代
    压缩=选项['compression']#压缩
    格式=选项['format']#适配器
    信号=选项.get('signal')#取消
    当代版本=格式['currentVersion']#当代版本
    后缀=_断言代次路径(源路径,源版本,当代路径,当代版本,压缩)#断言
    if 源版本>=当代版本:#非历史
        raise Error(f'migration preparation requires a historical source, got v{源版本}')#须历史
    源=读稳定jsonl文件(源路径,信号)#读源
    try:#解码
        产物=_流式解码迁移(源['bytes'],压缩,源版本,格式,选项.get('validateHistoricalHeader'),信号)#解码
    except Exception as 错误:
        判定=格式.get('isUnsupportedMigrationError')#判定
        if 判定 is not None and 判定(错误):#不支持
            raise 代次不支持迁移错误(源版本,错误 if isinstance(错误,Exception) else Error(str(错误)))#包装
        if isinstance(错误,会话格式不支持迁移错误):#目录拒绝
            raise 代次不支持迁移错误(源版本,错误)#包装
        raise#其它
    if 产物['header']['version']!=当代版本:#版本不对
        raise Error(f'format migration returned v{产物["header"]["version"]}, expected v{当代版本}')#错误
    源身份=源['identity']#源身份
    校验相关=选项.get('validateRelatedSources')#相关源再校验
    if 校验相关 is not None:#有相关源
        校验相关()#解码后核一次
    发布承诺=[None]#单次发布槽

    def 发布():#幂等发布
        """编码、校验并独占发布；共享同一成功或失败。"""
        if 发布承诺[0] is None:#尚未启动
            发布承诺[0]=_发布已准备迁移(选项,后缀,产物,源身份)
        return 发布承诺[0]#共享结果

    return {'sourceIdentity':源身份,'artifact':产物,'publish':发布}#已准备

def 读解码jsonl源(路径,版本,压缩,格式,信号=None):#读解码jsonl源
    """经共享流式解析器读一份稳定源，不发布当代代。"""
    源=读稳定jsonl文件(路径,信号)#稳定读
    try:#解码
        产物=_流式解码迁移(源['bytes'],压缩,版本,格式,None,信号)#解码
    except BaseException as 错误:
        if 信号 is not None and 信号.is_set():#取消
            raise#原样
        if isinstance(错误,会话格式错误):#格式
            raise#原样
        raise 会话格式错误(str(错误)) from 错误#包装
    return {'artifact':产物,'identity':源['identity']}#产物与身份

def 默认代次格式适配器():#默认格式适配器
    """用会话格式目录构造代格式适配器。"""
    return {#适配器
        'currentVersion':会话格式目录.当前版本,#当代版本
        'createRestore':lambda 头:会话格式目录.创建恢复(头,{'recovery':'recoverable','validation':'transformed'}),#恢复器
        'encodeHeader':lambda 头,继承:会话格式目录.编码当代头(头,继承),#编码头
        'encodeEvent':lambda 事件:会话格式目录.编码当代事件(事件),#编码事件
        'isUnsupportedMigrationError':lambda 错误:isinstance(错误,会话格式不支持迁移错误),#不支持判定
    }#结束

class Error(Exception):#代次辅助错误
    """代次模块抛出的 Error 风格异常。"""

__all__=[#公开面
    '物理身份','身份串','读稳定jsonl文件','准备jsonl迁移','校验jsonl当代代',
    '读解码jsonl源','默认代次格式适配器','代次源变更错误','代次不支持迁移错误','代次目标冲突错误',
    '同步目录','_同步目录',
]#公开面结束

#公开别名
同步目录=_同步目录#POSIX 目录 fsync
