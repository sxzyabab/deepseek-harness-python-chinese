"""提问撰写器：composer 接管边界；载体键锚定本地草稿。

一条接管、两种形态：声明了本包可渲染展示意图的请求走该意图面（计划审阅），
其余走通用提问流。路由住在此处，避免两种形态争抢同一载体。

对齐上游 `ui-user-questions/src/client/QuestionComposer.tsx`。公开面仅中文名。
"""
import re#推荐后缀剥离
from .约定.槽位 import 取字段,解开,计划审阅于,待答提问#约定面
from .计划审阅面板 import 计划审阅面板#计划审阅接管面

__all__=['解析推荐标签','提问撰写器','样式表']#仅中文公开名

推荐后缀=re.compile(r'\s*(?:\((?:recommended|推荐)\)|（(?:recommended|推荐)）)\s*$',re.I)#推荐标签后缀

样式表='''#对齐 QuestionComposer.module.css 关键布局类
.frame{display:flex;justify-content:center;padding:6px calc(var(--dsh-composer-side-clearance) + 16px) 10px}
.card{display:flex;flex-direction:column;width:100%;max-width:var(--dsh-chat-content-width);max-height:min(60vh,520px);padding:0 0 10px;border:1px solid var(--dsw-alias-border-l2-darkmode-thin);border-radius:20px;background:var(--dsw-specific-input-major);box-shadow:var(--dsw-shadow-lv2);color:var(--dsw-alias-label-primary);overflow:hidden}
.header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-shrink:0;padding:20px 16px 0 24px}
.title{margin:0;font-size:16px;line-height:22px;font-weight:500}
.body{display:flex;flex:1 1 auto;flex-direction:column;min-height:0;overflow-y:auto}
.options{display:flex;flex-direction:column;gap:1px;margin:8px 0 0;padding:4px 12px}
.footer{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-shrink:0;margin-top:12px;padding:0 10px 0 18px}
.feedback{flex:1;min-height:16px;color:var(--dsw-alias-state-error-primary);font-size:11px;line-height:16px;text-align:right}
'''#样式表结束

def 解析推荐标签(标签):#剥离推荐后缀但不改答案值
    """拆常规推荐后缀；返回展示标签与是否推荐。"""
    if 推荐后缀.search(标签):#命中后缀
        return {'label':推荐后缀.sub('',标签),'recommended':True}#剥后缀并标推荐
    return {'label':标签,'recommended':False}#原样

def 空草稿():#一条空白草稿
    """一条空白草稿答案。"""
    return {'selected':[],'custom':'','skipped':False}#空选、空自定义、未跳过

