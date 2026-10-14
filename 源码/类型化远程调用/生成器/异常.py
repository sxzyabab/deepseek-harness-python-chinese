__all__=(#仅中文公开名
    'Typert分析错误','类型图渲染错误','Typert代码输出错误','模型错误',
)#公开面结束

def 去掉绝对路径(文本):
    '失败说明里去掉盘符路径、根路径和家目录路径'
    留下=[]
    for 词 in str(文本).split():
        统一=词.strip('\'"').replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~/'):
            continue
        if len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/':
            continue
        留下.append(词)
    return ' '.join(留下).strip()

def _说明(消息,兜底):
    '说明去掉绝对路径；掏空则用兜底'
    干净=去掉绝对路径(消息)
    if 干净=='':
        return 兜底
    return 干净

class Typert分析错误(Exception):#带源码向诊断的分析失败
    '带源码向诊断的分析失败；工作区导出校验亦复用此类型'
    name='TypertAnalysisError'#错误名
    def __init__(自身,消息=''):
        '说明去掉绝对路径'
        super().__init__(_说明(消息,自身.name))

class 类型图渲染错误(Exception):#类型图渲染错误
    '渲染或遍历内部不一致的 TypeGraph 时失败'
    name='TypeGraphRenderError'#错误名
    def __init__(自身,消息=''):
        '说明去掉绝对路径'
        super().__init__(_说明(消息,自身.name))

class Typert代码输出错误(Exception):#代码输出期失败
    '把已建模构造投影成制品失败'
    name='TypertEmitError'#错误名
    def __init__(自身,消息=''):
        '说明去掉绝对路径'
        super().__init__(_说明(消息,自身.name))

class 模型错误(Exception):
    '未覆盖的类型图变体'
    def __init__(自身,消息=''):
        '说明去掉绝对路径'
        super().__init__(_说明(消息,'模型错误'))
