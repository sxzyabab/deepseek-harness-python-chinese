"""VFS 镜像打包器：把一份已合成的配置档与包索引打成单个
gzip 压缩的 tar，供浏览器运行时解压并挂载为文件系统。

此处不做编译。镜像承载仓库的真实构建产物，
因此预览部署调试的正是已发布部署所交付的内容。本趟额外
做的是打包期模块变换，以及记录其变换所依据的
包装契约的清单。

本模块不含仓库知识：路径、通配与合成结果均作为
参数传入，同一库换一组调用即可打包不同树。定位这些输入
是 CLI 的职责。

对齐上游 `webworker-packer/src/pack.ts`。公开面仅中文名。
"""
import gzip,json,os,re,yaml#文件系统、压缩与YAML
from pathlib import PurePosixPath as 纯正斜杠路径#通配匹配
from ...依赖 import include#include方言
条目列表读取器=include.插件列表读取器#入口列表schema
from ..webworker_运行时 import (#从运行时导入打包所需符号
    降低模块源码,内存虚拟文件系统,打包Tar,工作线程模块加载器,#模块降级、内存VFS、打包tar、工作线程加载器
    默认根,镜像配置路径,镜像空目录,镜像清单路径,#默认根、配置路径、空目录、清单路径
    镜像叠加目录,#叠加层允许的目录
)#运行时包结束
from ..webworker_运行时.节点.外部包.已替换外部 import 已替换外部包#被替换的外部包
from ..webworker_运行时.模块代理 import 模块代理,模块代理前缀#模块代理与前缀
from .变换镜像 import 包装契约#包装契约
from .规则 import 排除,工作区排除,镜像入口种子,页面资源#排除规则、入口种子、页面资源

__all__=[#仅中文公开名
    '默认根','清单路径','配置路径',
    '打包虚拟文件系统镜像','打包虚拟文件系统叠加',
]#公开面结束

清单路径=镜像清单路径#清单在镜像中的路径
配置路径=镜像配置路径#已合成配置档在镜像中的路径
契约字段='lowered'#运行时据以判定镜像的清单字段

def 路径通配(模式们,选项=None):#对齐picomatch(patterns,{dot:true})
    """对齐 picomatch([...], {dot: true})：返回路径谓词。"""
    模式列表=[str(模式) for 模式 in 模式们]#模式列表
    def 匹配(路径):#路径是否命中任一模式
        正=路径.replace('\\','/')#正斜杠
        for 模式 in 模式列表:#逐模式
            if 纯正斜杠路径(正).full_match(模式.replace('\\','/')):return True#命中
        return False#未命中
    return 匹配#谓词

已排除=路径通配(list(排除),{'dot':True})#通用排除匹配器
工作区已排除=路径通配(list(排除)+list(工作区排除),{'dot':True})#工作区排除匹配器
是页面资源=路径通配(list(页面资源),{'dot':True})#页面资源匹配器

def 读json(文件):#读取并解析JSON
    """读取并解析 JSON 为记录。"""
    return json.loads(open(文件,'r',encoding='utf-8').read())#解析为记录

def 说明符包名(说明符):#模块说明符的包名
    """模块说明符的包名（`@scope/pkg/sub` → `@scope/pkg`）。

    对齐上游 `packageNameOf`。
    """
    段们=说明符.split('/')#按斜杠拆分
    首=段们[0] if len(段们)>0 else 说明符#首段
    次=段们[1] if len(段们)>1 else ''#次段
    return (首+'/'+次) if 首.startswith('@') else 首#作用域包取两段否则一段

def 收集模块名(行们,名称们):#从已解析入口行递归收集模块说明符
    """从已解析的入口行递归收集模块说明符 `name` 字段。

    对齐上游 `moduleNamesOf`。
    """
    if not isinstance(行们,list):return#非数组直接返回
    for 行 in 行们:#遍历每一行
        if not isinstance(行,dict) or 行 is None:continue#跳过非对象
        名=行.get('name')#取出name
        配置=行.get('config')#取出config
        if isinstance(名,str) and (名.startswith('@') or '/' in 名):#可作模块说明符
            名称们.add(说明符包名(名))#加入包名
        收集模块名(配置,名称们)#递归嵌套config

