'一条 skill 工具调用的强调摘要和说明披露'
import json
import os
from ...ui_基础界面组件.icons import 描边图标,图标下箭头描边常规#技能字形与下箭头
from ...ui_基础界面组件.文字闪烁 import 文字闪烁#行内高光
from ...ui_对话.异常 import 注入模块样式文件,标样式模块#样式模块
from .文案 import 中文#界面中文

__all__=['技能行']

样式模块='skill-row'#技能行样式模块

def 首行(文本):
    '折叠错误摘要和畸形参数回退用的第一物理行'
    换行=文本.find('\n')#第一处换行
    if 换行==-1:#没有换行
        return 文本#整段
    return 文本[:换行]#第一物理行

def 元素(文档,标签,类名):
    '造一个挂了技能行样式模块的节点'
    节点=文档.createElement(标签)#节点
    节点.className=类名#官方类名
    return 标样式模块(节点,样式模块)#接上模块

def 技能图标(窗口):
    '常规描边技能图标，边长 14'
    return 描边图标({'window':窗口,'size':14},'0 0 17 17',[#上游 IconSkillOutlineRegular
        'M4.57788 5.77124H10.7029',#标题线
        'M4.57788 8.89819H7.91879',#短线
        {'d':'M12.1404 1.19446C12.9442 1.19446 13.6404 1.81999 13.6404 2.64465V8.89856H12.6404V2.64465C12.6404 2.42015 12.4411 2.19446 12.1404 2.19446H3.14038C2.83968 2.19446 2.64038 2.42015 2.64038 2.64465V13.0929C2.64082 13.3172 2.84001 13.5421 3.14038 13.5421H8.88159V14.5421H3.14038C2.33675 14.5421 1.6408 13.9172 1.64038 13.0929V2.64465C1.64038 1.81999 2.33651 1.19446 3.14038 1.19446H12.1404Z','fill':'currentColor'},#页
        'M12.0051 15.1056C12.0051 13.6395 10.8166 12.451 9.35059 12.451C10.8166 12.451 12.0051 11.2626 12.0051 9.79651C12.0051 11.2626 13.1936 12.451 14.6597 12.451C13.1936 12.451 12.0051 13.6395 12.0051 15.1056Z',#星
    ],14)#边长 14

def 下箭头(窗口,类名):
    '常规描边下箭头，挂上技能行样式'
    图=图标下箭头描边常规({'window':窗口,'className':类名})#箭头
    return 标样式模块(图,样式模块)#类名属于本模块

