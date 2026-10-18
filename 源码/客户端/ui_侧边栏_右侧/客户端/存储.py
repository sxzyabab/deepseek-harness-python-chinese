'会话表面。布局计算交给停靠套件，这里只记一条意图'
from ...存储 import 声明存储
from ...ui_停靠套件.引擎.序列 import 空历史,记录,后退一步,前进一步
from ...ui_停靠套件.引擎.操作 import 回放
from ...ui_停靠套件.引擎.初值 import 创建初始状态
from ...ui_停靠套件.引擎.树 import 取窗格,查找标签窗格,停靠窗格标识列表
from ...ui_停靠套件.引擎.规划 import (
    查找内容标签,
    查找窗格内容标签,
    活动停靠窗格标识,
    规划设展开,
    规划设模式,
    规划分窗格,
    规划打开内容,
    规划复制标签,
    规划安置标签,
    规划投放标签,
    规划浮出标签,
    规划收回浮窗,
    规划调整分割,
    规划落定,
)
from .约定.种子 import 向导种类,页面地址
from .持久化 import 读侧栏布局,写侧栏布局,清侧栏布局

__all__=['可关闭标签','独一停靠标签','创建表面','创建右侧侧栏存储']


def 计数铸造(起点):
    '从已用次数接着铸造。第一次调用得到起点加一'
    计数=[起点]

    def 铸造(前缀):
        '下一标识'
        计数[0]+=1
        return 前缀+str(计数[0])

    def 已用():
        '当前计数'
        return 计数[0]

    return {'mint':铸造,'used':已用}


def 创建表面():
    '折叠、单窗、无签。默认页等展开后再种'
    计数=计数铸造(0)
    return {
        'layout':创建初始状态(计数['mint']),
        'history':{'entries':[],'cursor':空历史['cursor']},
        'minted':计数['used'](),
    }


def 窗内页面(状态,窗格标识,种类):
    '这个窗里该种类的页面签'
    return 查找窗格内容标签(状态,窗格标识,页面地址(种类),种类)


def 页面种类(状态,标签标识):
    '页面签返回种类，资源签返回 None'
    签=状态['tabs'].get(标签标识)
    if 签 is None:
        return None
    if 签['contentId']==页面地址(签['kind']):
        return 签['kind']
    return None


def 独一停靠标签(状态,标签标识):
    '停靠树只剩这一格、这一签'
    窗=查找标签窗格(状态,标签标识)
    return 窗['host']=='dock' and len(窗['tabs'])==1 and len(停靠窗格标识列表(状态))==1


def 可关闭标签(表面,标签标识):
    '没有这张签，或独一停靠向导，都不能关'
    签=表面['layout']['tabs'].get(标签标识)
    if 签 is None:
        return False
    if 签['kind']==向导种类 and 独一停靠标签(表面['layout'],标签标识):
        return False
    return True


def 抵达(状态,标签标识,到窗,否则):
    '页面抵达已有同种页面的窗时，关掉到达的签并聚焦原签'
    种类=页面种类(状态,标签标识)
    if 种类 is None:
        return 否则()
    已有=窗内页面(状态,到窗,种类)
    if 已有 is None or 已有==标签标识:
        return 否则()
    return [{'type':'closeTab','tabId':标签标识},{'type':'focusTab','tabId':已有}]


def 推进(表面,规划,种子):
    '规划、落定、记成一条历史。没有操作就原样返回'
    计数=计数铸造(表面['minted'])

    def 造签(标识):
        '按当前默认页造签'
        初始=种子()
        return {'id':标识,'kind':初始['kind'],'title':初始['title'],'contentId':页面地址(初始['kind'])}

    已规划=规划(表面['layout'],计数['mint'],造签)
    if len(已规划)==0:
        return 表面
    之后=回放(表面['layout'],已规划)
    造落定=造签 if 之后['expanded'] else None
    已落定=规划落定(之后,计数['mint'],造落定)
    步进=记录(表面['history'],表面['layout'],list(已规划)+list(已落定))
    return {'layout':步进['state'],'history':步进['history'],'minted':计数['used']()}


def 落座(状态,会话标识,下一步):
    '只换这一个会话的表面'
    已有=状态['bySession'].get(会话标识)
    更新=下一步(已有 if 已有 is not None else 创建表面())
    if 更新 is 已有:
        return 状态['bySession']
    下一=dict(状态['bySession'])
    下一[会话标识]=更新
    return 下一


def 历史步进(表面,步进):
    '按一个方向走历史'
    移动=步进(表面['history'],表面['layout'])
    if 移动 is None:
        return 表面
    下一=dict(表面)
    下一['layout']=移动['state']
    下一['history']=移动['history']
    return 下一


