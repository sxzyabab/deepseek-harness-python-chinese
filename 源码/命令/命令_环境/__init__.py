"""与工具无关的 shell 环境插件：拥有环境注册表，存放面向模型的 shell 工具消费的受信任、按次执行 DSH_* 变量。

内置 shell 事实由注册表自身拥有，插件可以注册额外的、可枚举事实，并随副作用拆除。
"""
import re#环境键后缀校验
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段#配置字段
服务=cordis.服务#Cordis服务基类
from ..命令 import 托管环境前缀#DSH_前缀
from ...工具.主目录路径 import 解析主目录,主目录环境键#解析harness主目录与DSH_HOME键

__all__=(
    '名称','依赖','配置',
    '主目录环境键','外壳键','会话ID键','会话JSONL键','保留环境键',
    '外壳环境注册表','应用',
)#仅中文公开名

名称='shell-env'#插件名
依赖=[]#无硬依赖
配置={#插件配置模式
    'dshHome':字符串字段(),#作为DSH_HOME暴露的家目录；默认$DSH_HOME或~/.dsh
}#配置模式结束
外壳键=托管环境前缀+'SHELL'#DSH_SHELL键
会话ID键=托管环境前缀+'SESSION_ID'#DSH_SESSION_ID键
会话JSONL键=托管环境前缀+'SESSION_JSONL'#DSH_SESSION_JSONL键
保留环境键=set((主目录环境键,外壳键,会话ID键))#注册表自留键
环境键后缀模式=re.compile(r'^[A-Z][A-Z0-9_]*\Z',re.ASCII)#前缀之后的合法后缀

