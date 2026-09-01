"""持久化投影缓存（对齐 upstream session-projection-cache）。"""
import copy,threading,time#克隆、脏状态、定时写
from ...依赖 import cordis,schemastery#Cordis 与配置
服务=cordis.服务#服务基类
from ...模型后端.llm import 结构化克隆#JSON 快照
from .规格 import 投影缓存域规格#域 spec
名称='session-projection-cache'#Cordis 插件名
注入=['storageDomain','sessionProjections','sessions']#依赖
配置=schemastery.对象字段({
    'writeEveryEvents':schemastery.数字字段(默认值=50),#事件阈值
    'writeIntervalMs':schemastery.数字字段(默认值=5000),#时间阈值
})#配置模式
__all__=['名称','注入','配置','会话投影缓存','默认']#公开面

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#可等待则等待
    """可等待则等待。"""
    if callable(getattr(值,'wait',None)):#Future
        return 值.wait()#等待
    if callable(getattr(值,'等待',None)):#中文
        return 值.等待()#等待
    return 值#同步

def 身份于(头):#头→身份
    """投影检查点记录绑定的生命周期身份。"""
    身份={'createdAt':取字段(头,'createdAt')}#创建时刻
    工作目录=取字段(头,'cwd')#cwd
    if 工作目录 is not None:#有 cwd
        身份['cwd']=工作目录#带上
    return 身份#返回

def 身份匹配(已存,期望):#身份一致
    """存储身份是否匹配期望。"""
    return 取字段(已存,'createdAt')==取字段(期望,'createdAt') and 取字段(已存,'cwd')==取字段(期望,'cwd')#字段相等