def 创建右侧侧栏存储(种子):
    '每个作用域一份表面。有作用域键时从 localStorage 灌入并回写'
    句柄=声明存储({
        'init':lambda: {'bySession':{}},
        'actions':{
            '打开':lambda 草稿,会话标识: 落座写入(草稿,会话标识,lambda 表面: 表面,种子),
            '设展开':lambda 草稿,会话标识,展开: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: 规划设展开(状态,展开),种子),种子),
            '切换展开':lambda 草稿,会话标识: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: 规划设展开(状态,not 状态['expanded']),种子),种子),
            '设模式':lambda 草稿,会话标识,模式: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: 规划设模式(状态,模式),种子),种子),
            '分窗格':lambda 草稿,会话标识,窗格标识=None,落定=None: 分窗格动作(草稿,会话标识,种子,窗格标识,落定),
            '打开内容':lambda 草稿,会话标识,意图,落定: 打开内容动作(草稿,会话标识,种子,意图,落定),
            '复制标签':lambda 草稿,会话标识,标签标识: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: [] if 页面种类(状态,标签标识) is not None else 规划复制标签(状态,铸造,标签标识)['ops'],种子),种子),
            '关闭标签':lambda 草稿,会话标识,标签标识: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: 关闭规划(表面,状态,标签标识),种子),种子),
            '聚焦标签':lambda 草稿,会话标识,标签标识: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: 聚焦标签规划(状态,标签标识),种子),种子),
            '聚焦窗格':lambda 草稿,会话标识,窗格标识: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: 聚焦窗格规划(状态,窗格标识),种子),种子),
            '安置标签':lambda 草稿,会话标识,标签标识,到窗,下标: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: 抵达(状态,标签标识,到窗,lambda: 规划安置标签(状态,标签标识,到窗,下标)),种子),种子),
            '投放标签':lambda 草稿,会话标识,标签标识,窗格标识,区: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: 投放规划(状态,铸造,造签,标签标识,窗格标识,区),种子),种子),
            '浮出标签':lambda 草稿,会话标识,标签标识,矩形=None: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: 规划浮出标签(状态,铸造,标签标识,矩形)['ops'],种子),种子),
            '收回浮窗':lambda 草稿,会话标识,窗格标识: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: 收回规划(状态,窗格标识),种子),种子),
            '移动浮动':lambda 草稿,会话标识,窗格标识,横,纵: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: [{'type':'moveFloat','paneId':窗格标识,'x':横,'y':纵}],种子),种子),
            '缩放浮动':lambda 草稿,会话标识,窗格标识,矩形: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: [{'type':'resizeFloat','paneId':窗格标识,'rect':矩形}],种子),种子),
            '调整分割':lambda 草稿,会话标识,分割标识,尺寸表: 落座写入(草稿,会话标识,lambda 表面: 推进(表面,lambda 状态,铸造,造签: 规划调整分割(分割标识,尺寸表,0.2),种子),种子),
            '撤销':lambda 草稿,会话标识: 落座写入(草稿,会话标识,lambda 表面: 历史步进(表面,后退一步),种子),
            '重做':lambda 草稿,会话标识: 落座写入(草稿,会话标识,lambda 表面: 历史步进(表面,前进一步),种子),
        },
    })
    原创建=句柄.create

    def 创建(作用域键=None):
        '铸造后灌入已存布局，并在变更时回写'
        实例=原创建(作用域键)
        if 作用域键 is None:
            return 实例
        已存=读侧栏布局(作用域键)
        if 已存 is not None:
            实例.store.set({'bySession':{作用域键:已存}})

        def 同步():
            '有表面就写回'
            表面=实例.getSnapshot()['bySession'].get(作用域键)
            if 表面 is not None:
                写侧栏布局(作用域键,表面)

        实例.subscribe(同步)

        def 清持久化():
            '删掉这个作用域的布局'
            清侧栏布局(作用域键)

        实例.clearPersisted=清持久化
        return 实例

    句柄.create=创建
    return 句柄


def 落座写入(草稿,会话标识,下一步,种子):
    '动作共用的落座。种子参数只为和动作闭包对齐'
    草稿['bySession']=落座(草稿,会话标识,下一步)


def 聚焦标签规划(状态,标签标识):
    '已经是活动窗的活动签就不动'
    窗=查找标签窗格(状态,标签标识)
    if 窗['activeTabId']==标签标识 and 状态['activePaneId']==窗['id']:
        return []
    return [{'type':'focusTab','tabId':标签标识}]


def 聚焦窗格规划(状态,窗格标识):
    '已经是活动窗就不动'
    if 状态['activePaneId']==窗格标识:
        return []
    return [{'type':'focusPane','paneId':窗格标识}]


