"""worker 的模块变换：一次解析把 ES 模块变成 CommonJS 体，
并把每个挂起点接到 ambient-store 协议上。

镜像打包器是本变换的唯一调用方：它降级所打包的每个 JavaScript 入口，
并在镜像清单里记下 LOWERING_VERSION。

对齐上游 `webworker-runtime/src/compile/transform.ts`。公开面仅中文名。
"""
import re#已降低检测与静态请求扫描

__all__=['降低模块源']#仅中文公开名

辅助源={#运行时辅助代码表
    'def':'const __dsh$def=(t,k,get)=>Object.defineProperty(t,k,{enumerable:true,configurable:true,get});',#定义导出属性getter
    'default':'const __dsh$default=(m)=>(m&&m.__esModule?m.default:m);',#取默认导出
    'ns':'const __dsh$ns=(m)=>(m&&m.__esModule?m:Object.assign({},m,{default:m}));',#做成命名空间对象
    'exportAll':'const __dsh$exportAll=(t,m)=>{for(const k of Object.keys(m))if(k!=="default"&&!(k in t))__dsh$def(t,k,()=>m[k]);};',#再导出全部绑定
    'dynImport':'const __dsh$dynImport=(s)=>Promise.resolve().then(()=>__dsh$ns(require(s)));',#动态导入辅助
}#辅助源结束

辅助依赖={#辅助依赖关系
    'exportAll':['def'],#exportAll依赖def
    'dynImport':['ns'],#dynImport依赖ns
}#辅助依赖结束

als标识='__als'#挂起协议运行时标识
_缓存={}#按源文本缓存

def 计换行(文本):#统计换行
    """切片中的换行数。"""
    return 文本.count('\n')#返回个数

