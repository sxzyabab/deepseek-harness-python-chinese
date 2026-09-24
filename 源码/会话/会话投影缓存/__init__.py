"""持久化投影缓存。"""
import threading,weakref#脏状态、定时写、会话身份
from ...依赖 import cordis#框架
from ...依赖.schemastery import 字典字段,数字字段#配置
服务=cordis.服务#服务基类
from ...模型后端.llm import 结构化克隆#JSON 快照
from ..会话投影 import 会话投影错误#注水失败
from .规格 import 投影缓存域规格#域 spec

class 投影缓存错误(Exception):
    """会话投影缓存包的异常基类。"""

包名='@deepseek-ai/dsh-session-projection-cache'
名称='session-projection-cache'
依赖=['storageDomain','sessionProjections','sessions']#依赖常量
配置模式=字典字段(字典结构={
    'writeEveryEvents':数字字段(默认值=50),#事件阈值
    'writeIntervalMs':数字字段(默认值=5000),#时间阈值
})#配置模式
__all__=['包名','名称','依赖','应用','默认','会话投影缓存','投影缓存错误']

前代标题键='title'#列表面仅暴露前代标题

def 生命周期身份于(头):
    """头单独能见证的生命周期身份。"""
    身份={'formatVersion':头['version'],'createdAt':头['createdAt'],'isSeeded':头.get('isSeeded',False)}#基
    if 'cwd' in 头:#有 cwd
        身份['cwd']=头['cwd']#带上
    return 身份#返回

def 身份于(头,继承事件数=0):
    """投影检查点记录绑定的完整折叠身份。"""
    切点=0 if 继承事件数 is None else 继承事件数#切点
    if not 头.get('isSeeded') and 切点!=0:#未播种却非零
        raise 投影缓存错误('unseeded projection-cache identity inherited event count must be 0')#拒绝
    return {**生命周期身份于(头),'inheritedEventCount':切点}#完整身份

def 生命周期身份匹配(已存,期望):
    """格式无关的生命周期字段是否匹配。"""
    已存播种=已存['isSeeded'] if 'isSeeded' in 已存 else False#缺省未播种
    期望播种=期望['isSeeded'] if 'isSeeded' in 期望 else False#期望
    已存目录=已存['cwd'] if 'cwd' in 已存 else None#已存 cwd
    期望目录=期望['cwd'] if 'cwd' in 期望 else None#期望 cwd
    return 已存['createdAt']==期望['createdAt'] and 已存目录==期望目录 and 已存播种==期望播种#字段相等

def 当代生命周期匹配(已存,期望):
    """是否在当代格式代下折叠自同一生命周期。"""
    return 已存.get('formatVersion')==期望.get('formatVersion') and 生命周期身份匹配(已存,期望)#格式加生命周期

def 身份匹配(已存,期望):
    """存储身份是否可播种调用方折叠。"""
    已存继承=已存['inheritedEventCount'] if 'inheritedEventCount' in 已存 else 0#缺省未播种切点
    return 当代生命周期匹配(已存,期望) and 已存继承==期望.get('inheritedEventCount',0)#切点也要同

def 前代身份匹配(已存,期望):
    """前代缓存记录是否匹配权威列出的生命周期。"""
    已存代=已存['formatVersion'] if 'formatVersion' in 已存 else None#已存代
    期望代=期望.get('formatVersion')#期望代
    前代=已存代 is None or (期望代 is not None and 已存代<期望代)#更早
    return 前代 and 生命周期身份匹配(已存,期望)#生命周期仍同

