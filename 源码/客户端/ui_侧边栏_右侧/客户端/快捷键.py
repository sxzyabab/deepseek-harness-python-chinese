"""右侧栏拥有的命令：对着当前已挂载页解析。
与可见控件共用同一控制器；关闭在桌面无焦点时可退到关窗。
"""
import builtins#页面全局

__all__=['登记右侧侧栏快捷键']#仅中文公开名

def 关闭顶层模态(文档):
    """对齐 closeTopModal：关掉最前登记模态的 onClose。"""
    builtins.closeTopModal(文档)#关顶层

def 登记右侧侧栏快捷键(快捷键,侧栏,译,关闭窗口):
    """在可见控件所用控制器上登记侧栏命令。
    快捷键为本窗口有效绑定注册表；侧栏为当前会话与页拥有方；
    译为 sidebarRight 命名空间翻译；关闭窗口用当前配置修订号的私有原生关窗。
    返回命令释放回调。
    """
    def 原因(种类,目标):
        """分栏/全屏不可用时的阻断文案，可用则 None。"""
        if 种类=='split':#分栏
            阻断=侧栏.splitBlock(目标)#阻断键
            return None if 阻断 is None else 译('command.'+阻断)#文案
        if 目标['host']=='float':#浮层
            return 译('command.float')#浮层不可全屏
        return None#可用
    拆除表=[]#释放器表
    def 切换解析(_面=None):
        """展开／收起右侧栏。"""
        目标=侧栏.commandTarget(None)#命令目标
        if 目标 is None:#无会话
            return {'status':'blocked','reason':译('command.noSession')}#阻断
        def 跑():
            """当前目标才切换。"""
            if 侧栏.isTargetCurrent(目标):#仍当前
                侧栏.toggleExpanded()#切
        return {'status':'handled','run':跑}#已处理
    def 切换标签():
        """切换右侧栏标签。"""
        return 译('command.toggle')#标签
    拆除表.append(快捷键.register({#切换右侧栏
        'id':'sidebar.right.toggle',#命令 id
        'label':切换标签,#标签
        'aliases':['right sidebar','toggle right panel'],#别名
        'defaults':{#各平台
            'desktop:macos':{'code':'KeyB','modifiers':['primary','alt']},
            'desktop:windows':{'code':'KeyB','modifiers':['primary','alt']},
            'desktop:linux':{'code':'KeyB','modifiers':['primary','alt']},
            'web:macos':{'code':'KeyB','modifiers':['primary','shift']},
            'web:windows':{'code':'KeyB','modifiers':['primary','shift']},
        },#默认结束
        'regions':['page','editable','terminal'],#区域
        'modals':[],#模态
        'resolve':切换解析,#解析
    }))#登记结束
    for 种类 in ('split','fullscreen'):#分栏与全屏
        绑定=({'code':'Backslash','modifiers':['primary']} if 种类=='split'
            else {'code':'Enter','modifiers':['primary','alt']})#绑定
        def 造标签(种=种类):
            """闭包固定种类的标签。"""
            def 标签():
                """分栏或全屏标签。"""
                return 译('dock.splitPane' if 种=='split' else 'command.fullscreen')#标签
            return 标签#标签器
        def 造解析(种=种类):
            """闭包固定种类。"""
            def 解析(面):
                """分栏或全屏。"""
                元素=面['target'] if isinstance(面,dict) else 面.target#元素
                目标=侧栏.focusedTarget(元素)#焦点目标
                if 目标 is None:#无焦点
                    return {'status':'blocked','reason':译('command.noFocus')}#阻断
                不可用=原因(种,目标)#阻断文案
                if 不可用 is not None:#不可用
                    return {'status':'blocked','reason':不可用}#阻断
                def 跑():
                    """当前目标才执行。"""
                    if not 侧栏.isTargetCurrent(目标):#已过期
                        return#止
                    if 种=='split':#分栏
                        侧栏.split(目标['paneId'])#分
                    else:#全屏
                        侧栏.toggleFullscreen(目标)#切
                return {'status':'handled','run':跑}#已处理
            return 解析#解析器
        拆除表.append(快捷键.register({#分栏或全屏
            'id':'pane.split' if 种类=='split' else 'pane.fullscreen.toggle',#命令 id
            'label':造标签(),#标签
            'aliases':[种类,'panel'],#别名
            'defaults':{#各平台同绑定
                'desktop:macos':绑定,'desktop:windows':绑定,'desktop:linux':绑定,
                'web:macos':绑定,'web:windows':绑定,
            },#默认结束
            'regions':['page','editable','terminal'],#区域
            'modals':[],#模态
            'resolve':造解析(),#解析
        }))#登记结束
    for 种类 in ('close','refresh'):#关闭与刷新
        桌面={'code':'KeyW' if 种类=='close' else 'KeyR','modifiers':['primary']}#桌面
        网页={**桌面,'modifiers':['primary','alt']}#网页
        默认={#各平台
            'desktop:macos':桌面,'desktop:windows':桌面,'desktop:linux':桌面,
            'web:windows':网页,
        }#默认
        if 种类=='close':#关闭才绑 web mac
            默认['web:macos']=网页#web mac
        def 造页标签(种=种类):
            """闭包固定种类的页命令标签。"""
            def 标签():
                """关页或刷新标签。"""
                return 译('command.'+种)#标签
            return 标签#标签器
        def 造页解析(种=种类):
            """闭包固定种类。"""
            def 解析(面):
                """关页或刷新。"""
                元素=面['target'] if isinstance(面,dict) else 面.target#元素
                来源=面['source'] if isinstance(面,dict) else 面.source#来源
                模态=面['modal'] if isinstance(面,dict) else 面.modal#模态
                if 种=='close' and 模态 is not None:#关模态优先
                    def 关模态():
                        """关顶层模态。"""
                        关闭顶层模态(builtins.document)#关
                    return {'status':'handled','run':关模态}#已处理
                目标=侧栏.focusedTarget(元素)#焦点目标
                if 目标 is None and (来源=='iframe' or (元素 is not None
                    and 元素.closest('[data-sidebar-right-session]'))):#陈旧
                    return {'status':'blocked','reason':译('command.stale')}#阻断
                if 种=='refresh':#刷新
                    出现=目标['occurrence'] if 目标 is not None else None#出现次
                    命令=出现['commands'] if 出现 is not None else None#命令表
                    刷新=命令['refresh'] if 命令 is not None and 'refresh' in 命令 else None#刷新
                    if 目标 is None or 刷新 is None:#无刷新
                        return {'status':'blocked','reason':译('command.noRefresh')}#阻断
                    def 跑刷新(目=目标,刷=刷新):
                        """仍当前且刷新句柄未换才刷。"""
                        现出现=目['occurrence']#现出现
                        现刷=现出现['commands']['refresh'] if 现出现 is not None else None#现刷
                        if 侧栏.isTargetCurrent(目) and 现刷 is 刷:#仍有效
                            刷()#刷
                    return {'status':'handled','run':跑刷新}#已处理
                if 目标 is not None and 侧栏.canCloseTarget(目标):#可关页
                    def 跑关(目=目标):
                        """关目标。"""
                        侧栏.closeTarget(目)#关
                    return {'status':'handled','run':跑关}#已处理
                if 快捷键.runtime!='desktop':#非桌面无退路
                    return {'status':'blocked','reason':译('command.noFocus')}#阻断
                def 跑关窗(目=目标):
                    """无目标或仍当前则关窗。"""
                    if 目 is None or 侧栏.isTargetCurrent(目):#可关窗
                        关闭窗口()#关窗
                return {'status':'handled','run':跑关窗}#已处理
            return 解析#解析器
        拆除表.append(快捷键.register({#关页或刷新
            'id':'page.'+种类,#命令 id
            'label':造页标签(),#标签
            'aliases':[种类,'page'],#别名
            'defaults':默认,#默认
            'regions':['page','editable','terminal'],#区域
            'modals':['settings','shortcuts','other'] if 种类=='close' else [],#关闭参与模态
            'resolve':造页解析(),#解析
        }))#登记结束
    def 拆除():
        """逆序释放全部命令。"""
        for 卸 in reversed(拆除表):#逆序
            卸()#卸
    return 拆除#拆除器
