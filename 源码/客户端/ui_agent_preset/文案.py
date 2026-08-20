"""智能体预设设置行/芯片/分区词典。

对齐上游 `ui-agent-preset/src/client/locales.ts`。公开面仅中文名。
"""

__all__=['命名空间','中文','英文','出厂预设键','预设展示文案']#仅中文公开名

命名空间='settings.agentPreset'#词表命名空间

中文={#简体中文
    'title':'Agent 预设',#标题
    'description':'对此后新建的会话生效。运行中的会话保持它开始时的预设。',#说明
    'loading':'正在加载预设…',#加载
    'error':'无法加载 Agent 预设。',#错误
    'userTrust':'自定义',#自定义信任
    'seatHint':'即将开始的这个会话所用的 Agent 预设',#座位提示
    'headerHint':'本会话运行的 Agent 预设，开始时即固定',#页眉提示
    'nav':'Agent 预设',#导航
    'sectionIntro':'预设即一个会话的 Agent 所运行的插件组装 —— 它的工具、提示词与能力。复制一份既有预设改成自己的，或用「创造模式」让 Agent 帮你创建。',#导语
    'builtIn':'内置',#内置
    'setDefault':'设为默认',#设默认
    'view':'查看',#查看
    'presetStandardName':'标准模式',#标准名
    'presetStandardDescription':'功能完整的编码 Agent，支持文件编辑、Shell、文件与网页检索、Skills、计划、目标、子代理和工作流。',#标准述
    'presetCodeName':'PTC 模式',#代码名
    'presetCodeDescription':'具备标准模式的全部能力，并通过 Code Mode SDK 呈现工具，让模型用一个 TypeScript 程序组合多步操作。',#代码述
    'presetMinimalName':'极简模式',#极简名
    'presetMinimalDescription':'仅提供持久 bash 与 str_replace_editor 的双工具编码 Agent。',#极简述
    'presetCordisName':'创造模式',#创造名
    'presetCordisDescription':'用于创建自定义 Agent preset：具备标准模式的全部能力，并提供运行时检查、插件实验和 preset 创作指导。',#创造述
    'duplicate':'复制',#复制
    'duplicateUnavailable':'此部署未配置可写的预设目录',#不可复制
    'delete':'删除',#删除
    'presetId':'标识符',#标识符
    'presetIdPlaceholder':'my-agent',#占位
    'displayName':'名称',#显示名
    'displayNamePlaceholder':'选择器中显示的名字，缺省用标识符',#显示名占位
    'inUse':'当前使用',#使用中
    'builtInGroup':'内置',#内置组
    'customGroup':'自定义',#自定义组
    'noDescription':'暂无描述。',#无描述
    'brokenBadge':'加载失败',#失败徽章
    'brokenNoCopy':'预设加载失败，不能复制',#失败不可复制
    'copyOf':'复制自',#复制自
    'composition':'组装（agent.cordis.yml）',#组装
    'cancel':'取消',#取消
    'close':'关闭',#关闭
    'retry':'重试',#重试
    'copyTitle':'复制预设',#复制标题
    'copyIntro':'整个预设会在本机复制一份。标识符将成为目录名，事后无法更改；其余内容之后直接在预设自己的文件里编辑。',#复制导语
    'create':'创建',#创建
    'creating':'正在创建…',#创建中
    'creatorDraft':'用「创造模式」创作自定义预设',#创造起草
    'openLocation':'打开目录',#打开目录
    'showLocation':'查看路径',#查看路径
    'revealedPathLabel':'预设文件：',#路径标签
    'idRequired':'请填写标识符。',#必填
    'idInvalid':'只能使用小写字母、数字与连字符，且以字母或数字开头。',#非法
    'idTaken':'该标识符已被占用。',#占用
    'deleteTitle':'删除该预设？',#删除标题
    'deleteDescription':'预设目录将被删除。已在其上运行的会话不受影响；新会话将无法再选择它。',#删除说明
    'deleteConfirm':'删除',#确认删除
    'deleting':'正在删除…',#删除中
}#中文结束

