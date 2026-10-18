from ...模块.客户端.通告 import 取握手窗口
import re
from ...ui_基础界面组件.icons import 图标
from ...ui_对话.异常 import 挂上
from .文案 import 中文
from .模型表行 import 模型表行
from .编辑器页脚 import 建,清空子

__all__=['解析容量','格式化容量','模型草稿表','校验DeepSeek模型','DeepSeek模型编辑器']

容量模式=re.compile(r'^(\d+(?:\.\d+)?)([km])?$',re.IGNORECASE)
容量尺度={'k':1000,'m':1000000}
行号模式=re.compile(r'^\d+')

def 解析容量(文本):
    '空着表示继承。读不出的容量是 NaN，留给保存时点名这一行'
    修剪=文本.strip()
    if len(修剪)==0:
        return None
    匹配=容量模式.match(修剪)
    if 匹配 is None:
        return float('nan')
    后缀=匹配.group(2)
    尺度=1
    if isinstance(后缀,str) and 后缀.lower() in 容量尺度:
        尺度=容量尺度[后缀.lower()]
    缩放=float(匹配.group(1))*尺度
    if 缩放>=0:
        圆整=int(缩放+0.5)
    else:
        圆整=int(缩放-0.5)
    if abs(缩放-圆整)<1e-6:
        return 圆整
    return 缩放