class 提问流:#通用提问翻页流
    """逐题作答：草稿、翻页、跳过、整批提交；载体键锚定草稿。"""
    def __init__(自身,待答,翻译):#域面与文案席
        """记下提问域面与翻译函数，并播种草稿。"""
        自身.待答=待答#提问域面
        自身.翻译=翻译#locale 翻译
        自身.下标=0#当前题下标
        自身.草稿们=[空草稿() for _ in 待答.questions]#与题目一一对应
        自身.忙碌=None#answer / cancel / None
        自身.错误=None#反馈：键或原文

    def 当前题(自身):#当前问题
        """返回当前下标的问题。"""
        return 自身.待答.questions[自身.下标]#当前题

    def 当前草稿(自身):#当前草稿
        """返回当前下标的草稿。"""
        return 自身.草稿们[自身.下标]#当前草稿

    def 已作答(自身,草稿):#是否已选或已填
        """草稿是否已选选项或填写自定义。"""
        return len(取字段(草稿,'selected'))>0 or 取字段(草稿,'custom').strip()!=''#有选或有自定义

    def 已完成(自身,草稿):#已作答或已跳过
        """草稿是否已完成（作答或跳过）。"""
        return 自身.已作答(草稿) or 取字段(草稿,'skipped') is True#作答或跳过

    def 改草稿(自身,更新):#改当前草稿并清错误
        """用更新函数改当前草稿。"""
        下标=自身.下标#当前下标
        自身.草稿们=[更新(项) if 号==下标 else 项 for 号,项 in enumerate(自身.草稿们)]#只改当前
        自身.错误=None#清错误

    def 取消(自身):#取消整组
        """以取消拒绝等待。"""
        自身.忙碌='cancel'#闩上
        自身.错误=None#清错误
        try:#投递
            解开(自身.待答.cancel())#取消
        except Exception as 原因:#失败
            自身.忙碌=None#重开闩
            自身.错误={'text':str(原因)}#原文错误

    def 选择(自身,标签):#点选选项
        """单选立即前进；多选切换勾选。"""
        题目=自身.当前题()#当前题
        多选=取字段(题目,'multiSelect') is True#是否多选
        def 更新(当前):#改草稿
            """按单选/多选改选中集。"""
            if 多选:#多选切换
                已选=取字段(当前,'selected')#当前选中
                if 标签 in 已选:#已勾
                    新选=[项 for 项 in 已选 if 项!=标签]#去掉
                else:#未勾
                    新选=list(已选)+[标签]#追加
                return {'selected':新选,'custom':取字段(当前,'custom'),'skipped':False}#保留自定义
            return {'selected':[标签],'custom':'','skipped':False}#单选互斥
        自身.改草稿(更新)#写入
        if (not 多选) and 自身.下标<len(自身.待答.questions)-1:#单选且非末题
            自身.下标+=1#前进

    def 提交草稿们(自身,草稿们):#整批提交
        """校验齐全后投递结构化答案。"""
        缺=None#首个未完成下标
        for 号,项 in enumerate(草稿们):#逐条
            if not 自身.已完成(项):#未完成
                缺=号#记下
                break#停
        if 缺 is not None:#有缺
            自身.下标=缺#跳到缺题
            自身.错误={'key':'error.incomplete'}#校验键
            return#不提交
        题目们=自身.待答.questions#题目列表
        答案列表=[]#结构化答案
        for 号,题目 in enumerate(题目们):#逐题
            值=草稿们[号]#对应草稿
            if 取字段(值,'skipped'):#跳过
                答案列表.append({'id':取字段(题目,'id'),'selected':[]})#空选
                continue#下题
            自定义=取字段(值,'custom').strip()#修剪自定义
            条目={'id':取字段(题目,'id'),'selected':取字段(值,'selected') if 自定义=='' or 取字段(题目,'multiSelect') is True else []}#单选自定义时清空选中
            if 自定义!='':#有自定义
                条目['custom']=自定义#带上
            答案列表.append(条目)#收下
        自身.忙碌='answer'#闩上
        自身.错误=None#清错误
        try:#投递
            解开(自身.待答.answer({'answers':答案列表}))#整批答案
        except Exception as 原因:#失败
            自身.忙碌=None#重开闩
            自身.错误={'text':str(原因)}#原文错误

    def 继续(自身):#下一题或提交
        """未作答报错；末题提交，否则前进。"""
        if not 自身.已作答(自身.当前草稿()):#未作答
            自身.错误={'key':'error.unanswered'}#未作答键
            return#停
        if 自身.下标<len(自身.待答.questions)-1:#非末题
            自身.下标+=1#前进
            自身.错误=None#清错误
            return#已前进
        自身.提交草稿们(自身.草稿们)#末题提交

    def 跳过(自身):#跳过本题
        """标跳过；末题则提交，否则前进。"""
        下标=自身.下标#当前
        新草稿们=[({'selected':[],'custom':'','skipped':True} if 号==下标 else 项) for 号,项 in enumerate(自身.草稿们)]#当前标跳过
        自身.草稿们=新草稿们#写入
        自身.错误=None#清错误
        if 自身.下标<len(自身.待答.questions)-1:#非末题
            自身.下标+=1#前进
            return#已前进
        自身.提交草稿们(新草稿们)#末题提交

    def 写自定义(自身,文本):#改自定义答案
        """多选保留已选；单选自定义清空选项。"""
        多选=取字段(自身.当前题(),'multiSelect') is True#是否多选
        def 更新(当前):#改草稿
            """写入自定义文本。"""
            return {'selected':取字段(当前,'selected') if 多选 else [],'custom':文本,'skipped':False}#按政策保留或清空选中
        自身.改草稿(更新)#写入

    def 反馈文案(自身):#错误展示
        """键走翻译，原文直出。"""
        if 自身.错误 is None:#无错
            return None#无反馈
        if 'key' in 自身.错误:#词典键
            return 自身.翻译(自身.错误['key'])#翻译
        return 自身.错误['text']#原文

    def 渲染(自身):#通用流结构树
        """返回通用提问流结构树。"""
        题目=自身.当前题()#当前题
        草稿=自身.当前草稿()#当前草稿
        选项们=取字段(题目,'options') or []#选项
        多选=取字段(题目,'multiSelect') is True#是否多选
        忙碌中=自身.忙碌 is not None#是否忙碌
        选项节点=[]#选项按钮
        for 号,选项 in enumerate(选项们):#逐选项
            标签=取字段(选项,'label')#选项标签
            已选=标签 in 取字段(草稿,'selected')#是否选中
            展示=解析推荐标签(标签)#剥推荐后缀
            选项节点.append({#选项按钮
                'type':'button','class':'option','role':'checkbox' if 多选 else 'radio',#角色
                'aria-checked':已选,'aria-label':展示['label'],'disabled':忙碌中,#无障碍与禁用
                'onClick':('choose',标签),'label':展示['label'],#点击带标签
                'recommended':展示['recommended'],'description':取字段(选项,'description'),#推荐与描述
                'index':号+1,'multiSelect':多选,'selected':已选,#展示辅助
            })#选项结束
        眉题=取字段(题目,'header')#可选眉题
        详情=取字段(题目,'detail')#可选详情
        反馈=自身.反馈文案()#反馈文案
        末题=自身.下标==len(自身.待答.questions)-1#是否末题
        主按钮文案=自身.翻译('action.next') if not 末题 else 'submit'#末题用 submit 字面量（上游词典未收该键时保持调用面）
        if 自身.忙碌=='answer':#提交中
            主按钮文案='submitting'#提交中字面量
        return {#结构树
            'type':'div','class':'frame','data-question-key':自身.待答.key,#外框
            'children':[{#卡片
                'type':'section','class':'card',#卡片
                'aria-labelledby':f"question-{自身.待答.key}-{自身.下标}",#标题 id
                'children':[#分区
                    {'type':'header','class':'header','children':[#页眉
                        {'type':'div','class':'headingBlock','children':[#标题块
                            *([{'type':'div','class':'eyebrow','children':[眉题]}] if 眉题 is not None else []),#眉题
                            {'type':'h2','class':'title','id':f"question-{自身.待答.key}-{自身.下标}",'children':[取字段(题目,'question')]},#题干
                        ]},#标题块结束
                        {'type':'button','class':'iconButton','aria-label':自身.翻译('nav.cancel'),'disabled':忙碌中,'onClick':'cancel'},#关闭
                    ]},#页眉结束
                    {'type':'div','class':'body','data-question-scroll':True,'children':[#正文
                        *([{'type':'div','class':'detail','children':[{'type':'MarkdownText','text':详情}]}] if 详情 is not None else []),#详情
                        {'type':'div','class':'options','role':'group' if 多选 else 'radiogroup','children':选项节点+[
                            {'type':'custom','value':取字段(草稿,'custom'),'hasOptions':len(选项们)>0,'placeholder':自身.翻译('custom.placeholder'),'disabled':忙碌中},#自定义行
                        ]},#选项区结束
                    ]},#正文结束
                    {'type':'footer','class':'footer','children':[#页脚
                        {'type':'div','class':'pager','children':[#翻页
                            {'type':'button','onClick':'prev','disabled':自身.下标==0 or 忙碌中,'aria-label':自身.翻译('nav.prev')},#上一题
                            {'type':'span','class':'progress','children':[f"{自身.下标+1} / {len(自身.待答.questions)}"]},#进度
                            {'type':'button','onClick':'next','disabled':末题 or 忙碌中,'aria-label':自身.翻译('nav.next')},#下一题
                        ]},#翻页结束
                        {'type':'div','class':'feedback','role':'status','children':[反馈] if 反馈 else []},#反馈
                        {'type':'div','class':'footerActions','children':[#动作
                            {'type':'button','variant':'outline','disabled':忙碌中,'onClick':'skip','label':自身.翻译('action.skip')},#跳过
                            {'type':'button','variant':'primary','disabled':忙碌中 or not 自身.已作答(草稿),'onClick':'continue','label':主按钮文案},#继续/提交
                        ]},#动作结束
                    ]},#页脚结束
                ],#分区结束
            }],#卡片结束
        }#结构树结束

    def 处理动作(自身,动作):#分发 UI 动作
        """把结构树上的动作名分发到流方法。"""
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
            自身.错误=None#清错误
            return#已处理
        if 动作=='next' and 自身.下标<len(自身.待答.questions)-1:#下一题
            自身.下标+=1#前进
            自身.错误=None#清错误
            return#已处理
        if isinstance(动作,tuple) and 动作 and 动作[0]=='choose':#点选
            自身.选择(动作[1])#选择标签

