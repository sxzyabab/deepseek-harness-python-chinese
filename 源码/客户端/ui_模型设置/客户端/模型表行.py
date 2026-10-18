from ...模块.客户端.通告 import 取握手窗口
from ...ui_基础界面组件.icons import 图标
from ...ui_对话.异常 import 挂上
from .文案 import 中文
from .编辑器页脚 import 建,清空子,采集焦点,还原焦点

__all__=['模型表行']

class 模型表行:
    '一行模型：标识、显示名，展开后是容量和输入类型'
    def __init__(自身,属性):
        '记下这一行的字段和动作'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.推理=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '两列文本和展开、删除。展开区交给输入类型和推理档位'
        from .模型推理强度 import 模型推理强度
        from .模型输入类型 import 模型输入类型
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        快照=None
        if 自身.根 is None:
            自身.根=建(文档,'div','modelEntry')
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            快照=采集焦点(文档,自身.根)
            清空子(自身.根)
        模型=属性.get('model')
        if isinstance(模型,dict) is False:
            模型={}
        位置=属性.get('position')
        禁用=属性.get('disabled') is True
        行=建(文档,'div','modelRow')
        for 字段 in ('id','name'):
            框=建(文档,'input','input')
            框.type='text'
            现=模型.get(字段)
            框.value=现 if isinstance(现,str) else ''
            框.placeholder=中文['modelId'] if 字段=='id' else 中文['modelName']
            标=中文['modelId'] if 字段=='id' else 中文['modelName']
            框.setAttribute('aria-label',标+' '+str(位置))
            框.disabled=禁用
            框.setAttribute('data-dsh-focus','model-'+str(位置)+'-'+字段)
            def 改(事件,字段=字段):
                '名称清空就从档案拿掉。标识保留空串'
                文=事件.target.value
                if 字段=='name' and 文=='':
                    属性['onFieldChange'](字段,None)
                else:
                    属性['onFieldChange'](字段,文)
            框.addEventListener('input',改)
            if 字段=='id' and 属性.get('onIdBlur') is not None:
                def 离开(事件):
                    '标识去掉首尾空白'
                    属性['onIdBlur'](事件.target.value)
                框.addEventListener('blur',离开)
            行.appendChild(框)
        展=建(文档,'button','iconButton')
        展.type='button'
        展.setAttribute('aria-label',中文['modelAdvanced']+' '+str(位置))
        展.setAttribute('aria-expanded','true' if 属性.get('expanded') is True else 'false')
        展.title=中文['modelAdvanced']
        if 属性.get('expanded') is True:
            挂上(展,图标('chevron-down-14',{'window':窗口}))
        else:
            挂上(展,图标('chevron-right-14',{'window':窗口}))
        def 点展(事件):
            '展开或收起这一行的选项'
            属性['onToggle']()
        展.addEventListener('click',点展)
        行.appendChild(展)
        删=建(文档,'button','iconButton iconButtonDanger')
        删.type='button'
        删.setAttribute('aria-label',中文['removeModel']+' '+str(位置))
        删.title=中文['removeModel']
        删.disabled=禁用
        挂上(删,图标('trash-16',{'window':窗口,'size':14}))
        def 点删(事件):
            '删掉这一行'
            属性['onRemove']()
        删.addEventListener('click',点删)
        行.appendChild(删)
        自身.根.appendChild(行)
        if 属性.get('expanded') is True:
            区=建(文档,'div','modelAdvanced')
            for 字段 in ('contextWindow','maxTokens'):
                容=属性.get(字段)
                if isinstance(容,dict) is False:
                    容={}
                签=建(文档,'label','modelField')
                字=建(文档,'span','modelFieldLabel')
                字.textContent=中文[字段]
                签.appendChild(字)
                框=建(文档,'input','input')
                框.type='text'
                框.setAttribute('inputmode','numeric')
                框.value=容.get('value') if 容.get('value') is not None else ''
                框.placeholder=容.get('placeholder') if 容.get('placeholder') is not None else ''
                框.setAttribute('aria-label',中文[字段]+' '+str(位置))
                框.disabled=禁用
                框.setAttribute('data-dsh-focus','model-'+str(位置)+'-'+字段)
                def 改容(事件,字段=字段,容=容):
                    '把这次键入交给容量缓冲'
                    容['onChange'](事件.target.value)
                框.addEventListener('input',改容)
                if 容.get('onBlur') is not None:
                    def 离容(事件,容=容):
                        '离开字段时落定容量'
                        容['onBlur']()
                    框.addEventListener('blur',离容)
                签.appendChild(框)
                区.appendChild(签)
            输入属性={
                'window':窗口,
                'model':模型,
                'field':属性.get('inputField'),
                'position':位置,
                'disabled':禁用 or 属性.get('inputLoading') is True,
                'fallback':属性.get('inputFallback'),
                'onChange':属性.get('onChange'),
            }
            挂上(区,模型输入类型(输入属性))
            推理档=属性.get('reasoningLevels')
            if isinstance(推理档,(list,tuple)) and len(推理档)>0:
                推理属性={
                    'window':窗口,
                    'model':模型,
                    'levels':推理档,
                    'position':位置,
                    'disabled':禁用,
                    'onChange':属性.get('onChange'),
                }
                if 自身.推理 is None:
                    自身.推理=模型推理强度(推理属性)
                else:
                    自身.推理.更新(推理属性)
                    自身.推理.渲染()
                挂上(区,自身.推理)
            自身.根.appendChild(区)
        还原焦点(文档,快照)
        return 自身.根
