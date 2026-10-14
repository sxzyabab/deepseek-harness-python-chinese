import re#推荐后缀剥离
from nicegui import ui as 界面
from ...ui_基础界面组件.icons import 图标上chevron14,图标下chevron14,图标勾14,图标编辑16
from .约定.槽位 import 计划审阅于,待答提问#约定面
from ..异常 import 提问错误,页面失败文案#本包异常与页面失败句
from .计划审阅面板 import 计划审阅面板#计划审阅接管面

__all__=['解析推荐标签','提问撰写器','样式表']#仅中文公开名

推荐后缀=re.compile(r'[ \t\r\n\f\v]*(?:\((?:recommended|推荐)\)|（(?:recommended|推荐)）)[ \t\r\n\f\v]*\Z',re.I)#推荐标签后缀

样式表='''#对齐 QuestionComposer.module.css 关键布局类。类名加前缀，避免盖到计划审阅卡
.question-frame{display:flex;justify-content:center;padding:6px calc(var(--dsh-composer-side-clearance) + 16px) 10px}
.question-card{display:flex;flex-direction:column;width:100%;max-width:var(--dsh-chat-content-width);max-height:min(60vh,520px);padding:0 0 10px;border:1px solid var(--dsw-alias-border-l2-darkmode-thin);border-radius:20px;background:var(--dsw-specific-input-major);box-shadow:var(--dsw-shadow-lv2);color:var(--dsw-alias-label-primary);overflow:hidden}
.question-header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-shrink:0;padding:20px 16px 0 24px}
.question-title{margin:0;font-size:16px;line-height:22px;font-weight:500}
.question-body{display:flex;flex:1 1 auto;flex-direction:column;min-height:0;overflow-y:auto}
.question-options{display:flex;flex-direction:column;gap:1px;margin:8px 0 0;padding:4px 12px}
.question-footer{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-shrink:0;margin-top:12px;padding:0 10px 0 18px}
.question-feedback{flex:1;min-height:16px;color:var(--dsw-alias-state-error-primary);font-size:11px;line-height:16px;text-align:right}
'''#样式表结束
界面.add_css(样式表,shared=True)

def 解析推荐标签(标签):#剥离推荐后缀但不改答案值
    '拆常规推荐后缀；返回展示标签与是否推荐'
    if 推荐后缀.search(标签):#命中后缀
        return {'label':推荐后缀.sub('',标签,count=1),'recommended':True}#剥后缀并标推荐
    return {'label':标签,'recommended':False}#原样

def 空草稿():#一条空白草稿
    '一条空白草稿答案'
    return {'selected':[],'custom':'','skipped':False}#空选、空自定义、未跳过

