from ...模块.客户端.通告 import 取握手窗口
from ...ui_基础界面组件.icons import 图标
from ...ui_基础界面组件.开关 import 开关
from ...ui_基础界面组件.提示泡 import 提示泡
from ...ui_对话.异常 import 挂上
from .DeepSeek模型编辑器 import 模型草稿表
from .文案 import 中文
from .编辑器页脚 import 建,清空子,采集焦点,还原焦点

__all__=['校验推理强度','模型推理强度']

初始档位=('off','low','medium','high')

def 默认值(档):
    'Off 不发送值。其余档位默认就把档位名发给接口'
    if 档=='off':
        return None
    return 档

def 接受值(档,线):
    '非空字符串可以。Off 也可以不带值'
    if isinstance(线,str):
        return len(线)>0
    return 线 is None and 档=='off'

def 读强度(模型):
    '按存下来的顺序读档位。字段不在或为 false 时没有这份声明'
    if 'reasoningEfforts' not in 模型:
        return None
    值=模型['reasoningEfforts']
    if 值 is None:
        return []
    if isinstance(值,dict) is False:
        return None
    return list(值.items())

def 校验推理强度(值):
    '手写路由的推理档位。第一行不合法就返回行号和文案键'
    序号=0
    for 模型 in 模型草稿表(值):
        条目=读强度(模型)
        if 条目 is not None:
            非法=False
            for 档,线 in 条目:
                if 接受值(档,线) is False:
                    非法=True
                    break
            if 非法:
                return {'index':序号,'key':'modelReasoningValueRequired'}
            有思考=False
            for 档,线 in 条目:
                if 档!='off':
                    有思考=True
                    break
            if 有思考 is False:
                return {'index':序号,'key':'modelReasoningNeedsLevel'}
        序号=序号+1
    return None