def 配置名册(配置):#合成配置档所点名的包名
    """合成配置档所点名的包名。

    对齐上游 `rosterOf`。
    """
    名称们=set()#包名集合
    收集模块名(yaml.load(配置,Loader=条目列表读取器),名称们)#解析并收集
    return list(名称们)#展开为数组

def 树名册(根):#一棵配置树下各合成所点名的包名
    """一棵配置树下各合成所点名的包名。

    对齐上游 `treeRosterOf`。
    """
    名称们=set()#包名集合
    def 遍历(目录):#递归遍历目录
        for 名字 in os.listdir(目录):#读取目录项
            绝对=os.path.join(目录,名字)#绝对路径
            if os.path.isdir(绝对):#若为目录
                遍历(绝对)#继续深入
                continue#下一目录项
            if not 名字.endswith('.yml') and not 名字.endswith('.yaml'):continue#非yaml跳过
            收集模块名(yaml.load(open(绝对,'r',encoding='utf-8').read(),Loader=条目列表读取器),名称们)#解析并收集
    遍历(根)#从根开始走
    return list(名称们)#展开为数组

def 解析依赖(起始目录,名):#按Node方式解析一个依赖
    """按 Node 方式解析一个依赖：从导入方向上游走。

    对齐上游 `resolveDependency`。
    """
    目录=起始目录#当前搜索目录
    while True:#向上循环
        候选=os.path.join(目录,'node_modules',名)#候选包路径
        if os.path.exists(os.path.join(候选,'package.json')):return os.path.realpath(候选)#找到则返回真实路径
        父=os.path.dirname(目录)#父目录
        if 父==目录:return None#已到根仍未找到
        目录=父#继续向上

def 收集树(根,目标,前缀,保留,保留目录=False):#收集一目录下的文件进镜像
    """收集一目录下的文件。

    对齐上游 `collectTree`。
    """
    def 遍历(目录):#递归遍历
        for 名字 in os.listdir(目录):#读取目录项
            绝对=os.path.join(目录,名字)#绝对路径
            if os.path.isdir(绝对):#若为目录
                if (not 保留目录) and (名字=='node_modules' or 名字.startswith('.')):continue#跳过嵌套与点目录
                遍历(绝对)#深入子目录
                continue#下一目录项
            if not os.path.isfile(绝对):continue#非文件跳过
            相对路径=os.path.relpath(绝对,根).replace('\\','/')#根相对正斜杠路径
            if not 保留(相对路径):continue#过滤器拒绝则跳过
            目标[前缀+'/'+相对路径]=open(绝对,'rb').read()#写入镜像条目
    遍历(根)#从根开始走

def 发布过滤器(模式们):#npm files白名单谓词
    """npm `files` 白名单谓词，采用标准 glob 语义。

    对齐上游 `publishedFilter`。
    """
    字符串们=[模式 for 模式 in 模式们 if isinstance(模式,str)]#仅保留字符串模式
    def 规范化(模式):#去掉./与尾斜杠
        return re.sub(r'/+$','',re.sub(r'^\./','',模式))#规范化
    def 加宽(模式):#目录名扩成整树
        return [模式,模式+'/**']#自身与子孙
    正向=[]#正向模式
    for 模式 in 字符串们:#收集正向
        if not 模式.startswith('!'):正向+=加宽(规范化(模式))#正向
    负向=[]#负向模式
    for 模式 in 字符串们:#收集负向
        if 模式.startswith('!'):负向+=加宽(规范化(模式[1:]))#负向
    承认=路径通配(正向,{'dot':True})#正向匹配器
    def 恒假(路径):#负向空时恒假
        return False#恒假
    拒绝=路径通配(负向,{'dot':True}) if len(负向)>0 else 恒假#负向匹配器或恒假
    def 谓词(路径):#对包根相对路径
        return 路径=='package.json' or (承认(路径) and not 拒绝(路径))#始终保留package.json
    return 谓词#谓词

