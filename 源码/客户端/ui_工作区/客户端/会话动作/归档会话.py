'归档菜单、行尾按钮，以及停止并归档的确认框'
from ....模块.客户端.通告 import 取握手窗口
from ....ui_基础界面组件.按钮 import 按钮
from ....ui_基础界面组件.模态 import 模态
from ....ui_基础界面组件.提示泡 import 提示泡
from .派生 import 菜单项按钮,画图标,换上
from ..文案 import 中文,填入,取消,关闭

__all__=['归档会话菜单项','归档会话行按钮','会话归档确认对话框','归档会话菜单项组件','归档会话行按钮组件','会话归档确认对话框组件']

_表单={}#按会话记住进行中和错误

def 活动行(条目):
    '一行工作：条数和名称。不认识的种类走其它'
    项目=条目.get('items') or []#项
    个数=len(项目)#条数
    名称=中文['archive.confirm.listSeparator'].join([项.get('label') or 项.get('id') or '' for 项 in 项目])#名称
    数='one' if 个数==1 else 'other'#单复数键，中文两句相同
    种类=条目.get('kind')#种类
    if 种类=='turn':#回合
        return 中文['archive.confirm.turn']#进行中的回合
    if 种类=='subagent':#子智能体
        键='archive.confirm.subagents.'+数#键
        return 填入(中文[键],{'n':个数,'names':名称})#句子
    if 种类=='job':#后台任务
        键='archive.confirm.jobs.'+数#键
        return 填入(中文[键],{'n':个数,'names':名称})#句子
    if 种类=='schedule':#定时
        键='archive.confirm.schedules.'+数#键
        return 填入(中文[键],{'n':个数,'names':名称})#句子
    键='archive.confirm.other.'+数#其它
    return 填入(中文[键],{'kind':种类,'n':个数})#句子

class 归档会话菜单项:
    '归档，或把已归档的行恢复'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.根=None#节点

    def 渲染(自身):
        '已归档不带归档快捷键'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        会话号=属性['sessionId']#会话
        def 是否归档(集):
            '是否已归档'
            return 会话号 in 集#成员
        归档=属性['useArchived'](是否归档)#归档
        打开对=属性['useMenuOpenState']()#菜单
        def 找归档(行列):
            '归档命令的快捷键'
            for 行 in 行列:#目录
                if 行.get('id')=='session.archive':#归档
                    return 行#这条
            return None#没有
        快捷=None if 归档 else 属性['useShortcuts'](找归档)#未归档才带快捷键
        def 点下():
            '关掉菜单再归档或恢复'
            打开对[1](False)#关掉
            if 归档:#已归档
                属性['unarchiveSession'](会话号)#恢复
            else:#未归档
                属性['archiveSession'](会话号)#归档
        名='unarchive-16' if 归档 else 'archive-16'#图标
        文=中文['menu.unarchiveSession'] if 归档 else 中文['menu.archiveSession']#文案
        根=菜单项按钮(窗口,文,点下,画图标(窗口,名,14),快捷)#菜单项
        return 换上(自身,根)#节点

class 归档会话行按钮:
    '行尾的归档或恢复按钮'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.根=None#节点

    def 渲染(自身):
        '提示泡里放图标按钮'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        会话号=属性['sessionId']#会话
        def 是否归档(集):
            '是否已归档'
            return 会话号 in 集#成员
        归档=属性['useArchived'](是否归档)#归档
        钮=文档.createElement('button')#按钮
        钮.type='button'#按钮
        钮.className='iconButton'#上游类名
        钮.setAttribute('aria-label',中文['menu.unarchiveSession'] if 归档 else 中文['menu.archiveSession'])#无障碍
        def 点击(事件):
            '归档或恢复'
            if 归档:#已归档
                属性['unarchiveSession'](会话号)#恢复
            else:#未归档
                属性['archiveSession'](会话号)#归档
        钮.addEventListener('click',点击)#点击
        图=画图标(窗口,'unarchive-16' if 归档 else 'archive-16',14)#图标
        if 图 is not None:#有
            钮.appendChild(图)#放入
        泡=提示泡({
            'window':窗口,
            'label':中文['actions.unarchive'] if 归档 else 中文['actions.archive'],
            'side':'bottom',
            'align':'end',
            'delayMs':500,
            'portal':True,
            'children':钮,
        })#提示
        return 换上(自身,泡.渲染())#节点

