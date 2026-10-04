__all__=(#仅中文公开名
    'Typert分析错误','类型图渲染错误','Typert代码输出错误','模型错误',
)#公开面结束

class Typert分析错误(Exception):#带源码向诊断的分析失败
    '带源码向诊断的分析失败；工作区导出校验亦复用此类型'
    name='TypertAnalysisError'#错误名

class 类型图渲染错误(Exception):#类型图渲染错误
    '渲染或遍历内部不一致的 TypeGraph 时失败'
    name='TypeGraphRenderError'#错误名

class Typert代码输出错误(Exception):#代码输出期失败
    '把已建模构造投影成制品失败'
    name='TypertEmitError'#错误名

class 模型错误(Exception):
    '未覆盖的类型图变体'