悬空源映射=re.compile(r'\n//# sourceMappingURL=\S+\s*$')#尾部sourceMappingURL注释

def 为调试器命名(字节,名,解码,编码):#为调试器命名一个JavaScript入口
    """为调试器命名一个 JavaScript 入口：追加 sourceURL 魔法注释。

    对齐上游 `nameForDebugger`。
    """
    源码=悬空源映射.sub('\n',解码(字节))#解码并剥悬空源映射
    return 编码(源码+'\n//# sourceURL='+名)#追加sourceURL并编码

def 调试器命名器(工作区们,解析自):#构造从镜像键到入口调试器名的映射函数
    """镜像入口的调试器名。

    对齐上游 `debuggerNamer`。
    """
    仓库目录们={#包名到仓库相对目录
        名:os.path.relpath(目录,解析自).replace('\\','/') for 名,目录 in 工作区们.items()
    }#仓库目录们结束
    def 命名(键):#按镜像键取调试器名
        if not 键.startswith('node_modules/'):return 键#非node_modules原样返回
        其余=键[len('node_modules/'):]#去掉前缀
        段们=其余.split('/')#路径段
        包名=(段们[0]+'/'+段们[1]) if (len(段们)>0 and 段们[0].startswith('@') and len(段们)>1) else (段们[0] if len(段们)>0 else '')#作用域或普通包名
        目录=仓库目录们.get(包名)#仓库相对目录
        return 键 if 目录 is None else (目录+其余[len(包名):])#有目录则拼仓库路径
    return 命名#映射函数

