"""本通用宿主读写的 LSP 线协议类型子集：initialize 能力、四种请求结果（Location、LocationLink、Hover），以及用来判定瞬时打开支持的 textDocumentSync 形态。仅词汇。真实服务器载荷中缺席的字段保持可选；翻译层把它们归一成 seam 的封闭联合。"""

线协议位置字段=('line','character')#线上的零基 UTF-16 位置（协议的 Position）
线协议范围字段=('start','end')#线协议范围（Range）
线协议定位字段=('uri','range')#Location：文档 URI 加一段范围
线协议定位链接字段=('targetUri','targetSelectionRange','targetRange')#LocationLink：目标 uri 加上要聚焦的选择范围
线协议标记内容字段=('kind','value')#MarkupContent 悬停正文（markdown 或 plaintext）
线协议带语言标记字段=('language','value')#MarkedString 对象形态（{ language, value }）
线协议悬停字段=('contents','range')#Hover：协议三种编码之一的 contents，外加可选范围
线协议文档同步种类=(0,1,2)#textDocumentSync 遗留枚举：0 None、1 Full、2 Incremental
线协议文档同步选项字段=('openClose','change')#textDocumentSync 选项形态
线协议服务器能力字段=('positionEncoding','textDocumentSync','definitionProvider','referencesProvider','implementationProvider','hoverProvider')#本宿主会检查的 ServerCapabilities 字段
线协议初始化结果字段=('capabilities',)#initialize 结果信封
