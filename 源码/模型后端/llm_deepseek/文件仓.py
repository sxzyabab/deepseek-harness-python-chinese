"""DeepSeek Files API 上传复用、作废与配额恢复。"""
import threading,time
from ..llm import 大模型错误
from .文件接口 import 深求文件客户端,是否文件配额错误
from .消息接口 import 消息接口根
from .上传索引 import 深求文件作用域摘要,深求上传索引
from ...工具.超时 import 若已中止则抛出

__all__=['最大图片字节','深求文件仓']

最大图片字节=32*1024*1024
自有文件前缀='dsh-'

def 文件作用域(连接):
    """Files 资源父 URL 标识上传命名空间。"""
    return 深求文件作用域摘要(消息接口根(连接['baseURL']),连接['apiKey'])

def 扩展名(媒体类型):
    """媒体类型到文件扩展名。"""
    if 媒体类型=='image/png':
        return 'png'
    if 媒体类型=='image/jpeg':
        return 'jpeg'
    if 媒体类型=='image/webp':
        return 'webp'
    return 'gif'

def 文件名(版本):
    """自有文件名。"""
    附件=str(版本['attachment']['attachmentId'])[len('sha256:'):len('sha256:')+16]
    变体=str(版本['variantId'])[len('sha256:'):len('sha256:')+8]
    return 自有文件前缀+附件+'-'+变体+'.'+扩展名(版本['mediaType'])

class 深求文件仓:
    """用户作用域耐久文件标识复用。"""
    def __init__(自身,选项=None):
        """可注入索引、时钟与传输。"""
        if 选项 is None:
            选项={}
        自身.索引=选项['index'] if 'index' in 选项 else 深求上传索引()
        自身.现在=选项['now'] if 'now' in 选项 else (lambda:int(time.time()*1000))
        自身.发=选项.get('fetch')
        自身.锁=threading.Lock()

    def 客户端(自身,连接):
        """按连接快照构造 Files 客户端。"""
        选项={'baseURL':连接['baseURL'],'apiKey':连接['apiKey']}
        if 连接.get('accountCredential') is not None:
            选项['accountCredential']=连接['accountCredential']
        if 自身.发 is not None:
            选项['fetch']=自身.发
        return 深求文件客户端(选项)

    def 确保已上传(自身,版本,连接,政策,信号=None):
        """解析或上传一张确定性请求图。"""
        若已中止则抛出(信号)
        with 自身.锁:
            return 自身.确保一次(版本,连接,政策,信号)

    def 确保一次(自身,版本,连接,政策,信号):
        """单次上传或命中缓存。"""
        if 版本['bytes']>最大图片字节:
            raise 大模型错误('DeepSeek image exceeds the 32 MiB per-image limit.','INVALID_REQUEST')
        作用域=文件作用域(连接)
        现在=自身.现在()
        边距毫秒=政策['refreshMarginSeconds']*1000
        缓存=自身.索引.取(作用域,版本['variantId'],现在,边距毫秒)
        if 缓存 is not None:
            return {'record':缓存,'uploaded':False}
        客户端=自身.客户端(连接)
        def 上传():
            """提交字节并校验响应长度。"""
            远程=客户端.上传({
                'data':版本['data'],
                'mediaType':版本['mediaType'],
                'filename':文件名(版本),
                'expiresAfterSeconds':政策['expiresAfterSeconds'],
                'signal':信号,
            })
            if 远程['bytes']!=len(版本['data']):
                raise 大模型错误('DeepSeek Files API upload response does not match the submitted image.','INVALID_RESPONSE')
            return {
                'scope':作用域,
                'attachmentId':版本['attachment']['attachmentId'],
                'variantId':版本['variantId'],
                'fileId':远程['id'],
                'bytes':远程['bytes'],
                'createdAt':远程['createdAt']*1000,
                'expiresAt':远程['expiresAt']*1000,
            }
        try:
            候选=上传()
        except Exception as 错误:
            if not 是否文件配额错误(错误):
                raise 错误
            已删=自身.回收最旧自有(连接,政策['quotaCleanupBatch'],信号)
            if 已删==0:
                raise 错误
            候选=上传()
        提交=自身.索引.提交(候选,自身.现在(),边距毫秒)
        if not 提交['accepted']:
            try:
                客户端.删除(候选['fileId'],信号)
            except Exception:
                pass
        return {'record':提交['record'],'uploaded':提交['accepted']}

    def 作废(自身,版本,文件号,连接):
        """模型请求拒远程 id 后作废精确本地映射。"""
        自身.索引.移除(文件作用域(连接),版本['variantId'],文件号)

    def 释放(自身,版本,连接,政策,信号=None):
        """删除索引中的远程文件并去掉本地映射。"""
        作用域=文件作用域(连接)
        记录=自身.索引.取(作用域,版本['variantId'],自身.现在(),政策['refreshMarginSeconds']*1000)
        if 记录 is None:
            return False
        自身.客户端(连接).删除(记录['fileId'],信号)
        自身.索引.移除(作用域,版本['variantId'],记录['fileId'])
        return True

    def 回收最旧自有(自身,连接,数量,信号=None):
        """删除文件名标识为 harness 自有的最旧提供方文件。"""
        客户端=自身.客户端(连接)
        之后=None
        自有=[]
        while True:
            选项={'limit':1000}
            if 之后 is not None:
                选项['after']=之后
            if 信号 is not None:
                选项['signal']=信号
            页=客户端.列出(选项)
            for 文件 in 页['data']:
                if not 文件['filename'].startswith(自有文件前缀):
                    continue
                自有.append({'id':文件['id'],'createdAt':文件['createdAt']})
            自有.sort(key=lambda 项:项['createdAt'])
            自有=自有[:数量]
            尾=页.get('lastId')
            if not 页['hasMore'] or 尾 is None or 尾==之后:
                break
            之后=尾
        for 文件 in 自有:
            客户端.删除(文件['id'],信号)
        return len(自有)

    def 释放全部(自身,连接,信号=None):
        """删除活动密钥命名空间内全部自有远程文件并清空索引。"""
        合计=0
        while True:
            已删=自身.回收最旧自有(连接,1000,信号)
            合计+=已删
            if 已删<1000:
                break
        自身.索引.清空(文件作用域(连接))
        return 合计
