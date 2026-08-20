"""默认 composer 栏：conversation.composer.bar 槽入口。

对齐上游 `ui-conversation/src/client/skeleton/InputBar.tsx`。公开面仅中文名。
机状态经 useInput/inputActions；键盘/停止经 inject。
"""
from .输入装饰 import 派生装饰,惰性装饰#镜像装饰
from .图像标签 import 附件错误文案,附件栏标签,拖放覆盖层标签,图像尺寸文案,灯箱标签#附件文案
from .上下文仪表 import 上下文仪表#占用环
from .权限选择 import 权限选择#访问模式

__all__=['输入栏']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 输入栏:#composer.bar 主体
    """草稿/附件/工具行/主按钮视图模型。"""

    def __init__(自身,属性=None):#构造
        """记下 props 与本地 UI 态。"""
        自身.属性=属性 or {}#合成
        自身.预览=None#灯箱附件
        自身.拖放中=False#拖放
        自身.吐司=None#瞬时横幅
        自身.吐司序号=0#吐司键
        自身.合成中=False#IME

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 显示吐司(自身,文):#瞬时横幅
        """递增序号。"""
        自身.吐司序号+=1#序
        自身.吐司={'seq':自身.吐司序号,'text':文}#吐司

    def 关吐司(自身):#关吐司
        """清。"""
        自身.吐司=None#清

    def 摄入图像(自身,文件们,附件们,限额,加图,翻译):#整批预检
        """限额失败整批拒；否则委派加图。"""
        if 加图 is None or not 文件们:#无
            return#停
        拒=None#拒文
        if 限额 is not None:#有限额
            类型们=取字段(限额,'mediaTypes') or []#类型
            if any(取字段(f,'type') not in 类型们 for f in 文件们):#格式
                拒=加图(文件们)#权威拒
            elif len(附件们)+len(文件们)>取字段(限额,'maxImagesPerMessage',0):#张数
                拒=翻译('image.tooMany',{'count':取字段(限额,'maxImagesPerMessage')})#张数
            elif any(取字段(f,'size',0)>取字段(限额,'maxImageBytes',0) for f in 文件们):#单张
                拒=翻译('image.fileTooLarge',{'size':图像尺寸文案(取字段(限额,'maxImageBytes'))})#体积
            else:#合计
                已有=sum(取字段(取字段(a,'file'),'size',0) for a in 附件们)#已有
                新增=sum(取字段(f,'size',0) for f in 文件们)#新增
                if 已有+新增>取字段(限额,'maxMessageImageBytes',0):#超
                    拒=翻译('image.totalTooLarge',{'size':图像尺寸文案(取字段(限额,'maxMessageImageBytes'))})#合计
                else:#通过预检
                    拒=加图(文件们)#加
        else:#无限额
            拒=加图(文件们)#加
        if 拒 is not None:#失败
            自身.显示吐司(拒)#横幅

    def 构建背景(自身,草稿,装饰,输入,有目标,翻译):#镜像层段
        """令牌/芯片/文本引用/提示。"""
        段=[]#段
        游标=0#游标
        令牌=装饰.get('token')#令牌
        if 令牌 is not None:#有
            段.append({'kind':'token','text':草稿[令牌['start']:令牌['end']]})#标
            游标=令牌['end']#推
        界=[]#边界
        for 芯 in 装饰.get('chips') or []:#芯片
            界.append({'at':芯['offset'],'kind':'chip','chip':芯})#界
        for 引 in 装饰.get('textRefs') or []:#引用
            界.append({'at':引['start'],'kind':'text-ref','ref':引})#界
        界.sort(key=lambda b:b['at'])#序
        for b in 界:#扫
            if b['at']<游标:#令牌覆盖
                continue#跳
            if b['at']>游标:#纯文
                段.append({'kind':'plain','text':草稿[游标:b['at']]})#文
            if b['kind']=='chip':#芯片
                芯=b['chip']#芯
                段.append({'kind':'chip','occurrenceId':芯['occurrenceId'],'label':芯['label'],'invalid':芯['invalid']})#芯
                游标=芯['offset']+1#占位
            else:#文本引用
                引=b['ref']#引
                段.append({'kind':'text-ref','text':草稿[引['start']:引['end']]})#标
                游标=引['end']#推
        if 游标<len(草稿):#尾
            段.append({'kind':'plain','text':草稿[游标:]})#尾
        if 装饰.get('hint') is not None:#提示
            认领=取字段(输入,'claim')#认领
            令牌文=取字段(认领,'token') or ''#令牌
            命令名=令牌文[1:].strip() if 令牌文.startswith('/') else 令牌文.strip()#名
            键=f'hint.{"goal.active" if 命令名=="goal" and 有目标 else 命令名}'#键
            译=翻译(键)#译
            显=译 if 译!=键 else 装饰['hint']#显
            段.append({'kind':'hint','text':显})#提示
        return 段#段

    def 渲染(自身):#结构树
        """胶囊卡视图。"""
        属性=自身.属性#props
        用会话=取字段(属性,'useSession')#会话
        用输入=取字段(属性,'useInput')#输入
        输入动作=取字段(属性,'inputActions')#动作
        键盘=取字段(属性,'keyboard')#键盘
        加图=取字段(属性,'addImages')#加图
        摘图=取字段(属性,'removeImage')#摘图
        草稿图=取字段(属性,'draftImages')#草稿图
        解析提交=取字段(属性,'resolveSubmitMode')#提交模式
        切换菜单=取字段(属性,'toggleCommandMenu')#命令菜单
        停止=取字段(属性,'stop')#停止
        命令=取字段(属性,'command')#命令
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        渲染槽=取字段(属性,'renderSlot',lambda *_a,**_k:None)#槽
        用通知=取字段(属性,'useNotices')#通知
        用词表=取字段(属性,'useLexicon')#词表
        用菜单=取字段(属性,'useMenuLauncher')#菜单启动
        用投影=取字段(属性,'useProjection')#投影
        会话标识=取字段(属性,'sessionId')#会话
        变体=取字段(属性,'variant') or 'composer'#变体
        惰性=bool(取字段(属性,'disabled',False))#无工作区
        阻断=取字段(属性,'blocked')#阻断
        挑选开=bool(取字段(属性,'workspacePickerOpen',False))#挑选
        请求工作区=取字段(属性,'onRequestWorkspace')#请求挑选
        占位=取字段(属性,'placeholder')#占位
        def 读(钩,选,缺省=None):#安全钩
            """钩缺席则缺省。"""
            if 钩 is None:#无
                return 缺省#缺
            return 钩(选)#投影
        输入=读(用输入,lambda s:s)#输入态
        通知=读(用通知,lambda s:s)#通知
        词表=读(用词表,lambda s:s) or {}#词表
        命令菜单开=读(用菜单,lambda 源:源=='command',False)#命令菜单
        提示错=读(用会话,lambda s:取字段(s,'promptError'))#提示错
        运行中=读(用会话,lambda s:取字段(s,'running'),False)#运行
        子代理=读(用会话,lambda s:取字段(s,'subagent'))#子代理
        已移除=读(用会话,lambda s:取字段(s,'removed'),False)#移除
        计划活=False#计划占位
        有目标=False#目标
        限额=None#限额
        权限=None#权限
        if 用投影 is not None:#有投影
            计划=用投影('plan')#计划
            if 计划 is not None:#有帧
                计划活=取字段(计划,'active') if not 取字段(计划,'pending') else not 取字段(计划,'active')#活
            有目标=用投影('goal') is not None#目标
            限额=用投影('imageLimits')#限额
            权限=用投影('permissions')#权限
        活着=输入 is not None and 键盘 is not None and 输入动作 is not None#机面齐全
        草稿=取字段(输入,'draft') or '' if 输入 is not None else ''#草稿
        图标识=取字段(输入,'imageIds') or [] if 输入 is not None else []#图 id
        附件=草稿图(图标识) if 草稿图 is not None and 输入 is not None else []#附件
        空=草稿.strip()=='' and len(附件)==0#空
        if 提示错 is not None:#提示失败
            错=取字段(提示错,'error')#错
            if 取字段(错,'code')=='attachment-error':#附件
                自身.显示吐司(附件错误文案(翻译,取字段(取字段(错,'details'),'reason'),限额))#文案
            else:#其它
                自身.显示吐司(f'{取字段(错,"message")} ({取字段(错,"code")})')#原文
        可续=取字段(取字段(子代理,'address'),'mode')=='continuable' if 子代理 is not None else False#可续
        父离线=可续 and not 取字段(子代理,'parentAvailable')#父离
        禁用=已移除 or 惰性 or not 活着 or 阻断 is not None or 父离线#禁用
        模型席锁=已移除 or 惰性 or not 活着#模型锁
        机忙=取字段(输入,'phase') in ('adjudicating','submitting') if 输入 is not None else False#忙
        工作区触发=惰性 and not 已移除 and 请求工作区 is not None#触发
        文本区禁用=已移除 or (禁用 and not 工作区触发)#文本禁用
        队列=取字段(输入,'queue') or [] if 输入 is not None else []#队列
        可转向=not 禁用 and not 机忙 and not 命令菜单开 and 空 and 运行中 and 子代理 is None and any(取字段(r,'placement')=='queued' for r in 队列)#整队转向
        装饰=惰性装饰 if 输入 is None else 派生装饰(输入,词表)#装饰
        背景=自身.构建背景(草稿,装饰,输入,有目标,翻译)#背景
        主停=运行中 and 子代理 is None#主钮停
        可中断=运行中 and 可续#独立停
        主标=翻译('input.stop') if 主停 else 翻译('input.send')#主标
        def 主点():#主钮
            """停或提交。"""
            if 主停:#停
                if 停止 is not None:#有
                    停止()#停
                return#停
            if 输入动作 is None:#无
                return#停
            if not 空 and not 禁用 and not 机忙:#可发
                提=取字段(输入动作,'submit')#提交
                if 提 is not None:#有
                    提()#发
        if 占位 is None:#派生占位
            if 父离线:#父离
                占位=翻译('placeholder.parentOffline')#占位
            elif 禁用:#不可用
                占位=翻译('placeholder.unavailable')#占位
            elif 可转向:#转向
                占位=翻译('placeholder.steerQueue')#占位
            elif 计划活:#计划
                占位=翻译('placeholder.plan')#占位
            else:#默认
                占位=翻译('placeholder.default')#占位
        访问=None if 命令 is None else 权限选择({'value':权限,'locked':禁用,'command':命令,'t':翻译})()#访问
        仪表=上下文仪表({'useProjection':用投影,'t':翻译})() if 用投影 is not None else None#仪表
        栏项=[{#轨
            'id':取字段(a,'id'),#id
            'previewUrl':取字段(a,'previewUrl'),#预览
            'alt':取字段(取字段(a,'file'),'name') or 翻译('image.pending'),#alt
            'removeLabel':翻译('image.remove',{'name':取字段(取字段(a,'file'),'name')}),#移除
            'attachment':a,#源
        } for a in 附件]#轨
        可拖=not 禁用 and not 机忙 and 加图 is not None#可拖
        return {#视图
            'type':'input-bar',#类型
            'variant':变体,#变体
            'hero':变体=='hero',#英雄
            'dragActive':自身.拖放中,#拖放
            'dropOverlay':拖放覆盖层标签(翻译,可拖,None if 限额 is None else {'count':取字段(限额,'maxImagesPerMessage'),'size':图像尺寸文案(取字段(限额,'maxImageBytes'))}) if 自身.拖放中 else None,#覆盖
            'toast':自身.吐司,#吐司
            'onDismissToast':自身.关吐司,#关吐司
            'notice':None if 通知 is None else {'text':取字段(通知,'text'),'level':取字段(通知,'level')},#通知
            'workspaceTrigger':工作区触发,#触发
            'onRequestWorkspace':请求工作区,#请求
            'overlay':取字段(属性,'overlay'),#叠层
            'accessory':取字段(属性,'accessory'),#附件配件
            'rail':栏项,#轨
            'railLabels':附件栏标签(翻译),#轨标
            'onOpenAttachment':lambda a:自身.__setattr__('预览',a),#开预览
            'onRemoveAttachment':lambda i:(摘图(i) if 摘图 is not None else None),#摘
            'draft':草稿,#草稿
            'backdrop':背景,#背景
            'mirror':草稿+'\n',#镜像
            'phase':取字段(输入,'phase') or 'inert',#相位
            'placeholder':占位,#占位
            'textareaDisabled':文本区禁用,#禁用
            'readOnly':机忙 or 工作区触发,#只读
            'workspaceAria':翻译('hero.chooseWorkspace') if 工作区触发 else None,#无障碍
            'workspaceExpanded':挑选开 if 工作区触发 else None,#展开
            'leftItems':取字段(属性,'leftItems'),#左
            'rightItems':取字段(属性,'rightItems'),#右
            'accessSelect':访问,#访问
            'planSlot':渲染槽('conversation.input.plan',{'locked':禁用}),#计划席
            'modelSlot':渲染槽('conversation.input.model',{'locked':模型席锁}),#模型席
            'contextMeter':仪表,#仪表
            'commandMenuOpen':命令菜单开,#菜单开
            'commandsLabel':翻译('input.commands'),#命令标
            'commandsDisabled':禁用 or 切换菜单 is None,#命令禁
            'onToggleCommands':切换菜单,#切换
            'interruptible':可中断,#独立停
            'stopLabel':翻译('input.stop'),#停标
            'onStop':停止,#停
            'primaryLabel':主标,#主标
            'primaryStops':主停,#主停
            'primaryDisabled':(停止 is None) if 主停 else (空 or 禁用 or 机忙),#主禁
            'onPrimary':主点,#主点
            'preview':自身.预览,#预览
            'previewLabels':灯箱标签(翻译),#灯箱
            'onClosePreview':lambda:自身.__setattr__('预览',None),#关预览
            'footer':取字段(属性,'footer'),#脚
            'sessionId':会话标识,#会话
            'resolveSubmitMode':解析提交,#提交模式
            'keyboard':键盘,#键盘面
            'canSteerQueue':可转向,#可转向
            'cssModule':'输入栏.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
