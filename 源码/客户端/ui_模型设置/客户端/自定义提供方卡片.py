from ...模块.客户端.通告 import 取握手窗口
import re
from urllib.parse import urlparse
from ...ui_对话.异常 import 挂上
from .文案 import 中文
from .协议标注 import 协议标注
from .密钥判定 import 密钥失败
from .密钥输入 import 密钥输入
from .存储 import 推导密钥引用
from .DeepSeek模型编辑器 import 校验DeepSeek模型
from .模型列表编辑器 import 模型列表编辑器
from .模型推理强度 import 校验推理强度
from .编辑器页脚 import 建,清空子,采集焦点,还原焦点,编辑器页脚

__all__=['自定义提供方卡片']

命名空间='llm-pi-ai'
路由模式=re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z')

class 自定义提供方卡片:
    '声明适配器目录里没有的提供方。路由标识要到提交时才写进设置'
    def __init__(自身,属性):
        '记下打开时的修订和一份空草稿'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.打开于=属性.get('revision')
        协议表=属性.get('protocols')
        if isinstance(协议表,(list,tuple)) is False:
            协议表=[]
        自身.路由=''
        自身.显示名=''
        自身.基址=''
        自身.协议=协议表[0] if len(协议表)>0 else ''
        自身.密钥草稿=''
        自身.模型列表=[]
        自身.忙=False
        自身.列表忙=False
        自身.失败=None
        自身.已提交=False
        自身.列表件=None
        自身.页脚=None
        自身.根=None
        自身.通知忙()
        自身.渲染()

    def 更新(自身,属性):
        '刷新只读和已占用标识。打开时的修订不变'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 通知忙(自身):
        '创建或探询在飞时，外层不要切走'
        回调=自身.属性.get('onBusyChange')
        if 回调 is not None:
            回调(自身.忙 is True or 自身.列表忙 is True)

    def 渲染(自身):
        '路由、名称、地址、协议、密钥和模型列表'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        快照=None
        if 自身.根 is None:
            自身.根=建(文档,'div','editor')
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            快照=采集焦点(文档,自身.根)
            清空子(自身.根)
        已占=属性.get('taken')
        if isinstance(已占,(list,tuple)) is False:
            已占=[]
        协议表=属性.get('protocols')
        if isinstance(协议表,(list,tuple)) is False:
            协议表=[]
        禁用=属性.get('readOnly') is True or 自身.忙
        档案禁用=禁用 or 自身.已提交
        路由非法=len(自身.路由)>0 and 路由模式.match(自身.路由) is None
        路由占用=自身.路由 in 已占
        规范基址=自身.基址.strip()
        基址非法=False
        if len(自身.基址)>0:
            try:
                解析=urlparse(规范基址)
                基址非法=解析.scheme not in ('http','https') or 解析.netloc==''
            except Exception as 解析错误:
                基址非法=True
        模型错=校验DeepSeek模型(自身.模型列表)
        if 模型错 is None:
            模型错=校验推理强度(自身.模型列表)
        密钥错=密钥失败(自身.密钥草稿)
        密钥值=自身.密钥草稿.strip()
        就绪=len(自身.路由)>0 and 路由非法 is False and 路由占用 is False and len(规范基址)>0 and 基址非法 is False and len(自身.模型列表)>0 and 模型错 is None and 密钥错 is None
        提示=None
        if 自身.失败 is None and 就绪 is False and 密钥错 is None and len(自身.路由)>0 and 路由非法 is False and 路由占用 is False and 基址非法 is False:
            if len(规范基址)==0:
                提示=中文['customNeedsBaseUrl']
            elif 模型错 is not None:
                提示=中文['model']+' '+str(模型错['index']+1)+': '+中文[模型错['key']]
            else:
                提示=中文['customNeedsModels']
        自身.画字段(文档,中文['customRoute'],'custom-route')
        路由框=建(文档,'input','input')
        路由框.type='text'
        路由框.value=自身.路由
        路由框.placeholder='acme-gateway'
        路由框.setAttribute('aria-label',中文['customRoute'])
        路由框.disabled=档案禁用
        路由框.setAttribute('data-dsh-focus','custom-route')
        def 改路由(事件):
            '写入路由草稿'
            自身.路由=事件.target.value
            自身.渲染()
        路由框.addEventListener('input',改路由)
        自身.根.appendChild(路由框)
        if 路由非法 or 路由占用:
            错=建(文档,'p','error')
            错.textContent=中文['customRouteInvalid'] if 路由非法 else 中文['customRouteTaken']
            自身.根.appendChild(错)
        else:
            注=建(文档,'p','advancedHint')
            注.textContent=中文['customRouteHint']
            自身.根.appendChild(注)
        自身.画字段(文档,中文['customDisplayName'],None)
        名框=建(文档,'input','input')
        名框.type='text'
        名框.value=自身.显示名
        名框.placeholder=中文['customDisplayName'] if len(自身.路由)==0 else 自身.路由
        名框.setAttribute('aria-label',中文['customDisplayName'])
        名框.disabled=档案禁用
        名框.setAttribute('data-dsh-focus','custom-name')
        def 改名(事件):
            '写入显示名草稿'
            自身.显示名=事件.target.value
            自身.渲染()
        名框.addEventListener('input',改名)
        自身.根.appendChild(名框)
        自身.画字段(文档,中文['baseUrl'],None)
        址框=建(文档,'input','input')
        址框.type='text'
        址框.value=自身.基址
        if 自身.协议=='anthropic-messages':
            址框.placeholder=中文['customAnthropicBaseUrlPlaceholder']
        else:
            址框.placeholder=中文['customBaseUrlPlaceholder']
        址框.setAttribute('aria-label',中文['baseUrl'])
        if 基址非法:
            址框.setAttribute('aria-invalid','true')
        址框.disabled=档案禁用
        址框.setAttribute('data-dsh-focus','custom-base')
        def 改址(事件):
            '写入端点草稿'
            自身.基址=事件.target.value
            自身.渲染()
        址框.addEventListener('input',改址)
        自身.根.appendChild(址框)
        if 基址非法:
            错=建(文档,'p','error')
            错.textContent=中文['customBaseUrlInvalid']
            自身.根.appendChild(错)
        自身.画字段(文档,中文['customApi'],None)
        选=建(文档,'select','input selectInput')
        选.value=自身.协议
        选.setAttribute('aria-label',中文['customApi'])
        选.disabled=档案禁用
        for 候选 in 协议表:
            项=文档.createElement('option')
            项.value=候选
            项.textContent=协议标注(候选)
            选.appendChild(项)
        def 改协议(事件):
            '写入协议草稿'
            自身.协议=事件.target.value
            自身.渲染()
        选.addEventListener('change',改协议)
        自身.根.appendChild(选)
        自身.画字段(文档,中文['keyInput'],None)
        挡=None
        if 基址非法:
            挡='customBaseUrlInvalid'
        elif 密钥错=='keyBlank':
            挡='keyBlankNew'
        elif 密钥错 is not None:
            挡=密钥错
        探询={'settingsNs':命名空间,'baseURL':规范基址,'api':自身.协议}
        if len(密钥值)>0:
            探询['apiKey']=密钥值
        def 改密钥(事件):
            '写入密钥草稿'
            自身.密钥草稿=事件.target.value
            自身.渲染()
        挂上(自身.根,密钥输入({
            'window':窗口,
            'value':自身.密钥草稿,
            'placeholder':中文['keyPlaceholder'],
            'aria-label':中文['keyInput'],
            'disabled':禁用,
            'focusKey':'custom-key',
            'onChange':改密钥,
        }))
        if 密钥错 is not None:
            错=建(文档,'p','error')
            if 密钥错=='keyBlank':
                错.textContent=中文['keyBlankNew']
            else:
                错.textContent=中文[密钥错]
            自身.根.appendChild(错)
        def 改模型(下一):
            '写入模型草稿'
            自身.模型列表=下一
            自身.渲染()
        def 列表忙变(忙):
            '探询在飞'
            自身.列表忙=忙 is True
            自身.通知忙()
        列表属性={
            'window':窗口,
            'models':自身.模型列表,
            'onChange':改模型,
            'reasoningLevels':属性.get('reasoningLevels'),
            'probe':探询,
            'probeBlocked':挡,
            'operations':属性.get('operations'),
            'disabled':档案禁用,
            'onBusyChange':列表忙变,
        }
        if 自身.列表件 is None:
            自身.列表件=模型列表编辑器(列表属性)
        else:
            自身.列表件.更新(列表属性)
            自身.列表件.渲染()
        挂上(自身.根,自身.列表件)
        if 自身.失败 is not None:
            错=建(文档,'p','error')
            错.textContent=自身.失败
            自身.根.appendChild(错)
        if 提示 is not None:
            注=建(文档,'p','advancedHint')
            注.textContent=提示
            自身.根.appendChild(注)
        def 取消():
            '关闭。档案已经写上则算变更'
            属性['onClose'](自身.已提交)
        def 提交():
            '创建提供方，密钥另存'
            自身.忙=True
            自身.失败=None
            自身.通知忙()
            引用=推导密钥引用(自身.路由)
            存密钥=len(密钥值)>0
            失败=None
            if 自身.已提交 is False:
                档案={}
                if len(自身.显示名)>0:
                    档案['displayName']=自身.显示名
                if 存密钥:
                    档案['apiKeyEnv']=引用
                档案['api']=自身.协议
                档案['baseURL']=规范基址
                模型拷=[]
                for 模型 in 自身.模型列表:
                    模型拷.append(dict(模型))
                档案['models']=模型拷
                写出=属性['operations']['写设置'](
                    命名空间,
                    [{'op':'set','path':['providers',自身.路由],'value':档案}],
                    自身.打开于,
                )
                if 写出['kind']!='written':
                    if 写出['kind']=='conflict':
                        失败=中文['conflict']
                    else:
                        失败=写出['message']
                else:
                    自身.已提交=True
            if 失败 is None and 存密钥:
                存=属性['operations']['存凭据'](引用,密钥值)
                if 存 is not None:
                    失败=存
            自身.忙=False
            自身.通知忙()
            if 失败 is not None:
                自身.失败=失败
                自身.渲染()
                return
            属性['onClose'](True)
        页脚属性={
            'window':窗口,
            'busy':自身.忙,
            'submitDisabled':禁用 or 就绪 is False,
            'submitLabelKey':'create',
            'submitBusyLabelKey':'creating',
            'onCancel':取消,
            'onSubmit':提交,
        }
        if 自身.页脚 is None:
            自身.页脚=编辑器页脚(页脚属性)
        else:
            自身.页脚.更新(页脚属性)
            自身.页脚.渲染()
        挂上(自身.根,自身.页脚)
        还原焦点(文档,快照)
        return 自身.根

    def 画字段(自身,文档,文,焦点):
        '一行字段名'
        行=建(文档,'div','field')
        标=建(文档,'span','fieldLabel')
        标.textContent=文
        行.appendChild(标)
        自身.根.appendChild(行)
