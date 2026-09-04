"""原生 Node Debugger 通知上的 SourceBackend 实现。"""
#对齐上游 worker/realms/host/sources.ts

from ......内核.智能体循环.辅助 import 解开#可等待则等待
from .脚本 import Host脚本键#脚本键

__all__=['Host源后端']#仅中文公开名

def _是整数(值):#是否非负安全整数
    """校验非负安全整数。"""
    return isinstance(值,int) and not isinstance(值,bool) and 值>=0 and 值<=9007199254740991#校验

class Host源后端:#Host源后端
    """维护 Node inspector 报告的脚本的一份连接本地目录。"""
    def __init__(自身,目标):#构造
        """订阅通知。"""
        自身.目标=目标#会话
        自身._脚本={}#脚本表
        自身._监听=set()#监听
        自身._取消订阅=目标.订阅(自身._接收)#订阅

    def 列脚本(自身):#列脚本
        """返回描述列表。"""
        return [项['descriptor'] for 项 in 自身._脚本.values()]#描述列表

    def 取脚本来源(自身,脚本键):#取脚本来源
        """请求原生脚本来源。"""
        脚本=自身._脚本.get(脚本键)#取脚本
        if 脚本 is None:#不可用
            raise RuntimeError('Host script is no longer available')#抛错
        结果=解开(自身.目标.请求('Debugger.getScriptSource',{'scriptId':脚本['nativeId']}))#请求
        if not isinstance(结果.get('scriptSource'),str):#无源
            raise RuntimeError('Host Debugger returned no script source')#抛错
        return 结果['scriptSource']#返回

    def 取源映射(自身,_脚本键):#取源映射
        """Host 不提供源映射。"""
        return None#Host不提供

    def 订阅(自身,监听):#订阅
        """订阅初始目录读取之后发现的脚本。"""
        自身._监听.add(监听)#加入
        return lambda:自身._监听.discard(监听)#释放

    def 关闭(自身):#关闭
        """释放原生通知订阅与缓存目录。"""
        自身._取消订阅()#取消
        自身._脚本.clear()#清脚本
        自身._监听.clear()#清监听

    def _接收(自身,消息):#接收通知
        """登记 scriptParsed。"""
        if 消息.get('method')!='Debugger.scriptParsed':#非解析
            return#返回
        参数=消息.get('params') or {}#参数
        if not isinstance(参数.get('scriptId'),str) or not isinstance(参数.get('url'),str):#缺字段
            return#返回
        if not all(_是整数(参数.get(键)) for 键 in ('startLine','startColumn','endLine','endColumn')):#行列
            return#返回
        脚本键=Host脚本键(参数['scriptId'])#规范化键
        描述={#描述
            'scriptKey':脚本键,'url':参数['url'],#URL
            'hash':参数['hash'] if isinstance(参数.get('hash'),str) else '',#哈希
            'startLine':参数['startLine'],'startColumn':参数['startColumn'],#起始
            'endLine':参数['endLine'],'endColumn':参数['endColumn'],#结束
        }#descriptor结束
        if isinstance(参数.get('buildId'),str):#构建id
            描述['buildId']=参数['buildId']#写入
        if isinstance(参数.get('sourceMapURL'),str) and 参数['sourceMapURL']:#源映射
            描述['sourceMapUrl']=参数['sourceMapURL']#写入
        if _是整数(参数.get('executionContextId')):#上下文
            描述['executionContextId']=参数['executionContextId']#写入
        if isinstance(参数.get('isModule'),bool):#模块
            描述['isModule']=参数['isModule']#写入
        if _是整数(参数.get('length')):#长度
            描述['length']=参数['length']#写入
        自身._脚本[脚本键]={'descriptor':描述,'nativeId':参数['scriptId']}#登记
        for 监听 in list(自身._监听):#扫监听
            try:#隔离
                监听(描述)#通知
            except Exception:#故障
                pass#一个源消费者不能阻止对兄弟消费者的投递