英文={#英文（与上游键对齐）
    'title':'Agent preset','description':'Applies to sessions you start from now on. Running sessions keep the preset they began with.',
    'loading':'Loading presets…','error':'Could not load agent presets.','userTrust':'Custom',
    'seatHint':'Agent preset for the session you are about to start',
    'headerHint':'The agent preset this session runs, fixed when it started',
    'nav':'Agent presets',
    'sectionIntro':"A preset is the plugin composition one session's agent runs — its tools, prompt, and capabilities. Duplicate an existing one and make it yours, or let the agent draft one for you in Creator mode.",
    'builtIn':'Built-in','setDefault':'Set as default','view':'View',
    'presetStandardName':'Standard mode',
    'presetStandardDescription':'Full coding agent with file editing, shell, file and web search, skills, planning, goals, subagents, and workflows.',
    'presetCodeName':'Code mode',
    'presetCodeDescription':'All Standard mode capabilities, with tools exposed through the Code Mode SDK so the model can combine multi-step operations in one TypeScript program.',
    'presetMinimalName':'Minimal mode',
    'presetMinimalDescription':'Two-tool coding agent with persistent bash and str_replace_editor.',
    'presetCordisName':'Creator mode',
    'presetCordisDescription':'Built for creating custom agent presets, with all Standard mode capabilities plus runtime inspection, plugin experiments, and preset-authoring guidance.',
    'duplicate':'Duplicate','duplicateUnavailable':'This deployment has no writable preset directory','delete':'Delete',
    'presetId':'Identifier','presetIdPlaceholder':'my-agent','displayName':'Name',
    'displayNamePlaceholder':'Shown in the picker; defaults to the identifier',
    'inUse':'In use','builtInGroup':'Built-in','customGroup':'Custom','noDescription':'No description.',
    'brokenBadge':'Failed to load','brokenNoCopy':'A preset that failed to load cannot be duplicated','copyOf':'Copied from',
    'composition':'Composition (agent.cordis.yml)','cancel':'Cancel','close':'Close','retry':'Retry',
    'copyTitle':'Duplicate preset',
    'copyIntro':"The whole preset is copied on this machine. The identifier becomes its directory name and cannot be changed later; everything else is edited in the preset's own files.",
    'create':'Create','creating':'Creating…','creatorDraft':'Draft a custom preset with Creator mode',
    'openLocation':'Open folder','showLocation':'Show location','revealedPathLabel':'Preset files:',
    'idRequired':'Give the preset an identifier.',
    'idInvalid':'Use lowercase letters, digits, and hyphens, starting with a letter or digit.',
    'idTaken':'A preset with this identifier already exists.',
    'deleteTitle':'Delete this preset?',
    'deleteDescription':'The preset directory is deleted. Sessions already running on it keep working; new sessions cannot select it.',
    'deleteConfirm':'Delete','deleting':'Deleting…',
}#英文结束

出厂预设键={#出厂 id → 语言键
    'standard':{'name':'presetStandardName','description':'presetStandardDescription'},#标准
    'code':{'name':'presetCodeName','description':'presetCodeDescription'},#代码
    'minimal':{'name':'presetMinimalName','description':'presetMinimalDescription'},#极简
    'cordis':{'name':'presetCordisName','description':'presetCordisDescription'},#创造
}#结束

def 预设展示文案(预设,翻译):#解析展示文案
    """出厂预设走语言包；用户自写用元数据。"""
    信任=预设.get('trust') if isinstance(预设,dict) else getattr(预设,'trust',None)#信任
    标识=预设.get('id') if isinstance(预设,dict) else getattr(预设,'id',None)#id
    键=出厂预设键.get(标识) if 信任=='system' else None#语言键
    if 键 is not None:#出厂
        return {'name':翻译(键['name']),'description':翻译(键['description'])}#本地化
    名=预设.get('name') if isinstance(预设,dict) else getattr(预设,'name',None)#名
    述=预设.get('description') if isinstance(预设,dict) else getattr(预设,'description',None)#述
    出={'name':名 if 名 is not None else 标识}#回退 id
    if 述 is not None:#有述
        出['description']=述#带上
    return 出#回退
