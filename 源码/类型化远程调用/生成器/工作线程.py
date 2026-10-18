'工作区生成的工作线程入口。生成请求里的每一个显式贡献者，回恰好一条消息'
import traceback
from .工作区 import 工作区Typert生成器

__all__=['运行工作线程']

def 面合法(面列表):
    '每一项都只能是 host 或 client'
    if not isinstance(面列表,list):
        return False
    for 面 in 面列表:
        if 面!='host' and 面!='client':
            return False
    return True

def 解析请求(值):
    '校验工作数据。options 必须是对象；checkDiagnostics 缺席可以，出现则必须是布尔'
    if isinstance(值,dict):
        请求=值
    else:
        请求={}
    根=请求['root'] if 'root' in 请求 else None
    有面='faces' in 请求
    面=请求['faces'] if 有面 else None
    if 'options' not in 请求 or not isinstance(请求['options'],dict):
        检查诊断缺席=False
        检查诊断=None
    elif 'checkDiagnostics' not in 请求['options']:
        检查诊断缺席=True
        检查诊断=None
    else:
        检查诊断缺席=False
        检查诊断=请求['options']['checkDiagnostics']
    面不合法=有面 and not 面合法(面)
    诊断不合法=(not 检查诊断缺席) and type(检查诊断) is not bool
    if not isinstance(根,str) or 面不合法 or 诊断不合法:
        raise TypeError('typert-generator: malformed workspace worker request')
    结果={'root':根}
    if 有面:
        结果['faces']=面
    if 检查诊断缺席:
        结果['options']={}
    else:
        结果['options']={'checkDiagnostics':检查诊断}
    return 结果

def 失败名(错误):
    '优先用错误自己的 name'
    名=getattr(错误,'name',None)
    if isinstance(名,str) and 名!='':
        return 名
    return type(错误).__name__

def 失败消息(错误):
    '取出错误说明'
    if len(错误.args)>0 and isinstance(错误.args[0],str):
        return 错误.args[0]
    return str(错误)

def 生成器选项(选项):
    '请求字段 checkDiagnostics 交给现有生成器的检查诊断'
    if 'checkDiagnostics' not in 选项:
        return {}
    return {'检查诊断':选项['checkDiagnostics']}

def 回应(工作数据):
    '生成显式贡献者，或把挡住生成的失败收成一条失败消息'
    try:
        请求=解析请求(工作数据)
        生成器=工作区Typert生成器(请求['root'],生成器选项(请求['options']))
        if 'faces' in 请求:
            制品列表=生成器.generateContributors(请求['faces'])
        else:
            制品列表=生成器.generateContributors()
        return {'kind':'artifacts','artifacts':制品列表}
    except Exception as 错误:
        失败={'kind':'failure','name':失败名(错误),'message':失败消息(错误)}
        if 错误.__traceback__ is not None:
            失败['stack']=''.join(traceback.format_exception(type(错误),错误,错误.__traceback__))
        return 失败

def 运行工作线程(父端口,工作数据):
    '必须在工作线程里跑。向父端口回恰好一条消息'
    if 父端口 is None:
        raise RuntimeError('typert-generator: the workspace worker entry must run in a Worker Thread')
    父端口.postMessage(回应(工作数据))
