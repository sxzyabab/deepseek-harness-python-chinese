from .压缩项 import 压缩项
from .泛型命令卡 import 泛型命令卡

__all__=['压缩命令卡']


class 压缩命令卡:
    '有检查点就画压缩标记，否则画通用命令卡'
    def __init__(自身,属性=None):
        '记下命令和可选的压缩节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '结构化检查点优先。还在跑时用压缩中的文案'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        压缩=属性.get('compaction')
        if 压缩 is not None:
            结局=属性.get('node') if isinstance(属性.get('node'),dict) else {}
            结局文=None
            if isinstance(结局.get('outcome'),dict):
                结局文=结局['outcome'].get('text')
            卡=压缩项({
                'window':属性['window'],
                'node':压缩,
                'title':翻译('message.compaction.commandTitle'),
                'fallbackSummary':结局文,
                't':翻译,
            })
        else:
            节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
            卡属性={'window':属性['window'],'node':节点,'t':翻译}
            if 节点.get('outcome') is None:
                卡属性['runningSummary']=翻译('message.compaction.running')
            卡=泛型命令卡(卡属性)
        自身.根=卡.根
        if 属性.get('parent') is not None and 自身.根 is not None:
            属性['parent'].appendChild(自身.根)
        return 自身.根