class 模型推理强度:
    '手写路由上一行模型的推理档位：开关，然后每个档位一行'
    def __init__(自身,属性):
        '记下模型。正在键入的原文单独留着'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.键入=None
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props。键入缓冲留着'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 写入(自身,条目):
        '换掉这一行的 reasoningEfforts，其它字段不动'
        模型=自身.属性.get('model')
        if isinstance(模型,dict) is False:
            模型={}
        下一=dict(模型)
        if 条目 is None:
            if 'reasoningEfforts' in 下一:
                del 下一['reasoningEfforts']
        else:
            下一['reasoningEfforts']=dict(条目)
        自身.属性['onChange'](下一)

    def 渲染(自身):
        '开关和档位行。显示用中文表原文'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        快照=None
        if 自身.根 is None:
            自身.根=建(文档,'div','modelReasoning')
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            快照=采集焦点(文档,自身.根)
            清空子(自身.根)
        模型=属性.get('model')
        if isinstance(模型,dict) is False:
            模型={}
        档位=属性.get('levels')
        if isinstance(档位,(list,tuple)) is False:
            档位=[]
        条目=读强度(模型)
        位置=属性.get('position')
        标签=中文['modelReasoning']+' '+str(位置)
        禁用=属性.get('disabled') is True
        自身.根.setAttribute('role','group')
        自身.根.setAttribute('aria-label',标签)
        头=建(文档,'div','modelReasoningHead')
        名=建(文档,'span','modelFieldLabel modelReasoningLabel')
        名.textContent=中文['modelReasoning']
        问=建(文档,'button','helpButton')
        问.type='button'
        问.setAttribute('aria-label',中文['modelReasoningHelp'])
        问.textContent='?'
        挂上(名,提示泡({
            'window':窗口,
            'label':中文['modelReasoningHelpText'],
            'side':'right',
            'delayMs':0,
            'focusDelayMs':0,
            'portal':True,
            'openOnClick':True,
            'children':问,
        }))
        头.appendChild(名)
        def 开关变(开):
            '打开时放上 Off 和常见三档里 schema 有的那些'
            if 开:
                初始=[]
                for 档 in 初始档位:
                    if 档 in 档位:
                        初始.append((档,默认值(档)))
                自身.写入(初始)
            else:
                自身.写入(None)
        挂上(头,开关({
            'window':窗口,
            'checked':条目 is not None,
            'label':标签,
            'disabled':禁用,
            'onChange':开关变,
        }))
        自身.根.appendChild(头)
        if 条目 is None:
            还原焦点(文档,快照)
            return 自身.根
        已用=[]
        for 档,线 in 条目:
            已用.append(档)
        if len(条目)>0:
            列头=建(文档,'div','modelReasoningRow')
            列头.setAttribute('aria-hidden','true')
            左=建(文档,'span','modelFieldLabel')
            左.textContent=中文['modelReasoningLevel']
            右=建(文档,'span','modelFieldLabel')
            右.textContent=中文['modelReasoningValue']
            列头.appendChild(左)
            列头.appendChild(右)
            自身.根.appendChild(列头)
        序号=0
        for 档,线 in 条目:
            行=建(文档,'div','modelReasoningRow')
            选=建(文档,'select','input selectInput')
            选.value=档
            选.setAttribute('aria-label',中文['modelReasoningLevel']+' '+str(序号+1))
            选.disabled=禁用
            可选=[]
            if 档 not in 档位:
                可选.append(档)
            for 候选 in 档位:
                if 候选==档 or 候选 not in 已用:
                    可选.append(候选)
            for 候选 in 可选:
                项=文档.createElement('option')
                项.value=候选
                项.textContent=候选
                选.appendChild(项)
            def 换档(事件,序号=序号,档=档,线=线,条目=list(条目)):
                '两个思考档之间的自定义拼写带着走。经过 Off 就重置'
                到=事件.target.value
                带走=isinstance(线,str) and len(线)>0 and 线!=档 and 档!='off' and 到!='off'
                新值=线 if 带走 else 默认值(到)
                下一=[]
                下标=0
                for 旧档,旧线 in 条目:
                    if 下标==序号:
                        下一.append((到,新值))
                    else:
                        下一.append((旧档,旧线))
                    下标=下标+1
                自身.写入(下一)
            选.addEventListener('change',换档)
            行.appendChild(选)
            框=建(文档,'input','input modelReasoningValueInput')
            框.type='text'
            if 自身.键入 is not None and 自身.键入.get('level')==档:
                框.value=自身.键入.get('text')
            elif isinstance(线,str):
                框.value=线
            else:
                框.value=''
            框.placeholder=中文['modelReasoningOffValuePlaceholder'] if 档=='off' else 档
            框.setAttribute('aria-label',档+' '+中文['modelReasoningValue'])
            if 接受值(档,线) is False:
                框.setAttribute('aria-invalid','true')
            框.disabled=禁用 or 档=='off'
            框.setAttribute('data-dsh-focus','reasoning-'+str(位置)+'-'+str(序号))
            def 改值(事件,序号=序号,档=档,条目=list(条目)):
                '键入时留住原文。空的存成这一档的默认值'
                文=事件.target.value
                自身.键入={'level':档,'text':文}
                修剪=文.strip()
                存=默认值(档) if len(修剪)==0 else 修剪
                下一=[]
                下标=0
                for 旧档,旧线 in 条目:
                    if 下标==序号:
                        下一.append((档,存))
                    else:
                        下一.append((旧档,旧线))
                    下标=下标+1
                自身.写入(下一)
            def 离开(事件,序号=序号,档=档,线=线,条目=list(条目)):
                '离开时适配器不接受的值改回档位名'
                自身.键入=None
                if 接受值(档,线) is False:
                    下一=[]
                    下标=0
                    for 旧档,旧线 in 条目:
                        if 下标==序号:
                            下一.append((档,默认值(档)))
                        else:
                            下一.append((旧档,旧线))
                        下标=下标+1
                    自身.写入(下一)
            框.addEventListener('input',改值)
            框.addEventListener('blur',离开)
            行.appendChild(框)
            删=建(文档,'button','iconButton iconButtonDanger')
            删.type='button'
            删.setAttribute('aria-label',中文['modelReasoningRemove']+' '+档)
            删.title=中文['modelReasoningRemove']
            删.disabled=禁用
            挂上(删,图标('trash-16',{'window':窗口,'size':14}))
            def 删行(事件,序号=序号,条目=list(条目)):
                '去掉这一档'
                下一=[]
                下标=0
                for 项 in 条目:
                    if 下标!=序号:
                        下一.append(项)
                    下标=下标+1
                自身.写入(下一)
            删.addEventListener('click',删行)
            行.appendChild(删)
            自身.根.appendChild(行)
            序号=序号+1
        拒绝=False
        for 档,线 in 条目:
            if 接受值(档,线) is False:
                拒绝=True
                break
        缺档=True
        for 档 in 已用:
            if 档!='off':
                缺档=False
                break
        if 拒绝:
            错=建(文档,'p','error')
            错.textContent=中文['modelReasoningValueRequired']
            自身.根.appendChild(错)
        elif 缺档:
            错=建(文档,'p','error')
            错.textContent=中文['modelReasoningNeedsLevel']
            自身.根.appendChild(错)
        加=建(文档,'button','addModelButton')
        加.type='button'
        满了=True
        for 档 in 档位:
            if 档 not in 已用:
                满了=False
                break
        加.disabled=禁用 or 满了
        挂上(加,图标('plus-16',{'window':窗口,'size':14}))
        加.appendChild(文档.createTextNode(中文['modelReasoningAdd']))
        def 加档(事件,条目=list(条目),已用=list(已用)):
            '优先加上比现有更高的下一档'
            最高=-1
            for 档 in 已用:
                下标=档位.index(档) if 档 in 档位 else -1
                if 下标>最高:
                    最高=下标
            选中=None
            下标=0
            for 候选 in 档位:
                if 下标>最高 and 候选 not in 已用:
                    选中=候选
                    break
                下标=下标+1
            if 选中 is None:
                for 候选 in 档位:
                    if 候选 not in 已用:
                        选中=候选
                        break
            if 选中 is None:
                return
            下一=list(条目)
            下一.append((选中,默认值(选中)))
            自身.写入(下一)
        加.addEventListener('click',加档)
        自身.根.appendChild(加)
        还原焦点(文档,快照)
        return 自身.根