class 外壳环境错误(Exception):#本包异常基类
    """shell 环境贡献方登记或收集失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 按名排序(贡献方):#sorted 的键函数
    """按贡献方名字排序。"""
    return 贡献方['name']#名

def 按键排序项(项):#sorted 的键函数
    """按快照键名排序。"""
    return 项[0]#键

def 按声明键排序(项):#列出结果的键函数
    """按声明键名排序。"""
    return 项['key']#键

class 外壳环境注册表(服务):#受信任按次执行DSH_*变量的注册表
    """受信任、按次执行 DSH_* 变量的注册表。命名空间为每次模型 shell 调用重建：执行器丢掉环境中的 DSH_* 值，然后注入注册表的当前快照。内置 shell 事实仍由注册表自身拥有，插件可以注册额外的、可枚举事实，并随副作用拆除。"""
    def __init__(自身,上下文,配置值=None):#安装shellEnv服务
        """创建并安装环境注册表服务。"""
        super().__init__(上下文,'shellEnv')#服务名shellEnv
        if 配置值 is None:#未传配置
            配置值={}#空配置
        自身.贡献方表={}#贡献方名到贡献方
        自身.键拥有者={}#键到拥有贡献方
        自身.家目录=解析主目录(配置值['dshHome'] if 'dshHome' in 配置值 else None)#解析家目录

    def 登记(自身,贡献方):#注册一个环境贡献方
        """注册一个环境贡献方。名与键唯一；内置键保留。注册随调用插件 fiber 拆除。贡献方是 dict。"""
        def 挂上():#随fiber拆除
            """挂上贡献并在拆除时摘掉。"""
            名字=贡献方['name']#贡献方名
            if 名字 is None or len(str(名字).strip())==0:#名为空
                raise 外壳环境错误('bash env contributor name must be non-empty')#名必须非空
            if 名字 in 自身.贡献方表:#名已占用
                raise 外壳环境错误('bash env contributor "'+str(名字)+'" is already registered')#贡献方重复
            变量表=贡献方['variables'] if 'variables' in 贡献方 else None#声明的键
            if 变量表 is None:#缺变量表
                变量表={}#空表
            键项列表=list(变量表.items())#键列表
            for 键,变量 in 键项列表:#逐键校验
                if (not str(键).startswith(托管环境前缀)) or (环境键后缀模式.fullmatch(str(键)[len(托管环境前缀):]) is None):#键非法
                    raise 外壳环境错误('bash env contributor "'+str(名字)+'" declared invalid key "'+str(键)+'"')#键非法
                if 键 in 保留环境键:#占用保留键
                    raise 外壳环境错误('bash env contributor "'+str(名字)+'" cannot own reserved key "'+str(键)+'"')#不能拥有保留键
                描述=变量['description'] if 'description' in 变量 else None#描述
                if 描述 is None or len(str(描述).strip())==0:#描述为空
                    raise 外壳环境错误('bash env contributor "'+str(名字)+'" must describe "'+str(键)+'"')#必须描述该键
                拥有者=自身.键拥有者[键] if 键 in 自身.键拥有者 else None#现有拥有者
                if 拥有者 is not None:#键已被占
                    raise 外壳环境错误('bash env key "'+str(键)+'" is already owned by contributor "'+str(拥有者)+'"; contributor "'+str(名字)+'" cannot also own it')#键冲突
            自身.贡献方表[名字]=贡献方#记下贡献方
            for 键,_变量 in 键项列表:#记下键所有权
                自身.键拥有者[键]=名字#键到贡献方
            def 摘掉():#拆除
                """拆除该贡献。"""
                自身.贡献方表.pop(名字,None)#去掉贡献方
                for 键,_变量 in 键项列表:#释放键
                    自身.键拥有者.pop(键,None)#释放键所有权
            return 摘掉#拆除器
        return 自身.ctx.副作用(挂上,'bashEnv.register()')#绑到本注册表并返回拆除句柄

    def 收集(自身,执行):#为一次shell工具执行构建受信任快照
        """为一次 shell 工具执行构建受信任的 `DSH_*` 快照。执行上下文是 dict。"""
        值表={#先放内置
            主目录环境键:自身.家目录,#家目录
            外壳键:'1',#shell标记
        }#内置结束
        智能体=执行['agent'] if 'agent' in 执行 else None#调用智能体
        if 智能体 is not None:#有调用智能体
            头=智能体.session.header#会话头
            值表[会话ID键]=头['id']#写入会话id
        for 贡献方 in sorted(自身.贡献方表.values(),key=按名排序):#按名排序遍历贡献方
            名字=贡献方['name']#贡献方名
            已解析=贡献方['resolve'](执行)#解析本次值
            if 已解析 is None:#无返回
                已解析={}#空映射
            变量表=贡献方['variables']#已声明键
            for 键,值 in 已解析.items():#逐返回键
                if 键 not in 变量表:#未声明
                    raise 外壳环境错误('bash env contributor "'+str(名字)+'" returned undeclared key "'+str(键)+'"')#返回了未声明键
                if not isinstance(值,str):#值不是字符串
                    raise 外壳环境错误('bash env contributor "'+str(名字)+'" returned a non-string value for "'+str(键)+'"')#值必须是字符串
                值表[键]=值#写入快照
        return dict(sorted(值表.items(),key=按键排序项))#按键排序后返回

    def 列出(自身):#枚举插件贡献的变量
        """枚举插件贡献的变量，不执行其解析器。注意：list() 不含注册表自有的内置变量，在诊断、提示词或 UI 把它当作穷尽环境目录之前需补上。"""
        结果=[]#声明列表
        for 贡献方 in 自身.贡献方表.values():#所有贡献方
            名字=贡献方['name']#拥有者
            if 'variables' not in 贡献方:#缺变量表
                continue#跳过
            变量表=贡献方['variables']#声明的键
            for 键,变量 in 变量表.items():#展开其键
                结果.append({
                    'contributor':名字,#拥有者
                    'description':变量['description'],#描述
                    'key':键,#键
                })#一条声明
        结果.sort(key=按声明键排序)#按键名排序
        return 结果#已排序声明

def 应用(上下文,配置值=None):#加载shell-env插件
    """加载 shell-env 插件：注册环境注册表服务与无关 shell 的持久化贡献方（DSH_SESSION_JSONL）。"""
    if 配置值 is None:#未传配置
        配置值={}#空配置
    注册表=外壳环境注册表(上下文,配置值)#安装注册表
    def 解析会话持久化(执行):#按次解析会话JSONL路径
        """为一次工具执行解析会话 JSONL 路径。"""
        智能体=执行['agent'] if 'agent' in 执行 else None#调用智能体
        if 智能体 is None:#没有智能体则不提供
            return {}#空贡献
        持久化=上下文.获取服务('sessionPersistence',False)#询问持久化服务
        if 持久化 is None:#未组合持久化
            return {}#空贡献
        头=智能体.session.header#会话头
        位置=持久化.定位(头)#询问持久化位置
        if 位置['kind']=='jsonl':#仅jsonl后端才给路径
            return {会话JSONL键:位置['path']}#会话JSONL路径
        return {}#其它后端不提供
    注册表.登记({#注册会话持久化贡献
        'name':'session-persistence',#贡献方名
        'variables':{#声明的键
            会话JSONL键:{#会话JSONL路径
                'description':'Absolute target path of the current session JSONL when the active persistence backend provides one.',#模型可见描述，不翻译字面量
            },#DSH_SESSION_JSONL结束
        },#variables结束
        'resolve':解析会话持久化,#按次解析
    })#register结束

name=名称#Cordis插件名
inject=依赖#Cordis依赖声明
Config=配置#Cordis配置模式
apply=应用#Cordis插件入口
default=应用#框架槽