def 格式化容量(值):
    '能整除 M 或 K 就用后缀。不是正整数就原样'
    if isinstance(值,bool):
        return str(值)
    整数=None
    if isinstance(值,int):
        整数=值
    elif isinstance(值,float) and 值==值 and 值==int(值):
        整数=int(值)
    if 整数 is None or 整数<=0:
        return str(值)
    if 整数%容量尺度['m']==0:
        return str(整数//容量尺度['m'])+'M'
    if 整数%容量尺度['k']==0:
        return str(整数//容量尺度['k'])+'K'
    return str(整数)

def 模型草稿表(值):
    '目录值收成对象行。不是对象的项变成空对象，隐藏字段留着'
    if isinstance(值,list) is False:
        return []
    结果=[]
    for 项 in 值:
        if isinstance(项,dict):
            结果.append(项)
        else:
            结果.append({})
    return 结果

def 校验DeepSeek模型(值):
    '适配器额外的约束。继承态没有值就算通过'
    if 值 is None:
        return None
    模型表=模型草稿表(值)
    见过=set()
    序号=0
    for 模型 in 模型表:
        标识=模型.get('id')
        修剪=标识.strip() if isinstance(标识,str) else None
        if 修剪 is None or len(修剪)==0:
            return {'index':序号,'key':'modelIdRequired'}
        if 修剪 in 见过:
            return {'index':序号,'key':'modelIdDuplicate'}
        见过.add(修剪)
        if 'name' in 模型:
            名称=模型['name']
            if isinstance(名称,str) is False or len(名称)==0:
                return {'index':序号,'key':'modelNameInvalid'}
        if 'contextWindow' in 模型:
            窗=模型['contextWindow']
            合法=False
            if isinstance(窗,bool) is False and isinstance(窗,int) and 窗>0:
                合法=True
            if isinstance(窗,float) and 窗==窗 and 窗==int(窗) and int(窗)>0:
                合法=True
            if 合法 is False:
                return {'index':序号,'key':'modelContextInvalid'}
        if 'maxTokens' in 模型:
            上限=模型['maxTokens']
            合法=False
            if isinstance(上限,bool) is False and isinstance(上限,int) and 上限>0:
                合法=True
            if isinstance(上限,float) and 上限==上限 and 上限==int(上限) and int(上限)>0:
                合法=True
            if 合法 is False:
                return {'index':序号,'key':'modelMaxTokensInvalid'}
        序号=序号+1
    return None

class DeepSeek模型编辑器:
    'DeepSeek 适配器的模型目录。标识和名称在行上，容量在展开里'
    def __init__(自身,属性):
        '容量按字段记键入。展开状态按行号'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.编辑中={}
        自身.已展开=set()
        自身.行实例=[]
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props。缓冲和展开留着'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '目录头、每一行、添加。文案用中文表原文'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.根 is None:
            自身.根=建(文档,'section','modelCatalog')
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            清空子(自身.根)
        自身.根.setAttribute('aria-label',中文['models'])
        模型表=属性.get('models')
        if isinstance(模型表,(list,tuple)) is False:
            模型表=[]
        头=建(文档,'div','modelListHead')
        题组=建(文档,'div','modelCatalogHeading')
        题=建(文档,'span','modelCatalogTitle')
        题.textContent=中文['models']
        题组.appendChild(题)
        注=建(文档,'span','modelCatalogMeta')
        if 属性.get('overridden') is True:
            注.textContent=中文['modelsCustomized']
        else:
            注.textContent=中文['modelsInherited']
        题组.appendChild(注)
        头.appendChild(题组)
        if 属性.get('overridden') is True:
            复=建(文档,'button','linkButton')
            复.type='button'
            复.disabled=属性.get('disabled') is True
            复.textContent=中文['resetModels']
            def 点复(事件):
                '清掉缓冲和展开，回到继承'
                自身.编辑中={}
                自身.已展开=set()
                自身.行实例=[]
                属性['onReset']()
            复.addEventListener('click',点复)
            头.appendChild(复)
        自身.根.appendChild(头)
        if len(模型表)==0:
            空=建(文档,'p','modelEmpty')
            空.textContent=中文['modelsEmpty']
            自身.根.appendChild(空)
        else:
            列表=建(文档,'div','modelList')
            while len(自身.行实例)<len(模型表):
                自身.行实例.append(None)
            if len(自身.行实例)>len(模型表):
                自身.行实例=自身.行实例[:len(模型表)]
            序号=0
            for 模型 in 模型表:
                行属性=自身.行属性(模型,序号)
                实例=自身.行实例[序号]
                if 实例 is None:
                    实例=模型表行(行属性)
                    自身.行实例[序号]=实例
                else:
                    实例.更新(行属性)
                    实例.渲染()
                挂上(列表,实例)
                序号=序号+1
            自身.根.appendChild(列表)
        加=建(文档,'button','addModelButton')
        加.type='button'
        加.disabled=属性.get('disabled') is True
        挂上(加,图标('plus-16',{'window':窗口,'size':14}))
        加.appendChild(文档.createTextNode(中文['addModel']))
        def 点加(事件):
            '末尾加一行空标识'
            下一=[]
            for 模型 in 模型表:
                下一.append(dict(模型))
            下一.append({'id':''})
            属性['onChange'](下一)
        加.addEventListener('click',点加)
        自身.根.appendChild(加)
        return 自身.根

    def 行属性(自身,模型,序号):
        '这一行要的字段动作。容量文本优先用键入缓冲'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        def 改字段(字段,值):
            '替换用户层数组里的这一行'
            下一=[]
            下标=0
            for 项 in 属性.get('models') or []:
                拷=dict(项)
                if 下标==序号:
                    if 值 is None:
                        if 字段 in 拷:
                            del 拷[字段]
                    else:
                        拷[字段]=值
                下一.append(拷)
                下标=下标+1
            属性['onChange'](下一)
        def 容量文本(字段):
            '键入中的原文，否则把存量拼短'
            键=str(序号)+':'+字段
            if 键 in 自身.编辑中:
                return 自身.编辑中[键]
            值=模型.get(字段)
            if isinstance(值,bool) is False and isinstance(值,(int,float)):
                return 格式化容量(值)
            return ''
        def 改容量(字段,文本):
            '记下原文，并把解析结果写进行'
            自身.编辑中[str(序号)+':'+字段]=文本
            改字段(字段,解析容量(文本))
        def 落定(字段):
            '读不出的文本留在屏上'
            键=str(序号)+':'+字段
            if 键 not in 自身.编辑中:
                return
            解析=解析容量(自身.编辑中[键])
            if 解析 is not None and 解析!=解析:
                return
            del 自身.编辑中[键]
        def 容量件(字段,回退):
            '输入框要的值、占位和两个回调'
            占位=中文['contextWindowPlaceholder'] if 字段=='contextWindow' else 中文['maxTokensPlaceholder']
            if isinstance(回退,(int,float)) and isinstance(回退,bool) is False:
                占位=格式化容量(回退)
            def 改这一容(文本,字段=字段):
                '把这一格的键入交给缓冲'
                改容量(字段,文本)
            def 离这一容(字段=字段):
                '离开这一格时落定'
                落定(字段)
            return {
                'value':容量文本(字段),
                'placeholder':占位,
                'onChange':改这一容,
                'onBlur':离这一容,
            }
        def 换行(下一):
            '整行替换，保留这一行以外的模型'
            结果=[]
            下标=0
            for 项 in 属性.get('models') or []:
                if 下标==序号:
                    结果.append(下一)
                else:
                    结果.append(项)
                下标=下标+1
            属性['onChange'](结果)
        def 标识离开(值):
            '首尾空白去掉后再写回'
            修剪=值.strip()
            if 修剪!=值:
                改字段('id',修剪)
        def 切换():
            '开着就收，收着就开'
            if 序号 in 自身.已展开:
                自身.已展开.remove(序号)
            else:
                自身.已展开.add(序号)
            自身.渲染()
        def 移除():
            '删行后，后面的缓冲和展开行号减一'
            新缓冲={}
            for 键,文 in 自身.编辑中.items():
                下标=int(键[:键.index(':')])
                if 下标==序号:
                    continue
                if 下标>序号:
                    新键=行号模式.sub(str(下标-1),键,count=1)
                else:
                    新键=键
                新缓冲[新键]=文
            自身.编辑中=新缓冲
            新展开=set()
            for 下标 in 自身.已展开:
                if 下标==序号:
                    continue
                if 下标>序号:
                    新展开.add(下标-1)
                else:
                    新展开.add(下标)
            自身.已展开=新展开
            if 序号<len(自身.行实例):
                del 自身.行实例[序号]
            下一=[]
            下标=0
            for 项 in 属性.get('models') or []:
                if 下标!=序号:
                    下一.append(dict(项))
                下标=下标+1
            属性['onChange'](下一)
        return {
            'window':窗口,
            'model':模型,
            'position':序号+1,
            'inputField':'inputModalities',
            'expanded':序号 in 自身.已展开,
            'disabled':属性.get('disabled') is True,
            'contextWindow':容量件('contextWindow',属性.get('defaultContextWindow')),
            'maxTokens':容量件('maxTokens',属性.get('defaultMaxTokens')),
            'onFieldChange':改字段,
            'onIdBlur':标识离开,
            'onChange':换行,
            'onToggle':切换,
            'onRemove':移除,
        }