def 关闭规划(表面,状态,标签标识):
    '不能关就空。独一停靠签关掉后收起，并退出全屏'
    if not 可关闭标签(表面,标签标识):
        return []
    if not 独一停靠标签(状态,标签标识):
        return [{'type':'closeTab','tabId':标签标识}]
    return [{'type':'closeTab','tabId':标签标识}]+list(规划设模式(状态,'push'))+list(规划设展开(状态,False))


def 分窗格动作(草稿,会话标识,种子,窗格标识,落定):
    '已有两格或目标窗没有签时不分。分成功后把新窗告诉落定'
    def 下一步(表面):
        '对照分栏前后的停靠窗'
        def 规划(状态,铸造,造签):
            '两格已满或空窗则空'
            目标=窗格标识 if 窗格标识 is not None else 活动停靠窗格标识(状态)
            if len(停靠窗格标识列表(状态))>=2 or len(取窗格(状态,目标)['tabs'])==0:
                return []
            return 规划分窗格(状态,铸造,窗格标识,造签)

        下一=推进(表面,规划,种子)
        if 落定 is not None and 下一 is not 表面:
            之前=set(停靠窗格标识列表(表面['layout']))
            for 标识 in 停靠窗格标识列表(下一['layout']):
                if 标识 not in 之前:
                    落定(标识)
        return 下一

    草稿['bySession']=落座(草稿,会话标识,下一步)


def 打开内容动作(草稿,会话标识,种子,意图,落定):
    '展开、落签、替换，一次记完。落定在规划时同步调用'
    def 下一步(表面):
        '交给推进'
        def 规划(状态,铸造,造签):
            '算出这一次打开的操作'
            种类=意图['kind']
            内容标识=意图['contentId']
            标题=意图['title']
            替换=意图.get('replaceTab')
            操作=list(规划设展开(状态,True))
            被替换窗=None if 替换 is None else 查找标签窗格(状态,替换)
            借出=被替换窗 if 替换 is not None and 被替换窗 is not None and 被替换窗.get('host')=='dock' else None
            窗格标识=借出['id'] if 借出 is not None else 意图.get('paneId')
            下标=None
            if 借出 is not None and 替换 is not None:
                下标=借出['tabs'].index(替换)
            是页面=内容标识==页面地址(种类)
            已持=None
            if 是页面:
                目标窗=窗格标识 if 窗格标识 is not None else 活动停靠窗格标识(状态)
                已持=窗内页面(状态,目标窗,种类)
            if 是页面:
                揭示=已持
            elif 意图.get('revealIfOpened') is False:
                揭示=None
            else:
                揭示=查找内容标签(状态,内容标识,种类)
            新窗签=[None]
            分裂=[]
            if 意图.get('preferNewPane') is True and 替换 is None and 揭示 is None:
                def 造新(标识):
                    '新窗里的这张签'
                    新窗签[0]=标识
                    return {'id':标识,'kind':种类,'contentId':内容标识,'title':标题}
                分裂=规划分窗格(状态,铸造,窗格标识,造新)
            if 揭示 is not None:
                已计划={'ops':[{'type':'focusTab','tabId':揭示}],'tabId':揭示}
            elif 新窗签[0] is not None:
                已计划={'ops':分裂,'tabId':新窗签[0]}
            else:
                入={'kind':种类,'contentId':内容标识,'title':标题}
                if 窗格标识 is not None:
                    入['paneId']=窗格标识
                if 下标 is not None:
                    入['index']=下标
                if 是页面:
                    入['revealIfOpened']=False
                elif 'revealIfOpened' in 意图:
                    入['revealIfOpened']=意图['revealIfOpened']
                已计划=规划打开内容(状态,铸造,入)
            操作.extend(已计划['ops'])
            if 替换 is not None and 替换!=已计划['tabId']:
                操作.append({'type':'closeTab','tabId':替换})
            落定(已计划['tabId'])
            return 操作

        return 推进(表面,规划,种子)

    草稿['bySession']=落座(草稿,会话标识,下一步)


def 投放规划(状态,铸造,造签,标签标识,窗格标识,区):
    '上下投放不做。已有两格时边沿投放不做。中心投放走页面合并'
    if 区=='top' or 区=='bottom':
        return []
    if 区!='center' and len(停靠窗格标识列表(状态))>=2:
        return []

    def 否则():
        '套件自己的投放'
        return 规划投放标签(状态,铸造,标签标识,窗格标识,区,造签)

    if 区=='center':
        return 抵达(状态,标签标识,窗格标识,否则)
    return 否则()


def 收回规划(状态,窗格标识):
    '浮窗收回活动停靠窗。页面签要合并'
    窗=取窗格(状态,窗格标识)
    浮签=窗['tabs'][0] if len(窗['tabs'])>0 else None

    def 否则():
        '套件收回'
        return 规划收回浮窗(状态,窗格标识)

    if 浮签 is None:
        return 否则()
    return 抵达(状态,浮签,活动停靠窗格标识(状态),否则)
