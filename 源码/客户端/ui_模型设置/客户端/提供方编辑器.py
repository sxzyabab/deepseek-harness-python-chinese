from ...模块.客户端.通告 import 取握手窗口
import copy
import json
from ...ui_基础界面组件.提示泡 import 提示泡
from ...ui_对话.异常 import 挂上
from .文案 import 中文
from .协议标注 import 协议标注
from .密钥判定 import 密钥失败
from .密钥输入 import 密钥输入
from .存储 import 推导密钥引用,协议选项,推理档位选项
from .DeepSeek模型编辑器 import DeepSeek模型编辑器,模型草稿表,校验DeepSeek模型
from .模型列表编辑器 import 模型列表编辑器
from .模型推理强度 import 校验推理强度
from .编辑器页脚 import 建,清空子,采集焦点,还原焦点,编辑器页脚

__all__=['提供方编辑器']

class 提供方编辑器:
    '一张提供方卡片：只写密钥，自定义区里是地址、协议和模型目录'
    def __init__(自身,属性):
        '从用户层播下草稿，修订钉在打开时的命名空间上'
        自身.属性=属性 if isinstance(属性,dict) else {}
        模式=属性.get('schema')
        命名空间=属性.get('namespace')
        路径=属性.get('settingsPath')
        if isinstance(路径,(list,tuple)) is False:
            路径=[]
        子树=None
        if 模式 is not None and 命名空间 is not None:
            子树=模式['取路径'](命名空间.get('user'),路径)
        if isinstance(子树,dict):
            自身.草稿=copy.deepcopy(子树)
        else:
            自身.草稿={}
        自身.密钥草稿=''
        自身.忙=False
        自身.列表忙=False
        自身.失败=None
        if 模式 is not None and 命名空间 is not None:
            自身.已提交原稿=模式['取路径'](命名空间.get('user'),路径)
            自身.期望修订=命名空间.get('revision')
        else:
            自身.已提交原稿=None
            自身.期望修订=None
        自身.目录件=None
        自身.目录种类=None
        自身.页脚=None
        自身.根=None
        自身.通知忙()
        自身.渲染()

    def 更新(自身,属性):
        '刷新只读和命名空间。草稿留着，避免推送冲掉键入'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 通知忙(自身):
        '提交或模型探询在飞时告诉外层'
        回调=自身.属性.get('onBusyChange')
        if 回调 is not None:
            回调(自身.忙 is True or 自身.列表忙 is True)

    def 字符串于(自身,源,键):
        '空白视作没有这个字段'
        模式=自身.属性.get('schema')
        if 模式 is None:
            return None
        值=模式['取路径'](源,[键])
        if isinstance(值,str) and len(值.strip())>0:
            return 值
        return None

    def 设字段(自身,键,下一):
        '纯空白清空，不把空格写进档案'
        模式=自身.属性['schema']
        if 下一 is None or len(下一.strip())==0:
            自身.草稿=模式['删路径'](自身.草稿,[键])
        else:
            自身.草稿=模式['设路径'](自身.草稿,[键],下一)

    def 渲染(自身):
        '标题、密钥、自定义区和页脚'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        快照=None
        模式=属性.get('schema')
        命名空间=属性.get('namespace')
        路径=属性.get('settingsPath')
        if isinstance(路径,(list,tuple)) is False:
            路径=[]
        if 模式 is None or 命名空间 is None:
            return 自身.根
        根模式=模式['再水合'](命名空间.get('schema'))
        节点=模式['路径节点'](根模式,路径)
        类名='addBlock' if 属性.get('credentialOnly') is True else 'editor'
        if 自身.根 is None:
            自身.根=建(文档,'div',类名)
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            快照=采集焦点(文档,自身.根)
            自身.根.className=类名
            清空子(自身.根)
        if 节点 is None:
            错=建(文档,'p','error')
            错.textContent=str(属性.get('provider'))+': '+中文['settingsPathUnresolvable']
            自身.根.appendChild(错)
            还原焦点(文档,快照)
            return 自身.根
        名字=命名空间.get('ns')
        if 名字=='llm-deepseek':
            布局='deepseek'
        elif 名字=='llm-pi-ai':
            布局='pi-ai'
        else:
            布局='unknown'
        if 属性.get('hideTitle') is not True:
            头=建(文档,'div','editorHeader')
            题=建(文档,'span','editorTitle')
            题.textContent=属性.get('displayName') if 属性.get('displayName') is not None else ''
            头.appendChild(题)
            if 属性.get('provider')!=属性.get('displayName'):
                路由=建(文档,'span','editorRoute')
                路由.textContent=str(属性.get('provider'))
                头.appendChild(路由)
            自身.根.appendChild(头)
        if 布局=='unknown':
            注=建(文档,'p','advancedHint')
            注.textContent=中文['advancedHint']+' ('+str(名字)+')'
            自身.根.appendChild(注)
        else:
            自身.画族(文档,窗口,布局,根模式,节点)
        if 自身.失败 is not None:
            错=建(文档,'p','error')
            错.textContent=自身.失败
            自身.根.appendChild(错)
        模型错=None
        if 属性.get('credentialOnly') is not True:
            模型错=自身.校验模型(模式['取路径'](自身.草稿,['models']))
            if 模型错 is not None:
                注=建(文档,'p','advancedHint')
                注.textContent=中文['model']+' '+str(模型错['index']+1)+': '+中文[模型错['key']]
                自身.根.appendChild(注)
        禁用=属性.get('readOnly') is True or 自身.忙
        密钥错=自身.所示密钥失败()
        密钥值=自身.密钥草稿.strip()
        不可交=禁用 or 布局=='unknown' or (属性.get('credentialOnly') is not True and 模型错 is not None) or 密钥错 is not None or (属性.get('credentialRequired') is True and len(密钥值)==0)
        def 取消():
            '关闭且没有变更'
            属性['onClose'](False)
        def 提交():
            '先写档案路径，再存密钥'
            先=属性.get('onSubmitCredential')
            if 先 is not None:
                先()
            自身.忙=True
            自身.失败=None
            自身.通知忙()
            失败=自身.提交一次(布局,根模式,节点)
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
            'submitDisabled':不可交,
            'submitLabelKey':属性.get('submitLabelKey') if 属性.get('submitLabelKey') is not None else 'apply',
            'submitBusyLabelKey':属性.get('submitBusyLabelKey') if 属性.get('submitBusyLabelKey') is not None else 'applying',
            'onCancel':取消,
            'onSubmit':提交,
        }
        if 属性.get('cancelLabelKey') is not None:
            页脚属性['cancelLabelKey']=属性['cancelLabelKey']
        if 自身.页脚 is None:
            自身.页脚=编辑器页脚(页脚属性)
        else:
            自身.页脚.更新(页脚属性)
            自身.页脚.渲染()
        挂上(自身.根,自身.页脚)
        还原焦点(文档,快照)
        return 自身.根

    def 所示密钥失败(自身):
        '必填时只含空白优先于格式错误'
        if 自身.属性.get('credentialRequired') is True and len(自身.密钥草稿)>0 and len(自身.密钥草稿.strip())==0:
            return 'keyRequired'
        return 密钥失败(自身.密钥草稿)

    def 校验模型(自身,值):
        '目录行，以及手写路由才检查的推理档位'
        错=校验DeepSeek模型(值)
        if 错 is not None:
            return 错
        命名空间=自身.属性.get('namespace')
        模式=自身.属性.get('schema')
        名字=命名空间.get('ns') if isinstance(命名空间,dict) else None
        if 名字=='llm-pi-ai' and 自身.属性.get('declared') is True:
            档=推理档位选项(命名空间,模式)
            if len(档)>0:
                return 校验推理强度(值)
        return None

    def 提交一次(自身,布局,根模式,节点):
        '返回失败文案。没有失败就是 None'
        属性=自身.属性
        模式=属性['schema']
        命名空间=属性['namespace']
        路径=属性.get('settingsPath')
        if isinstance(路径,(list,tuple)) is False:
            路径=[]
        名字=命名空间.get('ns')
        回退=模式['取路径'](命名空间.get('value'),路径)
        密钥值=自身.密钥草稿.strip()
        档案=模式['取路径'](命名空间.get('value'),路径)
        点名=None
        if isinstance(档案,dict):
            名=档案.get('apiKeyEnv')
            if isinstance(名,str) and len(名)>0:
                点名=名
        密钥引用=点名 if 点名 is not None else 推导密钥引用(属性.get('provider'))
        下一=自身.草稿
        if 布局=='pi-ai' and 自身.字符串于(自身.草稿,'apiKeyEnv') is None and 自身.字符串于(回退,'apiKeyEnv') is None and len(密钥值)>0:
            下一=模式['设路径'](自身.草稿,['apiKeyEnv'],密钥引用)
        if 属性.get('credentialOnly') is not True:
            错=自身.校验模型(模式['取路径'](下一,['models']))
            if 错 is not None:
                return 中文['model']+' '+str(错['index']+1)+': '+中文[错['key']]
        if 属性.get('credentialOnly') is not True and 节点 is not None and len(路径)==0:
            节错=模式['校验'](节点,下一)
            if 节错 is not None:
                return 节错
        原生空档=布局=='pi-ai' and 回退 is None and 自身.已提交原稿 is None and len(下一)==0
        if 属性.get('credentialOnly') is True:
            操作表=[]
        elif 原生空档:
            操作表=[{'op':'set','path':list(路径),'value':{}}]
        else:
            操作表=自身.路径操作(路径,自身.已提交原稿,下一)
        if len(操作表)>0:
            写出=属性['operations']['写设置'](名字,操作表,自身.期望修订)
            if 写出['kind']!='written':
                if 写出['kind']=='conflict':
                    return 中文['conflict']
                return 写出['message']
            自身.已提交原稿=模式['取路径'](写出['view'].get('user'),路径)
            自身.期望修订=写出['view'].get('revision')
            自身.草稿=下一
        if len(密钥值)>0:
            存=属性['operations']['存凭据'](密钥引用,密钥值)
            if 存 is not None:
                return 存
        自身.密钥草稿=''
        return None

    def 路径操作(自身,基路径,之前,之后):
        '只点名卡片看见的字段。两边都没有的字段不产生操作'
        先前={}
        if isinstance(之前,dict):
            先前=之前
        操作表=[]
        for 键,值 in 之后.items():
            if 键 in 先前:
                旧=json.dumps(先前[键],ensure_ascii=False,separators=(',',':'))
                新=json.dumps(值,ensure_ascii=False,separators=(',',':'))
                if 旧==新:
                    continue
            操作表.append({'op':'set','path':list(基路径)+[键],'value':值})
        for 键 in 先前.keys():
            if 键 not in 之后:
                操作表.append({'op':'unset','path':list(基路径)+[键]})
        return 操作表

    def 画族(自身,文档,窗口,族,根模式,节点):
        '密钥和折叠的自定义区'
        属性=自身.属性
        模式=属性['schema']
        命名空间=属性['namespace']
        路径=属性.get('settingsPath')
        if isinstance(路径,(list,tuple)) is False:
            路径=[]
        禁用=属性.get('readOnly') is True or 自身.忙
        回退=模式['取路径'](命名空间.get('value'),路径)
        拥有身份=族=='pi-ai' and 属性.get('declared') is True
        自定义模型=模式['取路径'](自身.草稿,['models'])
        已覆盖=模式['有路径'](自身.草稿,['models'])
        钉住=模式['取路径'](命名空间.get('base'),list(路径)+['models'])
        if 钉住 is None:
            模型节点=模式['路径节点'](根模式,list(路径)+['models'])
            元=模型节点.get('meta') if isinstance(模型节点,dict) else None
            继承=元.get('default') if isinstance(元,dict) else None
        else:
            继承=钉住
        模型行=模型草稿表(自定义模型 if 已覆盖 else 继承)
        默认窗=模式['取路径'](回退,['defaultContextWindow'])
        默认上限=模式['取路径'](回退,['maxTokens'])
        默认输入=模式['取路径'](回退,['defaultInput'])
        基址=自身.字符串于(回退,'baseURL')
        if 基址 is None:
            基址=属性.get('defaultBaseURL')
        端点环境=属性.get('baseURLEnv')
        if isinstance(端点环境,(list,tuple)) is False:
            端点环境=[]
        if 族=='deepseek':
            端点注=中文['deepSeekEndpointHint']
        elif 基址 is None and len(端点环境)>0:
            端点注=中文['baseUrlEnvironment'].replace('{env}',', '.join(端点环境))
        else:
            端点注=None
        点名=自身.字符串于(回退,'apiKeyEnv')
        原生=属性.get('nativeAuth') if 点名 is None else None
        if 点名 is None:
            认证引用=[]
            if isinstance(原生,dict) and isinstance(原生.get('env'),list):
                认证引用=list(原生.get('env'))
            留下=[]
            for 引用 in 认证引用:
                if isinstance(引用,str) and 引用.lower().find('oauth')<0 and 引用 not in 端点环境:
                    留下.append(引用)
            认证引用=留下
        else:
            认证引用=[点名]
        可见=[]
        for 引用 in 认证引用:
            if isinstance(引用,str) and 引用.lower().find('oauth')<0:
                可见.append(引用)
        提示引用=可见[0] if len(可见)>0 else None
        检查=属性.get('credentialChecks')
        if isinstance(检查,dict) is False:
            检查={}
        检测到=None
        检测引用=None
        for 引用 in 认证引用:
            信息=检查.get(引用)
            if 引用==点名 and 信息 is None:
                信息=属性.get('credential')
            if isinstance(信息,dict) and 信息.get('configured') is True:
                检测到=信息
                检测引用=引用
                break
        检测可见=检测引用 if 检测引用 in 可见 else None
        全缺=len(认证引用)>0
        for 引用 in 认证引用:
            信息=检查.get(引用)
            if 引用==点名 and 信息 is None:
                信息=属性.get('credential')
            if isinstance(信息,dict) is False or 信息.get('configured') is not False:
                全缺=False
                break
        已存文件=isinstance(检测到,dict) and 检测到.get('source')=='file'
        凭据注=None
        if len(自身.密钥草稿)==0 and 已存文件 is False and 提示引用 is not None and 属性.get('credentialRequired') is not True:
            if 检测引用 is None:
                键='keyFallbackMissing' if 全缺 else 'keyFallbackUnchecked'
            elif 检测可见 is None:
                键='keyFallbackDetectedHidden'
            else:
                键='keyFallbackDetected'
            填=检测可见 if 检测可见 is not None else 提示引用
            凭据注=中文[键].replace('{hint}',填)
        密钥说明=None
        if len(可见)>0:
            密钥说明=中文['keyHelp'].replace('{env}',' / '.join(可见))
        无密钥原生=isinstance(原生,dict) and isinstance(原生.get('env'),list) and len(原生.get('env'))==0 and 原生.get('oauth')
        if 提示引用 is None or 属性.get('credentialRequired') is True:
            占位=中文['keyPlaceholder']
        elif 已存文件:
            占位=中文['keyPlaceholderSaved'].replace('{hint}',提示引用)
        else:
            占位=中文['keyPlaceholderFallback'].replace('{hint}',提示引用)
        if 无密钥原生 is not True:
            行=建(文档,'div','field')
            标=建(文档,'span','fieldLabel')
            标.textContent=中文['keyInput']
            if 密钥说明 is not None:
                问=建(文档,'button','helpButton')
                问.type='button'
                问.setAttribute('aria-label',中文['authHelp'])
                问.textContent='?'
                挂上(标,提示泡({
                    'window':窗口,
                    'label':密钥说明,
                    'side':'right',
                    'delayMs':0,
                    'focusDelayMs':0,
                    'portal':True,
                    'openOnClick':True,
                    'children':问,
                }))
            行.appendChild(标)
            密钥错=自身.所示密钥失败()
            def 改密钥(事件):
                '写入只写密钥草稿'
                自身.密钥草稿=事件.target.value
                自身.渲染()
            挂上(行,密钥输入({
                'window':窗口,
                'value':自身.密钥草稿,
                'placeholder':占位,
                'aria-label':中文['keyInput'],
                'aria-invalid':密钥错 is not None,
                'aria-describedby':None if 凭据注 is None else str(属性.get('provider'))+'-credential-hint',
                'required':属性.get('credentialRequired') is True,
                'autoFocus':属性.get('autoFocusCredential') is True,
                'disabled':禁用,
                'focusKey':'provider-'+str(属性.get('provider'))+'-key',
                'onChange':改密钥,
            }))
            if 凭据注 is not None:
                if 全缺:
                    注类='notice'
                elif 检测引用 is None:
                    注类='advancedHint'
                else:
                    注类='savedNotice'
                注=建(文档,'p',注类)
                注.id=str(属性.get('provider'))+'-credential-hint'
                注.textContent=凭据注
                行.appendChild(注)
            if 密钥错 is not None:
                错=建(文档,'p','error')
                错.textContent=中文[密钥错]
                行.appendChild(错)
            自身.根.appendChild(行)
        if 属性.get('credentialOnly') is True:
            return
        折=建(文档,'details','customized')
        要=建(文档,'summary','customizedSummary')
        要.textContent=中文['customized']
        折.appendChild(要)
        体=建(文档,'div','customizedBody')
        if 拥有身份:
            行=建(文档,'div','field')
            标=建(文档,'span','fieldLabel')
            标.textContent=中文['customDisplayName']
            行.appendChild(标)
            框=建(文档,'input','input')
            框.type='text'
            现名=自身.字符串于(自身.草稿,'displayName')
            框.value=现名 if 现名 is not None else ''
            下层=模式['取路径'](命名空间.get('base'),路径)
            占=自身.字符串于(下层,'displayName')
            框.placeholder=占 if 占 is not None else str(属性.get('provider'))
            框.setAttribute('aria-label',中文['customDisplayName'])
            框.disabled=禁用
            框.setAttribute('data-dsh-focus','provider-'+str(属性.get('provider'))+'-name')
            def 改名(事件):
                '写入显示名'
                自身.设字段('displayName',事件.target.value)
                自身.渲染()
            框.addEventListener('input',改名)
            行.appendChild(框)
            体.appendChild(行)
        行=建(文档,'div','field')
        标=建(文档,'span','fieldLabel')
        标.textContent=中文['baseUrl']
        行.appendChild(标)
        框=建(文档,'input','input')
        框.type='text'
        现址=自身.字符串于(自身.草稿,'baseURL')
        框.value=现址 if 现址 is not None else ''
        if 族=='deepseek':
            框.placeholder=中文['deepSeekBaseUrl']
        elif 基址 is None:
            if len(端点环境)>0:
                框.placeholder=中文['baseUrlConfigured']
            else:
                框.placeholder=中文['baseUrlDefault']
        else:
            框.placeholder=中文['baseUrlPlaceholder'].replace('{url}',基址)
        if 端点注 is not None:
            框.setAttribute('aria-describedby',str(属性.get('provider'))+'-endpoint-hint')
        框.setAttribute('aria-label',中文['baseUrl'])
        框.disabled=禁用
        框.setAttribute('data-dsh-focus','provider-'+str(属性.get('provider'))+'-base')
        def 改址(事件):
            '空串清掉地址'
            文=事件.target.value
            自身.设字段('baseURL',None if 文=='' else 文)
            自身.渲染()
        框.addEventListener('input',改址)
        行.appendChild(框)
        if 端点注 is not None:
            注=建(文档,'span','advancedHint')
            注.id=str(属性.get('provider'))+'-endpoint-hint'
            注.textContent=端点注
            行.appendChild(注)
        体.appendChild(行)
        探询协议=自身.字符串于(自身.草稿,'api')
        if 探询协议 is None:
            探询协议=自身.字符串于(回退,'api')
        if 拥有身份:
            行=建(文档,'div','field')
            标=建(文档,'span','fieldLabel')
            标.textContent=中文['customApi']
            行.appendChild(标)
            选=建(文档,'select','input selectInput')
            选.value=探询协议 if 探询协议 is not None else ''
            选.setAttribute('aria-label',中文['customApi'])
            选.disabled=禁用
            if 探询协议 is None:
                空项=文档.createElement('option')
                空项.value=''
                空项.textContent=中文['customApiUnset']
                选.appendChild(空项)
            for 候选 in 协议选项(命名空间,模式):
                项=文档.createElement('option')
                项.value=候选
                项.textContent=协议标注(候选)
                选.appendChild(项)
            def 改协议(事件):
                '写入协议'
                自身.设字段('api',事件.target.value)
                自身.渲染()
            选.addEventListener('change',改协议)
            行.appendChild(选)
            体.appendChild(行)
        def 改模型(下一):
            '整份模型数组写入草稿'
            自身.草稿=模式['设路径'](自身.草稿,['models'],下一)
            自身.渲染()
        def 重置模型():
            '拿掉用户层的模型数组'
            自身.草稿=模式['删路径'](自身.草稿,['models'])
            自身.渲染()
        目录属性={
            'window':窗口,
            'models':模型行,
            'overridden':已覆盖,
            'disabled':禁用,
            'onChange':改模型,
            'onReset':重置模型,
        }
        if 族=='deepseek':
            if isinstance(默认窗,(int,float)) and isinstance(默认窗,bool) is False:
                目录属性['defaultContextWindow']=默认窗
            else:
                目录属性['defaultContextWindow']=None
            if isinstance(默认上限,(int,float)) and isinstance(默认上限,bool) is False:
                目录属性['defaultMaxTokens']=默认上限
            else:
                目录属性['defaultMaxTokens']=None
            if 自身.目录件 is None or 自身.目录种类!='deepseek':
                自身.目录件=DeepSeek模型编辑器(目录属性)
                自身.目录种类='deepseek'
            else:
                自身.目录件.更新(目录属性)
                自身.目录件.渲染()
        else:
            探询基址=自身.字符串于(自身.草稿,'baseURL')
            if 探询基址 is None:
                探询基址=自身.字符串于(回退,'baseURL')
            密钥值=自身.密钥草稿.strip()
            探询={
                'settingsNs':名字,
                'provider':属性.get('provider'),
            }
            if 探询基址 is not None:
                探询['baseURL']=探询基址
            if 探询协议 is not None:
                探询['api']=探询协议
            if len(密钥值)>0:
                探询['apiKey']=密钥值
            挡=密钥失败(自身.密钥草稿)
            def 列表忙变(忙):
                '端点探询在飞'
                自身.列表忙=忙 is True
                自身.通知忙()
            目录属性['catalogProvider']=None if 属性.get('declared') is True else 属性.get('provider')
            目录属性['reasoningLevels']=推理档位选项(命名空间,模式) if 属性.get('declared') is True else []
            目录属性['defaultInput']=默认输入 if isinstance(默认输入,list) else None
            目录属性['probe']=探询
            目录属性['probeBlocked']=挡
            目录属性['operations']=属性.get('operations')
            目录属性['onBusyChange']=列表忙变
            if 自身.目录件 is None or 自身.目录种类!='pi-ai':
                自身.目录件=模型列表编辑器(目录属性)
                自身.目录种类='pi-ai'
            else:
                自身.目录件.更新(目录属性)
                自身.目录件.渲染()
        挂上(体,自身.目录件)
        折.appendChild(体)
        自身.根.appendChild(折)