class 会话投影缓存(服务):
    """节流写后端的投影检查点缓存；读走域内存表。"""
    def __init__(自身,上下文,配置值):
        """登记服务并在 Service.init 打开域。"""
        super().__init__(上下文,'sessionProjectionCache')#服务名
        自身.配置=配置值#配置
        自身._表=None#Kv 表
        自身._脏=weakref.WeakKeyDictionary()#Session→脏状态
        自身._锁=threading.Lock()#并发锁
        自身.__dict__[服务.初始化]=自身._初始化#登记 init

    def _初始化(自身):
        """打开存储域并安装写路径。"""
        域=自身.ctx.storageDomain.open(投影缓存域规格)#打开域
        def 关域():
            """关闭域。"""
            域.close()#关闭
        yield 关域#effect
        自身._表=域.table('sessions')#sessions 表
        自身._安装写路径()#监听器

    def _要求表(自身):
        """取已打开的表。"""
        if 自身._表 is None:
            raise 投影缓存错误('session projection cache is not initialized')#错误
        return 自身._表#表

    def _记录于(自身,标识,期望):
        """身份匹配才返回记录。"""
        记录=自身._要求表().get(标识)#读行
        if 记录 is None:
            return None#无
        return 记录 if 身份匹配(记录['identity'],期望) else None#身份校验

    def 缓存快照(自身,头,键列表=None):
        """从存储行视图化检查点。"""
        记录=自身._要求表().get(头['id'])#读行
        if 记录 is None or not 当代生命周期匹配(记录['identity'],生命周期身份于(头)):
            return None#缺席或非当代生命周期
        return 自身._视图记录(记录,键列表)#视图

    def 缓存前代标题(自身,头):
        """只读前代检查点的标题作为列表面提示。"""
        记录=自身._要求表().get(头['id'])#读行
        if 记录 is None or not 前代身份匹配(记录['identity'],生命周期身份于(头)):
            return None#非前代或无关
        return 自身._视图记录(记录,[前代标题键])#仅标题

    def _视图记录(自身,记录,键列表=None):
        """把选中行收成最低水位块。"""
        值表=自身.ctx.sessionProjections.视图检查点(记录['rows'],键列表)#视图
        if len(值表)==0:
            return None#缺席
        水位=min(记录['rows'][键]['seq'] for 键 in 值表)#最低水位
        return {'asOfSeq':水位,'values':值表}#快照

    def 注水预备(自身,会话,事件列表):
        """为已预备会话安装恢复切面。"""
        记录=自身._记录于(会话.id,身份于(会话.header,getattr(会话,'inheritedEventCount',0)))#读记录
        if 记录 is None:
            return 自身.ctx.sessionProjections.注水(会话,{},事件列表,0)#空种子
        try:
            return 自身.ctx.sessionProjections.注水(会话,记录['rows'],事件列表,0)#注水
        except (TypeError,KeyError,ValueError,会话投影错误):
            return 自身.ctx.sessionProjections.注水(会话,{},事件列表,0)#畸形缓存回退

    def 写(自身,会话):
        """取投影表面切口并写域；活会话先刷耐久屏障。"""
        行表=自身.ctx.sessionProjections.检查点(会话)#表面切口
        自身._标干净(会话)#写前摘掉脏标记与定时器
        if 自身.ctx.sessions.get(会话.id) is 会话:
            自身.ctx.sessions.flush(会话).等待()#耐久屏障
        自身._放(会话.id,身份于(会话.header,getattr(会话,'inheritedEventCount',0)),行表)#写行

    def 冷快照(自身,头,继承事件数,事件列表):
        """从完整日志冷读并回写缓存。"""
        身份=身份于(头,继承事件数)#完整身份
        种子=自身._记录于(头['id'],身份)#读缓存
        种子行={} if 种子 is None else 种子['rows']#行
        已恢复=自身.ctx.sessionProjections.恢复(种子行,事件列表,0,头,继承事件数)#折叠
        try:
            自身._放(头['id'],身份,已恢复['checkpoint'])#回写
        except Exception as 错误:
            自身.ctx.日志.警告('session projection cache: cold-read write-back for "'+str(头['id'])+'" failed (cache stays stale): '+str(错误))#警告
        return 已恢复['snapshot']#快照

    def _安装写路径(自身):
        """节流与三个强制点。"""
        def 收到事件(会话,事件):
            """session/event。"""
            if 事件['type']=='turn/end':
                自身._软刷(会话,'turn/end')#刷
                return
            with 自身._锁:
                状态=自身._脏.get(会话)#脏状态
                if 状态 is None:
                    状态={'pending':0,'timer':None}#新脏状态
                    自身._脏[会话]=状态#登记
                状态['pending']+=1#计数
                if 状态['pending']>=自身.配置['writeEveryEvents']:
                    自身._软刷(会话,'count threshold')#刷
                    return
                if 状态['timer'] is None:
                    def 触发():
                        """间隔刷。"""
                        自身._软刷(会话,'interval')#间隔刷
                    状态['timer']=threading.Timer(自身.配置['writeIntervalMs']/1000.0,触发)#定时
                    状态['timer'].daemon=True#守护
                    状态['timer'].start()
        自身.ctx.监听('session/event',收到事件)#会话事件触发软刷
        def 收到创建(会话):
            """session/created。"""
            自身._软刷(会话,'create')#强制点
        自身.ctx.监听('session/created',收到创建)#新建会话强制写
        def 收到拆除(会话):
            """session/disposed。"""
            自身._软刷(会话,'detach')#强制点
            自身._标干净(会话)#拆除前清脏
            with 自身._锁:
                自身._脏.pop(会话,None)#移除
        自身.ctx.监听('session/disposed',收到拆除)#拆除时刷并摘脏
        def 清定时器效果():
            """插件拆除。"""
            def 清定时器():
                """取消全部定时器。"""
                with 自身._锁:
                    for 状态 in 自身._脏.values():
                        定时=状态['timer'] if 'timer' in 状态 else None#定时器
                        if 定时 is not None:
                            定时.cancel()#取消
                    自身._脏.clear()#清空
            return 清定时器#副作用拆除回调
        自身.ctx.副作用(清定时器效果,'sessionProjectionCache.timers')#插件寿命绑定定时器清理

    def _软刷(自身,会话,触发):
        """fail-soft 写。"""
        try:
            自身.写(会话)#耐久
        except Exception as 错误:
            自身.ctx.日志.警告('session projection cache: '+触发+' write for "'+str(会话.id)+'" failed (cache stays stale): '+str(错误))#警告

    def _标干净(自身,会话):
        """清脏。"""
        with 自身._锁:
            状态=自身._脏.get(会话)#脏状态
            if 状态 is None:
                return
            状态['pending']=0#清零
            定时=状态['timer'] if 'timer' in 状态 else None#定时器
            if 定时 is not None:
                定时.cancel()#取消
                状态['timer']=None#清空

    def _放(自身,标识,身份,行表):
        """写一行。"""
        分离=结构化克隆(行表)#JSON 快照
        if 分离 is None:
            raise TypeError('projection checkpoint is not losslessly JSON-serializable (a unit state violates the plain-JSON contract)')#拒绝
        自身._要求表().put(标识,{'identity':身份,'rows':分离})#写域

def 应用(上下文,配置值):
    """注册 sessionProjectionCache 服务。"""
    for 键 in ('writeEveryEvents','writeIntervalMs'):
        值=配置值[键] if 键 in 配置值 else None#读
        if not isinstance(值,int) or isinstance(值,bool) or 值<=0:
            raise 投影缓存错误('session-projection-cache: '+键+' must be a positive integer')#拒绝
    会话投影缓存(上下文,配置值)#构造即注册

默认=会话投影缓存
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置模式#框架槽
default=默认#框架槽
会话投影缓存.inject=依赖#框架槽
会话投影缓存.Config=配置模式#框架槽
会话投影缓存.name=名称#框架槽
