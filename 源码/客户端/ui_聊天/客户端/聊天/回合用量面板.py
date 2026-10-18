from ....ui_基础界面组件.icons import 图标数据16
from ....ui_对话.异常 import 标样式模块
from .令牌格式 import 格式化令牌,格式化精确令牌,格式化缓存命中百分比
from .统计对话框 import 统计对话框席
from .用披露 import 注入聊天样式

__all__=['回合用量面板']

样式模块='turn-usage'
对话框模块='stat-dialog'


def 紧凑计数(值,翻译):
    '紧凑数字再套上计数文案'
    return 翻译('message.turnUsage.count',{'count':格式化令牌(值,翻译)})


def 精确计数(值,翻译):
    '精确分组再套上计数文案'
    return 翻译('message.turnUsage.count',{'count':格式化精确令牌(值,翻译)})


class 回合用量面板:
    '图标行上的用量胶囊。点开后在正文里弹出明细'
    def __init__(自身,属性=None):
        '记下用量'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.席=统计对话框席()
        自身.席.变化=自身.渲染
        自身.根=None
        自身.面板=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '触发器留在行里。对话框挂到 body'
        属性=自身.属性
        if 'window' not in 属性:
            return 自身.根
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'回合用量面板.module.css')
        注入聊天样式(文档,对话框模块,'统计对话框.module.css')
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        用量=属性.get('usage') if isinstance(属性.get('usage'),dict) else {}
        if 自身.根 is None:
            自身.根=文档.createElement('span')
            自身.根.className='root'
            标样式模块(自身.根,样式模块)
        else:
            while 自身.根.firstChild is not None:
                自身.根.removeChild(自身.根.firstChild)
        自身.席.根=自身.根
        缓存=None
        if 用量.get('cacheReadTokens') is not None:
            输入=用量.get('totalTokens',0)-用量.get('outputTokens',0)
            缓存=格式化缓存命中百分比(用量.get('cacheReadTokens'),输入,1)
        总计=紧凑计数(用量.get('totalTokens') or 0,翻译)
        路线=''
        if isinstance(用量.get('routes'),list):
            路线=', '.join(str(条.get('provider'))+'/'+str(条.get('model')) for 条 in 用量['routes'] if isinstance(条,dict))
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='trigger'
        标样式模块(钮,样式模块)
        钮.setAttribute('aria-haspopup','dialog')
        钮.setAttribute('aria-expanded','true' if 自身.席.打开 else 'false')
        图=图标数据16({'window':窗口})
        if 图 is not None:
            钮.appendChild(图)
        标=文档.createElement('span')
        标.className='label'
        标样式模块(标,样式模块)
        标.textContent=翻译('message.turnUsage.consumed',{'total':总计})
        钮.appendChild(标)

        def 切换(事件=None):
            '开关明细'
            自身.席.设打开(not 自身.席.打开)
            自身.渲染()

        钮.addEventListener('click',切换)
        自身.根.appendChild(钮)
        if 自身.面板 is not None and 自身.面板.parentNode is not None:
            自身.面板.remove()
            自身.面板=None
        if 自身.席.打开:
            面板=文档.createElement('div')
            面板.className='panel'
            标样式模块(面板,对话框模块)
            面板.setAttribute('role','dialog')
            面板.setAttribute('aria-label',翻译('message.turnUsage.title'))
            题=文档.createElement('div')
            题.className='title'
            标样式模块(题,对话框模块)
            题标=文档.createElement('span')
            题标.className='titleLabel'
            标样式模块(题标,对话框模块)
            题图=图标数据16({'window':窗口})
            if 题图 is not None:
                题标.appendChild(题图)
            题标.appendChild(文档.createTextNode(翻译('message.turnUsage.title')))
            题值=文档.createElement('span')
            题值.className='titleValue'
            标样式模块(题值,对话框模块)
            题值.textContent=精确计数(用量.get('totalTokens') or 0,翻译)
            题.appendChild(题标)
            题.appendChild(题值)
            面板.appendChild(题)
            线=文档.createElement('div')
            线.className='titleRule'
            标样式模块(线,对话框模块)
            线.setAttribute('aria-hidden','true')
            面板.appendChild(线)
            表=文档.createElement('dl')
            表.className='details'
            标样式模块(表,对话框模块)
            表.setAttribute('data-turn-usage-details','')

            def 加行(名,值节点):
                '一行名称和值'
                名节=文档.createElement('dt')
                名节.textContent=名
                表.appendChild(名节)
                表.appendChild(值节点)

            if 路线!='':
                值=文档.createElement('dd')
                值.className='route'
                标样式模块(值,对话框模块)
                值.textContent=路线
                加行(翻译('message.turnUsage.model'),值)
            if 缓存 is not None:
                值=文档.createElement('dd')
                值.textContent=str(缓存)+'%'
                加行(翻译('message.turnUsage.cacheHit'),值)
            值=文档.createElement('dd')
            值.textContent=精确计数(用量.get('uncachedInputTokens') or 0,翻译)
            加行(翻译('message.turnUsage.input'),值)
            if 用量.get('cacheReadTokens') is not None:
                值=文档.createElement('dd')
                值.textContent=精确计数(用量['cacheReadTokens'],翻译)
                加行(翻译('message.turnUsage.cacheRead'),值)
            if 用量.get('cacheWriteTokens') is not None:
                值=文档.createElement('dd')
                值.textContent=精确计数(用量['cacheWriteTokens'],翻译)
                加行(翻译('message.turnUsage.cacheWrite'),值)
            出=文档.createElement('dd')
            出.textContent=精确计数(用量.get('outputTokens') or 0,翻译)
            if 用量.get('reasoningTokens') is not None:
                推理=文档.createElement('span')
                推理.className='reasoning'
                标样式模块(推理,对话框模块)
                推理.textContent=翻译('message.turnUsage.reasoning',{'tokens':精确计数(用量['reasoningTokens'],翻译)})
                出.appendChild(推理)
            加行(翻译('message.turnUsage.output'),出)
            面板.appendChild(表)
            文档.body.appendChild(面板)
            自身.面板=面板
            自身.席.面板=面板
            自身.席.监听(文档)
            自身.席.放置()
            自身.席.套样式(面板)
        if 属性.get('parent') is not None and 自身.根.parentNode is None:
            属性['parent'].appendChild(自身.根)
        return 自身.根
