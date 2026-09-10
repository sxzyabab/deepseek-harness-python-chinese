"""DeepSeek Files API 上传复用、失效与配额恢复。

对齐上游 `llm-deepseek/src/file-store.ts`。公开面仅中文名；无英文别名。
"""
import threading,time#共享上传与时钟
from ..llm import 大模型错误#LLM 错误
from .文件接口 import 深求文件客户端,是否文件配额错误#Files 客户端与配额判定
from .上传索引 import 深求文件作用域摘要,深求上传索引#作用域与上传索引

__all__=('最大聊天图字节','深求文件仓',)#仅中文公开名

最大聊天图字节=32*1024*1024#最大聊天图字节
自有文件前缀='dsh-'#自有文件前缀

class _仓中止信号:#仓内中止信号
    """仅服务文件仓共享上传的最小中止信号。"""
    def __init__(自身,事件对象,取原因):
        """绑到共享事件与原因读取。"""
        自身.事件对象=事件对象#事件
        自身.取原因=取原因#原因读取
    @property
    def 已中止(自身):
        """是否已中止。"""
        return 自身.事件对象.is_set()#置位
    @property
    def 原因(自身):
        """中止原因。"""
        return 自身.取原因()#原因

class _仓中止控制器:#仓内中止控制器
    """仅服务文件仓共享上传的最小中止控制器。"""
    def __init__(自身):
        """创建一对控制器与信号。"""
        自身.事件对象=threading.Event()#事件
        自身.中止原因值=None#原因
        自身.信号=_仓中止信号(自身.事件对象,lambda:自身.中止原因值)#信号
    def 中止(自身,原因=None):
        """发出中止；重复忽略。"""
        if 自身.事件对象.is_set():#已中止
            return#忽略
        自身.中止原因值=原因#记下
        自身.事件对象.set()#置位

def 中止原因(信号):#中止原因
    """把信号原因规范成 Error。"""
    原因=getattr(信号,'原因',None)#原因
    if isinstance(原因,BaseException):#已是异常
        return 原因#原样
    return RuntimeError('DeepSeek file upload cancelled with a non-Error reason.')#包装

def 上传失败(错误):#上传失败
    """非 Error 原因包装。"""
    if isinstance(错误,BaseException):#已是异常
        return 错误#原样
    return RuntimeError('DeepSeek file upload failed with a non-Error reason.')#包装

def 扩展名(媒体类型):#扩展名
    """媒体类型到扩展名。"""
    if 媒体类型=='image/png':#png
        return 'png'#png
    if 媒体类型=='image/jpeg':#jpeg
        return 'jpeg'#jpeg
    if 媒体类型=='image/webp':#webp
        return 'webp'#webp
    if 媒体类型=='image/gif':#gif
        return 'gif'#gif
    raise 大模型错误('unsupported DeepSeek upload media type','INVALID_REQUEST')#不支持

def 文件名(版本):#文件名
    """确定性请求图文件名。"""
    附件=str(版本['attachment']['attachmentId'])[len('sha256:'):len('sha256:')+16]#短附件
    变体=str(版本['variantId'])[len('sha256:'):len('sha256:')+8]#短变体
    return f'{自有文件前缀}{附件}-{变体}.{扩展名(版本["mediaType"])}'#文件名

