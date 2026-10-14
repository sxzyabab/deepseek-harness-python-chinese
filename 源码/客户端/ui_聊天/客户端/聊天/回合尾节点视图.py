from .消息图标动作 import 消息图标动作#图标行
from .回合用量面板 import 回合用量面板,回合时间面板#胶囊
from .消息项 import 打开列,收起列
from .聊天节点席 import 绘制已登记组件

__all__=['回合尾节点视图']#仅中文公开名

from nicegui import ui as 界面

from nicegui import ui as 界面

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 空渲染槽(*位置参数,**关键字参数):
    '未注入槽渲染时不画'
    return None#不画

class 回合尾节点视图:
    'turnTail 链 + 可选消息动作'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.动作=消息图标动作()#动作
        自身.用量=回合用量面板()#用量
        自身.时间=回合时间面板()#时间
        自身.根=None#列
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '无 turn 不画'
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 else None#节点
        数据=节点['data'] if 节点 is not None and 'data' in 节点 else None#数据
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        用聊天=属性['useChat'] if 'useChat' in 属性 else None#聊天
        打开文件=属性['openFile'] if 'openFile' in 属性 else None#打开
        分叉=属性['forkAt'] if 'forkAt' in 属性 else None#分叉
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#槽
        渲染链=属性['renderSlotChain'] if 'renderSlotChain' in 属性 else 空渲染槽#链
        位置=节点['location'] if 节点 is not None and 'location' in 节点 else None#位置
        种=位置['kind'] if 位置 is not None and 'kind' in 位置 else None#种
        回合=位置['turn'] if 种 in ('turn','step') and 位置 is not None and 'turn' in 位置 else None#回合
        if 回合 is None:#无
            收起列(自身)
            return
        有后节点=False#后
        是最新=False#最新
        数据回合=数据['turn'] if 数据 is not None and 'turn' in 数据 else None#数据回合
        节点键=节点['key'] if 节点 is not None and 'key' in 节点 else None#键
        if 用聊天 is not None:
            def 判后(快照):
                '本回合末键是否本节点。locations 为契约 dict'
                列=快照['locations']['getTurn'](数据回合)#列
                列=列 if 列 is not None else []#列；判 length
                末键=列[-1] if len(列)>0 else None#末
                return 末键!=节点键#后
            def 判最新(快照):
                'timeline.turnOrder 末'
                线=快照['timeline'] if 'timeline' in 快照 else None#线
                序=线['turnOrder'] if 线 is not None and 'turnOrder' in 线 and 线['turnOrder'] is not None else []#序
                return len(序)>0 and 序[-1]==数据回合#末；判 length
            有后节点=用聊天(判后) is True#后
            是最新=用聊天(判最新) is True#最新
        收尾=数据['closing'] if 数据 is not None and 'closing' in 数据 else None#closing
        if 收尾 is not None and 'finalNode' in 收尾 and 收尾['finalNode'] is not None:#定稿序号
            序号=收尾['finalNode']['seq'] if 'seq' in 收尾['finalNode'] else None#seq
        else:#节点序号
            序号=数据['seq'] if 数据 is not None and 'seq' in 数据 else None#seq
        属主={'turn':回合,'seq':序号,'openFile':打开文件}#属主
        with 打开列(自身,'回合尾'):
            if 是最新 is True:
                自身.根.classes(add='揭示始终')
            else:
                自身.根.classes(add='揭示悬停')
            尾=渲染链('conversation.chat.turnTail',属主)#链
            画了尾=绘制已登记组件(尾)
            if 收尾 is None:#无收尾
                if 画了尾 is not True:
                    收起列(自身)
                return
            起=回合['start'] if isinstance(回合,dict) and 'start' in 回合 else None#start
            终=回合['end'] if isinstance(回合,dict) and 'end' in 回合 else None#end
            起点=起['time'] if 起 is not None and 'time' in 起 else None#起点
            终点=终['time'] if 终 is not None and 'time' in 终 else None#终点
            运行毫秒=None if 起点 is None or 终点 is None else max(0,终点-起点)#时长
            终节=收尾['finalNode'] if 'finalNode' in 收尾 else None#终节
            消息标识=终节['messageId'] if 终节 is not None and 'messageId' in 终节 else None#消息
            定稿序号=终节['seq'] if 终节 is not None and 'seq' in 终节 else None#分支点
            def 分支():
                '分叉到定稿序号'
                if 分叉 is not None:
                    分叉(定稿序号)#叉
            with 界面.column().classes('回合尾动作'):
                if 数据 is not None and 'tokenUsage' in 数据 and 数据['tokenUsage'] is not None:#有用量
                    自身.用量.更新({'usage':数据['tokenUsage'],'t':翻译})
                    自身.用量.渲染()
                if 运行毫秒 is not None:#有墙钟
                    吞吐=数据['tokensPerSecond'] if 数据 is not None and 'tokensPerSecond' in 数据 else None#吞吐
                    首令=数据['ttftMs'] if 数据 is not None and 'ttftMs' in 数据 else None#TTFT
                    自身.时间.更新({'runMs':运行毫秒,'tokensPerSecond':吞吐,'ttftMs':首令,'t':翻译})
                    自身.时间.渲染()
            时=收尾['time'] if 'time' in 收尾 else None#时
            不可=数据['branchUnavailable'] is True if 数据 is not None and 'branchUnavailable' in 数据 else False#不可
            自身.动作.更新({'time':时,'clock':'end','onBranch':分支,'branchUnavailable':不可 is True or 有后节点 is True,'node':{'seq':定稿序号,'time':时,'branchUnavailable':不可 is True or 有后节点 is True},'t':翻译})
            自身.动作.渲染()
            if 消息标识 is not None:
                助手动作=渲染槽('conversation.chat.assistant-actions',{'messageId':消息标识})
                绘制已登记组件(助手动作)

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:
            自身.更新(属性)#刷
        自身.渲染()#画
