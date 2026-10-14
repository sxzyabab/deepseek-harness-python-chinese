'当前页有效时预览所选输入的电平，不把这段预览送去识别'
import math
from nicegui import ui as 界面
from ..异常 import 录制错误,失败说明

__all__=['麦克风选择器']

样式表='''
.设备行{display:flex;flex-direction:column;gap:4px;min-width:0}
.设备场{display:flex;align-items:center;gap:8px;min-width:0}
.电平{display:flex;align-items:flex-end;gap:2px;height:16px}
.电平格,.电平亮{width:3px;height:100%;border-radius:1px;background:var(--dsw-alias-border-l2)}
.电平亮{background:var(--dsw-alias-label-primary)}
.设备错误{color:var(--dsw-alias-status-error, #c24141);font-size:12px;line-height:18px}
'''
界面.add_css(样式表,shared=True)

def 读所选(属性):
    '注入面 hooks.microphoneDevice；空 id 跟随系统输入'
    钩=(属性.get('hooks') or {}).get('microphoneDevice')
    if 钩 is not None:
        值=钩.getSnapshot()
    else:
        取=属性.get('useMicrophoneDevice')
        值=None if 取 is None else 取(lambda 快照:快照)
    if not isinstance(值,dict):
        return {'id':'','label':''}
    标识=值.get('id') if isinstance(值.get('id'),str) else ''
    标签=值.get('label') if isinstance(值.get('label'),str) else ''
    return {'id':标识,'label':标签}

def 失败文(失败,翻译):
    '录制错误走 kind，其余走 failed'
    if isinstance(失败,录制错误):
        return 翻译(失败.kind)
    return 翻译('failed').format(message=失败说明(失败))

def 设备字段(项):
    '把字典或设备对象收成枚举字段'
    if isinstance(项,dict):
        return {
            'deviceId':项.get('deviceId') or '',
            'label':项.get('label') or '',
            'groupId':项.get('groupId') or '',
            'kind':项.get('kind'),
        }
    return {
        'deviceId':getattr(项,'deviceId','') or '',
        'label':getattr(项,'label','') or '',
        'groupId':getattr(项,'groupId','') or '',
        'kind':getattr(项,'kind',None),
    }

