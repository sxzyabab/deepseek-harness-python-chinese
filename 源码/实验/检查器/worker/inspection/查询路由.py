"""Worker 侧非 CDP 查询的准入、执行与有界结算。"""
#对齐上游 worker/inspection/query-router.ts

from .....内核.智能体循环.辅助 import 解开,在线程跑#可等待则等待|后台跑
from .cordis查询 import 执行检查器查询#查询执行

__all__=['检查器查询路由','检查器查询对端']#仅中文公开名

检查器协议版本=1#协议版本占位

def _json字节长(值):#估计JSON字节
    """粗估帧字节。"""
    import json#JSON
    return len(json.dumps(值,ensure_ascii=False).encode('utf-8'))#字节

def _渲染错误(错误):#渲染错误
    """统一为 Exception。"""
    return 错误 if isinstance(错误,Exception) else RuntimeError(str(错误))#统一

class 检查器查询路由:#查询路由
    """在一个共享语义读取器上创建隔离的查询对端。"""
    def __init__(自身,读取器,最大帧字节):#构造
        """保存读取器与上限。"""
        自身._读取器=读取器#读取器
        自身._最大帧字节=最大帧字节#帧字节上限
        自身._对端们=set()#对端集合
        自身._按源活动={}#活动表

    def 打开(自身,传输):#打开对端
        """为一个 Host MessagePort 或 Client WebSocket 创建查询状态。"""
        def 登记(已接受):#登记回调
            """清旧并登记。"""
            for 源id,活动 in list(自身._按源活动.items()):#扫活动
                if 活动['peer'] is 对端:#清旧
                    del 自身._按源活动[源id]#删除
            自身._按源活动[已接受['sourceId']]={**已接受,'peer':对端}#登记
        def 已登记(已接受):#是否已登记
            """代数匹配。"""
            活动=自身._按源活动.get(已接受['sourceId'])#取
            return 活动 is not None and 活动['peer'] is 对端 and 活动['generation']==已接受['generation']#匹配
        def 注销():#注销
            """移除对端活动。"""
            自身._对端们.discard(对端)#移除对端
            for 源id,活动 in list(自身._按源活动.items()):#扫活动
                if 活动['peer'] is 对端:#清除
                    del 自身._按源活动[源id]#删除
        对端=检查器查询对端(自身._读取器,自身._最大帧字节,传输,登记,已登记,注销)#创建对端
        自身._对端们.add(对端)#加入
        return 对端#返回

    def 断开(自身,源):#断开
        """源注册表关闭一个代数时吊销查询访问。"""
        活动=自身._按源活动.get(源['sourceId'])#取活动
        if 活动 is None or 活动['generation']!=源['generation']:#代数不符
            return#返回
        del 自身._按源活动[源['sourceId']]#删除
        活动['peer'].吊销(源['sourceId'],源['generation'])#吊销

    def 关闭(自身):#关闭
        """Worker 关闭期间吊销每一个对端。"""
        for 对端 in list(自身._对端们):#关全部
            对端.关闭()#关闭
        自身._按源活动.clear()#清空