def 扫描镜像(文件们,选项,根包们,根):#只保留工作线程可达的JavaScript并在途中变换
    """只保留工作线程可达的 JavaScript，并在途中变换。

    对齐上游 `sweepImage`。
    """
    def 解码(字节):#UTF-8解码
        return 字节.decode('utf-8')#解码
    def 编码(文本):#UTF-8编码
        return 文本.encode('utf-8')#编码
    虚拟文件系统=内存虚拟文件系统()#内存虚拟文件系统
    for 名,字节 in 文件们.items():#把候选灌入VFS
        if 名.endswith('/'):虚拟文件系统.seedDirectory(根+'/'+名)#目录种子
        else:虚拟文件系统.seed(根+'/'+名,字节)#文件种子
    def 桩():#替换模块桩
        return {}#空对象
    加载器=工作线程模块加载器({#工作线程模块加载器
        'vfs':虚拟文件系统,#虚拟文件系统
        'root':根,#虚拟根
        'staticModules':{名:桩 for 名 in 模块代理.keys()},#静态模块桩
        'staticModulePrefixes':{名:桩 for 名 in 模块代理前缀.keys()},#静态前缀桩
    })#加载器结束
    队列=[{'specifier':说明符,'from':根,'importer':'worker assembly entry'} for 说明符 in (选项['entries'] if 选项.get('entries') is not None else 镜像入口种子)]#入口种子入队
    for 名 in 根包们:#每个工作区根包的导出面
        清单字节=文件们.get('node_modules/'+名+'/package.json')#包清单字节
        if 清单字节 is None:continue#materialize已在missing下报告
        try:#尝试解析清单
            清单=json.loads(解码(清单字节))#解码并解析
        except Exception:#解析失败
            continue#跳过该包
        if 清单.get('exports') is None:#无exports则整包
            子路径们=['.']#整包
        else:#有exports
            子路径们=[键 for 键 in 清单['exports'].keys() if 键.startswith('.') and '*' not in 键]#过滤非通配面
        for 子路径 in 子路径们:#每个导出面入队
            队列.append({'specifier':名 if 子路径=='.' else (名+'/'+子路径[2:]),'from':根,'importer':'workspace face '+名})#面说明符
    已达={}#已达文件
    已见=set()#已见绝对路径
    失败们=[]#不可解析失败
    可容忍=set()#可容忍的未解析
    已访问=0#访问过的JS数
    已改写=0#已改写数
    while len(队列)>0:#BFS扫描
        条目=队列.pop(0)#取出队列项
        说明符=条目['specifier']#说明符
        来自=条目['from']#来自
        导入方=条目['importer']#导入方
        try:#尝试解析
            解析结果=加载器.resolve(说明符,来自)#按加载器算法解析
        except Exception as 原因:#解析失败
            外部=导入方.startswith('node_modules/') and not 导入方.startswith('node_modules/@deepseek-ai/')#是否第三方导入方
            if 外部 or 条目.get('meta') is True:可容忍.add(导入方+': "'+说明符+'"')#记入可容忍
            else:失败们.append(导入方+': "'+说明符+'" — '+str(原因))#记入失败
            continue#下一队列项
        种类=解析结果['kind'] if isinstance(解析结果,dict) else getattr(解析结果,'kind',None)#解析种类
        if 种类=='static':continue#静态模块无需体
        路径=解析结果['path'] if isinstance(解析结果,dict) else 解析结果.path#解析到的绝对路径
        if 路径 in 已见:continue#已见则跳过
        已见.add(路径)#标记已见
        键=路径[len(根)+1:]#镜像相对键
        字节=文件们.get(键)#候选字节
        if 字节 is None:continue#候选中无此文件
        if (not re.search(r'\.[cm]?js$',键)) or 是页面资源(键):#非JS或页面资源
            已达[键]=字节#原样保留
            continue#下一队列项
        已访问+=1#计入访问
        降级=降低模块源码({'filename':'/'+键,'source':解码(字节)})#降级变换
        if 降级['lowered']:已改写+=1#若已降级则计数
        已达[键]=编码(降级['code']) if 降级['lowered'] else 字节#写入已达
        目录=路径[:路径.rfind('/')]#导入方目录
        for 请求 in 降级['moduleRequests']:队列.append({'specifier':请求,'from':目录,'importer':键})#模块请求入队
        for 请求 in 降级['metaResolveRequests']:队列.append({'specifier':请求,'from':目录,'importer':键,'meta':True})#meta-resolve入队
    if len(失败们)>0:#存在不可解析请求
        raise Exception(#打包失败
            'vfs image: '+str(len(失败们))+' unresolvable module request(s); '#失败条数
            +'an undeclared or missing dependency fails the pack rather than the boot:\n  '#说明宁可打包失败
            +'\n  '.join(失败们),#拼接失败列表
        )#Error结束
    扫描后={}#扫描后镜像
    调试器名=调试器命名器(选项['workspaces'],选项['resolveFrom'])#调试器命名器
    脚本入口数=0#保留的JS入口数
    丢弃=0#丢弃数
    for 名,字节 in 文件们.items():#遍历全部候选
        是js=bool(re.search(r'\.[cm]?js$',名))#是否JS
        if (not 是js) or 是页面资源(名):#非JS或页面资源
            扫描后[名]=为调试器命名(字节,调试器名(名),解码,编码) if 是js else 字节#JS则命名否则原样
            if 是js:脚本入口数+=1#计入JS
            continue#下一文件
        留下=已达.get(名)#是否可达
        if 留下 is None:#不可达
            丢弃+=1#计入丢弃
            continue#下一文件
        扫描后[名]=为调试器命名(留下,调试器名(名),解码,编码)#命名后写入
        脚本入口数+=1#计入JS
    return {#返回扫描结果
        'swept':扫描后,#扫描后文件
        'transform':{'visited':已访问,'rewritten':已改写},#变换统计
        'javascriptEntries':脚本入口数,#JS入口数
        'droppedJavascriptEntries':丢弃,#丢弃JS数
        'unresolvedExternalRequests':list(可容忍),#未解析外部请求
    }#return结束