class 深求文件仓:#文件存储
    """DeepSeek 路由的用户作用域持久文件 id 复用。"""
    def __init__(自身,选项=None):#构造
        """可测试的索引、时钟与传输边界。"""
        if 选项 is None:#缺省
            选项={}#空
        自身.索引=选项['index'] if 'index' in 选项 else 深求上传索引()#索引
        自身.现在=选项['now'] if 'now' in 选项 else (lambda:int(time.time()*1000))#时钟毫秒
        自身.取传输=选项.get('fetch')#可选 fetch（本移植未用，预留给测试）
        自身.飞行中={}#飞行中上传
        自身.锁=threading.Lock()#飞行表锁

    def 客户端(自身,连接):#客户端
        """按连接事实构造 Files 客户端。"""
        return 深求文件客户端({'baseURL':连接['baseURL'],'apiKey':连接['apiKey']})#客户端

    def 确保已上传(自身,版本,连接,政策,信号=None):#确保已上传
        """解析或上传一张确定性请求图；并发调用共享一次上传。"""
        if 信号 is not None and getattr(信号,'已中止',False):#已中止
            raise 中止原因(信号)#中止
        作用域=深求文件作用域摘要(连接['baseURL'],连接['apiKey'])#作用域
        键=作用域+'\0'+版本['variantId']#共享键
        启动=None#可选新建线程
        with 自身.锁:#表锁
            活动=自身.飞行中.get(键)#飞行中
            if 活动 is not None and getattr(活动['controller'].信号,'已中止',False):#已中止共享
                自身.飞行中.pop(键,None)#清
                活动=None#重开
            if 活动 is None:#新建共享
                控制器=_仓中止控制器()#新建
                共享={'controller':控制器,'settled':False,'waiters':0,'结果':None,'错误':None,'事件':threading.Event()}#共享
                def 跑():#后台上传
                    """单次上传。"""
                    try:#上传
                        值=自身._确保已上传一次(版本,连接,政策,控制器.信号)#一次
                        共享['结果']=值#成功
                        共享['settled']=True#结算
                        共享['事件'].set()#唤醒
                    except BaseException as 错误:#失败
                        共享['错误']=上传失败(错误)#记下
                        共享['settled']=True#结算
                        共享['事件'].set()#唤醒
                    finally:#清表
                        with 自身.锁:#锁
                            if 自身.飞行中.get(键) is 共享:#仍是本共享
                                自身.飞行中.pop(键,None)#删
                自身.飞行中[键]=共享#登记
                活动=共享#本调用等待新建
                启动=跑#锁外启动
        if 启动 is not None:#新建
            threading.Thread(target=启动,daemon=True).start()#锁外启动
        return 自身._等待上传(活动,信号)#锁外等待

    def _等待上传(自身,操作,信号):#等待上传
        """等待共享上传，保留独立取消。"""
        if 信号 is not None and getattr(信号,'已中止',False):#已中止
            raise 中止原因(信号)#中止
        操作['waiters']+=1#等待者
        已释放=False#释放标记
        def 释放(取消原因=None):#释放等待者
            """减少等待者；无人则中止共享。"""
            nonlocal 已释放#改外层
            if 已释放:#已释放
                return#忽略
            已释放=True#标记
            操作['waiters']-=1#减
            if 取消原因 is not None and 操作['waiters']==0 and not 操作['settled']:#无人且未结算
                操作['controller'].中止(取消原因)#中止共享
        if 信号 is None:#无取消
            操作['事件'].wait()#等结算
            释放()#释放
            if 操作['错误'] is not None:#失败
                raise 操作['错误']#抛
            return 操作['结果']#成功
        while not 操作['事件'].wait(0.05):#轮询
            if getattr(信号,'已中止',False):#调用方中止
                原因=中止原因(信号)#原因
                释放(原因)#释放并可能中止共享
                raise 原因#抛
        释放()#结算后释放
        if 操作['错误'] is not None:#失败
            raise 操作['错误']#抛
        return 操作['结果']#成功

    def _确保已上传一次(自身,版本,连接,政策,信号):#单次确保上传
        """单次确保上传路径。"""
        if 版本.get('bytes',len(版本.get('data') or b''))>最大聊天图字节:#超聊天限
            raise 大模型错误('DeepSeek chat image exceeds the 32 MiB per-image limit.','INVALID_REQUEST')#超限
        作用域=深求文件作用域摘要(连接['baseURL'],连接['apiKey'])#作用域
        现在=自身.现在()#当前毫秒
        边距毫秒=政策['refreshMarginSeconds']*1000#刷新边距
        缓存=自身.索引.获取(作用域,版本['variantId'],现在,边距毫秒)#缓存
        if 缓存 is not None:#命中
            return {'record':缓存,'uploaded':False}#复用
        客户端=自身.客户端(连接)#客户端
        def 上传():#上传
            """远程上传并组记录。"""
            远程=客户端.上传({
                'data':版本['data'],#数据
                'mediaType':版本['mediaType'],#媒体
                'filename':文件名(版本),#文件名
                'expiresAfterSeconds':政策['expiresAfterSeconds'],#过期
                'signal':信号,#取消
            })#上传
            if 远程['bytes']!=len(版本['data']):#长度不符
                raise 大模型错误('DeepSeek Files API upload response does not match the submitted image.','INVALID_RESPONSE')#不符
            return {
                'scope':作用域,#作用域
                'attachmentId':版本['attachment']['attachmentId'],#附件
                'variantId':版本['variantId'],#变体
                'fileId':远程['id'],#文件 id
                'bytes':远程['bytes'],#字节
                'createdAt':远程['createdAt']*1000,#毫秒
                'expiresAt':远程['expiresAt']*1000,#毫秒
            }#记录
        try:#首传
            候选=上传()#上传
        except BaseException as 错误:#失败
            if not 是否文件配额错误(错误):#非配额
                raise#原样
            已删=自身.回收最旧自有(连接,政策['quotaCleanupBatch'],信号)#清理
            if 已删==0:#无法恢复
                raise 错误#原样
            候选=上传()#重试
        已提交=自身.索引.提交(候选,自身.现在(),边距毫秒)#提交索引
        if not 已提交['accepted']:#落败
            try:#删重复远程
                客户端.删除(候选['fileId'],信号)#删除
            except Exception:#忽略
                pass#配额由恢复重试
        return {'record':已提交['record'],'uploaded':已提交['accepted']}#结果

    def 失效(自身,版本,文件标识,连接):#失效
        """聊天端点拒绝远程 id 后失效精确本地映射。"""
        自身.索引.移除(
            深求文件作用域摘要(连接['baseURL'],连接['apiKey']),#作用域
            版本['variantId'],#变体
            文件标识,#文件 id
        )#移除

    def 释放(自身,版本,连接,政策,信号=None):#释放
        """删除一个附件的已索引远程文件并移除本地映射。"""
        作用域=深求文件作用域摘要(连接['baseURL'],连接['apiKey'])#作用域
        记录=自身.索引.获取(作用域,版本['variantId'],自身.现在(),政策['refreshMarginSeconds']*1000)#记录
        if 记录 is None:#无
            return False#无
        自身.客户端(连接).删除(记录['fileId'],信号)#删远程
        自身.索引.移除(作用域,版本['variantId'],记录['fileId'])#清索引
        return True#已删

    def 回收最旧自有(自身,连接,数量,信号=None):#回收最旧自有
        """删除文件名标识 harness 所有权的最旧提供方文件。"""
        客户端=自身.客户端(连接)#客户端
        之后=None#分页
        自有=[]#待删
        while len(自有)<数量:#凑满
            选项={'limit':1000,'order':'asc'}#升序页
            if 之后 is not None:#续页
                选项['after']=之后#after
            if 信号 is not None:#取消
                选项['signal']=信号#信号
            页=客户端.列出(选项)#列出
            for 文件 in 页['data']:#逐文件
                if not 文件['filename'].startswith(自有文件前缀):#非自有
                    continue#跳过
                自有.append(文件['id'])#记下
                if len(自有)==数量:#满
                    break#停
            if not 页['hasMore'] or 'lastId' not in 页 or 页['lastId']==之后:#无更多
                break#停
            之后=页['lastId']#续
        for 文件标识 in 自有:#删除
            客户端.删除(文件标识,信号)#删
        return len(自有)#删除数

    def 全部释放(自身,连接,信号=None):#全部释放
        """删除活动 API 密钥命名空间中每个远程 harness 自有文件并清空索引。"""
        总计=0#合计
        while True:#循环
            已删=自身.回收最旧自有(连接,1000,信号)#批删
            总计+=已删#累加
            if 已删<1000:#末批
                break#停
        自身.索引.清空(深求文件作用域摘要(连接['baseURL'],连接['apiKey']))#清索引
        return 总计#删除数