class 归档确认表单:
    '一份确认。进行中和错误跟着这次请求'
    def __init__(自身,属性):
        '新请求清掉进行中和错误'
        自身.属性=属性#属性
        请求=属性['request']#请求
        旧=_表单.get(请求['sessionId'])#旧态
        if 旧 is None or 旧.get('请求') is not 请求:#新的
            _表单[请求['sessionId']]={'请求':请求,'正在':False,'错误':None}#清空
        自身.根=None#节点

    def 态(自身):
        '这一份的进行中和错误'
        return _表单[自身.属性['request']['sessionId']]#态

    def 渲染(自身):
        '列出将被停止的工作'
        属性=自身.属性#属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
        文档=窗口.document#文档
        请求=属性['request']#请求
        态=自身.态()#态
        def 关闭框():
            '正在停止时不关'
            if 态['正在']:#进行中
                return#不关
            属性['onSettle']()#结束
        def 确认():
            '先停再归档'
            态['正在']=True#进行中
            态['错误']=None#清错误
            自身.渲染()#重画
            try:#停止并归档
                属性['stopAndArchiveSession'](请求['sessionId'])#执行
                态['正在']=False#结束
                属性['onSettle']()#关掉
            except Exception as 原因:#失败
                态['正在']=False#结束
                态['错误']=原因.args[0] if isinstance(原因,BaseException) and len(原因.args)>0 else str(原因)#说明
                自身.渲染()#重画
        清单=文档.createElement('ul')#工作列表
        清单.className='archiveActivity'#上游类名
        清单.setAttribute('aria-label',中文['archive.confirm.activity'])#将被停止的工作
        序号=0#下标
        for 条目 in 请求.get('activity') or []:#逐项
            项=文档.createElement('li')#一行
            项.textContent=活动行(条目)#句子
            清单.appendChild(项)#放入
            序号=序号+1#下一条
        体=文档.createElement('div')#正文
        体.appendChild(清单)#列表
        if 态['正在']:#进行中
            状=文档.createElement('div')#状态
            状.className='deleteStatus'#上游类名
            状.setAttribute('role','status')#状态
            状.textContent=中文['archive.confirm.pending']#正在停止并归档
            体.appendChild(状)#放入
        if 态['错误'] is not None:#失败
            警=文档.createElement('div')#错误
            警.className='renameError'#上游类名
            警.setAttribute('role','alert')#提示
            警.textContent=态['错误']#说明
            体.appendChild(警)#放入
        取消钮=按钮({'window':窗口,'variant':'outline','disabled':态['正在'],'onClick':关闭框,'children':取消})#取消
        确认钮=按钮({
            'window':窗口,
            'variant':'outline',
            'className':'deleteAction',
            'disabled':态['正在'],
            'onClick':确认,
            'children':中文['archive.confirm.action'],
        })#停止并归档
        框=模态({
            'window':窗口,
            'open':True,
            'onClose':关闭框,
            'closeLabel':关闭,
            'title':中文['archive.confirm.title'],
            'description':填入(中文['archive.confirm.desc'],{'title':请求.get('displayTitle') or ''}),
            'footer':[取消钮,确认钮],
            'children':体,
        })#对话框
        return 换上(自身,框.渲染())#节点

class 会话归档确认对话框:
    '没有待确认时不画'
    def __init__(自身,属性):
        '记下属性'
        自身.属性=属性#属性
        自身.表单=None#表单
        自身.根=None#节点

    def 渲染(自身):
        '按会话号换一份表单'
        属性=自身.属性#属性
        def 原样(待定):
            '请求本身'
            return 待定#原样
        请求=属性['useArchiveRequest'](原样)#请求
        if 请求 is None:#没有
            自身.表单=None#卸
            return 换上(自身,None)#不画
        if 自身.表单 is None or 自身.表单.属性['request'] is not 请求:#新请求
            自身.表单=归档确认表单({
                'window':属性.get('window') or 取握手窗口(),
                'request':请求,
                'stopAndArchiveSession':属性['stopAndArchiveSession'],
                'onSettle':属性['settleSessionArchive'],
            })#表单
        else:#同一请求
            自身.表单.属性['stopAndArchiveSession']=属性['stopAndArchiveSession']#更新
            自身.表单.属性['onSettle']=属性['settleSessionArchive']#更新
        return 换上(自身,自身.表单.渲染())#节点

def 归档会话菜单项组件(属性):
    '渲染器按函数调用'
    return 归档会话菜单项(属性).渲染()#节点

def 归档会话行按钮组件(属性):
    '渲染器按函数调用'
    return 归档会话行按钮(属性).渲染()#节点

def 会话归档确认对话框组件(属性):
    '同一登记只留一份确认框'
    if not hasattr(会话归档确认对话框组件,'实例'):#第一次
        会话归档确认对话框组件.实例=会话归档确认对话框(属性)#创建
    else:#再来
        会话归档确认对话框组件.实例.属性=属性#更新
    return 会话归档确认对话框组件.实例.渲染()#节点