def 丢弃可执行脚本(文件们):#从镜像丢弃可执行脚本
    """从镜像丢弃可执行脚本。

    对齐上游 `dropExecutables`。
    """
    def 解码(字节):#解码器
        return 字节.decode('utf-8')#解码
    已丢=[]#已丢弃列表
    for 名 in list(文件们.keys()):#遍历条目名（可删）
        字节=文件们[名]#字节
        if not re.search(r'\.[cm]?js$',名):continue#非JS跳过
        if 解码(字节[0:2])!='#!':continue#无shebang跳过
        已丢.append(名)#记录名
        del 文件们[名]#从镜像删除
    return 已丢#返回丢弃列表

def 物化(名册,选项):#将每个名册包的依赖闭包物化进镜像
    """将每个名册包的依赖闭包物化进镜像。

    对齐上游 `materialize`。
    """
    文件们={}#镜像文件表
    包们={}#包文件计数
    缺失=[]#缺失列表
    已替换=set(已替换外部包)#已替换外部包
    队列=[{'name':名,'from':选项['resolveFrom']} for 名 in 名册]#待物化队列
    while len(队列)>0:#BFS物化
        条目=队列.pop(0)#取出队列项
        名=条目['name']#包名
        来自=条目['from']#来自
        if 名 in 包们 or 名 in 已替换:continue#已处理或已替换则跳过
        目录=选项['workspaces'].get(名)#工作区或稍后node_modules
        if 目录 is None:目录=解析依赖(来自,名)#node_modules
        if 目录 is None:#未找到
            相对=os.path.relpath(来自,选项['resolveFrom']) or '.'#相对来源
            缺失.append(名+' (from '+相对+')')#记入缺失
            continue#下一队列项
        清单=读json(os.path.join(目录,'package.json'))#读取包清单
        前缀='node_modules/'+名#镜像前缀
        之前=len(文件们)#收集前条目数
        if 名 in 选项['workspaces']:#工作区包
            发布=发布过滤器(清单['files']) if isinstance(清单.get('files'),list) else None#发布过滤器
            def 工作区保留(相对路径,发布谓词=发布):#排除且符合发布视图
                return (not 工作区已排除(相对路径)) and (发布谓词 is None or 发布谓词(相对路径))#谓词
            收集树(目录,文件们,前缀,工作区保留)#收集工作区树
        else:#外部包
            def 外部保留(相对路径):#按通用排除收集
                return not 已排除(相对路径)#谓词
            收集树(目录,文件们,前缀,外部保留)#收集外部树
        包们[名]=len(文件们)-之前#记录本包贡献数
        for 字段 in ['dependencies','peerDependencies']:#遍历依赖字段
            if 字段=='peerDependencies' and 名 not in 选项['workspaces']:continue#外部包跳过peer
            依赖表=清单.get(字段)#依赖表
            if not isinstance(依赖表,dict) or 依赖表 is None:continue#非对象跳过
            for 依赖 in 依赖表.keys():队列.append({'name':依赖,'from':目录})#依赖入队
    return {'files':文件们,'packages':包们,'missing':缺失}#返回物化结果

压缩未知操作系统=255#gzip头里未知操作系统字节
压缩操作系统偏移=9#操作系统字段偏移

def 压缩镜像(归档):#把归档压成逐字节相同的单个gzip成员
    """把归档压成同一棵树总是逐字节相同的单个 gzip 成员。

    对齐上游 `compressImage`。
    """
    压缩=bytearray(gzip.compress(归档,compresslevel=9))#最高级压缩
    压缩[压缩操作系统偏移]=压缩未知操作系统#抹平平台字节
    return bytes(压缩)#返回压缩字节

