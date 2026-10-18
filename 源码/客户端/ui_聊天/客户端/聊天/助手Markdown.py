from urllib.parse import quote,unquote
from ....ui_基础界面组件.markdown.json块 import json块
from ....ui_基础界面组件.markdown.Markdown文本 import Markdown文本
from ....ui_对话.异常 import 标样式模块
from .....工具.工作区路径 import 是否绝对工作区路径
from ..markdown标签 import markdown标签
from .推理行 import 推理行
from .用披露 import 注入聊天样式,真属性,挂节点

__all__=['助手Markdown','本地路径媒体地址']

样式模块='assistant-markdown'


def 本地路径媒体地址(基址,值):
    '解码后的绝对路径走文件接口。不支持的协议返回空'
    try:
        路径=unquote(值.split('?')[0].split('#')[0])
    except Exception:
        return None
    if (not 基址.startswith('http:') and not 基址.startswith('https:') and not 基址.startswith('dsh-app://app/')):
        return None
    if not 是否绝对工作区路径(路径):
        return None
    if 路径.startswith('//') or 路径.startswith('\\\\'):
        return None
    return 基址.rstrip('/')+'/'+'api/file?path='+quote(路径,safe='')


class 助手Markdown:
    '推理披露和回复 Markdown 放在同一壳里'
    def __init__(自身,属性=None):
        '记下块'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '只有工具头的节点不画空壳。中断时在回复侧标已停止'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'助手Markdown.module.css')
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        块表=属性.get('blocks') if isinstance(属性.get('blocks'),list) else []
        流式=属性.get('streaming') is True
        中断=属性.get('interrupted') is True
        可见=流式 or 中断 or any(isinstance(块,dict) and 块.get('kind')!='tool-call' for 块 in 块表)
        if not 可见:
            return None
        根=文档.createElement('div')
        根.className='root'
        标样式模块(根,样式模块)
        真属性(根,'data-streaming',流式)
        体=文档.createElement('div')
        体.className='body'
        标样式模块(体,样式模块)
        标签=markdown标签(翻译)
        基址=''
        try:
            基址=文档.baseURI or ''
        except Exception:
            基址=''

        def 解析路径(值,基=基址):
            'Markdown 图片地址'
            return 本地路径媒体地址(基,值)
        组部分=属性.get('groupPart')
        下标=0
        while 下标<len(块表):
            块=块表[下标]
            if not isinstance(块,dict):
                下标+=1
                continue
            if 组部分=='reasoning' and 块.get('kind')!='reasoning':
                下标+=1
                continue
            if 组部分=='response' and 块.get('kind')=='reasoning':
                下标+=1
                continue
            if 块.get('kind')=='text':
                文=Markdown文本({
                    'window':窗口,
                    'text':块.get('text') or '',
                    'streaming':流式,
                    'labels':标签,
                    'fileMentions':属性.get('mentions'),
                    'pathImages':{'resolve':解析路径},
                })
                挂节点(体,文)
            elif 块.get('kind')=='reasoning':
                if isinstance(块.get('text'),str) and 块['text'].strip()!='':
                    行=推理行({
                        'window':窗口,
                        'text':块.get('text') or '',
                        'running':流式 and 下标==len(块表)-1,
                        'useDisclosure':属性.get('useDisclosure'),
                        'usePresentation':属性.get('usePresentation'),
                        'renderSlot':属性.get('renderSlot'),
                        't':翻译,
                    })
                    盒=文档.createElement('div')
                    隐藏=属性.get('reasoningHidden') is True
                    if 隐藏:
                        盒.setAttribute('data-turn-process-inline','true')
                    组动作=属性.get('useGroupAction')
                    if callable(组动作):
                        席=组动作(隐藏,属性.get('revealProcess'))
                        if hasattr(席,'绑'):
                            席.绑(盒)
                    挂节点(盒,行.根 if 行.根 is not None else 行)
                    体.appendChild(盒)
            elif 块.get('kind')=='image':
                组=[块]
                while 下标+1<len(块表) and isinstance(块表[下标+1],dict) and 块表[下标+1].get('kind')=='image':
                    下标+=1
                    组.append(块表[下标])
                槽=属性.get('renderSlot')
                if callable(槽):
                    挂节点(体,槽('conversation.chat.message.images',{
                        'images':[{'attachment':项.get('attachment')} for 项 in 组],
                        'loadImage':属性.get('loadImage'),
                        'align':'start',
                        'window':窗口,
                    }))
            elif 块.get('kind')=='tool-call':
                pass
            else:
                def 截断(总,译=翻译):
                    '截断脚'
                    return 译('json.truncated',{'total':总})
                未知=json块({
                    'window':窗口,
                    'label':翻译('message.unknownBlock'),
                    'payload':块.get('block'),
                    'truncatedLabel':截断,
                })
                挂节点(体,未知)
            下标+=1
        有非推理=False
        for 块 in 块表:
            if isinstance(块,dict) and 块.get('kind') not in ('reasoning','tool-call'):
                有非推理=True
                break
        if 中断 and (组部分 is None or 组部分=='response' or not 有非推理):
            停=文档.createElement('span')
            停.className='stopped'
            标样式模块(停,样式模块)
            停.textContent=翻译('message.stopped')
            体.appendChild(停)
        根.appendChild(体)
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根