class 会话投影缓存(服务):#ctx.sessionProjectionCache
    """节流写后端的投影检查点缓存；读走域内存表。"""
    inject=['storageDomain','sessionProjections','sessions']#Cordis 注入
    def __init__(自身,上下文,配置值):#构造
        """登记服务并在 Service.init 打开域。"""
        super().__init__(上下文,'sessionProjectionCache')#服务名
        自身.配置=配置值#配置
        自身._表=None#Kv 表
        自身._脏={}#Session→脏状态
        自身._锁=threading.Lock()#并发锁
        自身.__dict__[服务.初始化]=自身._初始化#登记 init

    def _初始化(自身):#Service.init
        域=解开(自身.ctx.storageDomain.open(投影缓存域规格))#打开域
        def 关域():解开(域.close())#关闭
        yield 关域#effect
        自身._表=域.table('sessions')#sessions 表
        自身._安装写路径()#监听器

    def _要求表(自身):#取表
        if 自身._表 is None:#未初始化
            raise Exception('session projection cache is not initialized')#错误
        return 自身._表#表

    def _记录于(自身,标识,期望):#读记录
        """身份匹配才返回记录。"""
        记录=自身._要求表().get(标识)#读行
        if 记录 is None:#缺席
            return None#无
        return 记录 if 身份匹配(取字段(记录,'identity'),期望) else None#身份校验

    def 缓存快照(自身,头,键们=None):#零 IO 列表读
        """从存储行视图化检查点。"""
        记录=自身._记录于(取字段(头,'id'),身份于(头))#读记录
        if 记录 is None:#无记录
            return None#缺席
        值们=自身.ctx.sessionProjections.viewCheckpoint(取字段(记录,'rows'),键们)#视图
        if len(值们)==0:#无可用行
            return None#缺席
        水位=min(取字段(记录['rows'][键],'seq') for 键 in 值们)#最低水位
        return {'asOfSeq':水位,'values':值们}#快照

    cachedSnapshot=缓存快照#Cordis 槽

    def 注水预备(自身,会话,头,事件们):#hydratePrepared
        """为已预备会话安装恢复切面。"""
        记录=自身._记录于(取字段(头,'id'),身份于(头))#读记录
        if 记录 is None:#无缓存
            return 自身.ctx.sessionProjections.hydrate(会话,{},事件们,0)#空种子
        try:#带缓存种子
            return 自身.ctx.sessionProjections.hydrate(会话,取字段(记录,'rows'),事件们,0)#注水
        except Exception:#畸形缓存
            return 自身.ctx.sessionProjections.hydrate(会话,{},事件们,0)#回退

    hydratePrepared=注水预备#Cordis 槽

    async def 写(自身,会话):#耐久检查点
        """取注册表 cut 并写域。"""
        行们=自身.ctx.sessionProjections.checkpoint(会话)#cut
        自身._标干净(会话)#清脏
        if 自身.ctx.sessions.get(取字段(会话,'id')) is 会话:#仍活
            await 自身.ctx.sessions.flush(会话)#耐久屏障
        await 自身._放(取字段(会话,'id'),身份于(取字段(会话,'header')),行们)#写行

    write=写#Cordis 槽

    def 冷快照(自身,头,事件们):#coldSnapshot
        """从完整日志冷读并回写缓存。"""
        种子=自身._记录于(取字段(头,'id'),身份于(头))#读缓存
        种子行={} if 种子 is None else 取字段(种子,'rows',{})#行
        已恢复=自身.ctx.sessionProjections.restore(种子行,事件们,0,头)#折叠
        try:#回写
            解开(自身._放(取字段(头,'id'),身份于(头),已恢复['checkpoint']))#fail-soft
        except Exception as 错误:#写失败
            自身.ctx.logger.warn('session projection cache: cold-read write-back for "'+str(取字段(头,'id'))+'" failed (cache stays stale): '+str(错误))#警告
        return 已恢复['snapshot']#快照

    coldSnapshot=冷快照#Cordis 槽

    def _安装写路径(自身):#监听器
        """节流与三个强制点。"""
        def 收到事件(会话,事件):#session/event
            if 取字段(事件,'type')=='turn/end':#强制点
                解开(自身._软刷(会话,'turn/end'))#刷
                return#结束
            with 自身._锁:#脏计数
                状态=自身._脏.get(会话) or {'pending':0,'timer':None}#脏状态
                自身._脏[会话]=状态#登记
                状态['pending']+=1#计数
                if 状态['pending']>=自身.配置['writeEveryEvents']:#阈值
                    解开(自身._软刷(会话,'count threshold'))#刷
                    return#结束
                if 状态['timer'] is None:#装定时器
                    def 触发():解开(自身._软刷(会话,'interval'))#间隔刷
                    状态['timer']=threading.Timer(自身.配置['writeIntervalMs']/1000.0,触发)#定时
                    状态['timer'].daemon=True#守护
                    状态['timer'].start()#启动
        自身.ctx.on('session/event',收到事件)#挂
        def 收到创建(会话):#session/created
            解开(自身._软刷(会话,'create'))#强制点
        自身.ctx.on('session/created',收到创建)#挂
        def 收到处置(会话):#session/disposed
            解开(自身._软刷(会话,'detach'))#强制点
            自身._标干净(会话)#清脏
            with 自身._锁:#删脏
                自身._脏.pop(会话,None)#移除
        自身.ctx.on('session/disposed',收到处置)#挂
        def 清定时器():#插件拆除
            with 自身._锁:#扫定时器
                for 状态 in 自身._脏.values():#每条
                    定时=状态.get('timer')#定时器
                    if 定时 is not None:#有
                        定时.cancel()#取消
                自身._脏.clear()#清空
        自身.ctx.effect(lambda:清定时器,'sessionProjectionCache.timers')#effect

    async def _软刷(自身,会话,触发):#fail-soft 写
        try:#写
            await 自身.写(会话)#耐久
        except Exception as 错误:#失败
            自身.ctx.logger.warn('session projection cache: '+触发+' write for "'+str(取字段(会话,'id'))+'" failed (cache stays stale): '+str(错误))#警告

    def _标干净(自身,会话):#清脏
        with 自身._锁:#脏表
            状态=自身._脏.get(会话)#脏状态
            if 状态 is None:#无
                return#结束
            状态['pending']=0#清零
            定时=状态.get('timer')#定时器
            if 定时 is not None:#有
                定时.cancel()#取消
                状态['timer']=None#清空

    async def _放(自身,标识,身份,行们):#写一行
        分离=结构化克隆(行们)#JSON 快照
        if 分离 is None:#不可序列化
            raise TypeError('projection checkpoint is not losslessly JSON-serializable')#拒绝
        await 自身._要求表().put(标识,{'identity':身份,'rows':分离})#写域

def 应用(上下文,配置值):#加载插件
    """注册 sessionProjectionCache 服务。"""
    for 键 in ('writeEveryEvents','writeIntervalMs'):#校验
        值=配置值.get(键)#读
        if not isinstance(值,int) or 值<=0:#非法
            raise Exception('session-projection-cache: '+键+' must be a positive integer')#拒绝
    会话投影缓存(上下文,配置值)#构造即注册

apply=应用#Cordis 插件入口
default=会话投影缓存#默认导出类
默认=会话投影缓存#中文默认导出