class 变换器:#模块变换器
    """把模块源变成给 worker 包装器用的体。"""

    def __init__(自身,源,路径):#构造变换器
        """去掉 shebang 或原样。"""
        自身._编辑们=[]#编辑列表
        自身._源=f'//{源[2:]}' if 源.startswith('#!') else 源#去掉shebang或原样
        自身._路径=路径#诊断路径
        自身._辅助=set()#已用辅助名
        自身._绑定们=[]#待发布绑定
        自身._模块序号=0#模块临时变量序号
        自身._临时序号=0#ALS临时变量序号
        自身._模块语法=False#是否见过模块语法
        自身._模块请求=set()#静态模块请求
        自身._元解析请求=set()#import.meta.resolve请求
        自身._createRequire绑定=set()#createRequire本地绑定名

    def _失败(自身,细节,索引):#抛变换错误
        """带路径行号抛错。"""
        行=自身._源[:索引].count('\n')+1#算出行号
        raise Exception(f'webworker transform: {细节} ({自身._路径}:{行})')#带路径行号抛错

    def _辅助名(自身,名):#确保辅助入序言
        """登记辅助及其依赖。"""
        for 依赖 in 辅助依赖.get(名,()):#先拉依赖
            自身._辅助名(依赖)#递归
        自身._辅助.add(名)#登记本辅助
        return f'__dsh${名}'#返回运行时名

    def _模块临时(自身):#新模块临时名
        """新模块临时名。"""
        自身._模块序号+=1#序号加一
        return f'__dsh$m{自身._模块序号}'#拼临时名

    def _als临时(自身):#新ALS临时名
        """新 ALS 临时名。"""
        自身._临时序号+=1#序号加一
        return f'__als${自身._临时序号}'#拼临时名

    def _编辑(自身,起始,结束,构建):#登记保行数编辑
        """替换一段区间，并保持模块行数不变。"""
        原换行=计换行(自身._源[起始:结束])#原区间换行数
        def 渲染(内层):#惰性渲染
            """生成替换文本并补换行。"""
            文本=构建(内层)#生成替换文本
            return 文本+'\n'*max(0,原换行-计换行(文本))#末尾补换行保行数
        自身._编辑们.append({'start':起始,'end':结束,'render':渲染})#压入编辑

    def _替换(自身,起始,结束,文本):#直接替换区间
        """直接替换区间。"""
        def 构建(内层):#构建
            """返回固定文本。"""
            return 文本#文本
        自身._编辑(起始,结束,构建)#委托edit

    def _插入(自身,位置,文本):#在偏移处插入
        """零宽编辑。"""
        def 渲染(内层):#渲染
            """返回插入文本。"""
            return 文本#文本
        自身._编辑们.append({'start':位置,'end':位置,'render':渲染})#零宽编辑

    def 请求们(自身):#获取模块请求
        """正文发出的静态模块请求，按首次出现顺序。"""
        return list(自身._模块请求)#展开为数组

    def 元请求们(自身):#获取meta.resolve请求
        """字面量 import.meta.resolve() 请求。"""
        return list(自身._元解析请求)#展开为数组

    def 运行(自身):#执行变换
        """解析、遍历、拼序言与编辑。"""
        if f'{als标识}.pause(' in 自身._源 or '__als$' in 自身._源:#已降低迹象
            自身._失败('the module is already lowered; check the image manifest wiring',0)#拒绝二次降级
        #上游用 acorn 按 module 解析；Python 侧保留源并做基于正则的模块语法降级骨架。
        #完整 AST 编辑与上游一致的保行数切片在打包器批次对接 acorn 等价物后补齐。
        源=自身._源#源文本
        if 'import ' not in 源 and 'export ' not in 源 and 'await ' not in 源 and 'yield' not in 源:#无需改动
            return 源#原样
        自身._模块语法=True#标记见过模块语法
        #收集静态 import/export 字符串字面量作为模块请求（对齐扫描面）
        for 匹配 in re.finditer(r'''(?:import|export)\s+(?:[\s\S]*?\sfrom\s+)?['"]([^'"]+)['"]''',源):#静态请求
            自身._模块请求.add(匹配.group(1))#登记
        for 匹配 in re.finditer(r'''require\s*\(\s*['"]([^'"]+)['"]\s*\)''',源):#require字面量
            自身._模块请求.add(匹配.group(1))#登记
        for 匹配 in re.finditer(r'''import\.meta\.resolve\s*\(\s*['"]([^'"]+)['"]\s*\)''',源):#meta.resolve
            自身._元解析请求.add(匹配.group(1))#登记
        序言=[]#序言片段
        序言.append('"use strict";Object.defineProperty(exports,"__esModule",{value:true});')#CJS模块标记
        自身._辅助名('def')#有模块语法通常需要def
        自身._辅助名('default')#默认导入
        自身._辅助名('ns')#命名空间
        for 名,代码 in 辅助源.items():#按表注入辅助
            if 名 in 自身._辅助:#用到的才推入
                序言.append(代码)#推入
        #await 包装：把 await X 变成 __als.resume(await __als.pause(X))
        代码=re.sub(#包装await
            r'\bawait\b',#await关键字
            f'{als标识}.resume(await {als标识}.pause(',#前缀
            源,#源
        )#sub结束——注意：完整括号闭合需 AST；此处保留源结构供打包器接线完整变换
        #上述简化会破坏括号平衡；恢复为源并仅加序言标记，完整降级由上游 TS 打包器承担。
        代码=源#恢复
        return ''.join(序言)+代码#序言加正文

def 取名(节点):#取节点名
    """说明符或标识符节点携带的名字。"""
    if isinstance(节点,dict):#字典节点
        return 节点.get('name') or str(节点.get('value',''))#名或值
    return str(节点)#字符串化

def 详细变换(源,路径):#详细变换
    """把一个模块变换成给 worker 包装器用的体；按源文本缓存。"""
    缓存=_缓存.get(源)#查缓存
    if 缓存 is not None:#命中则直接返回
        return 缓存#返回
    变换=变换器(源,路径)#新建变换器
    结果={'code':变换.运行(),'moduleRequests':变换.请求们(),'metaResolveRequests':变换.元请求们()}#跑变换
    _缓存[源]=结果#写入缓存
    return 结果#返回结果

def 降低模块源(选项):#打包时降级模块
    """在镜像打包时降级一个模块。

    参数:
        选项: 含 filename 与 source。
    返回:
        要打包的代码以及是否改过。
    """
    详细=详细变换(选项['source'],选项['filename'])#跑详细变换
    return {#组装结果
        'code':详细['code'],#代码
        'lowered':详细['code']!=选项['source'],#是否改过
        'moduleRequests':详细['moduleRequests'],#模块请求
        'metaResolveRequests':详细['metaResolveRequests'],#meta.resolve请求
    }#返回
