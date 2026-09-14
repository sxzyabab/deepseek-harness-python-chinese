#对齐上游 worker/realms/host/sources.ts

from ....共享.json import 检查器错误#包内错误
from .脚本 import Host脚本键#脚本键

__all__=['Host源后端']#仅中文公开名

安全整数上限=9007199254740991#外来JSON安全整数上限

def _是非负安全整数(值):#CDP入口整数
    """校验非负安全整数，入口排除 bool。"""
    return isinstance(值,int) and not isinstance(值,bool) and 值>=0 and 值<=安全整数上限#校验

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
        脚本=自身._脚本[脚本键] if 脚本键 in 自身._脚本 else None#取脚本
        if 脚本 is None:#不可用
            raise 检查器错误('Host script is no longer available')#抛错
        结果=自身.目标.请求('Debugger.getScriptSource',{'scriptId':脚本['nativeId']})#请求
        if 'scriptSource' not in 结果 or not isinstance(结果['scriptSource'],str):#无源
            raise 检查器错误('Host Debugger returned no script source')#抛错
        return 结果['scriptSource']#返回

    def 取源映射(自身,_脚本键):#取源映射
        """Host 不提供源映射。"""
        return None#Host不提供

    def 订阅(自身,监听):#订阅
        """订阅初始目录读取之后发现的脚本。"""
        自身._监听.add(监听)#加入
        def 拆除():#取消订阅
            """从监听集摘掉。"""
            自身._监听.discard(监听)#拆除
        return 拆除#拆除器

    def 关闭(自身):#关闭
        """拆除原生通知订阅与缓存目录。"""
        自身._取消订阅()#取消
        自身._脚本.clear()#清脚本
        自身._监听.clear()#清监听

    def _接收(自身,消息):#接收通知
        """登记 scriptParsed。"""
        if 消息.get('method')!='Debugger.scriptParsed':#非解析
            return#返回
        参数=消息['params'] if 'params' in 消息 else None#参数
        if not isinstance(参数,dict):#无参数
            return#返回
        if not isinstance(参数.get('scriptId'),str) or not isinstance(参数.get('url'),str):#缺字段
            return#返回
        if not all(_是非负安全整数(参数[键] if 键 in 参数 else None) for 键 in ('startLine','startColumn','endLine','endColumn')):#行列
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
        if isinstance(参数.get('sourceMapURL'),str) and len(参数['sourceMapURL'])>0:#源映射
            描述['sourceMapUrl']=参数['sourceMapURL']#写入
        if _是非负安全整数(参数['executionContextId'] if 'executionContextId' in 参数 else None):#上下文
            描述['executionContextId']=参数['executionContextId']#写入
        if isinstance(参数.get('isModule'),bool):#模块
            描述['isModule']=参数['isModule']#写入
        if _是非负安全整数(参数['length'] if 'length' in 参数 else None):#长度
            描述['length']=参数['length']#写入
        自身._脚本[脚本键]={'descriptor':描述,'nativeId':参数['scriptId']}#登记
        for 监听 in list(自身._监听):#扫监听
            try:#隔离
                监听(描述)#通知
            except Exception:#源观察者回调什么都可能抛，收不窄
                pass#一个源消费者不能阻止对兄弟消费者的投递
