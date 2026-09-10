"""交付卡片与收口消息文件提及共用的原生打开状态。

对齐上游 `ui-deliverables/src/client/present-open.ts`。公开面仅中文名。
async/await 翻成同步；Promise 翻成直接返回。中止用 threading.Event。
"""
import threading#寿命与元数据中止
from concurrent.futures import Future as _原生Future,wait as _等待全部#在飞任务
from ...客户端.存储 import 创建快照存储#快照存储
from .已呈现 import 已呈现文件网址,呈现宿主路径,是否已呈现宿主#坐标与宿主

__all__=['已呈现打开控制器','已呈现打开错误']#仅中文公开名

class 已呈现打开错误(Exception):
    """已呈现打开失败。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#英文

class _操作任务:#单次操作 Future
    """只留 等待。"""
    def __init__(自身):
        """构造未决。"""
        自身._未来=_原生Future()#底层

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._未来.done():#尚未
            自身._未来.set_result(值)#写入
        return 值#返回

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._未来.done():#尚未
            自身._未来.set_exception(错误 if isinstance(错误,BaseException) else 已呈现打开错误(str(错误)))#拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._未来.result(timeout=超时)#取结果

class 已呈现打开控制器:#浏览器侧打开控制器
    """一个插件一份；拆除时取消未完请求。"""
    def __init__(自身,拉取=None):
        """可选注入拉取函数（测用）；默认不发起真实 HTTP。"""
        自身.状态=创建快照存储({})#阶段存储 url→阶段
        自身.宿主=创建快照存储(None)#宿主元数据
        自身._加载中=None#在飞宿主读
        自身._元数据=threading.Event()#元数据中止；set=已中止
        自身._寿命=threading.Event()#寿命中止
        自身._在飞=set()#在飞 Future
        自身._拉取=拉取#可选拉取

    def 打开(自身,会话标识,序号,下标,动作='open'):#打开或揭示
        """同一坐标在飞时只打开一次。失败留在卡片上，后续手势可重试。"""
        网址=已呈现文件网址(会话标识,序号,下标)#动作 URL
        快照=自身.状态.getSnapshot()#当前
        阶段=快照[网址] if 网址 in 快照 else None#阶段
        if 自身._寿命.is_set() or 阶段 in ('opening','revealing'):#已中止或在飞
            return#空操作
        def 写进行中(状态):#进入进行中
            """更新阶段。"""
            状态[网址]='opening' if 动作=='open' else 'revealing'#进行中
        自身.状态.update(写进行中)#发布进行中
        任务=_操作任务()#新任务
        自身._在飞.add(任务._未来)#记下
        try:#请求
            自身._请求(网址,动作)#同步请求
            任务.兑现()#成功
        except BaseException as 错误:#失败
            任务.拒绝(错误)#拒绝
            raise#上抛
        finally:#结算
            自身._在飞.discard(任务._未来)#移出
        return 任务.等待()#已结算

    def 加载宿主(自身):#加载宿主元数据
        """读服务桌面元数据，合并并发读。"""
        if 自身._寿命.is_set():#已中止
            return#空
        if 自身._加载中 is not None:#合并并发
            return 自身._加载中.等待()#等既有
        自身.宿主.set(None)#清空
        任务=_操作任务()#新任务
        自身._加载中=任务#记下
        自身._在飞.add(任务._未来)#计入
        try:#读
            自身._读宿主()#同步读
            任务.兑现()#成功
        except BaseException as 错误:#失败
            任务.拒绝(错误)#拒绝
            raise#上抛
        finally:#结算
            if 自身._加载中 is 任务:#仍是本任务
                自身._加载中=None#清
            自身._在飞.discard(任务._未来)#移出
        return 任务.等待()#已结算

    def 重置宿主(自身):#连接替换时作废
        """作废桌面元数据；曾在读则重载。"""
        曾加载=自身._加载中 is not None#是否在读
        自身._元数据.set()#中止旧读
        自身._元数据=threading.Event()#新旗
        自身._加载中=None#清在飞
        自身.宿主.set(None)#清空
        if 曾加载:#曾在读
            自身.加载宿主()#重载

    def 拆除(自身):#拆除
        """取消未完，等到没有任何请求还能发布状态。"""
        自身._寿命.set()#中止寿命
        if len(自身._在飞)>0:#有在飞
            _等待全部(list(自身._在飞))#等全部

    def _读宿主(自身):#读宿主元数据
        """拉取 present.host。"""
        if 自身._寿命.is_set() or 自身._元数据.is_set():#已中止
            return#空
        宿主='error'#默认失败
        try:#拉取
            if 自身._拉取 is not None:#注入拉取
                应答=自身._拉取(呈现宿主路径,{'method':'GET'})#GET
                if 应答 is not None and 'ok' in 应答 and 应答['ok'] and 'json' in 应答:#成功
                    值=应答['json']#解码
                    if 是否已呈现宿主(值):#合法
                        宿主=值#采用
            else:#无拉取则保持错误
                宿主='error'#失败
        except Exception:#传输失败
            宿主='error'#失败
        if not 自身._寿命.is_set() and not 自身._元数据.is_set():#未中止才发布
            自身.宿主.set(宿主)#发布

    def _请求(自身,网址,动作):#发起打开请求
        """POST 打开或揭示。"""
        失败='error' if 动作=='open' else 'revealError'#失败阶段
        阶段='opened' if 动作=='open' else 'revealed'#默认成功
        try:#拉取
            目标=网址 if 动作=='open' else 网址+'&action=reveal'#URL
            if 自身._拉取 is not None:#有拉取
                应答=自身._拉取(目标,{'method':'POST'})#POST
                if 应答 is None or 'ok' not in 应答 or not 应答['ok']:#失败
                    状态码=应答['status'] if 应答 is not None and 'status' in 应答 else 0#状态
                    阶段='nativeUnavailable' if 状态码==422 else 失败#映射
            else:#无拉取视为失败
                阶段=失败#失败
        except Exception:#传输失败
            阶段=失败#失败
        if not 自身._寿命.is_set():#未中止才发布
            def 写阶段(状态):#写阶段
                """更新。"""
                状态[网址]=阶段#阶段
            自身.状态.update(写阶段)#发布
