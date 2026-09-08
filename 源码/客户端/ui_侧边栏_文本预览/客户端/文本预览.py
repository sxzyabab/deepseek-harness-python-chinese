"""文本预览正文：文件的已读页，或下一页未能显示的原因。

对齐上游 `ui-sidebar-textpreview/src/client/TextPreview.tsx`。公开面仅中文名。
两源在此汇合：标准资源钩给出文件元数据（版本与智能体是否写入），本类型自持存储
持有经面读到的页。宿主报告的变更只通告、不自动套用：读者脚下重载会丢位置，
栏等点击。元数据帧失败——文件已无、工作区未知——用同一栏盖住已载页，并带同一重载。
换行与重读控件坐在路径行末端；侧栏条带不带它们。

无 React：正文为视图模型类，产出结构树 dict；滚动落地由宿主按 data 属性执行。
"""
from .失败行 import 失败行#失败说明
from .图标 import 图标换行线16#换行图标
from .读页 import 宿主文件于#地址→宿主文件

__all__=[#仅中文公开名
    '页行列表','已载页列表','已载末行','文本预览','样式表',
]#公开面结束

样式表='''#对齐 TextPreview.module.css 核心结构类；完整样式见 文本预览.module.css
.preview{display:flex;flex:1 1 auto;flex-direction:column;height:100%;min-height:0}
.header{display:flex;flex:0 0 auto;gap:2px;align-items:center;padding:3px 6px 3px 10px;border-bottom:0.5px solid var(--dsw-alias-border-l1)}
.path{flex:1 1 auto;min-width:0;overflow:hidden;color:var(--dsw-alias-label-tertiary);font-size:12px;white-space:nowrap;text-overflow:ellipsis}
.changed{display:flex;flex:0 0 auto;gap:10px;align-items:center;margin:0;padding:6px 10px;color:var(--dsw-alias-label-secondary);font-size:12px;background:var(--dsw-alias-bg-layer-2);border-bottom:0.5px solid var(--dsw-alias-border-l1)}
.body{position:relative;flex:1 1 auto;min-height:0;padding:10px 0;overflow:auto;color:var(--dsw-alias-label-primary);font-size:var(--dsh-content-font-size-secondary, 13px);font-family:var(--dsw-font-mono, ui-monospace, monospace);line-height:1.6;white-space:pre}
.wrap{white-space:pre-wrap;word-break:break-word}
.page{margin:0;font:inherit;white-space:inherit}
.line{padding:0 10px}
.lineTarget{background:var(--dsw-alias-interactive-bg-hover)}
.statusLine{display:flex;gap:10px;align-items:center;margin:0;padding:6px 10px;color:var(--dsw-alias-label-secondary);font-size:var(--dsh-content-font-size-secondary, 13px);line-height:1.6;white-space:normal}
.status{display:flex;flex-direction:column;gap:8px;align-items:flex-start;padding:12px 10px}
.action{padding:4px 10px;color:var(--dsw-alias-label-primary);font-size:var(--dsh-content-font-size-secondary, 13px);font-family:var(--dsw-font, inherit);white-space:normal;background:var(--dsw-alias-bg-layer-2);border:0.5px solid var(--dsw-alias-border-l2);border-radius:6px;cursor:pointer}
.more{display:block;margin:8px 10px;padding:4px 10px;color:var(--dsw-alias-label-secondary);font-size:12px;font-family:var(--dsw-font, inherit);white-space:normal;background:var(--dsw-alias-bg-layer-2);border:0.5px solid var(--dsw-alias-border-l2);border-radius:6px;cursor:pointer}
.tool{display:flex;align-items:center;justify-content:center;width:24px;height:24px;padding:0;color:var(--dsw-alias-label-secondary);line-height:1;background:transparent;border:none;border-radius:4px;cursor:pointer}
.toolOn{color:var(--dsw-alias-label-primary);background:var(--dsw-alias-interactive-bg-hover)}
'''#样式表结束


def 页行列表(页):
    """一页的行。宿主用 `\\n` 连接且无终结符并计数，故越过末行的页（lines:0）无行，
    持有一行空文（lines:1, text:''）有一行；尾随 `\\n` 结束于空末行。页为 dict。
    """
    行数=页['lines'] if 'lines' in 页 else 0#行数
    if 行数==0:#越过末行
        return []#无行
    文本=页['text'] if 'text' in 页 else ''#页文
    return 文本.split('\n')#按行


