from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from .输入装饰 import 派生装饰,惰性装饰#镜像装饰
from .图像标签 import 附件错误文案,附件栏标签,拖放覆盖层标签,图像尺寸文案,灯箱标签#附件文案
from .上下文仪表 import 上下文仪表#占用环

__all__=['输入栏']#仅中文公开名

def 恒等翻译(键,参数=None):
    '无宿主文案时用本包中文词典，没有则返回键本身。'
    if 键 not in 对话文案:#词典没有
        return 键#键
    文本=对话文案[键]#词条
    if 参数 is None:#无参数
        return 文本#原文
    for 名 in 参数:#替换占位
        文本=文本.replace('{'+名+'}',str(参数[名]))#替换
    return 文本#译完

def 取自身(态):
    '选择器原样'
    return 态#原样

def 是命令源(源):
    '菜单源是否 command'
    return 源=='command'#是

def 取子代理(快照):
    'subagent'
    return 快照['subagent'] if 'subagent' in 快照 else None#子代理

def 取已移除(快照):
    'removed'
    return 快照['removed'] if 'removed' in 快照 else False#移除

def 按at(项):
    '边界 at 排序键'
    return 项['at']#at

class 输入栏:#composer.bar 主体
    '草稿/附件/工具行/主按钮视图模型'
    def __init__(自身,属性=None):
        '保存 props 与本地界面状态'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.预览=None#灯箱附件
        自身.拖放中=False#拖放
        自身.吐司=None#瞬时横幅
        自身.吐司序号=0#吐司键
        自身.合成中=False#IME
        自身.画面=None#可反复清空的画面
        自身.仪表=None#上下文占用
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 显示吐司(自身,文):
        '递增序号'
        自身.吐司序号+=1#序
        自身.吐司={'seq':自身.吐司序号,'text':文}#吐司

    def 关吐司(自身):
        '关掉吐司'
        自身.吐司=None

    def 开预览(自身,附件):
        '打开灯箱'
        自身.预览=附件

    def 关预览(自身):
        '关灯箱'
        自身.预览=None

    def 摘附件(自身,标识):
        '委派摘图'
        摘=自身.属性['removeImage'] if 'removeImage' in 自身.属性 else None#摘
        if 摘 is not None:
            摘(标识)#摘

    def 摄入图像(自身,文件列表,附件列表,限额,加图,翻译):
        '限额失败整批拒；否则委派加图。文件/限额为 dict'
        if 加图 is None or 文件列表 is None or len(文件列表)==0:#无；判 length
            return
        拒=None#拒文
        if 限额 is not None:
            类型列表=限额['mediaTypes'] if 'mediaTypes' in 限额 and 限额['mediaTypes'] is not None else []#类型
            超类型=False#格式
            for 文件 in 文件列表:#扫
                种=文件['type'] if 'type' in 文件 else None#种
                if 种 not in 类型列表:#不在
                    超类型=True
                    break
            if 超类型 is True:#格式
                拒=加图(文件列表)#权威拒
            elif len(附件列表)+len(文件列表)>(限额['maxImagesPerMessage'] if 'maxImagesPerMessage' in 限额 else 0):#张数；判 length
                拒=翻译('image.tooMany',{'count':限额['maxImagesPerMessage'] if 'maxImagesPerMessage' in 限额 else None})#张数
            else:#体积
                单限=限额['maxImageBytes'] if 'maxImageBytes' in 限额 else 0#单张
                超单=False#超
                for 文件 in 文件列表:#扫
                    体=文件['size'] if 'size' in 文件 else 0#体
                    if 体>单限:#超
                        超单=True
                        break
                if 超单 is True:#单张
                    拒=翻译('image.fileTooLarge',{'size':图像尺寸文案(单限)})#体积
                else:#合计
                    已有=0#已有
                    for 附 in 附件列表:#扫
                        文=附['file'] if 'file' in 附 else None#文件
                        已有+=(文['size'] if 文 is not None and 'size' in 文 else 0)#加
                    新增=0#新增
                    for 文件 in 文件列表:#扫
                        新增+=(文件['size'] if 'size' in 文件 else 0)#加
                    合计限=限额['maxMessageImageBytes'] if 'maxMessageImageBytes' in 限额 else 0#合计
                    if 已有+新增>合计限:#超
                        拒=翻译('image.totalTooLarge',{'size':图像尺寸文案(合计限)})#合计
                    else:#通过预检
                        拒=加图(文件列表)#加
        else:#无限额
            拒=加图(文件列表)#加
        if 拒 is not None:#失败
            自身.显示吐司(拒)#横幅

    def 构建背景(自身,草稿,装饰,输入,有目标,翻译):
        '令牌/芯片/文本引用/提示。装饰、输入为 dict'
        段=[]#段
        游标=0#游标
        令牌=装饰['token'] if 'token' in 装饰 else None#令牌
        if 令牌 is not None:
            段.append({'kind':'token','text':草稿[令牌['start']:令牌['end']]})#标
            游标=令牌['end']#推
        界=[]#边界
        芯片列表=装饰['chips'] if 'chips' in 装饰 and 装饰['chips'] is not None else []#芯片
        for 芯 in 芯片列表:#芯片
            界.append({'at':芯['offset'],'kind':'chip','chip':芯})#界
        引用列表=装饰['textRefs'] if 'textRefs' in 装饰 and 装饰['textRefs'] is not None else []#引用
        for 引 in 引用列表:#引用
            界.append({'at':引['start'],'kind':'text-ref','ref':引})#界
        界.sort(key=按at)#序
        for 边 in 界:#扫
            if 边['at']<游标:#令牌覆盖
                continue#跳
            if 边['at']>游标:#纯文
                段.append({'kind':'plain','text':草稿[游标:边['at']]})#文
            if 边['kind']=='chip':#芯片
                芯=边['chip']#芯
                段.append({'kind':'chip','occurrenceId':芯['occurrenceId'],'label':芯['label'],'invalid':芯['invalid']})#芯
                游标=芯['offset']+1#占位
            else:#文本引用
                引=边['ref']#引
                段.append({'kind':'text-ref','text':草稿[引['start']:引['end']]})#标
                游标=引['end']#推
        if 游标<len(草稿):#尾；判 length
            段.append({'kind':'plain','text':草稿[游标:]})#尾
        提示=装饰['hint'] if 'hint' in 装饰 else None#提示
        if 提示 is not None:#提示
            认领=输入['claim'] if 输入 is not None and 'claim' in 输入 else None#认领
            令牌文=认领['token'] if 认领 is not None and 'token' in 认领 and 认领['token'] is not None else ''#令牌
            命令名=令牌文[1:].strip() if 令牌文.startswith('/') else 令牌文.strip()#名
            键='hint.goal.active' if 命令名=='goal' and 有目标 is True else 'hint.'+命令名#键
            译=翻译(键)#译
            显=译 if 译!=键 else 装饰['hint']#显
            段.append({'kind':'hint','text':显})#提示
        return 段#段

    def 渲染(自身):
        '胶囊卡视图'
        属性=自身.属性#props
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话
        用输入=属性['useInput'] if 'useInput' in 属性 else None#输入
        输入动作=属性['inputActions'] if 'inputActions' in 属性 else None#动作
        键盘=属性['keyboard'] if 'keyboard' in 属性 else None#键盘
        加图=属性['addImages'] if 'addImages' in 属性 else None#加图
        摘图=属性['removeImage'] if 'removeImage' in 属性 else None#摘图
        草稿图=属性['draftImages'] if 'draftImages' in 属性 else None#草稿图
        解析提交=属性['resolveSubmitMode'] if 'resolveSubmitMode' in 属性 else None#提交模式
        切换菜单=属性['toggleCommandMenu'] if 'toggleCommandMenu' in 属性 else None#命令菜单
        停止=属性['stop'] if 'stop' in 属性 else None
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        缺键=[]
        if 'renderSlot' in 属性:
            渲染槽=属性['renderSlot']
        else:
            渲染槽=None
            缺键.append('renderSlot')
        用通知=属性['useNotices'] if 'useNotices' in 属性 else None#通知
        用词表=属性['useLexicon'] if 'useLexicon' in 属性 else None#词表
        用菜单=属性['useMenuLauncher'] if 'useMenuLauncher' in 属性 else None#菜单启动
        用投影=属性['useProjection'] if 'useProjection' in 属性 else None#投影
        会话标识=属性['sessionId'] if 'sessionId' in 属性 else None#会话
        变体=属性['variant'] if 'variant' in 属性 and 属性['variant'] is not None else 'composer'#变体
        惰性=属性['disabled'] is True if 'disabled' in 属性 else False#无工作区
        阻断=属性['blocked'] if 'blocked' in 属性 else None#阻断
        挑选开=属性['workspacePickerOpen'] is True if 'workspacePickerOpen' in 属性 else False#挑选
        请求工作区=属性['onRequestWorkspace'] if 'onRequestWorkspace' in 属性 else None#请求挑选
        占位=属性['placeholder'] if 'placeholder' in 属性 else None#占位
        输入=用输入(取自身) if 用输入 is not None else None#输入态
        通知=用通知(取自身) if 用通知 is not None else None#通知
        词表值=用词表(取自身) if 用词表 is not None else None#词表
        词表=词表值 if 词表值 is not None else {}#空则空表
        命令菜单开=用菜单(是命令源) if 用菜单 is not None else False#命令菜单
        会话快照=用会话(取自身) if 用会话 is not None else None
        if isinstance(会话快照,dict) and 'promptError' in 会话快照:
            提示错=会话快照['promptError']
        else:
            提示错=None
            缺键.append('promptError')
        if isinstance(会话快照,dict) and 'running' in 会话快照:
            运行中=会话快照['running']
        else:
            运行中=None
            缺键.append('running')
        子代理=用会话(取子代理) if 用会话 is not None else None#子代理
        已移除=用会话(取已移除) if 用会话 is not None else False#移除
        计划活=False#计划占位
        有目标=False#目标
        限额=None#限额
        if 用投影 is not None:
            计划=用投影('plan')#计划
            if 计划 is not None:
                待=计划['pending'] if 'pending' in 计划 else None#待
                活=计划['active'] if 'active' in 计划 else None#活
                计划活=活 if 待 is not True else (活 is not True)#活
            有目标=用投影('goal') is not None#目标
            限额=用投影('imageLimits')#限额
        活着=输入 is not None and 键盘 is not None and 输入动作 is not None#机面齐全
        草稿值=输入['draft'] if 输入 is not None and 'draft' in 输入 else None#草稿
        草稿=草稿值 if 草稿值 is not None else ''#空则空串
        图列=输入['imageIds'] if 输入 is not None and 'imageIds' in 输入 else None#图 id
        图标识=图列 if 图列 is not None else []#空则空表
        附件=草稿图(图标识) if 草稿图 is not None and 输入 is not None else []#附件
        空=草稿.strip()=='' and len(附件)==0#空；判 length
        if 提示错 is not None:#提示失败
            错=提示错['error'] if 'error' in 提示错 else None#错
            码=错['code'] if 错 is not None and 'code' in 错 else None#码
            if 码=='attachment-error':#附件
                详=错['details'] if 错 is not None and 'details' in 错 else None#详
                因=详['reason'] if 详 is not None and 'reason' in 详 else None#因
                自身.显示吐司(附件错误文案(翻译,因,限额))#文案
            else:#其它
                消息=错['message'] if 错 is not None and 'message' in 错 else None#消息
                自身.显示吐司(str(消息)+' ('+str(码)+')')#原文
        地址=子代理['address'] if 子代理 is not None and 'address' in 子代理 else None#地址
        可续=地址 is not None and ('mode' in 地址) and 地址['mode']=='continuable'#可续
        父离线=可续 is True and (子代理['parentAvailable'] is not True if 'parentAvailable' in 子代理 else True)#父离
        禁用=已移除 is True or 惰性 is True or 活着 is False or 阻断 is not None or 父离线 is True#禁用
        模型席锁=已移除 is True or 惰性 is True or 活着 is False#模型锁
        机忙=输入['phase'] in ('adjudicating','submitting') if 输入 is not None and 'phase' in 输入 else False#忙
        工作区触发=惰性 is True and 已移除 is False and 请求工作区 is not None#触发
        文本区禁用=已移除 is True or (禁用 is True and 工作区触发 is False)#文本禁用
        队列列=输入['queue'] if 输入 is not None and 'queue' in 输入 else None#队列
        队列=队列列 if 队列列 is not None else []#空则空表
        有排队=False#整队
        for 项 in 队列:#扫
            if ('placement' in 项) and 项['placement']=='queued':#排队
                有排队=True
                break
        可转向=禁用 is False and 机忙 is False and 命令菜单开 is False and 空 is True and 运行中 is True and 子代理 is None and 有排队 is True#整队转向
        装饰=惰性装饰 if 输入 is None else 派生装饰(输入,词表)#装饰
        背景=自身.构建背景(草稿,装饰,输入,有目标,翻译)#背景
        主停=运行中 is True and 子代理 is None#主钮停
        可中断=运行中 is True and 可续 is True#独立停
        主标=翻译('input.stop') if 主停 is True else 翻译('input.send')#主标
        def 主点():
            '停或提交'
            if 主停 is True:
                if 停止 is not None:
                    停止()
                return
            if 输入动作 is None:#无
                return
            if 空 is False and 禁用 is False and 机忙 is False:#可发
                提=输入动作['submit'] if 'submit' in 输入动作 else None#提交
                if 提 is not None:
                    提()#发
        if 占位 is None:#派生占位
            if 父离线 is True:#父离
                占位=翻译('placeholder.parentOffline')#占位
            elif 禁用 is True:#不可用
                占位=翻译('placeholder.unavailable')#占位
            elif 可转向 is True:#转向
                占位=翻译('placeholder.steerQueue')#占位
            elif 计划活 is True:#计划
                占位=翻译('placeholder.plan')#占位
            else:#默认
                占位=翻译('placeholder.default')#占位
        if 自身.画面 is None:
            自身.画面=界面.column().classes('输入栏')
            def 点卡():
                '没有工作区时，点整张卡片打开菜单。'
                现=自身.属性 if isinstance(自身.属性,dict) else {}
                请求=现['onRequestWorkspace'] if 'onRequestWorkspace' in 现 else None
                要选=现['disabled'] is True if 'disabled' in 现 else False
                if 要选 is True and 请求 is not None:
                    请求()
            自身.画面.on('click',点卡)
        自身.画面.classes(remove='输入卡 hero composer')
        自身.画面.classes(add='输入卡 '+变体)
        自身.画面.clear()
        可拖=禁用 is False and 机忙 is False and 加图 is not None#可拖
        覆盖限额=None if 限额 is None else {'count':限额['maxImagesPerMessage'] if 'maxImagesPerMessage' in 限额 else None,'size':图像尺寸文案(限额['maxImageBytes'] if 'maxImageBytes' in 限额 else None)}#覆盖
        轨标=附件栏标签(翻译)#轨标
        with 自身.画面:#栏
            for 键 in 缺键:
                界面.label(键).classes('槽位缺口')
            if 自身.吐司 is not None and 'text' in 自身.吐司 and 自身.吐司['text'] is not None:#吐司
                界面.label(str(自身.吐司['text']))#吐司
                def 点关吐司():
                    '关掉吐司。'
                    自身.关吐司()#关
                界面.button(翻译('image.closePreview'),on_click=点关吐司)#关闭
            if 通知 is not None and 'text' in 通知 and 通知['text'] is not None:#通知
                界面.label(str(通知['text']))#通知
            if 自身.拖放中 is True:#拖放
                覆盖=拖放覆盖层标签(翻译,可拖,覆盖限额)#覆盖
                界面.label(覆盖['title'])#标题
                if 'desc' in 覆盖 and 覆盖['desc'] is not None:#说明
                    界面.label(覆盖['desc'])#说明
            if len(附件)>0:#附件
                界面.label(轨标['group'])#待发
                for 附 in 附件:#逐个
                    文=附['file'] if 'file' in 附 else None#文件
                    名=文['name'] if 文 is not None and 'name' in 文 else None#名
                    显名=名 if 名 is not None else 翻译('image.pending')#名
                    def 点开(钉附=附):
                        '打开预览。'
                        自身.开预览(钉附)#开
                    def 点摘(钉标识=附['id'] if 'id' in 附 else None):
                        '移除附件。'
                        if 钉标识 is not None:
                            自身.摘附件(钉标识)#摘
                    界面.button(显名,on_click=点开)#预览
                    界面.button(翻译('image.remove',{'name':显名}),on_click=点摘)#移除
            for 段 in 背景:#背景
                种=段['kind'] if 'kind' in 段 else ''#种
                if 种=='chip':#芯片
                    标=段['label'] if 'label' in 段 and 段['label'] is not None else ''#标
                    if 标=='':#空芯片
                        pass#不画
                    else:#芯片
                        界面.label(标).classes('芯片')#芯片
                else:#文本
                    文=段['text'] if 'text' in 段 and 段['text'] is not None else ''#文
                    if 文=='':#空段
                        pass#不画
                    else:#段
                        界面.label(文)#段
            框=界面.textarea(value=草稿,placeholder=占位).props('borderless autogrow').classes('草稿')
            def 草稿变():
                '把草稿写回输入机。'
                if 输入动作 is None:#无
                    return
                设=输入动作['setDraft'] if 'setDraft' in 输入动作 else None#写
                if 设 is None:#无
                    return
                值=框.value if 框.value is not None else ''#文
                设(值)#写
            框.on_value_change(草稿变)#改
            if 文本区禁用 is True or 机忙 is True or 工作区触发 is True:#不可编辑
                框.props('disable')#禁用
            if 渲染槽 is not None and 会话标识 is not None:
                渲染槽('conversation.input.permission',{'locked':禁用})
            if 渲染槽 is not None:
                渲染槽('conversation.input.plan',{'locked':禁用})
                渲染槽('conversation.input.model',{'locked':模型席锁})
            if 用投影 is not None:#占用
                if 自身.仪表 is None:#首次
                    自身.仪表=上下文仪表()#仪表
                自身.仪表.更新({'useProjection':用投影,'t':翻译})#灌入
                自身.仪表.渲染()#自己画
            if 禁用 is False and 切换菜单 is not None:#命令
                def 点命令():
                    '打开命令菜单。'
                    切换菜单()#切换
                界面.button(翻译('input.commands'),on_click=点命令)#命令
            if 可中断 is True:#独立停止
                def 点停():
                    '停止生成。'
                    if 停止 is not None:
                        停止()
                界面.button(翻译('input.stop'),on_click=点停)
            with 界面.element('div').classes('工具行'):#底栏
                with 界面.element('div').classes('尾组'):#发送靠右
                    钮=界面.button(on_click=主点).props('unelevated round').classes('发送钮'+(' 发送空' if 空 is True else ''))
                    钮.tooltip(主标)
                    钮.props('aria-label="'+主标+'"')
                    with 钮:
                        界面.html('<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M8.3125 0.980183C8.66767 1.0531 8.97902 1.20418 9.2627 1.43233C9.48724 1.61297 9.73029 1.85793 9.97949 2.10714L14.707 6.83468L13.293 8.24874L9 3.95577V15.0417H7V3.95577L2.70703 8.24874L1.29297 6.83468L6.02051 2.10714C6.26971 1.85793 6.51277 1.61297 6.7373 1.43233C6.97662 1.23986 7.28445 1.04402 7.6875 0.980183C7.8973 0.947006 8.1031 0.95516 8.3125 0.980183Z"/></svg>',sanitize=False)
            if 自身.预览 is not None:#灯箱
                灯=灯箱标签(翻译)#标签
                界面.label(灯['dialog'])#预览
                def 点关预览():
                    '关闭预览。'
                    自身.关预览()#关
                界面.button(灯['close'],on_click=点关预览)#关闭
            脚=属性['footer'] if 'footer' in 属性 else None#脚
            if 脚 is not None and hasattr(脚,'渲染'):#脚组件
                脚.渲染()#自己画
        del 解析提交#提交模式仍由主按钮的输入动作决定
        del 键盘#按键仍由宿主输入机处理
        del 可转向#排队转向体现在占位文案
        del 挑选开#菜单开合由工作区按钮承担
        del 命令菜单开#命令按钮不依赖结构树标记

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()#渲