class 检查器查询对端:#查询对端
    """恰好关联一个源载体的查询协议状态。"""
    def __init__(自身,读取器,最大帧字节,传输,登记,已登记,注销):#构造
        """保存依赖。"""
        自身._读取器=读取器#读取器
        自身._最大帧字节=最大帧字节#帧上限
        自身._传输=传输#传输
        自身._登记=登记#登记
        自身._已登记=已登记#是否登记
        自身._注销=注销#注销
        自身._已接受=None#已接受
        自身._进行中={}#进行中
        自身._已关闭=False#是否已关闭

    def 接受(自身,源id,代数):#接受
        """源注册表接受后准入该源代数。"""
        if 自身._已关闭:#已关闭
            return#返回
        自身._已接受={'sourceId':源id,'generation':代数}#保存
        自身._进行中.clear()#清空进行中
        自身._登记(自身._已接受)#登记

    def 吊销(自身,源id,代数):#吊销
        """吊销一个代数，同时保留载体以供后续 source/open。"""
        if 自身._已接受 is None or 自身._已接受['sourceId']!=源id or 自身._已接受['generation']!=代数:#不符
            return#返回
        自身._已接受=None#清空
        自身._进行中.clear()#清空进行中

    def 接收(自身,值):#接收
        """当已解码载体值属于查询协议时消费它。"""
        if not isinstance(值,dict) or 值.get('t')!='query/request':#非查询信封
            return False#非查询
        try:#解析
            帧=值#已解析帧占位
            if _json字节长(帧)>自身._最大帧字节:#超限
                raise ValueError(f'inspector protocol: query request exceeds {自身._最大帧字节} bytes')#抛错
        except Exception as 错误:#畸形
            自身._拒绝畸形(值,_渲染错误(错误))#拒绝
            return True#已拥有
        已接受=自身._已接受#已接受
        if 自身._已关闭 or 已接受 is None or not 自身._已登记(已接受) or 已接受['sourceId']!=帧.get('sourceId') or 已接受['generation']!=帧.get('generation'):#不可用
            自身._发送失败(帧,'stale-source','Inspector query does not belong to the accepted source generation')#失败
            return True#已拥有
        if 帧.get('requestId') in 自身._进行中:#重复请求
            自身._发送失败(帧,'invalid-request','Inspector query requestId is already in flight')#失败
            return True#已拥有
        自身._进行中[帧['requestId']]=已接受#登记进行中
        在线程跑(lambda:自身._执行(帧,已接受))#后台执行
        return True#已拥有

    def 关闭(自身):#关闭
        """停止本对端并抑制进行中读取器的完成。"""
        if 自身._已关闭:#幂等
            return#返回
        自身._已关闭=True#置位
        自身._已接受=None#清空
        自身._进行中.clear()#清空
        自身._注销()#注销

    def _执行(自身,帧,已接受):#执行查询
        """跑查询并投递响应。"""
        try:#执行
            树读取=自身._读取器#读取器
            树=树读取() if not hasattr(树读取,'getTree') else 树读取.getTree()#取树
            树=解开(树)#可等待则等待
            结果={'op':帧['query']['op'],'tree':树}#结果
            if not 自身._可回复(帧,已接受):#不可回复
                return#返回
            响应={'v':检查器协议版本,'t':'query/response','sourceId':帧['sourceId'],'generation':帧['generation'],'requestId':帧['requestId'],'outcome':{'ok':True,'result':结果}}#响应
            if _json字节长(响应)>自身._最大帧字节:#结果过大
                自身._发送失败(帧,'result-too-large',f'Inspector query result exceeds {自身._最大帧字节} bytes')#失败
                return#返回
            自身._投递(响应)#投递
        except Exception as 错误:#执行失败
            if 自身._可回复(帧,已接受):#可回复
                自身._发送失败(帧,'internal-error',str(_渲染错误(错误)))#失败
        finally:#清理
            if 自身._进行中.get(帧['requestId']) is 已接受:#仍进行中
                del 自身._进行中[帧['requestId']]#移除

    def _拒绝畸形(自身,值,错误):#拒绝畸形
        """尽量带身份失败。"""
        try:#尽量带身份
            自身._发送失败(值,'invalid-request',str(错误))#失败响应
        except Exception:#无身份
            自身._拒绝传输(1008,str(错误))#关传输

    def _发送失败(自身,帧,码,信息):#发送失败
        """构造失败响应。"""
        if 自身._已关闭:#已关闭
            return#返回
        响应={'v':检查器协议版本,'t':'query/response','sourceId':帧['sourceId'],'generation':帧['generation'],'requestId':帧['requestId'],'outcome':{'ok':False,'error':{'code':码,'message':信息}}}#失败响应
        if _json字节长(响应)>自身._最大帧字节:#错误帧过大
            自身._拒绝传输(1009,'Inspector query error exceeds the frame limit')#关传输
            return#返回
        自身._投递(响应)#投递

    def _可回复(自身,帧,已接受):#可否回复
        """检查代数与进行中。"""
        return not 自身._已关闭 and 自身._已接受 is 已接受 and 自身._已登记(已接受) and 自身._进行中.get(帧['requestId']) is 已接受#条件

    def _投递(自身,帧):#投递响应
        """发送或关传输。"""
        try:#发送
            自身._传输['send'](帧)#发送
        except Exception as 错误:#发送失败
            自身._拒绝传输(1011,str(_渲染错误(错误)))#关传输

    def _拒绝传输(自身,码,原因):#拒绝传输
        """关对端与载体。"""
        自身.关闭()#关对端
        try:#关载体
            自身._传输['close'](码,原因[:123])#截断原因
        except Exception:#载体已废
            pass#载体已不可用；查询状态已达静默