class 技能行:
    '渲染一条 skill 工具调用为强调摘要和说明披露'
    展开表={}#按 callId 记住展开。槽位每次调用都是新实例

    def __new__(类,属性):
        '槽位把组件当函数调用，直接返回这一行的节点'
        自身=object.__new__(类)#实例
        自身.属性=属性#props
        return 自身.渲染()#节点

    def 渲染(自身):
        '准备中只画标题。已开始的行可以展开说明'
        属性=自身.属性#当前 props
        窗口=属性['window']#宿主窗口
        文档=窗口.document#文档
        注入模块样式文件(#技能行样式只插一次
            文档,
            '技能行样式',
            os.path.join(os.path.dirname(__file__),'技能行.module.css'),
            样式模块,
        )
        if 属性.get('phase')=='preparing':#准备中。缺席 phase 不是准备中
            卡=元素(文档,'div','card')#卡片
            卡.setAttribute('data-tool','skill')#工具名
            卡.setAttribute('data-state','preparing')#准备中
            行=元素(文档,'div','row')#摘要行
            前导=元素(文档,'span','leading')#前导
            前导.appendChild(技能图标(窗口))#技能图标
            行.appendChild(前导)#挂上
            隐藏=元素(文档,'span','visuallyHidden')#读屏
            隐藏.textContent=中文['row.preparing']#准备加载技能
            行.appendChild(隐藏)#挂上
            标题=元素(文档,'span','title')#标题
            标题.appendChild(文字闪烁({#活动高光
                'window':窗口,#窗口
                'active':True,#准备中一直扫
                'children':中文['row.title'],#加载技能
            }).渲染())
            行.appendChild(标题)#挂上
            卡.appendChild(行)#挂上
            return 卡#准备中没有说明
        块=属性['block']#耐久切片
        已结算='kind' in 块#已有结果
        if 已结算:#从 call 取参数
            调用=块['call'] if 'call' in 块 else None#调用
            原文=None if not isinstance(调用,dict) else 调用.get('argsRaw')#原始参数
        else:#还在流式参数
            原文=块.get('argsRaw')#原始参数
        原始参数='' if 原文 is None else 原文#缺席当空串
        调用标识=块['callId']#调用标识
        解析名=None#解析出的技能名
        try:#参数可能还是截断的 JSON
            解析=json.loads(原始参数)#解析
        except Exception as 解析错误:#截断前缀仍比换成无关目录有用，不抛
            解析=None#留到下面回退
        if isinstance(解析,dict):#对象才认 name
            候选=解析['name'] if 'name' in 解析 else None#name
            if isinstance(候选,str) and 候选!='':#非空字符串
                解析名=首行(候选)#第一行
        if 解析名 is None:#没有解析出名字
            if 原始参数=='':#空参数
                名=调用标识#回退调用标识
            else:#畸形或非对象
                名=首行(原始参数)#第一行
        else:#解析成功
            名=解析名#技能名
        输出=None#结果文本
        if 已结算:#压平耐久结果块
            片段=[]#文本片段
            for 项 in 块['content']:#逐块
                if isinstance(项,dict) and 项.get('type')=='text':#文本块
                    片段.append(项['text'])#原文
                else:#其余块
                    片段.append(json.dumps(项,indent=2,ensure_ascii=False))#两格缩进
            if len(片段)==0 and 'error' in 块 and 块['error'] is not None:#没有正文时用错误名
                错误体=块['error']#错误
                片段.append(str(错误体['name'])+': '+str(错误体['code']))#名与码
            接合='\n'.join(片段)#接成一段
            if 接合!='':#空串不当结果
                输出=接合#结果文本
        错误=块['error'] if 'error' in 块 else None#错误
        if not 已结算:#还在跑
            状态='running'#进行中
        elif isinstance(错误,dict) and 错误.get('code')=='interrupted':#中止
            状态='stopped'#已中止
        elif 块.get('isError'):#失败
            状态='error'#失败
        else:#成功
            状态='ok'#成功
        if 状态=='error' and 输出 is not None:#失败摘要取第一行
            错误摘要=首行(输出)#第一行
        else:#其余不另写错误摘要
            错误摘要=None#无
        可展开=输出 is not None#有输出才能展开
        打开=技能行.展开表.get(调用标识,False) is True and 可展开 is True#展开且有输出
        if 状态=='running':#进行中
            状态文案=中文['row.running']#正在加载 skill
        elif 状态=='error':#失败
            状态文案=中文['row.failed']#skill 加载失败
        else:#成功或中止不另写状态
            状态文案=None#无
        if 状态=='stopped':#中止写在摘要上
            摘要=中文['row.stopped']#skill 加载已中止
        elif 错误摘要 is not None:#错误第一行
            摘要=错误摘要#第一行
        else:#技能名
            摘要=名#名字
        摘要类='summary'#摘要类
        if 状态=='error':#失败色
            摘要类=摘要类+' errorSummary'#错误
        elif 状态=='stopped':#中止色
            摘要类=摘要类+' stoppedSummary'#中止
        卡=元素(文档,'div','card')#卡片
        卡.setAttribute('data-tool','skill')#工具名
        卡.setAttribute('data-state',状态)#状态
        行=元素(文档,'div','row')#摘要行
        if 可展开:#可点
            行.setAttribute('data-expandable','true')#可展开
            行.setAttribute('role','button')#按钮
            行.tabIndex=0#可聚焦
            行.setAttribute('aria-expanded','true' if 打开 else 'false')#展开态
            def 切换展开(事件=None):
                '有输出才切换展开，并换上新的一行'
                if 可展开 is not True:#不可展开
                    return#不动
                技能行.展开表[调用标识]=not 技能行.展开表.get(调用标识,False)#翻转
                新卡=自身.渲染()#按新状态再画
                父=卡.parentNode#当前位置
                if 父 is not None:#还在页面上
                    父.replaceChild(新卡,卡)#换上
            def 键盘切换(事件):
                '回车或空格与点击相同'
                if 可展开 is not True:#不可展开
                    return#不动
                if 事件.key!='Enter' and 事件.key!=' ':#不是确认键
                    return#不动
                事件.preventDefault()#不滚动
                切换展开()#切换
            行.addEventListener('click',切换展开)#点击
            行.addEventListener('keydown',键盘切换)#键盘
        前导=元素(文档,'span','leading')#前导
        if 打开:#已展开只留箭头
            前导.appendChild(下箭头(窗口,'chevron'))#箭头
        elif 可展开 is not True:#不能展开
            前导.appendChild(技能图标(窗口))#技能图标
        else:#悬停换成箭头
            静止=元素(文档,'span','iconIdle')#静止图标
            静止.appendChild(技能图标(窗口))#技能图标
            前导.appendChild(静止)#挂上
            前导.appendChild(下箭头(窗口,'chevron chevronHover'))#悬停箭头
        行.appendChild(前导)#挂上
        if 状态文案 is not None:#读屏状态
            隐藏=元素(文档,'span','visuallyHidden')#隐藏
            隐藏.textContent=状态文案#状态原文
            行.appendChild(隐藏)#挂上
        运行=状态=='running'#进行中才扫光
        标题=元素(文档,'span','title')#标题
        标题.appendChild(文字闪烁({#标题高光
            'window':窗口,#窗口
            'active':运行,#跟进行中
            'children':中文['row.title'],#加载技能
        }).渲染())
        行.appendChild(标题)#挂上
        分隔=元素(文档,'span','separator')#分隔点
        分隔.setAttribute('data-shimmer-decoration','')#扫光时跟颜色
        分隔.setAttribute('aria-hidden','true')#不读
        行.appendChild(分隔)#挂上
        摘要字=元素(文档,'span',摘要类)#摘要
        摘要字.appendChild(文字闪烁({#摘要高光
            'window':窗口,#窗口
            'active':运行,#跟进行中
            'children':摘要,#摘要原文
        }).渲染())
        行.appendChild(摘要字)#挂上
        卡.appendChild(行)#挂上
        if 打开:#展开说明
            体=元素(文档,'div','bodyWrap')#展开体
            区=元素(文档,'section','instructionsCard')#说明卡
            区.setAttribute('aria-label',中文['row.instructions'])#说明
            页眉=元素(文档,'div','instructionsHeader')#页眉
            页眉.textContent=中文['row.instructions']#说明
            区.appendChild(页眉)#挂上
            说明=元素(文档,'pre','instructions')#说明正文
            说明.textContent=输出#结果
            if 状态=='error':#失败色
                说明.setAttribute('data-error','true')#标失败
            区.appendChild(说明)#挂上
            体.appendChild(区)#挂上
            检视=属性['inspect'] if 'inspect' in 属性 else None#检视
            if 检视 is not None:#有检视
                钮=元素(文档,'button','inspectButton')#按钮
                钮.type='button'#按钮
                钮.appendChild(描边图标({#上游 IconInspectOutlineRegular
                    'window':窗口,#窗口
                    'size':12,#边长 12
                },'0 0 16 16',[
                    'M4.67398 4.25061L1.36094 7.86484C1.29085 7.9413 1.29085 8.05866 1.36094 8.13513L4.67398 11.7494',#左括号
                    'M11.3262 4.25061L14.6392 7.86484C14.7093 7.9413 14.7093 8.05866 14.6392 8.13513L11.3262 11.7494',#右括号
                    'M9.56222 3.62573L6.43774 12.3743',#斜线
                ],12))
                钮.appendChild(文档.createTextNode(中文['row.inspect']))#查看
                def 点检视(事件):
                    '打开这条调用的检视'
                    检视()#不把点击事件传进去
                钮.addEventListener('click',点检视)#点击
                体.appendChild(钮)#挂上
            卡.appendChild(体)#挂上
        return 卡#这一行