class 提问流:#通用提问翻页流
    '逐题作答：草稿、翻页、跳过、整批提交；载体键锚定草稿'
    def __init__(自身,待答,翻译):#域面与文案席
        '记下提问域面与翻译函数，并播种草稿'
        自身.待答=待答#提问域面
        自身.翻译=翻译#locale 翻译
        自身.下标=0#当前题下标
        自身.草稿列表=[空草稿() for _ in 待答.questions]#与题目一一对应
        自身.忙碌=None#answer / cancel / None
        自身.错误=None#反馈：键或原文
        自身.收起=False#卡片收起
        自身.画面=None#可反复清空的容器
        自身.画面失败=None

    def 当前题(自身):#当前问题
        '返回当前下标的问题'
        return 自身.待答.questions[自身.下标]#当前题

    def 当前草稿(自身):#当前草稿
        '返回当前下标的草稿'
        return 自身.草稿列表[自身.下标]#当前草稿

    def 已作答(自身,草稿):#是否已选或已填
        '草稿是否已选选项或填写自定义'
        return len(草稿['selected'])>0 or 草稿['custom'].strip()!=''#有选或有自定义

    def 已完成(自身,草稿):#已作答或已跳过
        '草稿是否已完成（作答或跳过）'
        return 自身.已作答(草稿) or 草稿['skipped'] is True#作答或跳过

    def 改草稿(自身,更新):#改当前草稿并清错误
        '用更新函数改当前草稿'
        下标=自身.下标#当前下标
        自身.草稿列表=[更新(项) if 号==下标 else 项 for 号,项 in enumerate(自身.草稿列表)]#只改当前
        自身.错误=None

    def 取消(自身):#取消整组
        '以取消拒绝等待。answer/cancel 已在域面内等待'
        自身.忙碌='cancel'#闩上
        自身.错误=None
        try:#投递
            自身.待答.cancel()#取消
        except 提问错误 as 原因:#失败
            自身.忙碌=None#重开闩
            自身.错误={'text':页面失败文案(原因)}#原文错误，不带路径、用户名或环境变量

    def 选择(自身,标签):#点选选项
        '单选立即前进；多选切换勾选'
        题目=自身.当前题()#当前题
        多选='multiSelect' in 题目 and 题目['multiSelect'] is True#是否多选
        def 更新(当前):#改草稿
            '按单选/多选改选中集'
            if 多选:#多选切换
                已选=当前['selected']#当前选中
                if 标签 in 已选:#已勾
                    新选=[项 for 项 in 已选 if 项!=标签]#去掉
                else:#未勾
                    新选=list(已选)+[标签]#追加
                return {'selected':新选,'custom':当前['custom'],'skipped':False}#保留自定义
            return {'selected':[标签],'custom':'','skipped':False}#单选互斥
        自身.改草稿(更新)#写入
        if (not 多选) and 自身.下标<len(自身.待答.questions)-1:#单选且非末题
            自身.下标+=1#前进

    def 提交草稿列表(自身,草稿列表):#整批提交
        '校验齐全后投递结构化答案'
        缺=None#首个未完成下标
        for 号,项 in enumerate(草稿列表):#逐条
            if not 自身.已完成(项):#未完成
                缺=号
                break
        if 缺 is not None:#有缺
            自身.下标=缺#跳到缺题
            自身.错误={'key':'error.incomplete'}#校验键
            return#不提交
        题目列表=自身.待答.questions#题目列表
        答案列表=[]#结构化答案
        for 号,题目 in enumerate(题目列表):#逐题
            值=草稿列表[号]#对应草稿
            if 值['skipped'] is True:#跳过
                答案列表.append({'id':题目['id'],'selected':[]})#空选
                continue#下题
            自定义=值['custom'].strip()#修剪自定义
            多选='multiSelect' in 题目 and 题目['multiSelect'] is True#是否多选
            条目={'id':题目['id'],'selected':值['selected'] if 自定义=='' or 多选 else []}#单选自定义时清空选中
            if 自定义!='':#有自定义
                条目['custom']=自定义#带上
            答案列表.append(条目)#收下
        自身.忙碌='answer'#闩上
        自身.错误=None
        try:#投递
            自身.待答.answer({'answers':答案列表})#整批答案
        except 提问错误 as 原因:#失败
            自身.忙碌=None#重开闩
            自身.错误={'text':页面失败文案(原因)}#原文错误，不带路径、用户名或环境变量

    def 继续(自身):#下一题或提交
        '未作答报错；末题提交，否则前进'
        if not 自身.已作答(自身.当前草稿()):#未作答
            自身.错误={'key':'error.unanswered'}#未作答键
            return
        if 自身.下标<len(自身.待答.questions)-1:#非末题
            自身.下标+=1#前进
            自身.错误=None
            return#已前进
        自身.提交草稿列表(自身.草稿列表)#末题提交

    def 跳过(自身):#跳过本题
        '标跳过；末题则提交，否则前进'
        下标=自身.下标#当前
        新草稿列表=[({'selected':[],'custom':'','skipped':True} if 号==下标 else 项) for 号,项 in enumerate(自身.草稿列表)]#当前标跳过
        自身.草稿列表=新草稿列表#写入
        自身.错误=None
        if 自身.下标<len(自身.待答.questions)-1:#非末题
            自身.下标+=1#前进
            return#已前进
        自身.提交草稿列表(新草稿列表)#末题提交

    def 写自定义(自身,文本):#改自定义答案
        '多选保留已选；单选自定义清空选项'
        题目=自身.当前题()#当前题
        多选='multiSelect' in 题目 and 题目['multiSelect'] is True#是否多选
        def 更新(当前):#改草稿
            '写入自定义文本'
            return {'selected':当前['selected'] if 多选 else [],'custom':文本,'skipped':False}#按政策保留或清空选中
        自身.改草稿(更新)#写入

    def 反馈文案(自身):#错误展示
        '键走翻译，原文直出'
        if 自身.错误 is None:#无错
            return None#无反馈
        if 'key' in 自身.错误:#词典键
            return 自身.翻译(自身.错误['key'])#翻译
        return 自身.错误['text']#原文

    def 渲染(自身):#通用流结构树
        '返回通用提问流结构树'
        题目=自身.当前题()#当前题
        草稿=自身.当前草稿()#当前草稿
        选项列表=题目['options'] if 'options' in 题目 and 题目['options'] is not None else []#选项
        多选='multiSelect' in 题目 and 题目['multiSelect'] is True#是否多选
        忙碌中=自身.忙碌 is not None#是否忙碌
        选项节点=[]#选项按钮
        for 号,选项 in enumerate(选项列表):#逐选项
            标签=选项['label']#选项标签
            已选=标签 in 草稿['selected']#是否选中
            展示=解析推荐标签(标签)#剥推荐后缀
            描述=选项['description'] if 'description' in 选项 else None#选项描述
            选项节点.append({#选项按钮
                'type':'button','class':'option','role':'checkbox' if 多选 else 'radio',#角色
                'aria-checked':已选,'aria-label':展示['label'],'disabled':忙碌中,#无障碍与禁用
                'onClick':('choose',标签),'label':展示['label'],#点击带标签
                'recommended':展示['recommended'],'description':描述,#推荐与描述
                'index':号+1,'multiSelect':多选,'selected':已选,#展示辅助
            })#选项结束
        眉题=题目['header'] if 'header' in 题目 else None#可选眉题
        详情=题目['detail'] if 'detail' in 题目 else None#可选详情
        反馈=自身.反馈文案()#反馈文案
        末题=自身.下标==len(自身.待答.questions)-1#是否末题
        if 自身.忙碌=='answer':#提交中
            主按钮文案=自身.翻译('submitting')#提交中
        elif 末题:#末题
            主按钮文案=自身.翻译('submit')#提交
        else:#下一题
            主按钮文案=自身.翻译('action.next')#下一题
        旧=getattr(自身,'画面',None)#已有容器
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:#父级清掉容器后，把失败留在页面上
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('question-frame question-card')#根
        自身.画面.clear()#再清一次
        def 取消():
            '取消提问'
            自身.处理动作('cancel')#取消
            自身.渲染()#重画
        def 上一题():
            '上一题'
            自身.处理动作('prev')#后退
            自身.渲染()#重画
        def 下一题():
            '下一题'
            自身.处理动作('next')#前进
            自身.渲染()#重画
        def 跳过():
            '跳过本题'
            自身.处理动作('skip')#跳过
            自身.渲染()#重画
        def 继续():
            '继续或提交'
            自身.处理动作('continue')#继续
            自身.渲染()#重画
        def 改自定义(事件):
            '写入自定义答案；同文不再重入'
            文=事件.value if 事件.value is not None else ''#文本
            if 文==草稿['custom']:#未变
                return
            自身.写自定义(文)#写入
            自身.渲染()#重画
        def 收起切换():
            '收起或展开卡片'
            自身.收起=自身.收起 is not True#翻转
            自身.渲染()#重画
        with 自身.画面:#根
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            with 界面.row().classes('question-header'):
                if isinstance(眉题,str) and 眉题!='':#眉题
                    界面.label(眉题).classes('question-title')#眉题
                界面.label(题目['question']).classes('question-title')#题目
            收起名=自身.翻译('nav.maximize') if 自身.收起 is True else 自身.翻译('nav.minimize')#收起文案
            收起钮=界面.button(收起名, on_click=收起切换)#收起或展开
            if 自身.收起 is True:#收起图标
                图标上chevron14()#展开箭头
            else:#展开图标
                图标下chevron14()#收起箭头
            if 忙碌中:#忙碌
                收起钮.disable()#禁
            关=界面.button(自身.翻译('nav.cancel'), on_click=取消)#取消
            if 忙碌中:#忙碌
                关.disable()#禁
            if 自身.收起 is True:#收起后只留标题
                return#不再画正文
            if isinstance(详情,str) and 详情!='':#详情
                界面.markdown(详情)#详情
            for 项 in 选项节点:#各选项
                def 点选项(动作=项['onClick']):
                    '点选该选项后重画'
                    自身.处理动作(动作)#选择
                    自身.渲染()#重画
                with 界面.row():#选项行
                    if 项['multiSelect'] is True:#多选
                        if 项['selected'] is True:#已勾
                            图标勾14()#勾选标记
                        else:#未勾
                            界面.label('')#空勾选位
                    else:#单选序号
                        界面.label(str(项['index']))#序号
                    钮=界面.button(项['label'], on_click=点选项)#标签
                    if 项['selected'] is True:#选中
                        钮.props('color=primary')#强调
                    if 项['disabled'] is True:#禁用
                        钮.disable()#禁
                    if 项['recommended'] is True:#推荐
                        界面.label(自身.翻译('option.recommended'))#推荐徽标
                    if isinstance(项['description'],str) and 项['description']!='':#描述
                        界面.label(项['description'])#描述
            if 草稿['skipped'] is True:#已跳过
                界面.label(自身.翻译('review.skipped'))#跳过说明
            with 界面.row():#自定义答案
                if 多选:#多选自定义
                    if 草稿['custom'].strip()!='':#已填写
                        图标勾14()#勾选标记
                else:#单选自定义
                    图标编辑16()#编辑图标
                自定义=界面.textarea(value=草稿['custom'], placeholder=自身.翻译('custom.placeholder'), on_change=改自定义)#多行答案
                if 忙碌中:#忙碌
                    自定义.disable()#禁
            with 界面.row():#翻页
                上=界面.button(自身.翻译('nav.prev'), on_click=上一题)#上一题
                界面.label(f"{自身.下标+1} / {len(自身.待答.questions)}")#进度
                下=界面.button(自身.翻译('nav.next'), on_click=下一题)#下一题
                if 自身.下标==0 or 忙碌中:#首题或忙碌
                    上.disable()#禁
                if 末题 or 忙碌中:#末题或忙碌
                    下.disable()#禁
            if isinstance(反馈,str) and 反馈!='':#反馈
                界面.label(反馈).classes('question-feedback')#反馈
            跳=界面.button(自身.翻译('action.skip'), on_click=跳过)#跳过
            主=界面.button(主按钮文案, on_click=继续)#主按钮
            if 忙碌中:#忙碌
                跳.disable()#禁
                主.disable()#禁
            elif not 自身.已作答(草稿):#未作答
                主.disable()#禁

    def 处理动作(自身,动作):#分发 UI 动作
        '把结构树上的动作名分发到流方法'
        if 动作=='cancel':#取消
            自身.取消()#取消
            return#已处理
        if 动作=='skip':#跳过
            自身.跳过()#跳过
            return#已处理
        if 动作=='continue':#继续
            自身.继续()#继续
            return#已处理
        if 动作=='prev' and 自身.下标>0:#上一题
            自身.下标-=1#后退
            自身.错误=None
            return#已处理
        if 动作=='next' and 自身.下标<len(自身.待答.questions)-1:#下一题
            自身.下标+=1#前进
            自身.错误=None
            return#已处理
        if isinstance(动作,tuple) and len(动作)>0 and 动作[0]=='choose':#点选
            自身.选择(动作[1])#选择标签

