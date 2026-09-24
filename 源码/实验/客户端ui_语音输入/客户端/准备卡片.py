from time import time as 墙钟

__all__=['准备卡片','语音准备工作']

def 读就绪(属性):
    """注入面 hooks.speechReadiness。"""
    钩=属性.get('hooks') or {}
    存储=钩.get('speechReadiness')
    if 存储 is not None:
        return 存储.getSnapshot()
    取=属性.get('useSpeechReadiness')
    if 取 is not None:
        def 全量(快照):
            """整份就绪快照。"""
            return 快照
        return 取(全量)
    return {'catalog':None,'connected':False,'error':None}

def 填(翻译,键,表=None):
    """词典插值。"""
    文=翻译(键)
    if 表 is None:
        return 文
    return 文.format(**表)

def 准备语气(态):
    """步骤点颜色。"""
    阶段=态.get('phase')
    if 阶段 in ('ready','standby'):
        return 'done'
    if 阶段=='failed':
        return 'error'
    if 阶段 in ('unprepared','cancelled'):
        return 'idle'
    return 'ongoing'

def 字节文案(态,翻译):
    """下载字节，不是安装百分比。"""
    完成=态['completedBytes']/1000000
    总量=态.get('totalBytes')
    if 总量 is None:
        return 填(翻译,'downloadUnknown',{'completed':f'{完成:.1f}'})
    百分=int(态['completedBytes']/总量*100)
    return 填(翻译,'downloadBytes',{
        'completed':f'{完成:.1f}',
        'total':f'{总量/1000000:.1f}',
        'percent':str(百分),
    })

def 失败视图(态,翻译):
    """本地下载失败分类。"""
    失败=态.get('download')
    if 失败 is None:
        return {
            'type':'preparation-error',
            'text':填(翻译,'preparationFailed',{'message':态.get('message','')}),
        }
    原因=失败['reason']
    状态码=失败.get('status')
    return {
        'type':'download-failure',
        'message':填(翻译,'download.'+原因,{
            'resource':失败['resource'],
            'status':'' if 状态码 is None else str(状态码),
        }),
        'advice':翻译('downloadAdvice.'+原因),
        'source':填(翻译,'downloadSource',{'source':失败['source']}),
        'code':None if 失败.get('code') is None else 填(翻译,'downloadCode',{'code':失败['code']}),
    }

