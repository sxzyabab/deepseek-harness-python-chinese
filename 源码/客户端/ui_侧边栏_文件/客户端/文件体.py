import re#自然排序分段与地址编码
from urllib.parse import quote as 百分号编码
from .面 import 子路径#子路径键

__all__=[#仅中文公开名
    '排序条目','失败行','工作区标题','文件资源地址','文件体','样式表',
]

_数字段=re.compile(r'([0-9]+)',re.ASCII)#自然排序数字段
_文件地址前缀='dsh-resource://file/'#文件资源地址前缀

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
'''#样式表结束


def _自然键(名):
    """大小写不敏感的自然名序键，使 file2 排在 file10 前。"""
    段列表=[]#键段
    for 部 in _数字段.split(名):#切分
        if 部=='':#空
            continue#跳过
        if 部.isdigit():#数字
            段列表.append((1,int(部)))#数值段
        else:#文字
            段列表.append((0,部.casefold()))#文字段
    return 段列表#键


def 排序条目(条目列表):
    """展示序：目录在前，其余其后；各组按自然名序。端点序是列举事实，本序是读者的。"""
    return sorted(条目列表,key=lambda 项:(0 if 项['type']=='directory' else 1,_自然键(项['name'])))#排序


def 失败行(翻译,失败):
    """用目录口吻说明为何列不出。失败为跨包 RemoteFailure dict。"""
    码=失败['code'] if 'code' in 失败 else None#错误码
    if 码=='workspace-file/not-found':#不存在
        return 翻译('error.notFound')#文案
    if 码=='workspace-file/outside-workspace':#工作区外
        return 翻译('error.outsideWorkspace')#文案
    if 码=='workspace-file/not-directory':#非目录
        return 翻译('error.notDirectory')#文案
    消息=失败['message'] if 'message' in 失败 else ''#载体消息
    return 翻译('error.unavailable',{'message':消息})#透传


def 工作区标题(路径):
    """取工作区路径末段作展示；仅分隔符则空串。"""
    修剪=路径.rstrip('/\\')#去尾分隔
    斜=修剪.rfind('/')#末 /
    反=修剪.rfind('\\')#末 \\
    分=斜 if 斜>反 else 反#更靠后的分隔
    return 修剪[分+1:]#末段


def _编码段(段):
    """编码一段 id 或路径，保留 `:` 字面量。"""
    return 百分号编码(段,safe=':')


def _编码路径(路径):
    """按 `/` 分段编码。"""
    return '/'.join(_编码段(段) for 段 in 路径.split('/'))#路径编码


def _会话文件地址(会话标识,路径):
    """会话作用域 `dsh-resource://file/session/…` 地址。"""
    归一=路径.replace('\\','/')#归一
    while 归一.startswith('./'):#去前导 ./
        归一=归一[2:]#削
    return _文件地址前缀+'session/'+_编码段(会话标识)+'/'+_编码路径(归一)#地址


def _绝对文件地址(路径):
    """绝对作用域 `dsh-resource://file/absolute/…` 地址。"""
    归一=路径.replace('\\','/')#归一
    是UNC=归一.startswith('//')#UNC
    绝对=归一.lstrip('/')#去前导 /
    return _文件地址前缀+'absolute/'+('/' if 是UNC else '')+_编码路径(绝对)#地址


def _是否绝对工作区路径(路径):
    """POSIX `/` 或 Windows 盘符 / UNC。"""
    if 路径.startswith('/'):#POSIX
        return True#绝对
    if len(路径)>=3 and 路径[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' and 路径[1]==':' and 路径[2] in '/\\':#盘符
        return True#绝对
    if 路径.startswith('\\\\'):#UNC
        return True#绝对
    return False#相对


def 文件资源地址(会话标识,工作目录,路径):
    """按调用方手里的路径选会话作用域地址：相对或落在 cwd 内的绝对 → 相对段；根外绝对仍写入 session 作用域。

    内嵌自 util/workspace-path，以免扩大移植面。
    """
    归一=路径.replace('\\','/')#归一
    if not _是否绝对工作区路径(归一):#相对
        return _会话文件地址(会话标识,归一)#session
    根='' if 工作目录 is None else 工作目录.replace('\\','/').rstrip('/')#根
    if 根!='' and 归一==根:#恰为根
        return _会话文件地址(会话标识,'')#根相对空
    if 根!='' and 归一.startswith(根+'/'):#根下
        return _会话文件地址(会话标识,归一[len(根)+1:])#相对后缀
    return _会话文件地址(会话标识,归一)#根外仍会话作用域绝对路径


class 文件体:#文件树正文视图模型
    """会话工作区根与读者已打开的下级；无 DOM，产出结构树。"""

    def __init__(自身,属性):
        """记下 tab、存储、注入面与文案。"""
        自身.属性=属性#合成 props

    def 更新(自身,属性):
        """props 变更。"""
        自身.属性=属性#最新

    def _读工作目录(自身):
        """当前会话 cwd；无会话或无键则为 None。"""
        属性=自身.属性#props
        会话标识=属性['sessionId'] if 'sessionId' in 属性 else None#会话
        读会话=属性['useSessions'] if 'useSessions' in 属性 else None#钩
        if 读会话 is not None:#有钩
            def 取工作目录(会话表):
                """由会话表取 cwd。"""
                按标识=会话表['byId'] if 'byId' in 会话表 else None#摘要表
                if 按标识 is None or 会话标识 not in 按标识:#缺席
                    return None#无
                会话=按标识[会话标识]#摘要
                return 会话['cwd'] if 'cwd' in 会话 else None#cwd
            return 读会话(取工作目录)#派生
        return None#无钩

    def _读标签(自身):
        """当前 tab 记录。"""
        属性=自身.属性#props
        读标签=属性['useTabInfo'] if 'useTabInfo' in 属性 else None#钩
        if 读标签 is None:#无
            return None#无
        信息=读标签()#tab 信息
        return 信息['tab'] if 'tab' in 信息 else None#记录

    def _读树(自身,标签标识):
        """该 tab 的树状态；尚未播种则为 None。"""
        属性=自身.属性#props
        读存储=属性['useStore'] if 'useStore' in 属性 else None#钩
        if 读存储 is not None:#有钩
            def 取桶(状态):
                """按 tab 取桶。"""
                按标签=状态['byTab'] if 'byTab' in 状态 else None#分桶
                if 按标签 is None or 标签标识 not in 按标签:#缺席
                    return None#无
                return 按标签[标签标识]#树
            return 读存储(取桶)#派生
        存储=属性['store'] if 'store' in 属性 else None#句柄
        if 存储 is None:#无
            return None#无
        状态=存储.getSnapshot()#快照
        按标签=状态['byTab'] if 'byTab' in 状态 else None#分桶
        if 按标签 is None or 标签标识 not in 按标签:#缺席
            return None#无
        return 按标签[标签标识]#树

    def 确保已播种(自身):
        """无桶且有 cwd、信号未中止时调用 start；对齐挂载 effect。"""
        标签=自身._读标签()#tab
        if 标签 is None:#无
            return#停
        标签标识=标签['id']#id
        信号=标签['signal'] if 'signal' in 标签 else None#寿命
        树=自身._读树(标签标识)#已有？
        工作目录=自身._读工作目录()#cwd
        if 树 is not None or 工作目录 is None:#已有或无根
            return#停
        if 信号 is not None and 信号.is_set():#已中止不得再播
            return#停
        启动=自身.属性['start'] if 'start' in 自身.属性 else None#面
        if 启动 is None:#无
            return#停
        启动(标签标识,工作目录,信号)#播种并列根

    def _渲染层级(自身,路径,树,翻译):
        """一级目录的行：加载中 / 失败 / 条目。"""
        层级表=树['levels']#层级
        层级=层级表[路径] if 路径 in 层级表 else None#该级
        if 层级 is None or 层级['kind']=='loading':#未问或加载中
            return [{'type':'li','class':'note','data-files-row':'loading','children':[翻译('loading')]}]#加载行
        if 层级['kind']=='failed':#失败
            失败=层级['failure']#跨包 dict
            return [{#失败行
                'type':'li','class':'note','data-files-row':'failed',
                'data-files-code':失败['code'] if 'code' in 失败 else None,
                'children':[失败行(翻译,失败)],
            }]#失败结束
        级=层级['level']#就绪内容
        条目列表=排序条目(级['entries'] if 'entries' in 级 and 级['entries'] is not None else [])#排序
        子=[]#行
        if len(条目列表)==0:#空
            子.append({'type':'li','class':'note','data-files-row':'empty','children':[翻译('empty')]})#空态
        for 条目 in 条目列表:#逐条
            子.append(自身._渲染条目(路径,条目,树,翻译))#条目
        if 'truncated' in 级 and 级['truncated'] is True:#截断
            子.append({'type':'li','class':'note','data-files-row':'truncated','children':[翻译('truncated')]})#截断提示
        return 子#子行

    def _渲染条目(自身,父,条目,树,翻译):
        """一条目录/文件/其它。"""
        路径=子路径(父,条目['name'])#绝对键
        类型=条目['type']#种类
        if 类型=='directory':#目录
            展开=路径 in 树['expanded']#是否展开
            子=[#行按钮
                {'type':'button','class':'row','aria-expanded':展开,'onClick':('toggle',路径),'children':[
                    {'type':'IconFolderOpen16' if 展开 else 'IconFolderClose16','class':'icon'},
                    {'type':'span','class':'name','children':[条目['name']]},
                ]},
            ]#按钮结束
            if 展开:#展开则嵌套
                子.append({'type':'ul','class':'level','children':自身._渲染层级(路径,树,翻译)})#下级
            return {'type':'li','class':'item','data-files-entry':'directory','data-files-path':路径,'children':子}#目录项
        if 类型=='file':#文件
            return {#文件项
                'type':'li','class':'item','data-files-entry':'file','data-files-path':路径,'children':[
                    {'type':'button','class':'row','onClick':('open',路径),'children':[
                        {'type':'DocumentFileIcon','class':'fileIcon'},
                        {'type':'span','class':'name','children':[条目['name']]},
                    ]},
                ],
            }#文件结束
        return {#其它
            'type':'li','class':'item','data-files-entry':'other','data-files-path':路径,'children':[
                {'type':'span','class':'row other','aria-disabled':True,'title':翻译('entry.other'),'children':[
                    {'type':'span','class':'name','children':[条目['name']]},
                ]},
            ],
        }#其它结束

    def 处理点击(自身,动作,路径):
        """响应结构树上的 toggle / open / reload。"""
        标签=自身._读标签()#tab
        if 标签 is None:#无
            return#停
        标签标识=标签['id']#id
        信号=标签['signal'] if 'signal' in 标签 else None#寿命
        树=自身._读树(标签标识)#树
        属性=自身.属性#props
        if 动作=='reload':#重新读取
            if 树 is None:#无树
                return#停
            存储动作=属性['actions'] if 'actions' in 属性 else None#store 动作
            加载=属性['load'] if 'load' in 属性 else None#面
            if 存储动作 is not None:#有写口
                存储动作['reset'](标签标识)#清层级
            if 加载 is not None:#有加载
                for 展开路径 in 树['expanded']:#已展开
                    加载(标签标识,展开路径,信号)#再列
            return#已处理
        if 动作=='toggle':#展开/折叠
            切换=属性['toggle'] if 'toggle' in 属性 else None#面
            if 切换 is None or 树 is None:#无
                return#停
            已有=路径 in 树['levels']#是否已有状态
            切换(标签标识,路径,已有,信号)#切换
            return#已处理
        if 动作=='open':#打开文件
            if 树 is None:#无
                return#停
            标签动作=标签['actions'] if 'actions' in 标签 else None#tabActions
            if 标签动作 is None or 'openResource' not in 标签动作:#无
                return#停
            会话标识=属性['sessionId'] if 'sessionId' in 属性 else None#会话
            地址=文件资源地址(会话标识,树['root'],路径)#资源地址
            标签动作['openResource'](地址)#打开
            return#已处理

    def 渲染(自身):
        """产出正文结构树；无工作区或尚未播种时返回对应空态。"""
        自身.确保已播种()#播种
        属性=自身.属性#props
        翻译=属性['t']#文案
        工作目录=自身._读工作目录()#cwd
        if 工作目录 is None:#无工作区
            return {#空态
                'type':'div','class':'status','data-files-state':'no-workspace','children':[
                    {'type':'p','class':'statusLine','children':[翻译('noWorkspace')]},
                ],
            }#空态结束
        标签=自身._读标签()#tab
        if 标签 is None:#无标签
            return None#未就绪
        树=自身._读树(标签['id'])#树
        if 树 is None:#尚未播种完
            return None#空
        标题=工作区标题(树['root']) or 树['root']#页眉名
        return {#树态
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
        }#树结束