class 麦克风选择器:
    '列出输入设备并预览电平；系统默认用空 id'
    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性
        自身.设备表=[]
        自身.预览=None
        自身.错误=None
        自身.上次标识=None
        自身.选择=None
        自身.电平=None
        自身._计时=None
        自身._枚举代=0
        自身._已安排=False

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 释放预览(自身):
        '停掉当前预览；拆除失败不影响选择'
        录音=自身.预览
        自身.预览=None
        if 录音 is None or not hasattr(录音,'拆除'):
            return
        结果=录音.拆除()
        if hasattr(结果,'捕获'):
            结果.捕获(lambda 失败:None)

    def 页面隐藏(自身):
        '页面隐藏时不保持预览'
        文档=globals().get('document')
        if 文档 is None:
            return False
        return bool(getattr(文档,'hidden',False))

    def 进程里有媒体(自身):
        '采集接口在本进程里，预览才能走录制对象'
        导航=globals().get('navigator')
        return 导航 is not None and getattr(导航,'mediaDevices',None) is not None

    def 设备名(自身,设备,下标):
        '系统行、浏览器标签，或按序号的未命名设备'
        翻译=自身.属性['t']
        所选=读所选(自身.属性)
        if 设备['id']=='':
            if 设备.get('label'):
                return 翻译('systemMicrophoneNamed').format(name=设备['label'])
            return 翻译('systemMicrophone')
        标签=设备.get('label') or ''
        if not 标签 and 设备['id']==所选['id']:
            标签=所选['label']
        if 标签:
            return 标签
        if 下标>0:
            return 翻译('unnamedMicrophone').format(number=str(下标))
        return 翻译('unnamedSelectedMicrophone')

    def 可选项(自身):
        '不可用设备只保留系统行和当前选择'
        所选=读所选(自身.属性)
        结果=[]
        for 设备 in 自身.设备表:
            if not 设备.get('unavailable') or 设备['id']==所选['id'] or 设备['id']=='':
                结果.append(设备)
        return 结果

    def 应用输入(自身,输入):
        '用一次枚举结果更新可选设备；权限前的空标签不代表断开'
        所选=读所选(自身.属性)
        已知=len(输入)==0 or any(项.get('label') for 项 in 输入)
        if 所选['id']=='':
            缺失=len(输入)==0
        else:
            缺失=已知 and not any(项.get('deviceId')==所选['id'] for 项 in 输入)
        系统=None
        for 项 in 输入:
            if 项.get('deviceId')=='default':
                系统=项
                break
        活动=None
        if 所选['id']=='' and 自身.预览 is not None and hasattr(自身.预览,'设备信息'):
            活动=自身.预览.设备信息()
        组=''
        if isinstance(活动,dict) and 活动.get('groupId'):
            组=活动['groupId']
        elif 系统 is not None and 系统.get('groupId'):
            组=系统['groupId']
        物理=None
        if 组:
            for 项 in 输入:
                if 项.get('groupId')==组 and 项.get('deviceId') not in ('default','communications'):
                    物理=项
                    break
        默认标签=''
        if 物理 is not None and 物理.get('label'):
            默认标签=物理['label']
        elif isinstance(活动,dict) and 活动.get('label'):
            默认标签=活动['label']
        elif 系统 is not None and 系统.get('label'):
            默认标签=系统['label']
        选择=[{'id':'','label':默认标签,'unavailable':len(输入)==0}]
        for 项 in 输入:
            标识=项.get('deviceId') or ''
            if 标识!='' and 标识!='default':
                选择.append({'id':标识,'label':项.get('label') or ''})
        if 所选['id']!='':
            已有=any(项['id']==所选['id'] for 项 in 选择)
            if not 已有:
                已知设备=None
                位置=-1
                for 下标,项 in enumerate(自身.设备表):
                    if 项['id']==所选['id']:
                        已知设备=项
                        位置=下标
                        break
                标签='' if 已知设备 is None else (已知设备.get('label') or '')
                选择.insert(max(1,位置),{'id':所选['id'],'label':标签,'unavailable':缺失})
        自身.设备表=选择
        if 缺失:
            自身.释放预览()
            自身.错误=None
        elif not 自身.页面隐藏() and 自身.预览 is None and 自身.进程里有媒体():
            自身.取得预览()

    def 取得预览(自身):
        '打开电平预览；中断或失败后重新枚举'
        建=自身.属性.get('createRecording')
        if 建 is None:
            return
        录音=建()
        自身.预览=录音
        自身.错误=None
        def 中断(失败):
            '采集中断则拆掉预览并重新枚举'
            if 自身.预览 is not 录音:
                return
            自身.释放预览()
            自身.错误={'failure':失败}
            自身.枚举()
        try:
            结果=录音.preview(中断)
        except Exception as 失败:
            if 自身.预览 is 录音:
                自身.释放预览()
                自身.错误={'failure':失败}
            return
        def 成功(值=None):
            '预览仍是这一次才清掉错误并刷新列表'
            if 自身.预览 is not 录音:
                return
            自身.错误=None
            自身.枚举()
        def 失败(失败值):
            '预览失败则拆掉并记下错误'
            if 自身.预览 is not 录音:
                return
            自身.释放预览()
            自身.错误={'failure':失败值}
        if hasattr(结果,'然后'):
            结果.然后(成功,失败)

    def 枚举(自身):
        '同步或期约枚举音频输入；没有接口时返回假'
        导航=globals().get('navigator')
        媒体=None if 导航 is None else getattr(导航,'mediaDevices',None)
        if 媒体 is None or not hasattr(媒体,'enumerateDevices'):
            return False
        自身._枚举代+=1
        代=自身._枚举代
        try:
            全部=媒体.enumerateDevices()
        except Exception as 失败:
            自身.错误={'failure':失败}
            return True
        def 应用(值):
            '忽略过期的枚举'
            if 代!=自身._枚举代:
                return
            输入=[]
            for 项 in 值 or []:
                字段=设备字段(项)
                if 字段['kind']=='audioinput':
                    输入.append(字段)
            自身.应用输入(输入)
            自身.刷新选择()
        if hasattr(全部,'然后'):
            全部.然后(应用,lambda 失败:自身.记失败(代,失败))
            return True
        应用(全部)
        return True

    def 记失败(自身,代,失败):
        '只记下仍是这一次枚举的失败'
        if 代!=自身._枚举代:
            return
        自身.错误={'failure':失败}

    def 安排浏览器枚举(自身):
        '本进程没有媒体接口时，向页面要一次输入设备列表'
        if 自身._已安排:
            return
        自身._已安排=True
        async def 拉():
            '页面里的 enumerateDevices'
            try:
                原始=await 界面.run_javascript('''
                    const media=navigator.mediaDevices;
                    if(!media||!media.enumerateDevices) return null;
                    const inputs=await media.enumerateDevices();
                    return inputs.filter((item)=>item.kind==="audioinput").map((item)=>({
                      deviceId:item.deviceId,label:item.label,groupId:item.groupId,kind:item.kind
                    }));
                ''')
            except Exception as 失败:
                自身.错误={'failure':失败}
                return
            if 原始 is None:
                自身.错误={'failure':录制错误('unavailable')}
                return
            输入=[]
            for 项 in 原始:
                字段=设备字段(项)
                if 字段['kind']=='audioinput':
                    输入.append(字段)
            自身.应用输入(输入)
            自身.刷新选择()
        界面.timer(0.2,拉,once=True)

    def 改选(自身,事件):
        '写回空 id 的系统默认，或带标签的具体设备'
        值=事件.value if hasattr(事件,'value') else 事件
        for 设备 in 自身.可选项():
            if 设备['id']!=值 or 设备.get('unavailable'):
                continue
            标签='' if 设备['id']=='' else (设备.get('label') or '')
            自身.属性['selectMicrophone']({'id':设备['id'],'label':标签})
            return

    def 刷新选择(自身):
        '枚举回来后替换选项，不重建整行'
        if 自身.选择 is None:
            return
        翻译=自身.属性['t']
        选项={}
        for 下标,设备 in enumerate(自身.可选项()):
            文=自身.设备名(设备,下标)
            if 设备.get('unavailable'):
                文=文+' — '+翻译('deviceUnavailable')
            选项[设备['id']]=文
        自身.选择.options=选项
        自身.选择.value=读所选(自身.属性)['id']
        自身.选择.update()

    def 刷电平(自身):
        '按当前 RMS 点亮 8 格'
        if 自身.电平 is None or 自身.预览 is None or not hasattr(自身.预览,'振幅'):
            return
        分贝=20*math.log10(max(自身.预览.振幅(),0.00001))
        数量=math.ceil(max(0,min(1,(分贝+60)/60))*8)
        自身.电平.clear()
        with 自身.电平:
            for 下标 in range(8):
                界面.element('span').classes('电平亮' if 下标<数量 else '电平格')

    def 渲染(自身):
        '设备下拉；有预览且设备仍在时显示电平'
        所选=读所选(自身.属性)
        if 自身.上次标识!=所选['id']:
            自身.上次标识=所选['id']
            自身.释放预览()
            自身.错误=None
            自身.设备表=[{
                'id':所选['id'],
                'label':'' if 所选['id']=='' else 所选['label'],
            }]
        if not 自身.枚举():
            自身.安排浏览器枚举()
        翻译=自身.属性['t']
        缺失=False
        选项={}
        for 下标,设备 in enumerate(自身.可选项()):
            文=自身.设备名(设备,下标)
            if 设备.get('unavailable'):
                文=文+' — '+翻译('deviceUnavailable')
                if 设备['id']==所选['id']:
                    缺失=True
            选项[设备['id']]=文
        if not 选项:
            选项={'':自身.设备名({'id':'','label':所选['label']},0)}
        with 界面.column().classes('设备行'):
            界面.label(翻译('inputDevice'))
            with 界面.row().classes('设备场'):
                自身.选择=界面.select(选项, value=所选['id'], on_change=自身.改选).props('dense options-dense')
                if 自身.预览 is not None and not 缺失:
                    自身.电平=界面.row().classes('电平')
                    自身.电平.props(f'role=img aria-label="{翻译("inputLevel")}"')
                    自身.刷电平()
                    if 自身._计时 is None:
                        自身._计时=界面.timer(0.1,自身.刷电平)
            if 自身.错误:
                界面.label(失败文(自身.错误['failure'],翻译)).classes('设备错误')

    def __call__(自身,属性=None):
        '对齐调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
