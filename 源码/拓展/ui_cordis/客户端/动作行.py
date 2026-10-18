from ....客户端.模块.客户端.通告 import 取握手窗口
import os
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块
from ....客户端.ui_基础界面组件.icons import 图标停止填充常规,描边图标,常规描边
from ....客户端.ui_基础界面组件.icons.共享画稿 import 代码括号画稿
from .卡片模型 import 动作卡片
from .准备行 import 准备行

__all__=['动作行']

样式模块='ui-cordis-run'#与运行行共用一张样式
垃圾桶路径=[#IconTrashOutlineRegular
    'M1.28149 3.88831H14.7187',
    'M5.41602 3.88833V2.47962C5.41602 2.29282 5.52492 2.11366 5.71876 1.98157C5.9126 1.84948 6.17551 1.77527 6.44964 1.77527H9.55053C9.82466 1.77527 10.0876 1.84948 10.2814 1.98157C10.4753 2.11366 10.5842 2.29282 10.5842 2.47962V3.88833',
    'M2.57349 3.88831L3.19366 13.2943C3.21937 13.5502 3.33952 13.7872 3.53065 13.9593C3.72178 14.1313 3.97016 14.2259 4.22729 14.2246H11.7728C12.0299 14.2259 12.2783 14.1313 12.4694 13.9593C12.6605 13.7872 12.7807 13.5502 12.8064 13.2943L13.4266 3.88831',
    'M6.44946 6.98926V11.1238',
    'M9.55054 6.98926V11.1238',
]

def 确保样式(文档):
    '运行行样式只插一次'
    注入模块样式文件(
        文档,
        'ui-cordis-run-style',
        os.path.join(os.path.dirname(__file__),'运行行.module.css'),
        样式模块,
    )

def 节点(文档,标签,类名):
    '带运行行样式模块的节点'
    元素=文档.createElement(标签)#元素
    if 类名:#有类
        元素.className=类名#官方类名
    标样式模块(元素,样式模块)#接上样式
    return 元素#节点

def 画垃圾桶(窗口):
    '常规描边垃圾桶。共享图标里没有这一枚'
    return 描边图标({'window':窗口,'size':14},'0 0 16 16',垃圾桶路径,14,常规描边)

def 画停止(窗口):
    '填充停止方块'
    return 图标停止填充常规({'window':窗口,'size':14})

class 动作行:
    '停止或移除调用的一行'
    def __init__(自身,属性):
        '记下属性并画出'
        自身.属性=属性#宿主交来的属性
        自身.根=None#还没画
        自身.渲染()#首画

    def 更新(自身,属性):
        '换成新属性'
        自身.属性=属性#新属性

    def 拆除(自身):
        '没有订阅'
        return

    def 渲染(自身):
        '准备中走前缀。落定后画出标题、摘要和结果'
        属性=自身.属性#当前属性
        if 'window' in 属性 and 属性['window'] is not None:#调用方窗口
            窗口=属性['window']#用它
        else:#没有单独窗口
            窗口=取握手窗口()#当前页
        文档=窗口.document#文档
        确保样式(文档)#样式
        移除=属性.get('toolName')=='cordis_undefine'#移除而不是停止
        if 移除:#移除
            标题='移除 Cordis 插件'#中文标题
            图标=画垃圾桶(窗口)#垃圾桶
        else:#停止
            标题='停止 Cordis 插件'#中文标题
            图标=画停止(窗口)#停止
        if 属性.get('phase')=='preparing':#参数还没到
            准备=准备行({
                'window':窗口,
                'toolName':属性.get('toolName'),
                'icon':图标,
                'title':标题,
                'className':'card',
                'rowClassName':'row',
                'titleClassName':'title',
                '样式模块':样式模块,
            })#前缀
            新根=准备.根#前缀根
        else:#已开始
            卡片=动作卡片(属性['block'])#卡片数据
            摘要=卡片['errorSummary']#错误优先
            if 摘要 is None:#没有错误
                摘要=卡片['pluginId'] if 卡片['pluginId'] is not None else 属性['callId']#插件或调用号
            新根=节点(文档,'div','card')#卡片
            新根.setAttribute('data-tool',属性.get('toolName') or '')#工具名
            新根.setAttribute('data-state',卡片['state'])#调用状态
            行=节点(文档,'div','row')#一行
            图标座=节点(文档,'span','icon')#图标
            图标座.appendChild(图标)#放上
            行.appendChild(图标座)#图标
            题=节点(文档,'span','title')#标题
            题.textContent=标题#中文
            行.appendChild(题)#标题
            隔=节点(文档,'span','separator')#分隔点
            隔.setAttribute('aria-hidden','true')#装饰
            行.appendChild(隔)#点
            要=节点(文档,'span','error' if 卡片['errorSummary'] is not None else 'summary')#摘要
            要.textContent=摘要#文字
            行.appendChild(要)#摘要
            检视=属性.get('inspect')#检查回调
            if 检视 is not None:#有检查
                钮=节点(文档,'button','inspect')#检查按钮
                钮.type='button'#按钮
                钮.setAttribute('aria-label','查看')#无障碍名
                钮.appendChild(代码括号画稿({'window':窗口,'size':12},常规描边))#检视图标
                def 点查看(事件):
                    '打开这一次调用的检查'
                    检视()#回调
                钮.addEventListener('click',点查看)#点击
                行.appendChild(钮)#按钮
            新根.appendChild(行)#行
            if 卡片['output'] is not None:#有结果
                预=节点(文档,'pre','output')#结果
                预.textContent=卡片['output']#原文
                新根.appendChild(预)#结果
        旧=自身.根#上一棵
        父=None#挂载点
        if 旧 is not None:#换掉
            父=旧.parentNode#记住位置
            旧.remove()#拆掉
        自身.根=新根#新根
        if 父 is None and 'parent' in 属性:#宿主指定的父节点
            父=属性['parent']#用它
        if 父 is not None and 新根 is not None and 新根.parentNode is not 父:#还没挂上
            父.appendChild(新根)#挂上
        return 新根#节点
