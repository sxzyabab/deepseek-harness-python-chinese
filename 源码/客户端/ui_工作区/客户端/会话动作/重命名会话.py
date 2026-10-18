'改名菜单只提出请求。对话框在浮层里，行卸掉之后还在'
from ....模块.客户端.通告 import 取握手窗口
from ....ui_基础界面组件.按钮 import 按钮
from ....ui_基础界面组件.模态 import 模态
from .派生 import 菜单项按钮,画图标,换上
from ..文案 import 中文,取消,关闭

__all__=['重命名会话菜单项','会话重命名对话框','重命名会话菜单项组件','会话重命名对话框组件']

_表单={}#按会话记住草稿，同一次请求不重置

class 重命名会话菜单项:
    '用当前标题打开改名对话框'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#宿主属性
        自身.根=None#节点

    def 渲染(自身):
        '关掉菜单后提出改名'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        打开对=属性['useMenuOpenState']()#菜单
        def 找改名(行列):
            '改名命令的快捷键'
            for 行 in 行列:#目录
                if 行.get('id')=='session.rename':#改名
                    return 行#这条
            return None#没有
        快捷=属性['useShortcuts'](找改名)#改名快捷键
        def 点下():
            '关掉并请求'
            打开对[1](False)#关掉
            属性['requestSessionRename'](属性['sessionId'],属性.get('displayTitle') or '')#请求
        根=菜单项按钮(窗口,中文['rename'],点下,画图标(窗口,'edit-16'),快捷)#菜单项
        return 换上(自身,根)#节点

class 重命名表单:
    '一份请求的对话框。草稿从请求标题来，未改名也能提交，空标题不行'
    def __init__(自身,属性):
        '第一次用请求标题做草稿'
        自身.属性=属性#属性
        请求=属性['request']#请求
        旧=_表单.get(请求['sessionId'])#已有草稿
        if 旧 is None or 旧.get('请求') is not 请求:#新请求
            _表单[请求['sessionId']]={'请求':请求,'草稿':请求.get('currentTitle') or '','正在':False,'错误':None,'组合':False}#播种
        自身.根=None#节点

    def 态(自身):
        '这一份请求的草稿'
        return _表单[自身.属性['request']['sessionId']]#态

    def 渲染(自身):
        '画出改名对话框'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        态=自身.态()#草稿
        请求=属性['request']#请求
        剪=态['草稿'].strip()#去空白
        挡住=态['正在'] or 剪==''#不能提交
        def 关闭框():
            '正在改名时不关'
            if 态['正在']:#进行中
                return#不关
            属性['onSettle']()#结束请求
        def 确认():
            '提交剪过的标题'
            if 挡住:#不能
                return#停
            态['正在']=True#进行中
            态['错误']=None#清错误
            自身.渲染()#重画
            try:#改名
                属性['renameSession'](请求['sessionId'],剪)#改名
                态['正在']=False#结束
                属性['onSettle']()#关掉
            except Exception as 原因:#失败
                态['正在']=False#结束
                态['错误']=原因.args[0] if isinstance(原因,BaseException) and len(原因.args)>0 else str(原因)#说明
                自身.渲染()#重画
        输入=文档.createElement('input')#标题
        输入.className='renameInput'#上游类名
        输入.value=态['草稿']#草稿
        输入.setAttribute('aria-label',中文['field.sessionName'])#名称
        输入.setAttribute('data-modal-autofocus','')#自动聚焦
        输入.disabled=态['正在']#进行中不可改
        def 聚焦(事件):
            '聚焦时选中全文'
            事件.target.select()#选中
        def 输入时(事件):
            '改草稿并清掉错误'
            态['草稿']=事件.target.value#草稿
            态['错误']=None#清错误
        def 组合开始(事件):
            '输入法组合中，回车不提交'
            态['组合']=True#组合
        def 组合结束(事件):
            '组合结束'
            态['组合']=False#结束
        def 按键(事件):
            '回车提交，组合中的回车除外'
            if 事件.key=='Enter' and not 态['组合']:#提交
                事件.preventDefault()#不换行
                确认()#提交
        输入.addEventListener('focus',聚焦)#聚焦
        输入.addEventListener('input',输入时)#输入
        输入.addEventListener('compositionstart',组合开始)#组合开始
        输入.addEventListener('compositionend',组合结束)#组合结束
        输入.addEventListener('keydown',按键)#按键
        体=文档.createElement('div')#正文
        体.appendChild(输入)#输入
        if 态['错误'] is not None:#有错误
            警=文档.createElement('div')#错误
            警.className='renameError'#上游类名
            警.setAttribute('role','alert')#提示
            警.textContent=态['错误']#说明
            体.appendChild(警)#放入
        取消钮=按钮({'window':窗口,'variant':'outline','disabled':态['正在'],'onClick':关闭框,'children':取消})#取消
        确认钮=按钮({'window':窗口,'variant':'primary','disabled':挡住,'onClick':确认,'children':中文['rename']})#重命名
        框=模态({
            'window':窗口,
            'open':True,
            'onClose':关闭框,
            'closeLabel':关闭,
            'title':中文['rename.session.title'],
            'footer':[取消钮,确认钮],
            'children':体,
        })#对话框
        return 换上(自身,框.渲染())#节点

class 会话重命名对话框:
    '没有请求时不画。有请求就按会话号用一份表单'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.表单=None#表单
        自身.根=None#节点

    def 渲染(自身):
        '读请求。空则卸掉'
        属性=自身.属性#属性
        def 原样(待定):
            '请求本身'
            return 待定#原样
        请求=属性['useRenameRequest'](原样)#请求
        if 请求 is None:#没有
            自身.表单=None#卸
            return 换上(自身,None)#不画
        if 自身.表单 is None or 自身.表单.属性['request'] is not 请求:#新请求
            自身.表单=重命名表单({
                'window':属性.get('window') or 取握手窗口(),
                'request':请求,
                'renameSession':属性['renameSession'],
                'onSettle':属性['settleSessionRename'],
            })#新表单
        else:#同一请求
            自身.表单.属性['renameSession']=属性['renameSession']#更新
            自身.表单.属性['onSettle']=属性['settleSessionRename']#更新
        return 换上(自身,自身.表单.渲染())#节点

def 重命名会话菜单项组件(属性):
    '渲染器按函数调用'
    return 重命名会话菜单项(属性).渲染()#节点

def 会话重命名对话框组件(属性):
    '渲染器按函数调用。同一登记只留一份对话框'
    if not hasattr(会话重命名对话框组件,'实例'):#第一次
        会话重命名对话框组件.实例=会话重命名对话框(属性)#创建
    else:#再来
        会话重命名对话框组件.实例.属性=属性#更新
    return 会话重命名对话框组件.实例.渲染()#节点
