"""基于 worker VFS 的 CommonJS 模块加载器。它填补 Cordis 对每次入口导入使用的
`loader.internal` 接缝，并支撑 `node:module` 的 `createRequire` 代理。

对齐上游 `webworker-runtime/src/module-system/module-loader.ts`。公开面仅中文名。
"""
import json as _json#清单解析
from ..polyfill.async_context.als运行时 import 创建als运行时#ALS运行时
from .posix路径 import 目录名,文件url转路径,是否绝对,拼接,路径转文件url,解析 as 解析路径#路径工具
from ..镜像布局 import 包装参数们#包装参数列表

__all__=[#仅中文公开名
    '默认条件们','工作线程模块加载器','设活动模块加载器','要求活动模块加载器',
]#公开面结束

默认条件们=('browser','require','import','default')#exports条件顺序
扩展名们=('.js','.json','.mjs','.cjs')#探测扩展名列表
_活动=None#当前活动加载器

def 是否记录(值):#判断是否为普通对象
    """非 null 非数组对象。"""
    return isinstance(值,dict)#普通对象

class 工作线程模块加载器:#Worker模块加载器
    """单个 VFS 挂载的加载器；每个 worker 构造一次。"""

    def __init__(自身,选项):#构造加载器
        """绑定 VFS、静态表与 ALS。"""
        自身._vfs=选项['vfs']#绑定VFS
        自身._根=选项.get('root') or '/dsh'#默认虚拟根
        自身._静态模块=dict(选项['staticModules'])#静态模块转表
        前缀条目=list((选项.get('staticModulePrefixes') or {}).items())#静态前缀条目
        def 前缀长度(项):#前缀长度键
            """按前缀字符串长度排序。"""
            return len(项[0])#长度
        前缀条目.sort(key=前缀长度,reverse=True)#按前缀长度降序
        自身._静态前缀=前缀条目#前缀列表
        自身._条件=set(选项.get('conditions') or 默认条件们)#条件集合
        自身._als=创建als运行时(选项.get('alsCausality'))#创建ALS运行时
        自身._模块们={}#已加载模块缓存
        自身._清单们={}#包清单缓存
        自身._栈=[]#导入链栈
        def 内部解析(说明符,父网址=None):#内部解析闭包
            """解析为内部接缝结果。"""
            来自=自身._根 if 父网址 is None else 自身._基目录(父网址)#解析基目录
            解析结果=自身.解析(说明符,来自)#解析说明符
            if 解析结果['kind']=='static':#静态作内建
                return {'format':'builtin','url':解析结果['specifier']}#内建
            return {#文件模块解析结果
                'format':'json' if 解析结果['path'].endswith('.json') else 'commonjs',#按扩展选格式
                'url':路径转文件url(解析结果['path']),#路径转文件URL
            }#返回文件解析
        def 异步导入(说明符,父网址=None,属性=None):#异步导入实现
            """解析并加载。"""
            来自=自身._根 if 父网址 is None else 自身._基目录(父网址)#导入基目录
            return 自身.加载(自身.解析(说明符,来自))#解析并加载
        def 异步解析(说明符,父网址=None,属性=None):#异步解析转发
            """转发内部解析。"""
            return 内部解析(说明符,父网址)#转发
        自身.internal={#装配内部接缝
            'version':'worker',#接缝版本
            'import':异步导入,#异步导入
            'resolve':异步解析,#异步解析
            'resolveSync':内部解析,#同步解析
        }#internal赋值结束

    def _失败(自身,细节):#抛出带导入链的错误
        """抛出加载错误。"""
        链='' if len(自身._栈)==0 else f" (importer chain: {' -> '.join(自身._栈)})"#导入链文本
        raise Exception(f'webworker modules: {细节}{链}')#抛出加载错误

    def _基目录(自身,基):#计算基目录
        """基路径或 URL 据以解析说明符的目录。"""
        文本=基 if isinstance(基,str) else getattr(基,'href',str(基))#统一为字符串
        路径=文件url转路径(文本) if 文本.startswith('file://') else 文本#文件URL转路径
        if 路径.endswith('/'):#尾斜杠即目录
            return 解析路径(路径)#目录
        if 自身._vfs.existsSync(路径) and 自身._vfs.statSync(路径).isDirectory():#是目录
            return 解析路径(路径)#目录
        return 目录名(路径)#父目录

    def _清单(自身,目录):#读取包清单
        """读取并缓存 package.json。"""
        缓存=自身._清单们.get(目录)#查清单缓存
        if 缓存 is not None:#命中则返回
            return 缓存#返回
        路径=拼接(目录,'package.json')#清单路径
        文本=自身._vfs.readFileSync(路径,'utf8')#读取清单文本
        try:#尝试解析JSON
            解析值=_json.loads(文本)#解析package.json
        except Exception as 原因:#JSON无效
            自身._失败(f'{路径} is not valid JSON: {原因}')#报告JSON错误
        if not 是否记录(解析值):#必须为对象
            自身._失败(f'{路径} does not hold an object')#拒绝
        自身._清单们[目录]=解析值#写入缓存
        return 解析值#返回清单

    def _选择导出(自身,字段,子路径,包名):#选择exports目标
        """按条件集与请求子路径走一个 exports 值。"""
        if 字段 is None:#null不可导出
            return None#无
        if isinstance(字段,str):#字符串仅根路径
            return 字段 if 子路径=='.' else None#根或无
        if isinstance(字段,list):#数组取首个命中
            for 候选 in 字段:#遍历候选
                选中=自身._选择导出(候选,子路径,包名)#递归选择
                if 选中 is not None:#命中即返回
                    return 选中#返回
            return None#无一命中
        条目们=list(字段.items())#对象条目
        是子路径图=any(键=='.' or 键.startswith('./') for 键,_ in 条目们)#是否子路径映射
        if not 是子路径图:#条件映射而非子路径
            if 子路径!='.':#非根路径拒绝
                return None#无
            return 自身._选择条件(字段,包名)#按条件选择
        for 键,值 in 条目们:#精确子路径匹配
            if 键==子路径:#键等于子路径
                return 值 if isinstance(值,str) else 自身._选择条件(值,包名,子路径)#字符串或条件
        for 键,值 in 条目们:#通配符子路径匹配
            星=键.find('*')#星号位置
            if 星<0:#无星号跳过
                continue#下一项
            前缀=键[:星]#前缀
            后缀=键[星+1:]#后缀
            if not 子路径.startswith(前缀) or not 子路径.endswith(后缀):#前后缀不匹配
                continue#下一项
            捕获=子路径[len(前缀):len(子路径)-len(后缀) if len(后缀)>0 else None]#捕获段
            目标=值 if isinstance(值,str) else 自身._选择条件(值,包名,子路径)#目标模板
            if 目标 is not None:#命中
                return 目标.replace('*',捕获)#替换星号
        return None#未匹配

    def _选择条件(自身,字段,包名,子路径='.'):#按条件选目标
        """选取本运行时满足的第一个条件分支。"""
        if 字段 is None:#null无目标
            return None#无
        if isinstance(字段,str):#字符串即目标
            return 字段#目标
        if isinstance(字段,list):#数组取首个命中
            for 候选 in 字段:#遍历候选
                选中=自身._选择条件(候选,包名,子路径)#递归条件选择
                if 选中 is not None:#命中即返回
                    return 选中#返回
            return None#无一命中
        for 键,值 in 字段.items():#遍历条件键
            if 键 not in 自身._条件:#条件未启用
                continue#下一项
            选中=自身._选择条件(值,包名,子路径)#递归取值
            if 选中 is not None:#命中即返回
                return 选中#返回
        return None#无匹配条件

    def _探测(自身,路径,说明符):#探测实际文件
        """对具体路径做扩展名与目录探测。"""
        候选们=[路径]+[路径+扩 for 扩 in 扩展名们]#候选路径列表
        for 候选 in 候选们:#遍历候选
            if 自身._vfs.existsSync(候选) and 自身._vfs.statSync(候选).isFile():#命中文件
                return 候选#返回
        if 自身._vfs.existsSync(路径) and 自身._vfs.statSync(路径).isDirectory():#路径为目录
            if 自身._vfs.existsSync(拼接(路径,'package.json')):#目录含package.json
                主=自身._清单(路径).get('main')#读取main字段
                if 主 is not None:#有main
                    return 自身._探测(拼接(路径,主),说明符)#探测main
            return 自身._探测(拼接(路径,'index'),说明符)#回退index
        return 自身._失败(f'cannot resolve "{说明符}": no file at {", ".join(候选们)}')#探测失败

    def _静态模块(自身,说明符):#查找静态模块
        """返回静态说明符的 Worker 提供实现。"""
        精确=自身._静态模块.get(说明符)#精确匹配
        if 精确 is not None:#命中精确
            return 精确#返回
        for 前缀,工厂 in 自身._静态前缀:#前缀匹配
            if 说明符.startswith(前缀):#命中前缀
                return 工厂#返回
        return 自身._静态模块.get(f'node:{说明符}')#回退node:前缀

    def 解析(自身,说明符,来自目录):#解析说明符
        """按请求该说明符的模块方式解析说明符。"""
        静态=自身._静态模块(说明符)#查静态模块
        if 静态 is not None:#返回静态解析
            return {'kind':'static','specifier':说明符,'factory':静态}#静态
        if 说明符.startswith('cordis:') or 说明符.startswith('node:'):#未注册协议
            return 自身._失败(f'no static module is registered for "{说明符}"')#缺少静态注册
        if 说明符.startswith('file://'):#文件URL
            return {'kind':'file','path':自身._探测(文件url转路径(说明符),说明符)}#探测文件URL路径
        if 说明符.startswith('.'):#相对路径
            return {'kind':'file','path':自身._探测(拼接(来自目录,说明符),说明符)}#相对基目录探测
        if 是否绝对(说明符):#绝对路径
            return {'kind':'file','path':自身._探测(说明符,说明符)}#直接探测
        段们=说明符.split('/')#按斜杠分段
        包名='/'.join(段们[:2]) if 说明符.startswith('@') else (段们[0] if 段们 else 说明符)#作用域或包名
        剩余=说明符[len(包名):].lstrip('/')#包内剩余子路径
        包目录=拼接(自身._根,'node_modules',包名)#包目录
        if not 自身._vfs.existsSync(拼接(包目录,'package.json')):#镜像无清单
            return 自身._失败(f'cannot resolve "{说明符}": {包目录}/package.json is not in the image')#清单缺失
        清单=自身._清单(包目录)#读取包清单
        子路径='.' if 剩余=='' else f'./{剩余}'#exports子路径
        if 'exports' in 清单:#有exports字段
            目标=自身._选择导出(清单['exports'],子路径,包名)#选择导出目标
            if 目标 is None:#子路径未导出
                return 自身._失败(f'"{包名}" does not export "{子路径}" under conditions [{", ".join(自身._条件)}]')#导出失败
            return {'kind':'file','path':自身._探测(拼接(包目录,目标),说明符)}#探测导出目标
        旧式=清单.get('main') or 'index.js' if 子路径=='.' else 剩余#旧式main或子路径
        if 子路径=='.':#根
            旧式=清单.get('main') or 'index.js'#main
        else:#子路径
            旧式=剩余#剩余
        return {'kind':'file','path':自身._探测(拼接(包目录,旧式),说明符)}#探测旧式入口

    def 加载(自身,解析结果):#加载模块
        """加载已解析模块，复用缓存并以 CommonJS 部分导出语义容忍循环。"""
        if 解析结果['kind']=='static':#静态直接工厂
            return 解析结果['factory']()#工厂
        路径=解析结果['path']#文件路径
        缓存=自身._模块们.get(路径)#查模块缓存
        if 缓存 is not None:#命中返回导出
            return 缓存['module']['exports']#导出
        if 路径.endswith('.json'):#JSON模块
            解析值=_json.loads(自身._vfs.readFileSync(路径,'utf8'))#解析JSON
            自身._模块们[路径]={'module':{'exports':解析值}}#写入缓存
            return 解析值#返回解析值
        导出={}#初始导出对象
        记录={'module':{'exports':导出}}#模块记录
        自身._模块们[路径]=记录#先入缓存以支持循环
        自身._栈.append(路径)#压入导入栈
        try:#执行模块体
            源=自身._vfs.readFileSync(路径,'utf8')#读取源码
            工厂=自身._编译(源,路径)#编译为工厂
            目录=目录名(路径)#模块目录
            def 元解析(说明符):#import.meta.resolve
                """相对本目录解析。"""
                子=自身.解析(说明符,目录)#相对本目录解析
                return 子['specifier'] if 子['kind']=='static' else 路径转文件url(子['path'])#静态或文件URL
            元={'url':路径转文件url(路径),'resolve':元解析}#import.meta面
            工厂(记录['module']['exports'],自身.从目录创建require(目录),记录['module'],路径,目录,元,自身._als)#调用包装工厂
            return 记录['module']['exports']#返回最终导出
        except Exception:#加载失败
            自身._模块们.pop(路径,None)#清除坏缓存
            raise#原样抛出
        finally:#无论成败
            自身._栈.pop()#弹出导入栈

    def _编译(自身,代码,路径):#编译模块体
        """编译镜像已降级的模块体。上游用 new Function(...WRAPPER_PARAMS, code)。"""
        形参=','.join(包装参数们)#形参表
        源=f'def __dsh_factory({形参}):\n'#工厂头
        for 行 in 代码.splitlines() or ['pass']:#逐行缩进
            源+=f'    {行}\n'#缩进体
        try:#尝试编译
            环境={}#执行环境
            exec(compile(源,'<worker-module>','exec'),环境,环境)#编译工厂
            return 环境['__dsh_factory']#返回工厂
        except SyntaxError as 原因:#编译失败
            消息=str(原因)#消息
            if 'await' in 消息.lower():#顶层await
                自身._失败(f'{路径} uses top-level await, which cannot run as CommonJS in the worker: {消息}')#报告await
            if 'import' in 消息.lower() or 'export' in 消息.lower():#仍含模块语法
                自身._失败(f'{路径} still carries module syntax, so the image was not lowered by the packer ({消息}); rebuild the image')#报告未降级
            自身._失败(f'{路径} failed to compile: {消息}')#一般编译失败

    def 从目录创建require(自身,来自目录):#从目录创建require
        """构建绑定到某目录的 require。"""
        def 要求(说明符):#绑定加载
            """加载并返回导出。"""
            return 自身.加载(自身.解析(说明符,来自目录))#绑定加载
        def 解析说明符(说明符):#resolve实现
            """解析说明符为 VFS 路径。"""
            解析结果=自身.解析(说明符,来自目录)#解析说明符
            if 解析结果['kind']=='static':#静态无VFS路径
                return 自身._失败(f'"{说明符}" is a worker-provided module and has no VFS path')#拒绝静态路径
            return 解析结果['path']#返回文件路径
        def 路径们(说明符):#paths实现
            """返回搜索根。"""
            if 自身._静态模块(说明符) is not None or 说明符.startswith('node:'):#静态或node无根
                return None#无根
            if 说明符.startswith('.'):#相对用当前目录
                return [解析路径(来自目录,'.')]#当前目录
            return [拼接(自身._根,'node_modules')]#裸名用node_modules
        要求.resolve=解析说明符#挂resolve
        要求.resolve.paths=路径们#挂paths
        return 要求#装配require对象

    def 创建require(自身,基):#创建require
        """面向 VFS 的 node:module createRequire。"""
        return 自身.从目录创建require(自身._基目录(基))#按基目录绑定

    def 用量(自身):#用量统计
        """报告本加载器已做之事，供主机启动诊断。"""
        return {'modules':len(自身._模块们)}#已加载模块数

def 设活动模块加载器(加载器):#设置活动加载器
    """发布 node:module 代理所经由解析的加载器。"""
    global _活动#槽位
    _活动=加载器#发布加载器

def 要求活动模块加载器():#获取活动加载器
    """读取已发布的加载器。"""
    if _活动 is None:#尚未挂载
        raise Exception('webworker modules: no loader is mounted; the worker entry must call setActiveModuleLoader before any createRequire use')#未挂载错误
    return _活动#返回活动加载器
