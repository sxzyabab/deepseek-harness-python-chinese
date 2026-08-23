"""凭证引用能力缝（ctx.credentials）的服务定义。设置与组合文件携带的是密钥的引用——环境变量名——而提供方拥有实际值及其存储。消费方每次操作解析一次引用，因此变更后的凭证会在无需重启插件的情况下到达下一次操作；配置面描述引用，却从不看见其值。"""
import re,threading#正则与后台观察拒绝
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
是否thenable=cordis.工具.是否thenable#可等待判定
from .类型 import 凭证引用品牌#再导出凭证引用品牌

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '引用形态','引用模式','凭证引用','已解析凭证字段','已解析凭证',
    '凭证信息字段','凭证信息','凭证提供方','凭证引用品牌','默认',
]#公开面结束

引用形态='^[A-Za-z_][A-Za-z0-9_]*$'#POSIX 标识符形态源
引用模式=re.compile(引用形态)#POSIX 标识符形态的引用

def 凭证引用(值):#校验并品牌化引用
    """把原始字符串打成凭证引用。候选引用须为 POSIX shell 标识符，例如 DEEPSEEK_API_KEY。"""
    if 引用模式.fullmatch(值) is None:#引用不符合标识符规则
        raise TypeError('credential ref "'+值+'" must match /'+引用形态+'/')#拒绝非法引用
    return 值#返回品牌化引用

已解析凭证字段=(#一条已解析的凭证值，以及给出它的源层
    'value',#非空密钥值
    'source',#提供方定义的源层 id（本地提供方使用 env、file、project-env 和 user-env）
)#已解析凭证字段结束
已解析凭证=已解析凭证字段#中文别名

凭证信息字段=(#一条引用的来源与可写性事实，可供配置 UI 使用——绝不含值
    'configured',#CredentialProvider.resolve 当前是否会返回值
    'source',#当前提供该值的源层；未配置时缺省
    'writable',#CredentialProvider.set 当前是否会对这条引用成功
)#凭证信息字段结束
凭证信息=凭证信息字段#中文别名

class 凭证提供方(服务):#凭证提供方服务定义
    """抽象凭证服务。提供方在各自源层上实现这四个操作；整条缝有一条共同规则：空的已存值在任何地方都算缺席——解析跳过它，描述报未配置——因此空白绝不能冒充已配置的密钥。"""
    def __init__(自身,ctx):#把本服务登记为 credentials
        """把本服务登记为 credentials。"""
        super().__init__(ctx,'credentials')#以 credentials 名安装服务

    def 解析(自身,引用):#按次解析引用
        """把一条引用解析成当前值。解析是按次的：消费方每次操作都重新解析，不得跨操作缓存——正是这次按操作读取，才让变更后的凭证无需重启就能到达下一次操作。未配置时为 None。返回已解析凭证字段（value、source）或 None。"""
        raise NotImplementedError('CredentialProvider.resolve')#子类必须实现

    def 描述(自身,引用):#描述引用而不给值
        """为配置面描述一条引用，不暴露其值。返回凭证信息字段（configured、source?、writable）。"""
        raise NotImplementedError('CredentialProvider.describe')#子类必须实现

    def 设置(自身,引用,值):#写入可写源
        """把一个值持久写入提供方管理的可写源。只读源正在遮蔽该引用时拒绝——写看起来会成功，解析却仍返回遮蔽值——也拒绝空值（改用移除）。"""
        raise NotImplementedError('CredentialProvider.set')#子类必须实现

    def 移除(自身,引用):#从可写源删除
        """从提供方管理的可写源移除一条引用；移除本就不存在的引用是空操作。只读源正在遮蔽该引用时拒绝，与设置相同。"""
        raise NotImplementedError('CredentialProvider.unset')#子类必须实现

    def 通知已更新(自身,引用):#向监听器扇出已提交变更
        """以内含监听失败的方式扇出 credentials/updated：每个监听器都会跑；同步抛出或异步拒绝只记日志，不改变已提交操作的结果——带 INVARIANT 码的失败除外，它们会在每个监听器都跑完后重新抛出（该重抛只从同步监听器到达调用方，因此本事件上的不变量检查不得写成 async 函数）。提供方只在写入或重载真正提交之后调用，这样坏掉的观察者绝不能让一次持久变更看起来失败。"""
        不变量失败=None#暂存不变量失败以便全部跑完再抛
        参数=['credentials/updated',引用]#组装 emit 派发参数
        for 监听器 in 自身.ctx.events.dispatch('emit',参数):#逐个取出监听器
            try:#同步执行单个监听器
                返回=监听器(引用)#调用监听器并拿到可能的承诺
                if 是否thenable(返回):#返回值像承诺则接管拒绝
                    def 盯住(任务=返回,当前引用=引用):#把异步拒绝接到诊断
                        """把异步拒绝接到诊断。"""
                        try:#等待承诺
                            任务.等待()#等待承诺
                        except Exception as 错误:#异步拒绝
                            自身.警告监听失败(当前引用,错误)#记录异步监听失败
                    线程=threading.Thread(target=盯住)#后台观察
                    线程.daemon=True#不挡住退出
                    线程.start()#启动
            except Exception as 错误:#同步抛出
                if getattr(错误,'code',None)=='INVARIANT':#不变量失败要保留
                    if 不变量失败 is None:#尚未记下
                        不变量失败=错误#只记下第一次不变量失败
                    continue#继续跑完其余监听器
                自身.警告监听失败(引用,错误)#普通失败只记日志
        if 不变量失败 is not None:#有不变量失败
            raise 不变量失败#全部跑完后抛出不变量失败

    def 警告监听失败(自身,引用,错误):#记录单个监听失败
        """同步与异步失败路径共用的内含监听诊断。"""
        自身.ctx.logger.warn('credentials: a credentials/updated listener for "%s" failed',引用)#警告监听失败
        自身.ctx.logger.warn(错误)#再打印失败对象

default=凭证提供方#默认导出凭证提供方基类
默认=凭证提供方#中文默认导出
