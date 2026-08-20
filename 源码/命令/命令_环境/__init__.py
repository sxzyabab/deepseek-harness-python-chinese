"""与工具无关的 shell 环境插件：拥有 `ctx.shellEnv` 注册表，存放面向模型的 shell 工具（`dsh-tool-bash`、`dsh-tool-pwsh`）消费的受信任、按次执行 `DSH_*` 变量。

对齐上游 `@deepseek-ai/dsh-shell-env`。公开面仅中文名；Cordis 槽 `name`/`inject`/`Config`/`apply`/`default` 为协议兼容，不入 `__all__`。
内置 shell 事实由注册表自身拥有，插件可以注册额外的、可枚举事实，并随 effect 拆除。
"""
import re#环境键后缀校验
from cordis import 服务#Cordis服务基类
from schemastery import 模式#配置校验库
from shell import 托管环境前缀#DSH_前缀
from home_paths import 解析主目录,主目录环境键#解析harness主目录与DSH_HOME键

__all__=(
    '名称','注入','配置',
    '主目录环境键','外壳键','会话ID键','会话JSONL键','保留环境键',
    '外壳环境注册表','应用','默认',
)#仅中文公开名；Cordis 槽另见模块尾

名称='shell-env'#插件名
注入=[]#无硬依赖
name=名称#Cordis插件名（协议槽）
inject=注入#Cordis依赖声明（协议槽）
配置=模式.对象({#插件配置模式
    'dshHome':模式.字符串(),#作为DSH_HOME暴露的家目录；默认$DSH_HOME或~/.dsh
})#配置模式结束
Config=配置#Cordis配置模式（协议槽）
外壳键=托管环境前缀+'SHELL'#DSH_SHELL键
会话ID键=托管环境前缀+'SESSION_ID'#DSH_SESSION_ID键
会话JSONL键=托管环境前缀+'SESSION_JSONL'#DSH_SESSION_JSONL键
保留环境键=set((主目录环境键,外壳键,会话ID键))#注册表自留键
环境键后缀模式=re.compile(r'^[A-Z][A-Z0-9_]*$')#前缀之后的合法后缀

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 有自有(对象,键):#对齐Object.hasOwn
    """对齐 Object.hasOwn。"""
    if 对象 is None:#空对象
        return False#没有
    if isinstance(对象,dict):#映射
        return 键 in 对象#映射键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:#没有字典
        return False#没有
    return 键 in 字典#自有