def 已载页列表(页表):
    """已载页按文件序。页表为起始行 → 页。"""
    列表=[]#结果
    if 页表 is None:#无
        return 列表#空
    for 键,页 in 页表.items():#逐页
        列表.append({'offset':int(键),'text':页['text'],'lines':页['lines']})#带偏移
    列表.sort(key=lambda 项:项['offset'])#升序
    return 列表#已序


def 已载末行(页列表):
    """已载页按宿主行数到达的末行；尚无页则为 0。页列表须升序。"""
    if 页列表 is None or len(页列表)==0:#无页
        return 0#零
    末=页列表[-1]#末页
    return 末['offset']+末['lines']-1#末行号


class 文本预览:#文本预览正文视图模型
    """已读页与控件，或进度行；无 DOM，产出结构树。"""

    def __init__(自身,属性):
        """记下 tab、存储、注入面与文案。"""
        自身.属性=属性#合成 props
        自身._曾有页=False#是否已见过页（对齐 remount 滚动恢复键）

    def 更新(自身,属性):
        """props 变更。"""
        自身.属性=属性#最新

    def _读标签(自身):
        """当前 tab 记录。"""
        属性=自身.属性#props
        读标签=属性['useTabInfo'] if 'useTabInfo' in 属性 else None#钩
        if 读标签 is None:#无
            return None#无
        信息=读标签()#tab 信息
        return 信息['tab'] if 'tab' in 信息 else None#记录

    def _读桶(自身,标签标识):
        """该 tab 的预览状态；尚未写入则为 None。"""
        属性=自身.属性#props
        读存储=属性['useStore'] if 'useStore' in 属性 else None#钩
        if 读存储 is not None:#有钩
            def 取桶(状态):
                """按 tab 取桶。"""
                按标签=状态['byTab'] if 'byTab' in 状态 else None#分桶
                if 按标签 is None or 标签标识 not in 按标签:#缺席
                    return None#无
                return 按标签[标签标识]#桶
            return 读存储(取桶)#派生
        存储=属性['store'] if 'store' in 属性 else None#句柄
        if 存储 is None:#无
            return None#无
        状态=存储.getSnapshot()#快照
        按标签=状态['byTab'] if 'byTab' in 状态 else None#分桶
        if 按标签 is None or 标签标识 not in 按标签:#缺席
            return None#无
        return 按标签[标签标识]#桶

    def _读元数据(自身,内容标识):
        """文件资源快照；无钩则为空闲。"""
        属性=自身.属性#props
        用资源=属性['useResource'] if 'useResource' in 属性 else None#钩
        if 用资源 is None:#无
            return {'status':'none','value':None,'failure':None,'reload':lambda:None}#空闲
        return 用资源(内容标识)#快照

    def _宿主文件(自身,标签):
        """地址命名的会话与路径。"""
        属性=自身.属性#props
        会话标识=属性['sessionId'] if 'sessionId' in 属性 else None#席位会话
        return 宿主文件于(标签['contentId'],会话标识)#宿主文件

    def _导航行(自身,标签):
        """导航参数中的 1 起算行号；无则为 None。"""
        导航=标签['navigation'] if 'navigation' in 标签 else None#导航
        if 导航 is None:#无
            return None#无
        参数=导航['params'] if 'params' in 导航 else None#参数
        if 参数 is None or 'line' not in 参数:#无行
            return None#无
        return 参数['line']#行号

    def 确保已开读(自身):
        """无桶时请求首行页；对齐挂载 effect。"""
        标签=自身._读标签()#tab
        if 标签 is None:#无
            return#停
        标签标识=标签['id']#id
        态=自身._读桶(标签标识)#已有？
        if 态 is not None:#已开读
            return#停
        信号=标签['signal'] if 'signal' in 标签 else None#寿命
        加载=自身.属性['loadPage'] if 'loadPage' in 自身.属性 else None#面
        if 加载 is None:#无
            return#停
        加载(标签标识,自身._宿主文件(标签),1,信号)#首行

    def 应答导航(自身):
        """应答一次导航：未覆盖则续载；已覆盖则请求滚到行并记下修订。"""
        标签=自身._读标签()#tab
        if 标签 is None:#无
            return None#无指令
        标签标识=标签['id']#id
        态=自身._读桶(标签标识)#桶
        if 态 is None:#尚未开读
            return None#无
        导航=标签['navigation'] if 'navigation' in 标签 else None#导航
        if 导航 is None:#无
            return None#无
        修订=导航['revision'] if 'revision' in 导航 else None#修订
        if 态['revision']==修订:#已应答
            return None#无
        动作=自身.属性['actions'] if 'actions' in 自身.属性 else None#store 动作
        行=自身._导航行(标签)#目标行
        if 行 is None:#无行参数
            if 动作 is not None:#有写口
                动作['navigated'](标签标识,修订)#记下
            return None#无滚
        已载=已载页列表(态['pages'] if 'pages' in 态 else {})#页
        载至=已载末行(已载)#末行
        if 行>载至 and not (态['eof'] is True if 'eof' in 态 else False):#未覆盖且未尾
            失败中=('failure' in 态) and 态['failure'] is not None#有失败
            if not (态['loading'] is True if 'loading' in 态 else False) and not 失败中:#可续
                加载=自身.属性['loadPage'] if 'loadPage' in 自身.属性 else None#面
                信号=标签['signal'] if 'signal' in 标签 else None#寿命
                if 加载 is not None:#有
                    加载(标签标识,自身._宿主文件(标签),载至+1,信号)#续页
            return None#尚不滚
        if 动作 is not None:#有写口
            动作['navigated'](标签标识,修订)#记下应答
        return {'scrollToLine':行}#请宿主滚到行

    def 处理(自身,动作名,*参数):
        """响应结构树上的 wrap / reload / retry / more / scroll。"""
        标签=自身._读标签()#tab
        if 标签 is None:#无
            return#停
        标签标识=标签['id']#id
        信号=标签['signal'] if 'signal' in 标签 else None#寿命
        属性=自身.属性#props
        动作=属性['actions'] if 'actions' in 属性 else None#store 动作
        文件=自身._宿主文件(标签)#宿主文件
        态=自身._读桶(标签标识)#桶
        载至=已载末行(已载页列表(态['pages'] if 态 is not None and 'pages' in 态 else {}))#末行
        下一=载至+1#下一页起点
        if 动作名=='wrap':#切换换行
            if 动作 is not None:#有
                动作['toggledWrap'](标签标识)#翻转
            return#已处理
        if 动作名=='reload':#重载元数据与页
            元=自身._读元数据(标签['contentId'])#资源
            重载资源=元['reload'] if 'reload' in 元 else None#资源重载
            if 重载资源 is not None:#有
                重载资源()#再 stat
            重载页=属性['reloadPages'] if 'reloadPages' in 属性 else None#面
            if 重载页 is not None:#有
                重载页(标签标识,文件,信号)#再读页
            return#已处理
        if 动作名=='retry' or 动作名=='more':#重试或加载更多
            加载=属性['loadPage'] if 'loadPage' in 属性 else None#面
            if 加载 is not None:#有
                加载(标签标识,文件,下一,信号)#读下一页
            return#已处理
        if 动作名=='scroll':#记下滚动
            顶=参数[0] if len(参数)>0 else 0#滚动顶
            if 动作 is not None:#有
                动作['scrolled'](标签标识,顶)#记下
            return#已处理

    def 视图(自身):
        """投影预览结构树。"""
        自身.确保已开读()#首读
        标签=自身._读标签()#tab
        翻译=自身.属性['t'] if 't' in 自身.属性 else (lambda 键,_参=None:键)#文案
        if 标签 is None:#无 tab
            return {'type':'div','class':'status','data-textpreview-state':'loading','children':[
                {'type':'p','class':'statusLine','children':[翻译('loading')]},
            ]}#加载
        标签标识=标签['id']#id
        态=自身._读桶(标签标识)#桶
        if 态 is None:#尚在首读
            return {'type':'div','class':'status','data-textpreview-state':'loading','children':[
                {'type':'p','class':'statusLine','children':[翻译('loading')]},
            ]}#加载
        导航指令=自身.应答导航()#导航副作用
        文件=自身._宿主文件(标签)#宿主文件
        元=自身._读元数据(标签['contentId'])#元数据
        页表=态['pages'] if 'pages' in 态 and 态['pages'] is not None else {}#页表
        已载=已载页列表(页表)#已序页
        有页=len(已载)>0#是否有页
        行=自身._导航行(标签)#目标行
        恢复滚动=None#remount 恢复
        if 有页 and not 自身._曾有页:#首次见到页
            恢复滚动=态['scrollTop'] if 'scrollTop' in 态 else 0#恢复
        自身._曾有页=有页#记下
        值=元['value'] if 'value' in 元 else None#元数据值
        展示路径=文件['path']#回退路径
        if 值 is not None and 'absolutePath' in 值 and 值['absolutePath'] is not None:#有绝对
            展示路径=值['absolutePath']#展示
        换行=态['wrap'] is True if 'wrap' in 态 else True#是否换行
        子=[]#根子节点
        元失败=元['failure'] if 'failure' in 元 else None#元失败
        if 元失败 is not None:#元数据失败盖住变更栏
            子.append({#变更/失败栏
                'type':'p','class':'changed',
                'data-textpreview-meta-failed':元失败['code'] if 'code' in 元失败 else None,
                'children':[
                    {'type':'span','children':[失败行(翻译,元失败)]},
                    {'type':'button','class':'action','data-textpreview-reload-now':True,'onClick':'reload','children':[翻译('reloadNow')]},
                ],
            })#栏结束
        elif 值 is not None and ('changed' in 值) and 值['changed'] is True:#文件已改
            子.append({#变更栏
                'type':'p','class':'changed','data-textpreview-changed':True,'children':[
                    {'type':'span','children':[翻译('changed')]},
                    {'type':'button','class':'action','data-textpreview-reload-now':True,'onClick':'reload','children':[翻译('reloadNow')]},
                ],
            })#栏结束
        子.append({#页眉
            'type':'div','class':'header','children':[
                {'type':'div','class':'path','title':展示路径,'data-textpreview-path':True,'children':[展示路径]},
                {'type':'button','class':('tool toolOn' if 换行 else 'tool'),'aria-pressed':换行,
                 'aria-label':翻译('wrap'),'title':翻译('wrap'),'data-textpreview-tool':'wrap','onClick':'wrap',
                 'children':[图标换行线16()]},
                {'type':'button','class':'tool','aria-label':翻译('reload'),'title':翻译('reload'),
                 'data-textpreview-tool':'reload','onClick':'reload',
                 'children':[{'type':'IconRefreshOutline16'}]},
            ],
        })#页眉结束
        正文子=[]#正文子
        for 页 in 已载:#逐页
            行节点=[]#行
            for 下标,内容 in enumerate(页行列表(页)):#逐行
                号=页['offset']+下标#行号
                目标=行 is not None and 号==行#是否导航目标
                行属性={#行属性
                    'type':'div',
                    'class':('line lineTarget' if 目标 else 'line'),
                    'data-textpreview-line':号,
                    'children':[内容+'\n'],
                }#行结束
                if 目标:#目标行
                    行属性['data-textpreview-target']=号#标记
                行节点.append(行属性)#追加
            正文子.append({'type':'pre','class':'page','data-textpreview-page':页['offset'],'children':行节点})#页块
        失败=态['failure'] if 'failure' in 态 else None#页失败
        if 失败 is not None:#读失败
            正文子.append({#失败行
                'type':'p','class':'statusLine',
                'data-textpreview-failed':失败['code'] if 'code' in 失败 else None,
                'children':[
                    {'type':'span','children':[失败行(翻译,失败)]},
                    {'type':'button','class':'action','data-textpreview-retry':True,'onClick':'retry','children':[翻译('retry')]},
                ],
            })#失败结束
        if not (态['eof'] is True if 'eof' in 态 else False) and 失败 is None:#未尾且无失败
            在飞=态['loading'] is True if 'loading' in 态 else False#在飞
            正文子.append({#更多
                'type':'button','class':'more','disabled':在飞,'data-textpreview-more':True,'onClick':'more',
                'children':[翻译('loading') if 在飞 else 翻译('loadMore')],
            })#更多结束
        正文属性={#正文
            'type':'div',
            'class':('body wrap' if 换行 else 'body'),
            'data-textpreview-body':True,
            'onScroll':'scroll',
            'children':正文子,
        }#正文结束
        if 换行:#换行态
            正文属性['data-textpreview-wrap']=''#空串旗
        if 恢复滚动 is not None:#需恢复
            正文属性['scrollTop']=恢复滚动#宿主写入
        子.append(正文属性)#挂正文
        根={#根
            'type':'div','class':'preview','data-textpreview-state':'text',
            'data-textpreview-url':标签['contentId'],'children':子,
        }#根结束
        if 导航指令 is not None:#有滚行
            根['scrollToLine']=导航指令['scrollToLine']#请宿主
        return 根#视图

    def __call__(自身,属性=None):
        """对齐组件调用；返回视图模型。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.视图()#视图
