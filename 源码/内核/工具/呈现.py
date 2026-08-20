"""工具渲染意图词汇：工具经 presentCall/presentResult 声明的、与提供方无关的卡片约定。对齐上游 `tools/src/presentation.ts`。公开面仅中文名；字段键保持上游字面量。"""

__all__=(
    '调用类别','调用卡片','结果卡片','搜索形态','网页种类',
    '文件位置字段','文件差异字段','读取文件行字段',
    '通用调用字段','终端调用字段','差异调用字段',
    '通用结果字段','终端结果字段','差异结果字段',
    '搜索行匹配字段','搜索文件匹配字段','搜索匹配结果字段','搜索路径结果字段',
    '读取结果字段','网页来源字段','网页搜索结果字段','网页抓取结果字段',
)#仅中文公开名

调用类别=('read','edit','delete','move','search','execute','fetch','other')#调用类别，供 UI 选图标或待遇
调用卡片=('generic','terminal','diff')#待处理调用卡片标签
结果卡片=('generic','terminal','diff','search','read','web')#完成调用卡片标签
搜索形态=('matches','paths')#搜索结果形态：分组匹配或扁平路径
网页种类=('search','fetch')#网页结果种类：检索或抓取
文件位置字段=('path','line')#跟着走的文件位置字段键
文件差异字段=('path','oldText','newText')#单文件变更字段键
读取文件行字段=('number','text')#带编号的读取行字段键
通用调用字段=('card','title','kind','rawInput','content','locations')#通用待处理卡片字段键
终端调用字段=('card','title','description','cwd')#终端待处理卡片字段键
差异调用字段=('card','title','diffs','locations')#diff 待处理卡片字段键
通用结果字段=('card','title','content')#通用完成卡片字段键
终端结果字段=('card','title','output','exitCode','signal')#终端完成卡片字段键
差异结果字段=('card','title','diffs')#diff 完成卡片字段键
搜索行匹配字段=('lineNumber','line')#搜索匹配行字段键
搜索文件匹配字段=('path','matches')#按文件分组的匹配字段键
搜索匹配结果字段=('card','shape','title','files','truncated','total')#内容搜索完成卡片字段键
搜索路径结果字段=('card','shape','title','paths','truncated','total')#路径搜索完成卡片字段键
读取结果字段=('card','title','path','offset','lines','totalLines','lang','content')#读取完成卡片字段键
网页来源字段=('url','title','snippet','publishedAt')#网页来源字段键
网页搜索结果字段=('card','kind','title','sources','answer','truncated')#网页搜索完成卡片字段键
网页抓取结果字段=('card','kind','title','url','statusCode','truncated')#网页抓取完成卡片字段键