class 外壳环境注册表(服务):#受信任按次执行DSH_*变量的注册表
    """受信任、按次执行 `DSH_*` 变量的注册表（`ctx.shellEnv`）。命名空间为每次模型 shell 调用重建：执行器丢掉环境中的 `DSH_*` 值，然后注入注册表的当前快照。内置 shell 事实仍由注册表自身拥有，插件可以注册额外的、可枚举事实，并随 effect 拆除。"""
    def __init__(自身,上下文对象,配置值=None):#安装shellEnv服务
        """创建并安装 `ctx.shellEnv` 服务。"""
        super().__init__(上下文对象,'shellEnv')#服务名shellEnv
        if 配置值 is None:#未传配置
            配置值={}#空配置
        自身.贡献方们={}#贡献方名到贡献方
        自身.键拥有者={}#键到拥有贡献方
        自身.家目录=解析主目录(取字段(配置值,'dshHome'))#解析家目录

    def 登记(自身,贡献方):#注册一个环境贡献方
        """注册一个环境贡献方。名与键唯一；内置键保留。注册随调用插件 fiber 拆除。"""
        def 挂上():#随fiber拆除
            """挂上贡献并在拆除时摘掉。"""
            名字=取字段(贡献方,'name')#贡献方名
            if 名字 is None or len(str(名字).strip())==0:#名为空
                raise Exception('bash env contributor name must be non-empty')#名必须非空
            if 名字 in 自身.贡献方们:#名已占用
                raise Exception('bash env contributor "'+str(名字)+'" is already registered')#贡献方重复
            变量表=取字段(贡献方,'variables')#声明的键
            if 变量表 is None:#缺变量表
                变量表={}#空表
            if isinstance(变量表,dict):#映射
                键项们=list(变量表.items())#键列表
            else:#对象则读属性字典
                键项们=list(getattr(变量表,'__dict__',{}).items())#属性项
            for 键,变量 in 键项们:#逐键校验
                if (not str(键).startswith(托管环境前缀)) or (环境键后缀模式.fullmatch(str(键)[len(托管环境前缀):]) is None):#键非法
                    raise Exception('bash env contributor "'+str(名字)+'" declared invalid key "'+str(键)+'"')#键非法
                if 键 in 保留环境键:#占用保留键
                    raise Exception('bash env contributor "'+str(名字)+'" cannot own reserved key "'+str(键)+'"')#不能拥有保留键
                描述=取字段(变量,'description')#描述
                if 描述 is None or len(str(描述).strip())==0:#描述为空
                    raise Exception('bash env contributor "'+str(名字)+'" must describe "'+str(键)+'"')#必须描述该键
                拥有者=自身.键拥有者.get(键)#现有拥有者
                if 拥有者 is not None:#键已被占
                    raise Exception('bash env key "'+str(键)+'" is already owned by contributor "'+str(拥有者)+'"; contributor "'+str(名字)+'" cannot also own it')#键冲突
            自身.贡献方们[名字]=贡献方#记下贡献方
            for 键,_变量 in 键项们:#记下键所有权
                自身.键拥有者[键]=名字#键到贡献方
            def 摘掉():#拆除
                """拆除该贡献。"""
                自身.贡献方们.pop(名字,None)#去掉贡献方
                for 键,_变量 in 键项们:#释放键
                    自身.键拥有者.pop(键,None)#释放键所有权
            return 摘掉#拆除器
        return 自身.ctx.effect(挂上,'bashEnv.register()')#绑到本注册表并返回拆除句柄

    def 收集(自身,执行):#为一次shell工具执行构建受信任快照
        """为一次 shell 工具执行构建受信任的 `DSH_*` 快照。"""
        值表={#先放内置
            主目录环境键:自身.家目录,#家目录
            外壳键:'1',#shell标记
        }#内置结束
        智能体=取字段(执行,'agent')#调用智能体
        if 智能体 is not None:#有调用智能体
            会话=取字段(智能体,'session')#所属会话
            头=取字段(会话,'header')#会话头
            值表[会话ID键]=取字段(头,'id')#写入会话id
        for 贡献方 in sorted(自身.贡献方们.values(),key=lambda 项:取字段(项,'name')):#按名排序遍历贡献方
            名字=取字段(贡献方,'name')#贡献方名
            解析器=取字段(贡献方,'resolve')#按次解析器
            已解析=解析器(执行)#解析本次值
            if 已解析 is None:#无返回
                已解析={}#空映射
            变量表=取字段(贡献方,'variables')#已声明键
            if isinstance(已解析,dict):#映射
                返回项们=list(已解析.items())#返回项
            else:#对象
                返回项们=list(getattr(已解析,'__dict__',{}).items())#属性项
            for 键,值 in 返回项们:#逐返回键
                if not 有自有(变量表,键):#未声明
                    raise Exception('bash env contributor "'+str(名字)+'" returned undeclared key "'+str(键)+'"')#返回了未声明键
                if not isinstance(值,str):#值不是字符串
                    raise Exception('bash env contributor "'+str(名字)+'" returned a non-string value for "'+str(键)+'"')#值必须是字符串
                值表[键]=值#写入快照
        return dict(sorted(值表.items(),key=lambda 项:项[0]))#按键排序后返回

    def 列出(自身):#枚举插件贡献的变量
        """枚举插件贡献的变量，不执行其解析器。TODO(bash-env-list-builtins): 在诊断、提示词或UI把list()当作穷尽环境目录之前，把注册表自有内置也列进去。"""
        结果=[]#声明列表
        for 贡献方 in 自身.贡献方们.values():#所有贡献方
            名字=取字段(贡献方,'name')#拥有者
            变量表=取字段(贡献方,'variables')#声明的键
            if 变量表 is None:#缺变量表
                continue#跳过
            if isinstance(变量表,dict):#映射
                键项们=list(变量表.items())#键列表
            else:#对象
                键项们=list(getattr(变量表,'__dict__',{}).items())#属性项
            for 键,变量 in 键项们:#展开其键
                结果.append({
                    'contributor':名字,#拥有者
                    'description':取字段(变量,'description'),#描述
                    'key':键,#键
                })#一条声明
        结果.sort(key=lambda 项:取字段(项,'key'))#按键名排序
        return 结果#已排序声明

def 应用(上下文对象,配置值=None):#加载shell-env插件
    """加载 shell-env 插件：注册 `ctx.shellEnv` 服务与无关 shell 的持久化贡献方（`DSH_SESSION_JSONL`）。"""
    if 配置值 is None:#未传配置
        配置值={}#空配置
    注册表=外壳环境注册表(上下文对象,配置值)#安装注册表
    def 解析会话持久化(执行):#按次解析会话JSONL路径
        """为一次工具执行解析会话 JSONL 路径。"""
        智能体=取字段(执行,'agent')#调用智能体
        if 智能体 is None:#没有智能体则不提供
            return {}#空贡献
        持久化=上下文对象.get('sessionPersistence')#询问持久化服务
        if 持久化 is None:#未组合持久化
            return {}#空贡献
        头=取字段(取字段(智能体,'session'),'header')#会话头
        位置=持久化.定位(头)#询问持久化位置
        if 取字段(位置,'kind')=='jsonl':#仅jsonl后端才给路径
            return {会话JSONL键:取字段(位置,'path')}#会话JSONL路径
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

默认=应用#中文默认导出
apply=应用#Cordis插件入口（协议槽）
default=应用#Cordis默认导出（协议槽）
