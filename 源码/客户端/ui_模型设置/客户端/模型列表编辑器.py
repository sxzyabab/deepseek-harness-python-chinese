from ...模块.客户端.通告 import 取握手窗口
import re
from ...ui_基础界面组件.icons import 图标
from ...ui_基础界面组件.按钮 import 按钮
from ...ui_基础界面组件.模态 import 模态
from ...ui_对话.异常 import 挂上
from .DeepSeek模型编辑器 import 格式化容量,解析容量
from .文案 import 中文
from .模型表行 import 模型表行
from .编辑器页脚 import 建,清空子,样式模块

__all__=['模型列表编辑器']

容量提示={'contextWindow':'256K','maxTokens':'32K'}
行号模式=re.compile(r'^\d+')

def 文本自(模型,键):
    '行上的文本字段。不是字符串就当空'
    值=模型.get(键)
    if isinstance(值,str):
        return 值
    return ''

class 模型列表编辑器:
    'pi-ai 档案上的模型列表，以及向端点询问可用模型'
    def __init__(自身,属性):
        '记下草稿。目录默认和挑选都还没开始'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.忙=False
        自身.失败=None
        自身.继承目录=None
        自身.已读键=None
        自身.候选=None
        自身.已选=set()
        自身.查询=''
        自身.已展开=set()
        自身.编辑中={}
        自身.行实例=[]
        自身.根=None
        自身.通知忙()
        自身.读目录()
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props。本地挑选和键入留着'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.读目录()

    def 通知忙(自身):
        '把探询是否在飞告诉拥有这张卡的表面'
        回调=自身.属性.get('onBusyChange')
        if 回调 is not None:
            回调(自身.忙 is True)

    def 读目录(自身):
        '已安装提供方的目录不走端点。提供方变了才再问'
        属性=自身.属性
        提供方=属性.get('catalogProvider')
        探询=属性.get('probe')
        if isinstance(探询,dict) is False:
            探询={}
        键=(提供方,探询.get('settingsNs'))
        if 提供方 is None:
            自身.继承目录=None
            自身.已读键=None
            return
        if 自身.已读键==键:
            return
        应答=属性['operations']['探询模型'](探询.get('settingsNs'),{'provider':提供方})
        if 应答['kind']=='found':
            自身.继承目录={'provider':提供方,'models':应答['models']}
            自身.失败=None
        else:
            自身.继承目录={'provider':提供方,'models':[]}
            自身.失败=应答['message']
        自身.已读键=键

    def 渲染(自身):
        '列表、获取按钮，以及挑选对话框'
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
        探询=属性.get('probe')
        if isinstance(探询,dict) is False:
            探询={}
        目录模型=None
        if 自身.继承目录 is not None and 自身.继承目录.get('provider')==属性.get('catalogProvider'):
            目录模型=自身.继承目录.get('models')
        输入默认={}
        if isinstance(目录模型,list):
            for 项 in 目录模型:
                if isinstance(项,dict) and 'id' in 项:
                    输入默认[项['id']]=项.get('inputModalities')
        头=建(文档,'div','modelListHead')
        题组=建(文档,'div','modelCatalogHeading')
        题=建(文档,'span','modelCatalogTitle')
        题.textContent=中文['models']
        题组.appendChild(题)
        if 'overridden' in 属性 and 属性.get('overridden') is not None:
            注=建(文档,'span','modelCatalogMeta')
            if 属性.get('overridden') is True:
                注.textContent=中文['modelsCustomized']
            else:
                注.textContent=中文['modelsInherited']
            题组.appendChild(注)
        头.appendChild(题组)
        if 属性.get('overridden') is True and 属性.get('onReset') is not None:
            复=建(文档,'button','linkButton')
            复.type='button'
            复.disabled=属性.get('disabled') is True
            复.textContent=中文['resetModels']
            def 点复(事件):
                '回到继承，清掉本列表的展开和缓冲'
                自身.已展开=set()
                自身.编辑中={}
                自身.行实例=[]
                属性['onReset']()
            复.addEventListener('click',点复)
            头.appendChild(复)
        可问=探询.get('provider') is not None or (isinstance(探询.get('baseURL'),str) and len(探询.get('baseURL'))>0)
        取=建(文档,'button','linkButton')
        取.type='button'
        取.disabled=属性.get('disabled') is True or 自身.忙 or 可问 is False or 属性.get('probeBlocked') is not None
        if 属性.get('probeBlocked') is not None:
            取.title=中文[属性['probeBlocked']]
        elif 可问 is False:
            取.title=中文['fetchNeedsBaseUrl']
        取.textContent=中文['fetching'] if 自身.忙 else 中文['fetchModels']
        def 点取(事件):
            '按表单上现在的端点、协议和密钥去问'
            自身.忙=True
            自身.失败=None
            自身.通知忙()
            自身.渲染()
            请求={}
            if 探询.get('provider') is not None:
                请求['provider']=探询['provider']
            if isinstance(探询.get('baseURL'),str) and len(探询['baseURL'])>0:
                请求['baseURL']=探询['baseURL']
            if 探询.get('api') is not None:
                请求['api']=探询['api']
            if 探询.get('apiKey') is not None:
                请求['apiKey']=探询['apiKey']
            应答=属性['operations']['探询模型'](探询.get('settingsNs'),请求)
            自身.忙=False
            自身.通知忙()
            if 应答['kind']=='refused':
                自身.失败=应答['message']
                自身.渲染()
                return
            找到=应答['models']
            if 属性.get('catalogProvider') is not None:
                自身.继承目录={'provider':属性['catalogProvider'],'models':找到}
                自身.已读键=(属性['catalogProvider'],探询.get('settingsNs'))
            if len(找到)==0:
                自身.失败=中文['fetchEmpty']
                自身.渲染()
                return
            已知=set()
            for 模型 in 模型表:
                已知.add(文本自(模型,'id'))
            自身.查询=''
            自身.候选=找到
            自身.已选=set()
            for 项 in 找到:
                if 项.get('id') not in 已知:
                    自身.已选.add(项.get('id'))
            自身.渲染()
        取.addEventListener('click',点取)
        头.appendChild(取)
        自身.根.appendChild(头)
        if len(模型表)==0:
            空=建(文档,'p','modelEmpty')
            空.textContent=中文['modelsEmpty']
            自身.根.appendChild(空)
        列表=建(文档,'div','modelList')
        while len(自身.行实例)<len(模型表):
            自身.行实例.append(None)
        if len(自身.行实例)>len(模型表):
            自身.行实例=自身.行实例[:len(模型表)]
        序号=0
        for 模型 in 模型表:
            行属性=自身.行属性(模型,序号,输入默认,目录模型)
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
                下一.append(模型)
            下一.append({'id':''})
            属性['onChange'](下一)
        加.addEventListener('click',点加)
        自身.根.appendChild(加)
        if 自身.失败 is not None:
            错=建(文档,'p','error')
            错.textContent=自身.失败
            自身.根.appendChild(错)
        自身.根.appendChild(自身.挑选(窗口,文档))
        return 自身.根

    def 行属性(自身,模型,序号,输入默认,目录模型):
        '一行的容量缓冲和删除后的行号移动'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        模型表=属性.get('models') or []
        def 补丁(下标,改动):
            '清空的可选字段从档案里拿掉'
            下一=[]
            序=0
            for 项 in 模型表:
                if 序!=下标:
                    下一.append(项)
                else:
                    清掉=set()
                    for 键,值 in 改动.items():
                        if 值 is None or 值=='':
                            清掉.add(键)
                    合并=dict(项)
                    合并.update(改动)
                    留下={}
                    for 键,值 in 合并.items():
                        if 键 not in 清掉:
                            留下[键]=值
                    下一.append(留下)
                序=序+1
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
            '记下原文并解析写进行'
            自身.编辑中[str(序号)+':'+字段]=文本
            补丁(序号,{字段:解析容量(文本)})
        def 重排缓冲(下标):
            '删行后后面的缓冲行号减一'
            新缓冲={}
            for 键,文 in 自身.编辑中.items():
                在=int(键[:键.index(':')])
                if 在==下标:
                    continue
                if 在>下标:
                    新键=行号模式.sub(str(在-1),键,count=1)
                else:
                    新键=键
                新缓冲[新键]=文
            自身.编辑中=新缓冲
        def 切换():
            '开着就收，收着就开'
            if 序号 in 自身.已展开:
                自身.已展开.remove(序号)
            else:
                自身.已展开.add(序号)
            自身.渲染()
        def 移除():
            '删行，展开和缓冲跟着行号走'
            下一=[]
            序=0
            for 项 in 模型表:
                if 序!=序号:
                    下一.append(项)
                序=序+1
            属性['onChange'](下一)
            新展开=set()
            for 在 in 自身.已展开:
                if 在<序号:
                    新展开.add(在)
                elif 在>序号:
                    新展开.add(在-1)
            自身.已展开=新展开
            重排缓冲(序号)
            if 序号<len(自身.行实例):
                del 自身.行实例[序号]
        标识=文本自(模型,'id')
        回退=输入默认.get(标识)
        if 回退 is None:
            回退=属性.get('defaultInput')
        def 改字段(字段,值):
            '标识或名称'
            补丁(序号,{字段:值})
        def 换行(下一):
            '整行替换'
            结果=[]
            序=0
            for 项 in 模型表:
                if 序==序号:
                    结果.append(下一)
                else:
                    结果.append(项)
                序=序+1
            属性['onChange'](结果)
        def 改窗(文本):
            '上下文窗口'
            改容量('contextWindow',文本)
        def 改上限(文本):
            '最大输出'
            改容量('maxTokens',文本)
        return {
            'window':窗口,
            'model':模型,
            'position':序号+1,
            'inputField':'input',
            'inputFallback':回退,
            'inputLoading':属性.get('catalogProvider') is not None and 目录模型 is None,
            'reasoningLevels':属性.get('reasoningLevels'),
            'expanded':序号 in 自身.已展开,
            'disabled':属性.get('disabled') is True,
            'contextWindow':{
                'value':容量文本('contextWindow'),
                'placeholder':容量提示['contextWindow'],
                'onChange':改窗,
            },
            'maxTokens':{
                'value':容量文本('maxTokens'),
                'placeholder':容量提示['maxTokens'],
                'onChange':改上限,
            },
            'onFieldChange':改字段,
            'onChange':换行,
            'onToggle':切换,
            'onRemove':移除,
        }

    def 挑选(自身,窗口,文档):
        '候选对话框。没打开时不占页面'
        属性=自身.属性
        打开=自身.候选 is not None
        候选=自身.候选 if isinstance(自身.候选,list) else []
        查询=自身.查询.strip().lower()
        可见=[]
        for 项 in 候选:
            if len(查询)==0:
                可见.append(项)
                continue
            标识=项.get('id')
            名称=项.get('name')
            中标识=isinstance(标识,str) and 查询 in 标识.lower()
            中名称=isinstance(名称,str) and 查询 in 名称.lower()
            if 中标识 or 中名称:
                可见.append(项)
        全选=len(可见)>0
        for 项 in 可见:
            if 项.get('id') not in 自身.已选:
                全选=False
                break
        def 关掉():
            '清掉候选和勾选'
            自身.候选=None
            自身.已选=set()
            自身.查询=''
            自身.渲染()
        def 采纳():
            '已有行保留用户改过的容量'
            if 自身.候选 is None:
                return
            按标识={}
            顺序=[]
            for 模型 in 属性.get('models') or []:
                标识=文本自(模型,'id')
                按标识[标识]=模型
                顺序.append(标识)
            for 项 in 自身.候选:
                if 项.get('id') not in 自身.已选:
                    continue
                标识=项.get('id')
                if 标识 in 按标识:
                    continue
                新={'id':标识}
                if 项.get('name') is not None:
                    新['name']=项['name']
                if 项.get('contextWindow') is not None:
                    新['contextWindow']=项['contextWindow']
                if 项.get('maxTokens') is not None:
                    新['maxTokens']=项['maxTokens']
                if 项.get('inputModalities') is not None:
                    新['input']=list(项['inputModalities'])
                按标识[标识]=新
                顺序.append(标识)
            下一=[]
            for 标识 in 顺序:
                下一.append(按标识[标识])
            属性['onChange'](下一)
            关掉()
        def 改查询(事件):
            '过滤候选'
            自身.查询=事件.target.value
            自身.渲染()
        def 切可见():
            '可见的全选或全部取消'
            if 全选:
                自身.已选=set()
            else:
                下一=set(自身.已选)
                for 项 in 可见:
                    下一.add(项.get('id'))
                自身.已选=下一
            自身.渲染()
        体=建(文档,'div')
        条=建(文档,'div','candidateToolbar')
        搜=建(文档,'input','input candidateSearch')
        搜.type='search'
        搜.value=自身.查询
        搜.placeholder=中文['fetchSearch']
        搜.setAttribute('aria-label',中文['fetchSearch'])
        搜.setAttribute('data-dsh-focus','model-fetch-search')
        搜.addEventListener('input',改查询)
        条.appendChild(搜)
        全选钮=按钮({
            'window':窗口,
            'variant':'ghost',
            'size':'sm',
            'disabled':len(可见)==0,
            'onClick':切可见,
            'children':中文['fetchDeselectAll'] if 全选 else 中文['fetchSelectAll'],
        }).渲染()
        条.appendChild(全选钮)
        体.appendChild(条)
        if len(可见)==0:
            无=建(文档,'p','candidateEmpty')
            无.setAttribute('role','status')
            无.textContent=中文['fetchNoMatches']
            体.appendChild(无)
        else:
            列=建(文档,'ul','candidateList')
            for 项 in 可见:
                项行=建(文档,'li','candidate')
                签=建(文档,'label','candidateLabel')
                勾=文档.createElement('input')
                勾.type='checkbox'
                勾.checked=项.get('id') in 自身.已选
                def 点勾(事件,标识=项.get('id')):
                    '有就去掉，没有就加上'
                    if 标识 in 自身.已选:
                        自身.已选.remove(标识)
                    else:
                        自身.已选.add(标识)
                    自身.渲染()
                勾.addEventListener('change',点勾)
                签.appendChild(勾)
                字=建(文档,'span','candidateId')
                字.title=项.get('name') if 项.get('name') is not None else 项.get('id')
                字.textContent=项.get('id') if 项.get('id') is not None else ''
                签.appendChild(字)
                项行.appendChild(签)
                列.appendChild(项行)
            体.appendChild(列)
        取消=按钮({'window':窗口,'variant':'outline','onClick':关掉,'children':中文['cancel']}).渲染()
        加入=按钮({'window':窗口,'variant':'outline','onClick':采纳,'children':中文['fetchAdopt']}).渲染()
        脚=文档.createElement('div')
        脚.appendChild(取消)
        脚.appendChild(加入)
        罩=模态({
            'window':窗口,
            'open':打开,
            'onClose':关掉,
            'title':中文['fetchTitle'],
            'closeLabel':中文['close'],
            'description':中文['fetchDescription'],
            'className':'fetchDialog',
            'children':体,
            'footer':脚,
        }).渲染()
        if 罩 is not None:
            卡=罩.querySelector('.fetchDialog')
            if 卡 is not None:
                卡.setAttribute('data-dsh-css',样式模块)
            return 罩
        return 文档.createElement('span')