class 提问撰写器:#composer 接管入口
    """按计划审阅意图路由到决策卡或通用提问流。"""
    def __init__(自身,属性):#合成 props
        """从匹配载体铸造域面，并按意图选面。"""
        自身.属性=属性#合成 props
        自身.待答=待答提问(取字段(属性,'matched'))#域面
        自身.翻译=取字段(属性,'t')#翻译
        审阅=计划审阅于(自身.待答.questions)#尝试收窄
        if 审阅 is None:#通用流
            自身.面=提问流(自身.待答,自身.翻译)#通用提问流
            自身.计划面=None#无计划面
        else:#计划审阅
            自身.计划面=计划审阅面板(自身.待答,审阅,自身.翻译)#决策卡
            自身.面=None#无通用流

    def 更新(自身,属性):#props 变更
        """刷新 props；同载体键保留草稿面。"""
        旧键=自身.待答.key#旧键
        自身.属性=属性#新 props
        自身.待答=待答提问(取字段(属性,'matched'))#新域面
        自身.翻译=取字段(属性,'t')#新翻译
        if 自身.待答.key!=旧键:#换请求
            审阅=计划审阅于(自身.待答.questions)#再收窄
            if 审阅 is None:#通用
                自身.面=提问流(自身.待答,自身.翻译)#新流
                自身.计划面=None#清计划
            else:#计划
                自身.计划面=计划审阅面板(自身.待答,审阅,自身.翻译)#新卡
                自身.面=None#清通用
            return#已换面
        if 自身.面 is not None:#通用流仍挂着
            自身.面.待答=自身.待答#换域面引用
            自身.面.翻译=自身.翻译#换翻译
        if 自身.计划面 is not None:#计划面仍挂着
            自身.计划面.待答=自身.待答#换域面
            自身.计划面.翻译=自身.翻译#换翻译

    def 渲染(自身):#当前面结构树
        """返回当前接管面的结构树。"""
        if 自身.计划面 is not None:#计划审阅
            return 自身.计划面.渲染()#决策卡
        return 自身.面.渲染()#通用流

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用；返回结构树。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()#结构树