class 准备卡片:
    """单个识别器的资源就绪与显式准备。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性
        自身.已展开=False
        自身.错误=''
        自身.源=''
        自身.提交中=False

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 切展开(自身):
        """展开或收起步骤。"""
        自身.已展开=not 自身.已展开

    def 改源(自身,值):
        """本次任务的下载源。"""
        自身.源=值

    def 执行(自身,动作):
        """串行跑一项。"""
        自身.错误=''
        自身.提交中=True
        try:
            动作()
        except Exception as 失败:
            自身.错误=str(失败)
        自身.提交中=False

    def 开始准备(自身):
        """按所选源启动或加入 Host 准备。"""
        提供方=自身.属性['provider']
        选=自身.所选源()
        if 选=='':
            def 无源():
                """沿用提供方策略。"""
                自身.属性['prepare'](提供方['id'])
            自身.执行(无源)
        else:
            def 有源():
                """只走指定源。"""
                自身.属性['prepare'](提供方['id'],{'downloadSource':选})
            自身.执行(有源)

    def 取消准备(自身):
        """显式取消。"""
        提供方=自身.属性['provider']
        def 取消():
            """交给注入面。"""
            自身.属性['cancelPreparation'](提供方['id'])
        自身.执行(取消)

    def 所选源(自身):
        """合法源或单源默认。"""
        源表=自身.属性['provider'].get('downloadSources') or []
        if 自身.源 in 源表:
            return 自身.源
        if len(源表)==1:
            return 源表[0]
        return ''

    def 渲染(自身):
        """估算、步骤与动作。"""
        翻译=自身.属性['t']
        提供方=自身.属性['provider']
        已连接=bool(自身.属性.get('connected'))
        态=提供方.get('preparation') or {'phase':'unprepared'}
        源表=提供方.get('downloadSources') or []
        选=自身.所选源()
        可准备=态.get('phase') in ('unprepared','cancelled','failed')
        步骤表=态.get('steps') or []
        当前=None
        for 步 in 步骤表:
            if 步.get('status') in ('running','failed','cancelled'):
                当前=步
                break
        进行中=准备语气(态)=='ongoing'
        起步=None if 当前 is None else 当前.get('startedAt')
        if 起步 is None and 'startedAt' in 态:
            起步=态['startedAt']
        现在=int(墙钟()*1000)
        if 态.get('phase')=='downloading':
            度量=字节文案(态,翻译)
        elif 进行中 and 起步 is not None:
            秒=max(0,int((现在-起步)/1000))
            度量=填(翻译,'elapsed',{'seconds':str(秒)})
        else:
            度量=''
        if not 已连接:
            摘要=翻译('reconnecting')
        elif 进行中 and 当前 is not None:
            摘要=填(翻译,'step.'+当前['kind'],{'name':提供方['name']})
        elif 态.get('phase')=='downloading':
            摘要=翻译('short.downloading')
        elif 态.get('phase')=='failed':
            摘要=翻译('short.failed')
        elif 态.get('phase')=='ready' and 提供方.get('location')=='cloud':
            摘要=翻译('cloudReady')
        else:
            摘要=填(翻译,'preparation.'+态.get('phase','unprepared'),{'name':提供方['name']})
        估算=None
        估=提供方.get('setupEstimate')
        if 态.get('phase')=='unprepared' and 提供方.get('location')=='host-local' and 估 is not None:
            估算={
                'local':翻译('setup.local'),
                'disk':翻译('setup.disk'),
                'diskValue':填(翻译,'setup.diskValue',{'gb':str(估['recommendedDiskBytes']/1000000000)}),
                'memory':翻译('setup.memory'),
                'memoryValue':填(翻译,'setup.memoryValue',{'gb':str(估['expectedMemoryBytes']/1000000000)}),
                'time':翻译('setup.time'),
                'timeValue':填(翻译,'setup.timeValue',{
                    'min':str(估['minimumMinutes']),
                    'max':str(估['maximumMinutes']),
                }),
                'note':翻译('setup.estimateNote'),
            }
        行=[]
        for 步 in 步骤表:
            点='idle'
            if 步.get('status')=='complete':
                点='done'
            elif 步.get('status')=='running':
                点='ongoing'
            elif 步.get('status')=='failed':
                点='error'
            行.append({
                'kind':步['kind'],
                'status':步['status'],
                'tone':点,
                'label':填(翻译,'step.'+步['kind'],{'name':提供方['name']}),
                'statusLabel':翻译('stepStatus.'+步['status']),
                'running':步.get('status')=='running',
                'resource':态.get('resource') if 态.get('phase')=='downloading' else None,
            })
        选项=[]
        for 源 in 源表:
            if 源=='https://huggingface.co':
                名=翻译('sourceHuggingFace')
            elif 源=='https://hf-mirror.com':
                名=翻译('sourceMirror')
            else:
                名=源
            选项.append({'value':源,'label':名})
        失败=失败视图(态,翻译) if 态.get('phase')=='failed' else None
        准备文=翻译('prepare' if 态.get('phase')=='unprepared' else 'retryPrepare')
        return {
            'type':'preparation-card',
            'cssModule':'语音输入.module.css',
            'providerId':提供方['id'],
            'name':提供方['name'],
            'estimate':估算,
            'expanded':自身.已展开,
            'expandable':len(步骤表)>0,
            'summary':翻译('preparationSteps') if 自身.已展开 else 摘要,
            'tone':准备语气(态),
            'metric':度量,
            'progress':态 if 态.get('phase')=='downloading' and 态.get('totalBytes') is not None else None,
            'steps':行,
            'failure':失败,
            'canPrepare':可准备,
            'sources':选项,
            'selectedSource':选,
            'sourceHelp':翻译('sourceAutoHelp' if 选=='' else 'sourceManualHelp'),
            'sourceChoice':翻译('sourceChoice'),
            'sourceAuto':翻译('sourceAuto'),
            'connected':已连接,
            'submitting':自身.提交中,
            'prepareLabel':准备文,
            'cancelLabel':翻译('cancelPrepare'),
            'preparing':进行中,
            'cancelling':态.get('phase')=='cancelling',
            'waking':态.get('phase')=='waking',
            'error':None if not 自身.错误 else 填(翻译,'failed',{'message':自身.错误}),
            'onToggle':自身.切展开,
            'onSource':自身.改源,
            'onPrepare':自身.开始准备,
            'onCancel':自身.取消准备,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 语音准备工作:
    """识别偏好与准备卡片，插件详情与设置共用。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性
        自身.保存中=False
        自身.错误=''
        自身.卡片表={}

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性

    def 配置(自身,补丁):
        """持久化偏好。"""
        自身.保存中=True
        自身.错误=''
        try:
            自身.属性['configure'](补丁)
        except Exception as 失败:
            自身.错误=str(失败)
        自身.保存中=False

    def 改提供方(自身,标识):
        """写 providerId。"""
        自身.配置({'providerId':标识})

    def 改语言(自身,语言):
        """写 language。"""
        自身.配置({'language':语言})

    def 卡片(自身,提供方,已连接):
        """按 id 复用准备卡片。"""
        标识=提供方['id']
        面={
            'provider':提供方,
            'connected':已连接,
            'prepare':自身.属性['prepare'],
            'cancelPreparation':自身.属性['cancelPreparation'],
            't':自身.属性['t'],
        }
        if 标识 not in 自身.卡片表:
            自身.卡片表[标识]=准备卡片(面)
        return 自身.卡片表[标识](面)

    def 渲染(自身):
        """偏好选择器与各提供方卡片。"""
        翻译=自身.属性['t']
        就绪=读就绪(自身.属性)
        目录=就绪.get('catalog')
        语言名={
            'auto':翻译('auto'),
            'zh':翻译('zh'),
            'en':翻译('en'),
            'yue':翻译('yue'),
            'ja':翻译('ja'),
            'ko':翻译('ko'),
        }
        选中=None
        提供方选项=[]
        语言选项=[]
        卡片=[]
        if 目录 is not None:
            选=目录.get('selection') or {}
            for 项 in 目录.get('providers') or []:
                提供方选项.append({'id':项['id'],'name':项['name']})
                if 项.get('id')==选.get('providerId'):
                    选中=项
                卡片.append(自身.卡片(项,bool(就绪.get('connected'))))
            if 选中 is not None:
                for 语言 in 选中.get('languages') or []:
                    语言选项.append({'id':语言,'name':语言名.get(语言,语言)})
        位置='cloud' if 选中 is not None and 选中.get('location')=='cloud' else 'local'
        return {
            'type':'voice-preparation',
            'cssModule':'语音输入.module.css',
            'catalog':目录 is not None,
            'providerLabel':翻译('provider'),
            'languageLabel':翻译('language'),
            'providers':提供方选项,
            'languages':语言选项,
            'providerId':None if 目录 is None else (目录.get('selection') or {}).get('providerId'),
            'language':None if 目录 is None else (目录.get('selection') or {}).get('language'),
            'hint':翻译(位置),
            'connected':bool(就绪.get('connected')),
            'saving':自身.保存中,
            'error':None if not 自身.错误 else 填(翻译,'failed',{'message':自身.错误}),
            'loading':翻译('loading') if 目录 is None else None,
            'readinessError':None if not 就绪.get('error') else 填(翻译,'failed',{'message':就绪['error']}),
            'cards':卡片,
            'onProvider':自身.改提供方,
            'onLanguage':自身.改语言,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
