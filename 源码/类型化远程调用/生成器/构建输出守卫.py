'认出分析面里装进来的工作区构建输出，以及解析不到的工作区导入。拒绝构建输出时只读源码，结果不随包有没有编译过而变'
import json,os,re
from .异常 import Typert分析错误

__all__=[
    '找出构建输出装载','找出未解析工作区导入',
]

需要程序='typert: 分析需要 TypeScript 程序'

def 相对(起点,目标):
    '同一路径得到空串。跨盘时得到目标的绝对路径'
    if os.path.normpath(起点)==os.path.normpath(目标):
        return ''
    try:
        return os.path.relpath(目标,起点)
    except ValueError as 跨盘:#不同盘符时相对路径不存在
        return os.path.abspath(目标)

def 先存在(候选列表):
    '按顺序返回第一个存在的路径'
    for 候选 in 候选列表:
        if os.path.exists(候选):
            return 候选
    return None

def 源干(包根,相对文本):
    'lib/types 下的声明路径换成 src 下的源路径'
    换成=re.sub(r'\.d\.([cm]?)ts$',r'.\1ts',相对文本)
    return os.path.join(包根,'src',*换成.split('/'))

def 包名于(说明符):
    '说明符里的包名。作用域包占两段'
    段=说明符.split('/')
    if 说明符.startswith('@'):
        return '/'.join(段[:2])
    return 段[0]

def 取属性(值,键):
    '普通 dict 上的键。其余给 None'
    if isinstance(值,dict) and 键 in 值:
        return 值[键]
    return None

def 导出源(包根,说明符):
    '从包导出的 types 条件推出 src 下的源文件。清单读不到则不给建议路径'
    包名=包名于(说明符)
    if 说明符==包名:
        子路径='.'
    else:
        子路径='.'+说明符[len(包名):]
    try:
        文件=open(os.path.join(包根,'package.json'),'r',encoding='utf-8')
        try:
            清单=json.loads(文件.read())
        finally:
            文件.close()
    except (OSError,UnicodeError,json.JSONDecodeError) as 读不到清单:#不给建议源路径
        return None
    条目=取属性(取属性(清单,'exports'),子路径)
    if isinstance(条目,str):
        类型路径=条目
    else:
        类型路径=取属性(条目,'types')
    if not isinstance(类型路径,str) or not 类型路径.startswith('./lib/types/'):
        return None
    干=源干(包根,类型路径[len('./lib/types/'):])
    return 先存在([干,干+'x'])

def 预处理文件(文本,脚本=True,脚本扩展=True):
    '对应 typescript.preProcessFile。当前运行时没有 TypeScript 程序'
    raise Typert分析错误(需要程序)

def 解析模块名(说明符,所在文件,选项,宿主,缓存=None):
    '对应 typescript.resolveModuleName。当前运行时没有 TypeScript 程序'
    raise Typert分析错误(需要程序)

def 原样文件名(文件):
    '模块解析缓存的规范名：原样返回'
    return 文件

def 建模块解析缓存(根,规范名,选项):
    '记下建缓存时的根、规范名和编译选项。真正解析仍要 TypeScript 程序'
    return {'根':根,'规范名':规范名,'选项':选项}

def 按文件与说明符(项):
    '先比导入文件，再比说明符'
    return (项['file'],项['specifier'])

