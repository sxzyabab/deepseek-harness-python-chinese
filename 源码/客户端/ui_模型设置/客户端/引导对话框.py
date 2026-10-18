from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,挂上
from .文案 import 中文
from .存储 import 提供方可用
from .提供方编辑器 import 提供方编辑器
from .引导模态 import 引导模态
from .编辑器页脚 import 清空子

__all__=['官方引导对话框']

样式模块='官方引导'
样式标识='官方引导样式'

def 确保样式(文档):
    '官方引导样式按文档只插一次'
    注入模块样式文件(
        文档,
        样式标识,
        os.path.join(os.path.dirname(__file__),'官方引导.module.css'),
        样式模块,
    )

def 建(文档,标签,类名=None):
    '带官方引导类名的节点'
    确保样式(文档)
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
    节点.setAttribute('data-dsh-css',样式模块)
    return 节点

class 官方引导对话框:
    '还没有任何可用提供方时，请用户配置官方 DeepSeek 密钥'
    def __init__(自身,属性):
        '显式打开时直接进入密钥。否则先留登录槽'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.用密钥=属性.get('explicit') is True
        自身.编辑器=None
        自身.模态=None
        自身.根=None
        自身.绘制中=False
        自身.待重画=False
        自身.已订=False
        自身.退订=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '按就绪度决定显示密钥编辑器、登录槽，或直接完成'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.画出()
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 画出(自身):
        '和模型页同一份拼合结果。任一可用提供方就结束'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.style.display='contents'
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            清空子(自身.根)
        钩=属性.get('useModels')
        控制器=属性.get('controller')
        if 钩 is None or 控制器 is None:
            return
        def 全量(快照):
            '整份模型页快照'
            return 快照
        状态=钩(全量)
        自动=属性.get('automatic') is True
        显式=属性.get('explicit') is True
        if (自动 or 显式) and 状态.get('status')=='idle':
            控制器.加载()
            状态=钩(全量)
        就绪=自身.就绪度(状态)
        if (自动 is not True and 显式 is not True) or 就绪['kind']=='adapter-absent' or (显式 is not True and 就绪['kind']=='provider-ready') or 就绪['kind']=='unavailable':
            完成=属性.get('complete')
            if 完成 is not None:
                完成()
        if 自动 is not True and 显式 is not True:
            自身.订上()
            return
        if 就绪['kind'] in ('loading','adapter-absent','unavailable'):
            自身.订上()
            return
        if 就绪['kind']=='provider-ready' and 显式 is not True:
            自身.订上()
            return
        if 就绪['kind'] not in ('provider-ready','credential-missing'):
            raise Exception('unexpected DeepSeek onboarding state')
        行=None
        for 候选 in 状态.get('rows') or []:
            条目=候选['entry']
            if 条目['provider']=='deepseek-official' and 条目['settingsNs']=='llm-deepseek' and len(条目['settingsPath'])==0:
                行=候选
                break
        空间=状态.get('namespaces')
        if isinstance(空间,dict) is False:
            空间={}
        命名空间=空间.get('llm-deepseek')
        if 行 is None or 命名空间 is None:
            自身.订上()
            return
        def 结束凭据(已变):
            '没保存就完成。保存了就重拉拼合结果'
            if 已变 is not True:
                完成=属性.get('complete')
                if 完成 is not None:
                    完成()
                return
            控制器.加载()
        说明=建(文档,'p','description')
        说明.textContent=中文['onboardingDescription']
        区=建(文档,'div','editor')
        def 点保存():
            '桌面埋点。没有采集器就跳过'
            跟踪=属性.get('track')
            if 跟踪 is not None:
                跟踪('api_key_save_click',{})
        编辑属性={
            'window':窗口,
            'provider':行['entry']['provider'],
            'displayName':行['entry']['displayName'],
            'namespace':命名空间,
            'schema':属性.get('schema'),
            'settingsPath':行['entry']['settingsPath'],
            'operations':属性.get('operations'),
            'readOnly':False,
            'hideTitle':True,
            'credentialOnly':True,
            'onSubmitCredential':点保存,
            'credentialRequired':True,
            'autoFocusCredential':True,
            'cancelLabelKey':'onboardingLater',
            'submitLabelKey':'onboardingSave',
            'submitBusyLabelKey':'onboardingSaving',
            'onClose':结束凭据,
        }
        if 自身.编辑器 is None:
            自身.编辑器=提供方编辑器(编辑属性)
        else:
            自身.编辑器.更新(编辑属性)
            自身.编辑器.渲染()
        挂上(区,自身.编辑器)
        子=[说明,区]
        模态属性={
            'window':窗口,
            'title':中文['onboardingTitle'],
            'children':子,
        }
        if 自身.模态 is None:
            自身.模态=引导模态(模态属性)
        else:
            自身.模态.更新(模态属性)
            自身.模态.渲染()
        if 自身.用密钥:
            挂上(自身.根,自身.模态)
        else:
            def 改用密钥():
                '登录槽选择改用密钥'
                自身.用密钥=True
                自身.渲染()
            槽=属性.get('renderSlot')
            if 槽 is not None:
                挂上(自身.根,槽(
                    'settings.models.sign-in',
                    {'complete':属性.get('complete'),'useApiKey':改用密钥},
                    {'fallback':自身.模态},
                ))
            else:
                挂上(自身.根,自身.模态)
        自身.订上()

    def 就绪度(自身,状态):
        '任一可用提供方即结束。否则只看官方 DeepSeek 路由能不能填密钥'
        if 状态.get('status') in ('idle','loading') and len(状态.get('rows') or [])==0:
            return {'kind':'loading'}
        if 状态.get('status')=='error':
            return {'kind':'unavailable','reason':'load-failed'}
        有可用=False
        for 行 in 状态.get('rows') or []:
            if 提供方可用(行):
                有可用=True
                break
        if 有可用:
            return {'kind':'provider-ready'}
        行=None
        for 候选 in 状态.get('rows') or []:
            条目=候选['entry']
            if 条目['provider']=='deepseek-official' and 条目['settingsNs']=='llm-deepseek' and len(条目['settingsPath'])==0:
                行=候选
                break
        if 行 is None:
            return {'kind':'adapter-absent'}
        if 行['entry'].get('active') is not True:
            return {'kind':'unavailable','reason':'provider-inactive'}
        if 状态.get('credentialError') is not None or 行.get('credential') is None:
            return {'kind':'unavailable','reason':'credentials-unavailable'}
        if 状态.get('writable') is not True:
            return {'kind':'unavailable','reason':'settings-read-only'}
        凭据=行.get('credential')
        if isinstance(凭据,dict) is False or 凭据.get('writable') is not True:
            return {'kind':'unavailable','reason':'credential-read-only'}
        return {'kind':'credential-missing'}

    def 订上(自身):
        '模型页快照变了就重画'
        if 自身.已订:
            return
        钩=自身.属性.get('useModels')
        订=getattr(钩,'_subscribe',None) if 钩 is not None else None
        if callable(订) is not True:
            return
        def 变更():
            '绘制中只记一笔'
            if 自身.绘制中:
                自身.待重画=True
                return
            if 自身.根 is None or 自身.根.parentNode is None:
                if 自身.退订 is not None:
                    退=自身.退订
                    自身.退订=None
                    自身.已订=False
                    退()
                return
            自身.渲染()
        自身.退订=订(变更)
        自身.已订=True