def 打包虚拟文件系统镜像(选项):#打包一份VFS镜像
    """打包一份 VFS 镜像。

    对齐上游 `packVfsImage`。
    """
    根=选项['root'] if 选项.get('root') is not None else 默认根#虚拟根
    def 编码(文本):#编码器
        return 文本.encode('utf-8')#编码
    配置树们=选项['configTrees'] if 选项.get('configTrees') is not None else []#配置树
    for 树 in 配置树们:#校验每棵配置树存在
        if not os.path.exists(树['directory']):#目录缺失
            raise Exception('vfs image: config tree '+树['mount']+' is missing at '+树['directory'])#抛错
    名册=list(dict.fromkeys(#合并去重名册（保序）
        配置名册(选项['config'])+[名 for 树 in 配置树们 if 树.get('scanRoster') is True for 名 in 树名册(树['directory'])],#主配置与扫描树
    ))#名册结束
    物化结果=物化(名册,选项)#物化闭包
    文件们=物化结果['files']#镜像文件
    包们=物化结果['packages']#包计数
    缺失=物化结果['missing']#缺失
    文件们[配置路径]=编码(选项['config'])#写入合成配置
    for 树 in 配置树们:#复制配置树
        def 配置保留(相对路径):#排除谓词
            return not 已排除(相对路径)#谓词
        收集树(树['directory'],文件们,树['mount'],配置保留)#收集
    可执行们=丢弃可执行脚本(文件们)#丢弃可执行脚本
    根包们=[名 for 名 in 包们.keys() if 名 in 选项['workspaces']]#工作区根包
    扫描=扫描镜像(文件们,选项,根包们,根)#可达性扫描
    扫描后=扫描['swept']#扫描后文件
    变换=扫描['transform']#变换统计
    扫描后[清单路径]=编码(json.dumps({#写入清单
        'root':根,#虚拟根
        'profile':选项['profile'],#配置档名
        契约字段:包装契约,#包装契约
        'javascriptEntries':扫描['javascriptEntries'],#JS入口数
        'visitedEntries':变换['visited'],#访问条目数
        'rewrittenEntries':变换['rewritten'],#改写条目数
    },indent=2,ensure_ascii=False)+'\n')#JSON格式化并编码
    for 目录 in (选项['emptyDirectories'] if 选项.get('emptyDirectories') is not None else 镜像空目录):#创建空目录
        扫描后[目录]=b''#空目录占位
    return {#返回打包结果
        'image':压缩镜像(打包Tar(扫描后)),#压缩tar镜像
        'files':扫描后,#未压缩条目
        'packages':包们,#包计数
        'workspacePackages':len([名 for 名 in 包们.keys() if 名 in 选项['workspaces']]),#工作区包数
        'roster':名册,#名册
        'missing':缺失,#缺失
        'executables':可执行们,#可执行脚本
        'pageBundles':[名 for 名 in 扫描后.keys() if 是页面资源(名)],#页面包
        'javascriptEntries':扫描['javascriptEntries'],#JS入口数
        'droppedJavascriptEntries':扫描['droppedJavascriptEntries'],#丢弃JS数
        'unresolvedExternalRequests':扫描['unresolvedExternalRequests'],#未解析外部请求
        'transform':变换,#变换结果
        'contract':包装契约,#契约
    }#return结束

def 打包虚拟文件系统叠加(树们):#把不透明数据树打成有序VFS叠加层
    """把不透明数据树打成一份有序 VFS 叠加层。

    对齐上游 `packVfsOverlay`。
    """
    文件们={}#叠加文件表
    for 树 in 树们:#遍历每棵树
        if not os.path.exists(树['directory']):#目录缺失
            raise Exception('vfs overlay: tree '+树['mount']+' is missing at '+树['directory'])#抛错
        挂载=re.sub(r'/$','',re.sub(r'^\./','',树['mount']))#规范化挂载路径
        首=挂载.split('/')[0] if 挂载!='' else None#首段目录
        段们=挂载.split('/')#全部分段
        if (挂载=='' or 首 is None or 首 not in 镜像叠加目录#挂载合法性
            or any(段=='' or 段=='.' or 段=='..' for 段 in 段们)):#禁空段与相对段
            raise Exception(#非法挂载
                'vfs overlay: mount '+json.dumps(树['mount'])+' must stay under '+' or '.join(镜像叠加目录),#错误信息
            )#Error结束
        def 全保留(相对路径):#全量收集
            return True#保留
        收集树(树['directory'],文件们,挂载,全保留,True)#全量收集并保留目录
    return {'image':压缩镜像(打包Tar(文件们)),'files':文件们}#压缩并返回