class 构建输出分类器:
    '按真实路径分类。符号链接和 Windows 长路径都收成同一条。报出来的路径仍用调用方的根的拼法'
    def __init__(自身,根):
        '记住调用方的根，并解析它的真实路径'
        自身.根=根
        自身._包根表={}
        自身._真实路径={}
        自身._真实根=自身.规范(根)

    def 规范(自身,文件):
        '绝对路径到真实路径。路径不存在时保留绝对拼法'
        绝对=os.path.abspath(文件)
        if 绝对 in 自身._真实路径:
            return 自身._真实路径[绝对]
        if os.path.lexists(绝对):
            try:
                真实=os.path.realpath(绝对)
            except OSError as 路径缺失:#解析不了就保留绝对拼法
                真实=绝对
        else:
            真实=绝对
        自身._真实路径[绝对]=真实
        return 真实

    def 展示(自身,文件):
        '落在真实根里面的路径改拼到调用方的根下。根外的路径保持绝对路径'
        路径=相对(自身._真实根,自身.规范(文件))
        if 路径.startswith('..') or os.path.isabs(路径):
            return os.path.abspath(文件)
        return os.path.join(自身.根,路径)

    def 是工作区文件(自身,文件):
        '真实路径落在工作区根里，且路径段里没有 node_modules'
        路径=相对(自身._真实根,自身.规范(文件))
        if 路径=='' or 路径.startswith('..') or os.path.isabs(路径):
            return False
        return 'node_modules' not in 路径.split(os.sep)

    def 是构建输出(自身,文件):
        '工作区包的 lib 目录下的程序文件'
        if not 自身.是工作区文件(文件):
            return False
        真实=自身.规范(文件)
        包根=自身._包根(os.path.dirname(真实))
        if 包根 is None:
            return False
        相对路径=相对(包根,真实)
        if 相对路径=='':
            return False
        return 相对路径.split(os.sep)[0]=='lib'

    def 源文件(自身,文件):
        'lib/types 下的声明对应的 src 源文件。没有则 None'
        真实=自身.规范(文件)
        包根=自身._包根(os.path.dirname(真实))
        if 包根 is None:
            return None
        部分=相对(包根,真实).split(os.sep)
        if len(部分)<3:
            return None
        库=部分[0]
        类型目录=部分[1]
        其余=部分[2:]
        末=其余[-1]
        if 库!='lib' or 类型目录!='types':
            return None
        干名=re.sub(r'\.d\.([cm]?)ts$',r'.\1ts',末)
        干=os.path.join(包根,'src',*其余[:-1],干名)
        命中=先存在([干,干+'x'])
        if 命中 is None:
            return None
        return 自身.展示(命中)

    def 链接的工作区包(自身,导入者,包名):
        '从导入文件向上找 node_modules 链接。链接目标在工作区里才返回包根'
        目录=os.path.dirname(os.path.abspath(导入者))
        while True:
            链接=os.path.join(目录,'node_modules',*包名.split('/'))
            if os.path.exists(链接):
                目标=自身.规范(链接)
                if 自身.是工作区文件(os.path.join(目标,'package.json')):
                    return 目标
                return None
            if 自身.规范(目录)==自身._真实根 or os.path.dirname(目录)==目录:
                return None
            目录=os.path.dirname(目录)

    def _包根(自身,目录):
        '向上找到最近的 package.json。到工作区真实根还没有则 None'
        if 目录 in 自身._包根表:
            return 自身._包根表[目录]
        if os.path.exists(os.path.join(目录,'package.json')):
            找到=目录
        elif 目录==自身._真实根 or os.path.dirname(目录)==目录:
            找到=None
        else:
            找到=自身._包根(os.path.dirname(目录))
        自身._包根表[目录]=找到
        return 找到

def 找出构建输出装载(程序,根,宿主):
    '列出工作区包 lib 里的程序文件，以及工作区源文件里解析到它们的导入。没有构建输出时为空。导入说明符的再次解析需要 TypeScript 程序'
    分类器=构建输出分类器(根)
    输出表={}
    for 源文件 in 程序.getSourceFiles():
        if 分类器.是构建输出(源文件.fileName):
            输出表[分类器.规范(源文件.fileName)]=[]
    if len(输出表)==0:
        return []
    选项=程序.getCompilerOptions()
    for 源文件 in 程序.getSourceFiles():
        if not 分类器.是工作区文件(源文件.fileName) or 分类器.是构建输出(源文件.fileName):
            continue
        for 项 in 预处理文件(源文件.text,True,True).importedFiles:
            说明符=项.fileName
            已解析=解析模块名(说明符,源文件.fileName,选项,宿主).resolvedModule
            if 已解析 is None:
                continue
            导入者=输出表.get(分类器.规范(已解析.resolvedFileName))
            if 导入者 is None:
                continue
            导入者.append({'file':分类器.展示(源文件.fileName),'specifier':说明符})
    结果=[]
    键列表=list(输出表.keys())
    键列表.sort()
    for 键 in 键列表:
        结果.append({
            'file':分类器.展示(键),
            'importers':输出表[键],
            'source':分类器.源文件(键),
        })
    return 结果

def 找出未解析工作区导入(程序,根,宿主):
    '列出工作区程序文件里点了工作区包、但模块解析落空的导入。认不出包则留给类型检查。子路径的源文件从导出的 lib/types 条件推'
    分类器=构建输出分类器(根)
    选项=程序.getCompilerOptions()
    缓存=建模块解析缓存(根,原样文件名,选项)
    找到=[]
    for 源文件 in 程序.getSourceFiles():
        if not 分类器.是工作区文件(源文件.fileName) or 分类器.是构建输出(源文件.fileName):
            continue
        for 项 in 预处理文件(源文件.text,True,True).importedFiles:
            说明符=项.fileName
            if 说明符.startswith('.') or os.path.isabs(说明符) or ':' in 说明符:
                continue
            if 解析模块名(说明符,源文件.fileName,选项,宿主,缓存).resolvedModule is not None:
                continue
            包根=分类器.链接的工作区包(源文件.fileName,包名于(说明符))
            if 包根 is None:
                continue
            源=导出源(包根,说明符)
            if 源 is None:
                展示源=None
            else:
                展示源=分类器.展示(源)
            找到.append({
                'file':分类器.展示(源文件.fileName),
                'specifier':说明符,
                'source':展示源,
            })
    找到.sort(key=按文件与说明符)
    return 找到
