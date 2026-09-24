import re
from urllib.parse import quote as 百分号编码
from .面 import 子路径

__all__=[
    '排序条目','失败行','工作区标题','文件资源地址','文件体','样式表',
]

#常量
_数字段=re.compile(r'([0-9]+)',re.ASCII)
_文件地址前缀='dsh-resource://file/'

样式表='''
.root{display:flex;flex:1 1 auto;flex-direction:column;min-height:0;overflow:auto;padding:4px 0 8px;color:var(--dsw-alias-label-primary);font-size:var(--dsh-content-font-size-secondary, 13px);line-height:1.5}
.header{display:flex;flex:0 0 auto;gap:6px;align-items:center;padding:4px 10px;color:var(--dsw-alias-label-secondary);font-weight:500}
.level{margin:0;padding:0;list-style:none}
.level .level{padding-left:14px}
.item{margin:0;padding:0}
.row{display:flex;gap:6px;align-items:center;width:100%;min-width:0;padding:3px 10px;color:inherit;font:inherit;text-align:left;background:transparent;border:0;border-radius:6px;cursor:pointer}
.row:hover{background:var(--dsw-alias-interactive-bg-hover)}
.icon{flex:0 0 auto;color:var(--dsw-alias-label-secondary)}
.fileIcon{flex:0 0 auto;width:14px;height:16px}
.name{min-width:0;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.other{color:var(--dsw-alias-label-tertiary);cursor:default}
.other:hover{background:transparent}
.note{margin:0;padding:3px 10px;color:var(--dsw-alias-label-tertiary);font-size:12px}
.status{display:flex;flex-direction:column;padding:12px 10px}
.statusLine{margin:0;color:var(--dsw-alias-label-secondary);font-size:var(--dsh-content-font-size-secondary, 13px);line-height:1.6}
.tool{display:inline-flex;flex:0 0 auto;align-items:center;justify-content:center;width:24px;height:24px;margin-left:auto;padding:0;color:var(--dsw-alias-label-secondary);background:transparent;border:0;border-radius:6px;cursor:pointer}
.tool:hover{background:var(--dsw-alias-interactive-bg-hover)}
'''

#工具
def _自然键(名):
    """大小写不敏感。数字段按数值比，使 file2 排在 file10 前。"""
    段列表=[]
    for 部 in _数字段.split(名):
        if 部=='':
            continue
        if 部.isdigit():
            段列表.append((1,int(部)))
        else:
            段列表.append((0,部.casefold()))
    return 段列表


def 排序条目(条目列表):
    """目录在前，其余在后；各组内部按自然名序。列举端点的顺序不采用。"""
    return sorted(条目列表,key=lambda 项:(0 if 项['type']=='directory' else 1,_自然键(项['name'])))


def 失败行(翻译,失败):
    """用目录口吻说明为何列不出。失败为跨包 RemoteFailure dict，码决定用哪句文案。"""
    码=失败['code'] if 'code' in 失败 else None
    if 码=='workspace-file/not-found':
        return 翻译('error.notFound')
    if 码=='workspace-file/outside-workspace':
        return 翻译('error.outsideWorkspace')
    if 码=='workspace-file/not-directory':
        return 翻译('error.notDirectory')
    消息=失败['message'] if 'message' in 失败 else ''
    return 翻译('error.unavailable',{'message':消息})


def 工作区标题(路径):
    """取路径末段。整段都是分隔符时返回空串，调用方再回退到完整路径。"""
    修剪=路径.rstrip('/\\')
    斜=修剪.rfind('/')
    反=修剪.rfind('\\')
    分=斜 if 斜>反 else 反
    return 修剪[分+1:]


def _编码段(段):
    """编码一段。`:` 保留字面量，盘符不会被百分号吃掉。"""
    return 百分号编码(段,safe=':')


def _编码路径(路径):
    """按 `/` 分段编码，分隔符本身不编码。"""
    return '/'.join(_编码段(段) for 段 in 路径.split('/'))


def _会话文件地址(会话标识,路径):
    """会话作用域地址。前导 `./` 削掉，否则会变成路径段。"""
    归一=路径.replace('\\','/')
    while 归一.startswith('./'):
        归一=归一[2:]
    return _文件地址前缀+'session/'+_编码段(会话标识)+'/'+_编码路径(归一)


def _绝对文件地址(路径):
    """绝对作用域地址。UNC 的双斜杠不能被 lstrip 吃掉。"""
    归一=路径.replace('\\','/')
    是UNC=归一.startswith('//')
    绝对=归一.lstrip('/')
    return _文件地址前缀+'absolute/'+('/' if 是UNC else '')+_编码路径(绝对)


