"""用配置档模块解析、不启动插件地检查已声明 Config 模式。"""
import os,json,yaml
from ...依赖.loader import 组,是组插件,模块加载器
from ...依赖.include import 包含,应用插件补丁,插件列表读取器
from ...依赖.工具 import 是否表达式节点,路径转文件url,文件url转路径
from ..配置解析.解析器 import 安装配置解析
from .原生 import 是否原生配置数据架构
from .文档 import 构建配置数据架构文档

__all__=['收集配置数据架构']

内建={'group':组,'include':包含}

def 像对象(值):
    """对象或函数。"""
    return 值 is not None and (isinstance(值,dict) or callable(值) or hasattr(值,'Config'))

def 是记录(值):
    """非数组对象。"""
    return isinstance(值,dict)

def 配置于(插件):
    """读 Config 槽。"""
    return getattr(插件,'Config',None) if 像对象(插件) else None

def 解包(导出):
    """取出默认导出。"""
    if 导出 is None:
        return None
    if hasattr(导出,'default'):
        return 导出.default
    return 导出

def 校验元数据(行):
    """id/name 必须字面字符串。"""
    for 键 in ('id','name'):
        值=行.get(键)
        if 值 is not None and not isinstance(值,str):
            raise Exception(键+' must be a literal string')
    组值=行.get('group')
    if 组值 is not None and not isinstance(组值,bool):
        raise Exception('group must be a literal boolean or null')

def 校验条目(值):
    """条目必须带字面插件名。"""
    if not 是记录(值) or not isinstance(值.get('name'),str):
        raise Exception('each entry must be a mapping with a literal plugin name')
    校验元数据(值)

def 条目列表(值):
    """字面条目列表。"""
    if 值 is None:
        raise Exception('entry list config is missing')
    if not isinstance(值,list):
        raise Exception('expected a literal entry list; config expressions are not evaluated')
    return 值

def 包含补丁(值):
    """字面补丁列表。"""
    if 值 is None:
        return None
    if not isinstance(值,list):
        raise Exception('include patches must be a literal patch list; config expressions are not evaluated')
    for 补丁 in 值:
        if not 是记录(补丁) or 是否表达式节点(补丁):
            raise Exception('include patches must be literal mappings; config expressions are not evaluated')
        校验元数据(补丁)
        if 补丁.get('insert') is not None:
            条目列表(补丁['insert'])
    return 值