class 提问撰写器:#composer 接管入口
    '按计划审阅意图路由到决策卡或通用提问流'
    def __init__(自身,属性):#合成 props
        '从匹配载体铸造域面，并按意图选面。键齐才画。子面由本组件渲染，构造时不自己画'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成 props
        自身.待答=None#域面
        自身.翻译=None#文案
        自身.面=None#通用流
        自身.计划面=None#计划面
        if 'matched' in 自身.属性 and 't' in 自身.属性:
            自身._装面(自身.属性)
            自身.渲染()#槽位只调用构造，键齐了就画

    def _装面(自身,属性):#按载体选面
        '铸造域面。提问流和计划卡构造时不画，由渲染调用'
        自身.待答=待答提问(属性['matched'])#域面
        自身.翻译=属性['t']#翻译
        审阅=计划审阅于(自身.待答.questions)#尝试收窄
        槽=属性['renderSlot'] if 'renderSlot' in 属性 else None#计划动作槽
        if 审阅 is None:#通用流
            自身.面=提问流(自身.待答,自身.翻译)#通用提问流
            自身.计划面=None#无计划面
            return
        自身.计划面=计划审阅面板(自身.待答,审阅,自身.翻译,槽)#决策卡
        自身.面=None#无通用流

    def 更新(自身,属性):#props 变更
        '刷新 props；同载体键保留草稿面'
        自身.属性=属性 if isinstance(属性,dict) else {}#新 props
        if 'matched' not in 自身.属性 or 't' not in 自身.属性:
            return
        旧键=自身.待答.key if 自身.待答 is not None else None#旧键
        自身.待答=待答提问(自身.属性['matched'])#新域面
        自身.翻译=自身.属性['t']#新翻译
        槽=自身.属性['renderSlot'] if 'renderSlot' in 自身.属性 else None#计划动作槽
        if 自身.待答.key!=旧键:#换请求
            自身._装面(自身.属性)#新面仍不在构造里画
            return
        if 自身.面 is not None:#通用流仍挂着
            自身.面.待答=自身.待答#换域面引用
            自身.面.翻译=自身.翻译#换翻译
        if 自身.计划面 is not None:#计划面仍挂着
            自身.计划面.待答=自身.待答#换域面
            自身.计划面.翻译=自身.翻译#换翻译
            自身.计划面.渲染槽=槽#换动作槽

    def 渲染(自身):#当前面结构树
        '返回当前接管面的结构树'
        if 自身.计划面 is not None:#计划审阅
            自身.计划面.渲染()
            return
        if 自身.面 is not None:#通用流
            自身.面.渲染()

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 组件调用；返回结构树'
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()#结构树
