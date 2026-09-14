from .输入装饰 import 派生装饰,惰性装饰#镜像装饰
from .图像标签 import 附件错误文案,附件栏标签,拖放覆盖层标签,图像尺寸文案,灯箱标签#附件文案
from .上下文仪表 import 上下文仪表#占用环
from .权限选择 import 权限选择#访问模式

__all__=['输入栏']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键

def 空渲染槽(*位置参数,**关键字参数):
    """未注入槽渲染时不画。"""
    return None#不画

def 取自身(态):
    """选择器原样。"""
    return 态#原样

def 是命令源(源):
    """菜单源是否 command。"""
    return 源=='command'#是

def 取提示错(快照):
    """promptError。快照为 dict。"""
    return 快照['promptError'] if 'promptError' in 快照 else None#错

def 取运行(快照):
    """running。"""
    return 快照['running'] if 'running' in 快照 else False#运行

def 取子代理(快照):
    """subagent。"""
    return 快照['subagent'] if 'subagent' in 快照 else None#子代理

def 取已移除(快照):
    """removed。"""
    return 快照['removed'] if 'removed' in 快照 else False#移除

def 按at(项):
    """边界 at 排序键。"""
    return 项['at']#at

class 输入栏:#composer.bar 主体
    """草稿/附件/工具行/主按钮视图模型。"""
    def __init__(自身,属性=None):
        """记下 props 与本地 UI 态。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.预览=None#灯箱附件
        自身.拖放中=False#拖放
        自身.吐司=None#瞬时横幅
        自身.吐司序号=0#吐司键
        自身.合成中=False#IME

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 显示吐司(自身,文):
        """递增序号。"""
        自身.吐司序号+=1#序
        自身.吐司={'seq':自身.吐司序号,'text':文}#吐司

    def 关吐司(自身):
        """清。"""
        自身.吐司=None#清

    def 开预览(自身,附件):
        """打开灯箱。"""
        自身.预览=附件#记下

    def 关预览(自身):
        """关灯箱。"""
        自身.预览=None#清

    def 摘附件(自身,标识):
        """委派摘图。"""
        摘=自身.属性['removeImage'] if 'removeImage' in 自身.属性 else None#摘
        if 摘 is not None:#有
            摘(标识)#摘

    def 摄入图像(自身,文件列表,附件列表,限额,加图,翻译):
        """限额失败整批拒；否则委派加图。文件/限额为 dict。"""
        if 加图 is None or 文件列表 is None or len(文件列表)==0:#无；判 length
            return#停
        拒=None#拒文
        if 限额 is not None:#有限额
            类型列表=限额['mediaTypes'] if 'mediaTypes' in 限额 and 限额['mediaTypes'] is not None else []#类型
            超类型=False#格式
            for 文件 in 文件列表:#扫
                种=文件['type'] if 'type' in 文件 else None#种
                if 种 not in 类型列表:#不在
                    超类型=True#记下
                    break#停
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
                        超单=True#记下
                        break#停
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
        """令牌/芯片/文本引用/提示。装饰、输入为 dict。"""
        段=[]#段
        游标=0#游标
        令牌=装饰['token'] if 'token' in 装饰 else None#令牌
        if 令牌 is not None:#有
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
        """胶囊卡视图。"""
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
        停止=属性['stop'] if 'stop' in 属性 else None#停止
        命令=属性['command'] if 'command' in 属性 else None#命令
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#槽
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
        提示错=用会话(取提示错) if 用会话 is not None else None#提示错
        运行中=用会话(取运行) if 用会话 is not None else False#运行
        子代理=用会话(取子代理) if 用会话 is not None else None#子代理
        已移除=用会话(取已移除) if 用会话 is not None else False#移除
        计划活=False#计划占位
        有目标=False#目标
        限额=None#限额
        权限=None#权限
        if 用投影 is not None:#有投影
            计划=用投影('plan')#计划
            if 计划 is not None:#有帧
                待=计划['pending'] if 'pending' in 计划 else None#待
                活=计划['active'] if 'active' in 计划 else None#活
                计划活=活 if 待 is not True else (活 is not True)#活
            有目标=用投影('goal') is not None#目标
            限额=用投影('imageLimits')#限额
            权限=用投影('permissions')#权限
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
                有排队=True#有
                break#停
        可转向=禁用 is False and 机忙 is False and 命令菜单开 is False and 空 is True and 运行中 is True and 子代理 is None and 有排队 is True#整队转向
        装饰=惰性装饰 if 输入 is None else 派生装饰(输入,词表)#装饰
        背景=自身.构建背景(草稿,装饰,输入,有目标,翻译)#背景
        主停=运行中 is True and 子代理 is None#主钮停
        可中断=运行中 is True and 可续 is True#独立停
        主标=翻译('input.stop') if 主停 is True else 翻译('input.send')#主标
        def 主点():
            """停或提交。"""
            if 主停 is True:#停
                if 停止 is not None:#有
                    停止()#停
                return#停
            if 输入动作 is None:#无
                return#停
            if 空 is False and 禁用 is False and 机忙 is False:#可发
                提=输入动作['submit'] if 'submit' in 输入动作 else None#提交
                if 提 is not None:#有
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
        访问=None if 命令 is None else 权限选择({'value':权限,'locked':禁用,'command':命令,'t':翻译})()#访问
        仪表=上下文仪表({'useProjection':用投影,'t':翻译})() if 用投影 is not None else None#仪表
        栏项=[]#轨
        for 附 in 附件:#扫
            文=附['file'] if 'file' in 附 else None#文件
            名=文['name'] if 文 is not None and 'name' in 文 else None#名
            栏项.append({#轨
                'id':附['id'] if 'id' in 附 else None,#id
                'previewUrl':附['previewUrl'] if 'previewUrl' in 附 else None,#预览
                'alt':名 if 名 is not None else 翻译('image.pending'),#alt
                'removeLabel':翻译('image.remove',{'name':名}),#移除
                'attachment':附,#源
            })#结束
        可拖=禁用 is False and 机忙 is False and 加图 is not None#可拖
        覆盖限额=None if 限额 is None else {'count':限额['maxImagesPerMessage'] if 'maxImagesPerMessage' in 限额 else None,'size':图像尺寸文案(限额['maxImageBytes'] if 'maxImageBytes' in 限额 else None)}#覆盖
        相位=输入['phase'] if 输入 is not None and 'phase' in 输入 and 输入['phase'] is not None else 'inert'#相位
        通知文=None if 通知 is None else {'text':通知['text'] if 'text' in 通知 else None,'level':通知['level'] if 'level' in 通知 else None}#通知
        return {#视图
            'type':'input-bar',#类型
            'variant':变体,#变体
            'hero':变体=='hero',#英雄
            'dragActive':自身.拖放中,#拖放
            'dropOverlay':拖放覆盖层标签(翻译,可拖,覆盖限额) if 自身.拖放中 is True else None,#覆盖
            'toast':自身.吐司,#吐司
            'onDismissToast':自身.关吐司,#关吐司
            'notice':通知文,#通知
            'workspaceTrigger':工作区触发,#触发
            'onRequestWorkspace':请求工作区,#请求
            'overlay':属性['overlay'] if 'overlay' in 属性 else None,#叠层
            'accessory':属性['accessory'] if 'accessory' in 属性 else None,#附件配件
            'rail':栏项,#轨
            'railLabels':附件栏标签(翻译),#轨标
            'onOpenAttachment':自身.开预览,#开预览
            'onRemoveAttachment':自身.摘附件,#摘
            'draft':草稿,#草稿
            'backdrop':背景,#背景
            'mirror':草稿+'\n',#镜像
            'phase':相位,#相位
            'placeholder':占位,#占位
            'textareaDisabled':文本区禁用,#禁用
            'readOnly':机忙 is True or 工作区触发 is True,#只读
            'workspaceAria':翻译('hero.chooseWorkspace') if 工作区触发 is True else None,#无障碍
            'workspaceExpanded':挑选开 if 工作区触发 is True else None,#展开
            'leftItems':属性['leftItems'] if 'leftItems' in 属性 else None,#左
            'rightItems':属性['rightItems'] if 'rightItems' in 属性 else None,#右
            'accessSelect':访问,#访问
            'planSlot':渲染槽('conversation.input.plan',{'locked':禁用}),#计划席
            'modelSlot':渲染槽('conversation.input.model',{'locked':模型席锁}),#模型席
            'contextMeter':仪表,#仪表
            'commandMenuOpen':命令菜单开,#菜单开
            'commandsLabel':翻译('input.commands'),#命令标
            'commandsDisabled':禁用 is True or 切换菜单 is None,#命令禁
            'onToggleCommands':切换菜单,#切换
            'interruptible':可中断,#独立停
            'stopLabel':翻译('input.stop'),#停标
            'onStop':停止,#停
            'primaryLabel':主标,#主标
            'primaryStops':主停,#主停
            'primaryDisabled':(停止 is None) if 主停 is True else (空 is True or 禁用 is True or 机忙 is True),#主禁
            'onPrimary':主点,#主点
            'preview':自身.预览,#预览
            'previewLabels':灯箱标签(翻译),#灯箱
            'onClosePreview':自身.关预览,#关预览
            'footer':属性['footer'] if 'footer' in 属性 else None,#脚
            'sessionId':会话标识,#会话
            'resolveSubmitMode':解析提交,#提交模式
            'keyboard':键盘,#键盘面
            'canSteerQueue':可转向,#可转向
            'cssModule':'输入栏.module.css',#样式
        }#结束

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
