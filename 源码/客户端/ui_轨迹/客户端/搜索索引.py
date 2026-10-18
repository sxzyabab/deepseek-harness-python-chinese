import json
from .轨迹记录 import 轨迹记录身份#稳定身份
from .轨迹预览 import 轨迹预览文本#有界预览

__all__=['轨迹搜索索引']

class 轨迹搜索索引:
    '会话视图本地索引：仅当某条记录的源片段变化时才重解析 Markdown'
    def __init__(自身):
        '初始化条目表与布局引用'
        自身.条目={}#身份到源片段与检索文本
        自身.布局列表=None#上次同步的布局引用

    def 更新(自身,布局列表):
        '增量同步一份或多份当前轨迹布局切片；布局引用变化时返回真'
        if 自身.布局列表 is 布局列表:
            return False#同一份引用
        自身.布局列表=布局列表#记下
        见过=set()#本轮仍在的身份
        for 轮次列表 in 布局列表:
            for 轮次 in 轮次列表:
                for 组 in 轮次['groups']:
                    for 格 in 组['cells']:
                        if 格.get('requestOnly') is True:
                            continue
                        身份=轨迹记录身份(格)#稳定身份
                        块列表=list(格.get('sourceBlocks') or [])+list(格.get('outputBlocks') or [])
                        源片段=[
                            'between turns' if 轮次['turn'] is None else 'turn '+str(轮次['turn']),
                            组.get('title') or '',
                            格.get('kind') or '',
                            'assistant' if 格.get('kind')=='message' else '',
                            格.get('text') or '',
                            格.get('previewMarkdown') or '',
                            格.get('inputDetail') or '',
                            格.get('outputDetail') or '',
                            格.get('thinkingDetail') or '',
                            格.get('schemaDetail') or '',
                            格.get('result') or '',
                            格.get('resultPreviewMarkdown') or '',
                            格.get('callId') or '',
                        ]
                        for 块 in 块列表:
                            源片段.append(块.get('type') or '')
                            源片段.append(块.get('content') or '')
                            源片段.append(块.get('callId') or '')
                            源片段.append(块.get('toolName') or '')
                            附件=块.get('attachment')
                            源片段.append('' if not isinstance(附件,dict) else 附件.get('name') or '')
                        for 值 in (格.get('messageSource'),格.get('promptDetail'),格.get('previousPromptDetail')):
                            if 值 is None:
                                源片段.append('')
                            else:
                                try:
                                    源片段.append(json.dumps(值,ensure_ascii=False))
                                except (TypeError,ValueError) as 错误:#无法序列化则空串
                                    源片段.append('')
                        先前=自身.条目.get(身份)
                        if 先前 is not None and 先前['sources']==源片段:
                            条目=先前#源没变，不重解析
                        else:
                            预览=''
                            if 格.get('previewMarkdown') is not None:
                                抽出=轨迹预览文本(格['previewMarkdown'])
                                if 格.get('text')=='':
                                    预览=抽出
                                elif 抽出=='':
                                    预览=格.get('text') or ''
                                else:
                                    预览=(格.get('text') or '')+' · '+抽出
                            if 格.get('resultPreviewMarkdown') is None:
                                结果预览=格.get('result') or ''
                            else:
                                结果预览=轨迹预览文本(格['resultPreviewMarkdown'])
                            条目={
                                'sources':源片段,
                                'text':'\n'.join(源片段+[预览,结果预览]).lower(),
                            }
                        自身.条目[身份]=条目
                        见过.add(身份)
        for 身份 in list(自身.条目):
            if 身份 not in 见过:
                del 自身.条目[身份]#布局里已经没有
        return True

    def 搜索(自身,查询):
        '空格分隔、大小写不敏感；无查询词时为 None'
        词=[项 for 项 in 查询.strip().lower().split() if 项!='']
        if len(词)==0:
            return None
        命中=set()
        for 身份,条目 in 自身.条目.items():
            if all(词项 in 条目['text'] for 词项 in 词):
                命中.add(身份)
        return 命中
