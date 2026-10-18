from ...ui_基础界面组件.鱼标 import 鱼标#官方鱼标
from ...ui_基础界面组件.品牌字标 import 品牌字标#官方字标

__all__=['官方品牌标志','官方品牌名称']

class 官方品牌标志:
    '按宿主面请求的边长画出官方鲸鱼标志'
    def __init__(自身,属性):
        '记下宿主交来的属性，并画出标志'
        自身.属性=属性#宿主交来的属性
        自身.根=None#尚未画出
        自身.渲染()#构造时画出

    def __call__(自身,属性=None):
        '宿主改了边长就重画这一只标志'
        if 属性 is not None:
            自身.属性=属性#换成新属性
        return 自身.渲染()#重画

    def 渲染(自身):
        '把请求的边长交给鱼标。边长缺省时由鱼标按 24 画'
        属性=自身.属性#当前属性
        窗口=属性['window']#宿主窗口
        鱼属性={'window':窗口}#交给鱼标
        if 'size' in 属性:
            鱼属性['size']=属性['size']#宿主请求的边长
        旧=自身.根#上一只
        父=None#挂载点
        if 旧 is not None:
            父=旧.parentNode#先记住位置
            旧.remove()#拆掉旧标志
        根=鱼标(鱼属性).渲染()#画出新鱼标
        自身.根=根#留下节点
        if 父 is None and 'parent' in 属性:
            父=属性['parent']#宿主指定的父节点
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)#挂上
        return 根#节点

class 官方品牌名称:
    '画出官方名称字标，不含单独成槽的那只鱼'
    def __init__(自身,属性):
        '记下宿主交来的属性，并画出名称'
        自身.属性=属性#宿主交来的属性
        自身.根=None#尚未画出
        自身.渲染()#构造时画出

    def __call__(自身,属性=None):
        '宿主再次渲染时重画名称'
        if 属性 is not None:
            自身.属性=属性#换成新属性
        return 自身.渲染()#重画

    def 渲染(自身):
        '字标不含鱼。高度缺省时由字标按 24 画'
        属性=自身.属性#当前属性
        窗口=属性['window']#宿主窗口
        字属性={'window':窗口,'includeMark':False}#不含重复的鱼
        旧=自身.根#上一只
        父=None#挂载点
        if 旧 is not None:
            父=旧.parentNode#先记住位置
            旧.remove()#拆掉旧名称
        根=品牌字标(字属性).渲染()#画出新字标
        自身.根=根#留下节点
        if 父 is None and 'parent' in 属性:
            父=属性['parent']#宿主指定的父节点
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)#挂上
        return 根#节点