def 收集配置数据架构(配置档,条目,解析,诊断=None):
    """从已解析条目行与根树补丁生成 JSON Schema，不应用插件、不求值表达式。"""
    if 诊断 is None:
        诊断=[]
    结果={'entries':[],'diagnostics':list(诊断)}
    按选项={}
    拦截=安装配置解析(解析)
    try:
        加载器实例=模块加载器.从内部()
        if 加载器实例 is None:
            raise Exception('config schema dump requires the module loader used by profile resolution')
        原生载体={}
        def 载体(插件,基址):
            """识别 group/include 载体。"""
            if 插件 is 组:
                return 'group'
            if 插件 is 包含:
                return 'include'
            if not 像对象(插件) or not 是组插件(插件):
                return None
            已解析=原生载体.get(基址)
            if 已解析 is None:
                try:
                    组导出=加载器实例.import_('@deepseek-ai/cordis-plugin-group',基址,{})
                    组插件=解包(组导出)
                except Exception:
                    组插件=None
                try:
                    含导出=加载器实例.import_('@deepseek-ai/cordis-plugin-include',基址,{})
                    含插件=解包(含导出)
                except Exception:
                    含插件=None
                已解析={'group':组插件,'include':含插件}
                原生载体[基址]=已解析
            if 插件 is 已解析['group']:
                return 'group'
            if 插件 is 已解析['include']:
                return 'include'
            raise Exception('unrecognized Loader tree carrier; use cordis:group or cordis:include for native child collection')
        祖先=set()
        def 报告(路径,错误):
            """记下错误诊断，不含绝对路径。"""
            消息=错误 if isinstance(错误,str) else str(错误)
            结果['diagnostics'].append({'level':'error','path':路径,'message':消息})
        def 警告(路径):
            """带路径的警告函数。"""
            def 记(消息,*参数):
                """展开 %C。"""
                下标=[0]
                def 替(_):
                    """下一参数。"""
                    值=参数[下标[0]] if 下标[0]<len(参数) else None
                    下标[0]+=1
                    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)
                import re
                结果['diagnostics'].append({'level':'warning','path':路径,'message':re.sub(r'%C',替,消息)})
            return 记
        def 走包含(配置,基址,路径):
            """走 include 子树。"""
            if 配置 is None:
                raise Exception('include config is missing')
            if not 是记录(配置) or 是否表达式节点(配置):
                raise Exception('include config must be literal; config expressions are not evaluated')
            if not isinstance(配置.get('path'),str):
                raise Exception('include path must be literal; config expressions are not evaluated')
            文件名=文件url转路径(路径转文件url(os.path.join(文件url转路径(基址) if 基址.startswith('file:') else 基址,配置['path'])))
            扩展=os.path.splitext(文件名)[1]
            if 扩展 not in ('.json','.yaml','.yml'):
                raise Exception('include extension '+json.dumps(扩展,ensure_ascii=False)+' is not supported')
            try:
                规范=os.path.realpath(文件名)
            except OSError as 错误:
                if getattr(错误,'errno',None)!=2:
                    raise 错误
                规范=文件名
            if 规范 in 祖先:
                raise Exception('include cycle')
            内容=None
            源=None
            try:
                文件=open(文件名,'r',encoding='utf-8')
                try:
                    内容=文件.read()
                finally:
                    文件.close()
            except OSError as 错误:
                if getattr(错误,'errno',None)!=2:
                    raise 错误
                源=配置.get('initial')
                if 源 is None:
                    raise Exception('include file not found')
            if 内容 is not None:
                try:
                    源=json.loads(内容) if 扩展=='.json' else yaml.load(内容,Loader=插件列表读取器)
                except Exception as 错误:
                    位置=''
                    标记=getattr(错误,'problem_mark',None)
                    if 标记 is not None:
                        位置=' at line '+str(标记.line+1)+', column '+str(标记.column+1)
                    raise Exception('invalid '+('JSON' if 扩展=='.json' else 'YAML')+' include'+位置)
            补丁=包含补丁(配置.get('patches'))
            行表=条目列表(源)
            try:
                子=应用插件补丁(list(行表),补丁,警告(路径))
            except Exception as 错误:
                raise Exception('include patches could not be composed; child declarations are unavailable') from 错误
            祖先.add(规范)
            try:
                走(子,路径转文件url(os.path.dirname(文件名)+os.sep),路径+'/include')
            finally:
                祖先.discard(规范)
        def 走(行表,基址,前缀):
            """走条目行。"""
            for 下标,值 in enumerate(行表):
                路径=前缀+'/'+str(下标)
                身份=值 if 是记录(值) else None
                条目项={'path':路径,'status':'error'}
                if isinstance((身份 or {}).get('id'),str):
                    条目项['id']=身份['id']
                if isinstance((身份 or {}).get('name'),str):
                    条目项['name']=身份['name']
                结果['entries'].append(条目项)
                try:
                    校验条目(值)
                except Exception as 错误:
                    报告(路径,错误)
                    continue
                条目项['status']='absent'
                按选项[id(值)]=条目项
                插件=None
                try:
                    名=值['name']
                    if 名.startswith('cordis:'):
                        内建名=名[7:]
                        if 内建名 not in 内建:
                            raise Exception('unknown Cordis builtin '+json.dumps(名,ensure_ascii=False))
                        导出=内建[内建名]
                    else:
                        导出=加载器实例.import_(名,基址,{})
                    插件=解包(导出)
                    模式=配置于(插件)
                    if 模式 is not None:
                        if not 是否原生配置数据架构(模式):
                            条目项['status']='unsupported'
                            报告(路径,'Config is not a native Schemastery schema')
                        else:
                            条目项['status']='schema'
                            条目项['native']=模式
                except Exception as 错误:
                    条目项['status']='error'
                    报告(路径,错误)
                try:
                    种类=载体(插件,基址)
                    if 种类 is None:
                        continue
                    条目项['tree']=种类
                    if 值.get('config') is None and 值.get('group') is not True and (值.get('disabled') is True or 是否表达式节点(值.get('disabled'))):
                        continue
                    if 种类=='group':
                        走(条目列表(值.get('config')),基址,路径+'/config')
                    else:
                        走包含(值.get('config'),基址,路径)
                except Exception as 错误:
                    报告(路径,错误)
        走(条目,路径转文件url(os.path.join(配置档['dir'],'cordis.yml')),'')
        目标={}
        def 索引目标(行表):
            """last-id-wins 补丁目标。"""
            for 行 in 行表:
                if not 是记录(行):
                    continue
                标识=行.get('id')
                if isinstance(标识,str) and 标识:
                    条目项=按选项.get(id(行))
                    if 条目项 is not None:
                        目标[标识]=条目项
                    elif 标识 in 目标:
                        del 目标[标识]
                if 行.get('group') and isinstance(行.get('config'),list):
                    索引目标(行['config'])
        索引目标(条目)
        return 构建配置数据架构文档(配置档['name'],结果['entries'],目标,结果['diagnostics'])
    finally:
        拦截['拆除']()
