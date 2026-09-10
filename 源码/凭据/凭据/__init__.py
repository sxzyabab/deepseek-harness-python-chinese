"""凭证引用能力缝（ctx.credentials）的服务定义。设置与组合文件携带的是密钥的引用——环境变量名——而提供方拥有实际值及其存储。消费方每次操作解析一次引用，因此变更后的凭证会在无需重启插件的情况下到达下一次操作；配置面描述引用，却从不看见其值。

记录半边（CredentialKey）回答「这个插件为这个 id 持有什么凭证」；与引用文法互斥（含 `/`）。
"""
import re#正则
from ...依赖 import cordis#外部依赖胶水
from ...依赖.工具 import 获取内部数据#读事件总线内部成员
服务=cordis.服务#Cordis 服务基类
from .类型 import 凭证引用品牌#再导出凭证引用品牌

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '引用形态','引用模式','凭证引用','是否凭证引用名','键段形态','键段模式',
    '是否凭证键段','凭证键','解析凭证键','凭证键作用域','凭证键标识',
    '已解析凭证字段','已解析凭证',
    '凭证信息字段','凭证信息','凭证提供方','凭证引用品牌','默认',
]#公开面结束

引用形态='^[A-Za-z_][A-Za-z0-9_]*$'#POSIX 标识符形态源
引用模式=re.compile(引用形态)#POSIX 标识符形态的引用
键段形态='^[a-z][a-z0-9-]*$'#记录键段：小写连字符
键段模式=re.compile(键段形态)#键段正则

def 凭证引用(值):#校验并品牌化引用
    """把原始字符串打成凭证引用。候选引用须为 POSIX shell 标识符，例如 DEEPSEEK_API_KEY。"""
    if 引用模式.fullmatch(值) is None:#引用不符合标识符规则
        raise TypeError('credential ref "'+值+'" must match /'+引用形态+'/')#拒绝非法引用
    return 值#返回品牌化引用

def 是否凭证引用名(值):#引用名是否合法
    """原始字符串是否根本能命名一条引用。"""
    return isinstance(值,str) and 引用模式.fullmatch(值) is not None#测

def 是否凭证键段(值):#键段是否合法
    """原始字符串是否根本能作为凭证键段。"""
    return isinstance(值,str) and 键段模式.fullmatch(值) is not None#测

def 凭证键(作用域,标识):#构造记录键
    """把 scope 与 id 打成凭证键（`scope/id`）。"""
    for 段 in (作用域,标识):#逐段
        if not 是否凭证键段(段):#非法
            raise TypeError('credential key segment "'+str(段)+'" must match /'+键段形态+'/')#拒绝
    return 作用域+'/'+标识#品牌键

def 解析凭证键(值):#解析已存键串
    """把已存的 `<scope>/<id>` 字符串打成凭证键。"""
    段列表=值.split('/')#拆
    if len(段列表)!=2:#必须两段
        raise TypeError('credential key "'+值+'" must be "<scope>/<id>"')#拒绝
    return 凭证键(段列表[0],段列表[1])#再校验

def 凭证键作用域(键):#取 scope
    """一条键所属插件的名称。"""
    return 键[:键.index('/')]#斜杠前

def 凭证键标识(键):#取 id
    """一条键上拥有插件自己的寻址单元。"""
    return 键[键.index('/')+1:]#斜杠后

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
    """抽象凭证服务，覆盖引用与记录两套键空间。

    记录半边默认落在进程内表；本地文件后端覆写为 versioned `records` 节持久化。
    """
    def __init__(自身,ctx):#把本服务登记为 credentials
        """把本服务登记为 credentials。"""
        super().__init__(ctx,'credentials')#以 credentials 名安装服务
        自身._记录表={}#进程内记录：键 → 记录 dict（非本地后端回退）

    def 解析(自身,引用):#按次解析引用
        """把一条引用解析成当前值。未配置时为 None。"""
        raise NotImplementedError('CredentialProvider.resolve')#子类必须实现

    def 描述(自身,引用):#描述引用而不给值
        """为配置面描述一条引用，不暴露其值。"""
        raise NotImplementedError('CredentialProvider.describe')#子类必须实现

    def 设置(自身,引用,值):#写入可写源
        """把一个值持久写入提供方管理的可写源。"""
        raise NotImplementedError('CredentialProvider.set')#子类必须实现

    def 移除(自身,引用):#从可写源删除
        """从提供方管理的可写源移除一条引用。"""
        raise NotImplementedError('CredentialProvider.unset')#子类必须实现

    def 读记录(自身,键):#读记录
        """读一条已存记录；未存时为 None。"""
        return 自身._记录表[键] if 键 in 自身._记录表 else None#快照

    def 描述记录(自身,键):#描述记录
        """为配置面描述一条记录，不暴露其值。"""
        已存=自身.读记录(键)#读
        if 已存 is None:#未存
            return {'configured':False,'writable':True}#未配置
        return {'configured':True,'kind':已存['kind'],'writable':True}#已存

    def 列举记录(自身):#枚举记录
        """枚举每条已存记录的地址与标签。"""
        return [{'key':键,'kind':记录['kind']} for 键,记录 in 自身._记录表.items()]#条目

    def 修改记录(自身,键,变更):#串行读改写
        """对一条记录的读-改-写。变更(当前)→下一份或 None（不动）。"""
        当前=自身.读记录(键)#当前
        下一份=变更(当前)#决策
        if 下一份 is None:#不动
            return 当前#当前
        自身._记录表[键]=下一份#写入
        自身.通知记录已更新(键)#扇出
        return 下一份#新记录

    def 删除记录(自身,键):#删除记录
        """移除一条记录；本就不存在则为空操作。"""
        if 键 not in 自身._记录表:#无
            return#空
        del 自身._记录表[键]#删
        自身.通知记录已更新(键)#扇出

    def 通知已更新(自身,引用):#向监听器扇出已提交变更
        """扇出 credentials/updated（兼容）与 credentials/reference-updated。"""
        自身._扇出('credentials/updated',引用)#旧名
        自身._扇出('credentials/reference-updated',引用)#新名

    def 通知记录已更新(自身,键):#扇出记录变更
        """扇出 credentials/record-updated。"""
        自身._扇出('credentials/record-updated',键)#记录

    def _扇出(自身,事件名,主体):#内含扇出
        """两种通知共用的内含派发。"""
        不变量失败=None#暂存
        参数=[事件名,主体]#派发参数
        事件总线=获取内部数据(自身.ctx,'属性链')['事件']#事件总线
        for 监听器 in 获取内部数据(事件总线,'解析监听器')(事件总线,'emit',参数):#逐个
            try:
                监听器(主体)#同步
            except Exception as 错误:
                if getattr(错误,'code',None)=='INVARIANT':#不变量
                    if 不变量失败 is None:
                        不变量失败=错误#首个
                    continue#继续
                自身.警告监听失败(事件名,主体,错误)#日志
        if 不变量失败 is not None:
            raise 不变量失败#重抛

    def 警告监听失败(自身,事件名,主体,错误):#诊断
        """内含监听诊断。"""
        自身.ctx.日志.警告('credentials: a %s listener for "%s" failed',事件名,主体)#警告
        自身.ctx.日志.警告(错误)#详情

default=凭证提供方#默认导出
默认=凭证提供方#中文默认导出