def _是否绝对工作区路径(路径):
    """POSIX 根、Windows 盘符、UNC 算绝对。单写盘符没有分隔符不算。"""
    if 路径.startswith('/'):
        return True
    if len(路径)>=3 and 路径[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' and 路径[1]==':' and 路径[2] in '/\\':
        return True
    if 路径.startswith('\\\\'):
        return True
    return False


def 文件资源地址(会话标识,工作目录,路径):
    """相对路径，以及落在工作目录内的绝对路径，都写成会话作用域的相对段。工作目录之外的绝对路径仍进会话作用域，不改走绝对作用域。"""
    归一=路径.replace('\\','/')
    if not _是否绝对工作区路径(归一):
        return _会话文件地址(会话标识,归一)
    根='' if 工作目录 is None else 工作目录.replace('\\','/').rstrip('/')
    if 根!='' and 归一==根:
        return _会话文件地址(会话标识,'')
    if 根!='' and 归一.startswith(根+'/'):
        return _会话文件地址(会话标识,归一[len(根)+1:])
    return _会话文件地址(会话标识,归一)


#
class 文件体:
    """会话工作区根与已打开的下级。无 DOM，产出结构树。"""

    def __init__(自身,属性):
        """属性跨边界为 dict。"""
        自身.属性=属性

    def 更新(自身,属性):
        """替换整份属性，不合并。"""
        自身.属性=属性

    def _读工作目录(自身):
        """当前会话 cwd。无会话、无钩、摘要里没有该键，都是 None。"""
        属性=自身.属性
        会话标识=属性['sessionId'] if 'sessionId' in 属性 else None
        读会话=属性['useSessions'] if 'useSessions' in 属性 else None
        if 读会话 is not None:
            def 取工作目录(会话表):
                """由会话表取 cwd。缺席键不当成空串。"""
                按标识=会话表['byId'] if 'byId' in 会话表 else None
                if 按标识 is None or 会话标识 not in 按标识:
                    return None
                会话=按标识[会话标识]
                return 会话['cwd'] if 'cwd' in 会话 else None
            return 读会话(取工作目录)
        return None

    def _读标签(自身):
        """当前 tab 记录。无钩或记录里没有 tab 键则为 None。"""
        属性=自身.属性
        读标签=属性['useTabInfo'] if 'useTabInfo' in 属性 else None
        if 读标签 is None:
            return None
        信息=读标签()
        return 信息['tab'] if 'tab' in 信息 else None

    def _读树(自身,标签标识):
        """该 tab 的树。优先走钩子；没有钩子才读存储快照。尚未播种为 None。"""
        属性=自身.属性
        读存储=属性['useStore'] if 'useStore' in 属性 else None
        if 读存储 is not None:
            def 取桶(状态):
                """按 tab 取桶。"""
                按标签=状态['byTab'] if 'byTab' in 状态 else None
                if 按标签 is None or 标签标识 not in 按标签:
                    return None
                return 按标签[标签标识]
            return 读存储(取桶)
        存储=属性['store'] if 'store' in 属性 else None
        if 存储 is None:
            return None
        状态=存储.getSnapshot()
        按标签=状态['byTab'] if 'byTab' in 状态 else None
        if 按标签 is None or 标签标识 not in 按标签:
            return None
        return 按标签[标签标识]

    def 确保已播种(自身):
        """没有桶、有工作目录、信号未中止时才播种。已中止的标签不得再开请求。"""
        标签=自身._读标签()
        if 标签 is None:
            return
        标签标识=标签['id']
        信号=标签['signal'] if 'signal' in 标签 else None
        树=自身._读树(标签标识)
        工作目录=自身._读工作目录()
        if 树 is not None or 工作目录 is None:
            return
        if 信号 is not None and 信号.is_set():
            return
        启动=自身.属性['start'] if 'start' in 自身.属性 else None
        if 启动 is None:
            return
        启动(标签标识,工作目录,信号)

    def _渲染层级(自身,路径,树,翻译):
        """一级：未问过与加载中同一句；失败带错误码；空目录与截断是附加行。"""
        层级表=树['levels']
        层级=层级表[路径] if 路径 in 层级表 else None
        if 层级 is None or 层级['kind']=='loading':
            return [{'type':'li','class':'note','data-files-row':'loading','children':[翻译('loading')]}]
        if 层级['kind']=='failed':
            失败=层级['failure']
            return [{
                'type':'li','class':'note','data-files-row':'failed',
                'data-files-code':失败['code'] if 'code' in 失败 else None,
                'children':[失败行(翻译,失败)],
            }]
        级=层级['level']
        条目列表=排序条目(级['entries'] if 'entries' in 级 and 级['entries'] is not None else [])
        子=[]
        if len(条目列表)==0:
            子.append({'type':'li','class':'note','data-files-row':'empty','children':[翻译('empty')]})
        for 条目 in 条目列表:
            子.append(自身._渲染条目(路径,条目,树,翻译))
        if 'truncated' in 级 and 级['truncated'] is True:
            子.append({'type':'li','class':'note','data-files-row':'truncated','children':[翻译('truncated')]})
        return 子

    def _渲染条目(自身,父,条目,树,翻译):
        """目录可展开；文件点击打开；其它类型不可点，只给说明。"""
        路径=子路径(父,条目['name'])
        类型=条目['type']
        if 类型=='directory':
            展开=路径 in 树['expanded']
            子=[
                {'type':'button','class':'row','aria-expanded':展开,'onClick':('toggle',路径),'children':[
                    {'type':'IconFolderOpen16' if 展开 else 'IconFolderClose16','class':'icon'},
                    {'type':'span','class':'name','children':[条目['name']]},
                ]},
            ]
            if 展开:
                子.append({'type':'ul','class':'level','children':自身._渲染层级(路径,树,翻译)})
            return {'type':'li','class':'item','data-files-entry':'directory','data-files-path':路径,'children':子}
        if 类型=='file':
            return {
                'type':'li','class':'item','data-files-entry':'file','data-files-path':路径,'children':[
                    {'type':'button','class':'row','onClick':('open',路径),'children':[
                        {'type':'DocumentFileIcon','class':'fileIcon'},
                        {'type':'span','class':'name','children':[条目['name']]},
                    ]},
                ],
            }
        return {
            'type':'li','class':'item','data-files-entry':'other','data-files-path':路径,'children':[
                {'type':'span','class':'row other','aria-disabled':True,'title':翻译('entry.other'),'children':[
                    {'type':'span','class':'name','children':[条目['name']]},
                ]},
            ],
        }

    def 处理点击(自身,动作,路径):
        """reload 只清已加载级再按展开集重列，不收起。open 用树根而不是当前工作目录拼地址。"""
        标签=自身._读标签()
        if 标签 is None:
            return
        标签标识=标签['id']
        信号=标签['signal'] if 'signal' in 标签 else None
        树=自身._读树(标签标识)
        属性=自身.属性
        if 动作=='reload':
            if 树 is None:
                return
            存储动作=属性['actions'] if 'actions' in 属性 else None
            加载=属性['load'] if 'load' in 属性 else None
            if 存储动作 is not None:
                存储动作['reset'](标签标识)
            if 加载 is not None:
                for 展开路径 in 树['expanded']:
                    加载(标签标识,展开路径,信号)
            return
        if 动作=='toggle':
            切换=属性['toggle'] if 'toggle' in 属性 else None
            if 切换 is None or 树 is None:
                return
            已有=路径 in 树['levels']
            切换(标签标识,路径,已有,信号)
            return
        if 动作=='open':
            if 树 is None:
                return
            标签动作=标签['actions'] if 'actions' in 标签 else None
            if 标签动作 is None or 'openResource' not in 标签动作:
                return
            会话标识=属性['sessionId'] if 'sessionId' in 属性 else None
            地址=文件资源地址(会话标识,树['root'],路径)
            标签动作['openResource'](地址)
            return

    def 渲染(自身):
        """无工作目录给说明；标签或树还没有则什么都不画，避免先闪空态。"""
        自身.确保已播种()
        属性=自身.属性
        翻译=属性['t']
        工作目录=自身._读工作目录()
        if 工作目录 is None:
            return {
                'type':'div','class':'status','data-files-state':'no-workspace','children':[
                    {'type':'p','class':'statusLine','children':[翻译('noWorkspace')]},
                ],
            }
        标签=自身._读标签()
        if 标签 is None:
            return None
        树=自身._读树(标签['id'])
        if 树 is None:
            return None
        标题=工作区标题(树['root']) or 树['root']
        return {
            'type':'div','class':'root','data-files-state':'tree','data-files-root':树['root'],'children':[
                {'type':'div','class':'header','children':[
                    {'type':'IconFolderOpen16','class':'icon'},
                    {'type':'span','class':'name','children':[标题]},
                    {'type':'button','class':'tool','aria-label':翻译('reload'),'title':翻译('reload'),'data-files-reload':True,'onClick':('reload',None),'children':[
                        {'type':'IconRefreshOutline16'},
                    ]},
                ]},
                {'type':'ul','class':'level','children':自身._渲染层级(树['root'],树,翻译)},
            ],
        }
