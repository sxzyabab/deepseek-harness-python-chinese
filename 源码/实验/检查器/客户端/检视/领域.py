"""稳定的 Client 源身份：每个 WebSocket 代数使用新描述符。

对齐上游 `client/inspection/realm.ts`。公开面仅中文名。
"""
import time,uuid#时间与UUID
from ...共享.身份 import 检查器id#带品牌id
from ..cdp import 桥能力#桥能力集

__all__=['客户端领域源']#仅中文公开名

客户端源存储键='dsh.experimental-inspector.client-source-id.v0'#会话存储键

def 生成客户端源标识():#生成源id
    """生成源id。"""
    return 检查器id(f'client-{uuid.uuid4()}','sourceId')#新id

def 会话客户端源标识():#会话源id
    """会话源id。"""
    return 生成客户端源标识()#本页生命周期内

def 客户端来源():#Client origin
    """Client origin。"""
    try:#取location
        import builtins#全局
        定位=getattr(builtins,'location',None)#location
        来源=getattr(定位,'origin',None) if 定位 is not None else None#origin
        return 来源 if isinstance(来源,str) else ''#字符串或空
    except Exception:#无
        return ''#空

class 客户端领域源:#Client realm源
    """跨传输重连拥有一个浏览器 realm 的稳定 source id。"""
    def __init__(自身,标签,源标识=None,释放声明=None):#构造
        """保存标签与源id。"""
        自身.标签=标签#标签
        自身.sourceId=源标识 or 会话客户端源标识()#源id
        自身.释放声明=释放声明#释放声明

    @staticmethod
    def 声明(标签):#声明身份
        """在打开源传输前声明标签页身份。"""
        return 客户端领域源(标签,会话客户端源标识())#已声明的 realm 源

    def 连接(自身,有源):#连接描述
        """为一个新准入的传输代数创建描述符。"""
        return {#描述符
            'sourceId':自身.sourceId,#源id
            'generation':检查器id(str(uuid.uuid4()),'generation'),#代数
            'kind':'client',#种类
            'label':自身.标签,#标签
            'timeOriginMs':time.time()*1000,#时间原点
            'capabilities':桥能力(客户端来源(),有源),#能力集
        }#返回

    def 关闭(自身):#关闭
        """释放本页的身份声明。"""
        if 自身.释放声明 is not None:#释放锁
            自身.释放声明()#释放
        自身.释放声明=None#清空
