/** 在上游仅美元语法上扩展 TeX 分隔符，同时复用其记号词表。 */

import { factorySpace } from 'micromark-factory-space'//吃行前缀/空白的工厂
import type {} from 'micromark-extension-math'//引入 math 扩展的记号名增强
import { markdownLineEnding } from 'micromark-util-character'//是否为 Markdown 换行
import { codes, constants, types } from 'micromark-util-symbol'//码点、常量和记号类型名
import type { Construct, Extension, Previous, State, Tokenizer } from 'micromark-util-types'//构造/扩展/前码/状态/分词器类型

// oxlint-disable typescript/no-this-alias -- micromark binds tokenizer context only on the outer callback.

const previousBackslash: Previous = function (code) {//反斜杠文本构造的 previous 钩子
  if (code !== codes.backslash) return true//前一码不是反斜杠则可以开始
  const tail = this.events.at(-1)//取最后一个事件
  /* v8 ignore next -- a previous code necessarily has a preceding event. */
  if (tail === undefined) return false//没有前事件则拒绝（按约定到不了）
  return tail[1].type === types.characterEscape//前一反斜杠是字符转义才允许开始
}//结束 previousBackslash

const tokenizeBackslashMathText: Tokenizer = function (effects, ok, nok) {//分词 `\(...\)` 行内数学
  return start//从 start 状态开始

  function start(code: number | null): State | undefined {//遇到反斜杠则进入行内数学
    /* v8 ignore next -- the text construct is dispatched only for a backslash. */
    if (code !== codes.backslash) return nok(code)//非反斜杠则失败（按约定只会派发反斜杠）
    effects.enter('mathText')//进入行内数学记号
    effects.enter('mathTextSequence')//进入开序列
    effects.consume(code)//吃掉开反斜杠
    return open//等左圆括号
  }//结束 start

  function open(code: number | null): State | undefined {//开序列的左圆括号
    if (code !== codes.leftParenthesis) return nok(code)//不是 `(` 则失败
    effects.consume(code)//吃掉 `(`
    effects.exit('mathTextSequence')//结束开序列
    return between//进入内容区
  }//结束 open

  function between(code: number | null): State | undefined {//内容区：数据、换行或尝试闭合
    if (code === codes.eof) return nok(code)//文件结束仍未闭合则失败
    if (code === codes.backslash) {//可能是 `\)` 闭合
      return effects.attempt({ partial: true, tokenize: tokenizeClose }, close, afterCloseAttempt)(code)//尝试闭合，失败则 afterCloseAttempt
    }//结束 反斜杠
    if (markdownLineEnding(code)) {//行内数学允许换行
      effects.enter(types.lineEnding)//进入换行记号
      effects.consume(code)//吃掉换行
      effects.exit(types.lineEnding)//结束换行记号
      return between//换行后仍在内容区
    }//结束 换行
    return dataStart(code)//普通字符当数据
  }//结束 between

  function afterCloseAttempt(code: number | null): State | undefined {//闭合失败后的反斜杠
    return effects.check({ partial: true, tokenize: tokenizeOpen }, nok, dataStart)(code)//若是 `\(` 则整段失败，否则当数据
  }//结束 afterCloseAttempt

  function dataStart(code: number | null): State | undefined {//开始一段 mathTextData
    effects.enter('mathTextData')//进入数据记号
    effects.consume(code)//吃掉当前码点
    return code === codes.backslash ? afterDataBackslash : data//数据里的反斜杠要看下一个
  }//结束 dataStart

  function afterDataBackslash(code: number | null): State | undefined {//数据中反斜杠的后一码
    if (code === codes.backslash) {//连续两个反斜杠
      effects.consume(code)//第二个反斜杠也算数据
      return data//继续数据
    }//结束 双反斜杠
    return data(code)//不是双反斜杠则按普通数据
  }//结束 afterDataBackslash

  function data(code: number | null): State | undefined {//消费 mathTextData
    if (code === codes.eof || code === codes.backslash || markdownLineEnding(code)) {//数据段在这些码点处结束
      effects.exit('mathTextData')//结束数据记号
      return between(code)//回到内容区再分发
    }//结束 数据段边界
    effects.consume(code)//吃掉数据字符
    return data//继续数据
  }//结束 data

  function close(code: number | null): State | undefined {//闭合序列已匹配
    effects.exit('mathText')//结束行内数学
    return ok(code)//本构造成功
  }//结束 close

  function tokenizeClose(closeEffects: Parameters<Tokenizer>[0], closeOk: State, closeNok: State): State {//部分构造：匹配 `\)`
    return slash//从闭合反斜杠开始

    function slash(code: number | null): State | undefined {//闭合序列的反斜杠
      /* v8 ignore next -- this partial construct is attempted only at a backslash. */
      if (code !== codes.backslash) return closeNok(code)//非反斜杠则闭合失败
      closeEffects.enter('mathTextSequence')//进入闭序列
      closeEffects.consume(code)//吃掉闭反斜杠
      return parenthesis//等右圆括号
    }//结束 slash

    function parenthesis(code: number | null): State | undefined {//闭合序列的右圆括号
      if (code !== codes.rightParenthesis) return closeNok(code)//不是 `)` 则闭合失败
      closeEffects.consume(code)//吃掉 `)`
      closeEffects.exit('mathTextSequence')//结束闭序列
      return closeOk//闭合成功
    }//结束 parenthesis
  }//结束 tokenizeClose

  function tokenizeOpen(openEffects: Parameters<Tokenizer>[0], openOk: State, openNok: State): State {//部分构造：检查是否又是 `\(`
    return slash//从反斜杠开始

    function slash(code: number | null): State | undefined {//疑似开序列的反斜杠
      /* v8 ignore next -- the opening check follows a failed close attempt at a backslash. */
      if (code !== codes.backslash) return openNok(code)//非反斜杠则不是开序列
      openEffects.enter(types.chunkString)//暂记为字符串块（只检查，不发数学记号）
      openEffects.consume(code)//吃掉反斜杠
      return parenthesis//等左圆括号
    }//结束 slash

    function parenthesis(code: number | null): State | undefined {//疑似开序列的左圆括号
      if (code !== codes.leftParenthesis) return openNok(code)//不是 `(` 则不是开序列
      openEffects.consume(code)//吃掉 `(`
      openEffects.exit(types.chunkString)//结束检查用字符串块
      return openOk//确认是 `\(`
    }//结束 parenthesis
  }//结束 tokenizeOpen
}//结束 tokenizeBackslashMathText

function createMathFlow(marker: number, openMarker: number, closeMarker: number, multiline: boolean): Construct {//按开闭标记造一个流构造
  const tokenize: Tokenizer = function (effects, ok, nok) {//分词数学块围栏与内容
    const self = this//保存分词器 this（仅外层回调上有绑定）
    let oddBackslashRun = false//美元块里奇数反斜杠则下一美元不算闭标记
    const tail = self.events.at(-1)//前一事件
    const initialSize = tail?.[1].type === types.linePrefix//前一事件是行前缀则量其宽度
      ? tail[2].sliceSerialize(tail[1], true).length//序列化前缀得到缩进列数
      : 0//没有行前缀则缩进为 0

    return start//从 start 状态开始

    function start(code: number | null): State | undefined {//遇到本构造的开标记
      /* v8 ignore next -- the flow construct is dispatched only for its marker. */
      if (code !== marker) return nok(code)//不是本构造标记则失败
      effects.enter('mathFlow')//进入块级数学
      effects.enter('mathFlowFence')//进入开围栏
      effects.enter('mathFlowFenceSequence')//进入开围栏序列
      effects.consume(code)//吃掉开标记第一码
      return open//等开标记第二码
    }//结束 start

    function open(code: number | null): State | undefined {//开围栏的第二码
      if (code !== openMarker) return nok(code)//不是约定的开标记则失败
      effects.consume(code)//吃掉开标记第二码
      effects.exit('mathFlowFenceSequence')//结束开围栏序列
      effects.exit('mathFlowFence')//结束开围栏
      return marker === codes.dollarSign ? afterDollarOpen : content//美元块还要拒绝 `$$$`
    }//结束 open

    function afterDollarOpen(code: number | null): State | undefined {//`$$` 后再来一个 `$` 则不是本构造
      return code === codes.dollarSign ? nok(code) : content(code)//第三美元失败，否则进内容
    }//结束 afterDollarOpen

    function content(code: number | null): State | undefined {//块内容：数据、换行或尝试闭合
      if (code === codes.eof) return nok(code)//文件结束仍未闭合则失败
      if (code === marker && (marker !== codes.dollarSign || !oddBackslashRun)) {//命中开标记且美元块不在奇数反斜杠后
        return effects.attempt(//尝试闭合围栏
          { partial: true, tokenize: tokenizeClosingFence },//部分构造：闭合围栏
          closed,//成功则结束数学块
          afterClosingFenceAttempt,//失败则看是误开还是内容
        )(code)//用当前码点启动
      }//结束 尝试闭合
      if (markdownLineEnding(code)) {//遇到换行
        return multiline//是否允许多行块
          ? effects.attempt(nonLazyContinuation, afterContinuation, nok)(code)//非惰性续行成功则继续
          : nok(code)//单行块遇换行失败
      }//结束 换行
      return valueStart(code)//普通字符当块值
    }//结束 content

    function afterClosingFenceAttempt(code: number | null): State | undefined {//闭合失败后的标记码
      return marker === codes.backslash//反斜杠块要排除「这其实是又一个开围栏」
        ? effects.check({ partial: true, tokenize: tokenizeOpeningFence }, nok, markerValueStart)(code)//是开围栏则失败，否则当内容
        : markerValueStart(code)//美元块直接把标记当内容
    }//结束 afterClosingFenceAttempt

    function afterContinuation(code: number | null): State | undefined {//续行成功后再尝试闭合
      return effects.attempt(//换行后续尝试闭合围栏
        { partial: true, tokenize: tokenizeClosingFence },//部分构造：闭合围栏
        closed,//成功则结束数学块
        initialSize//有行前缀则先吃缩进再回 content
          ? factorySpace(effects, content, types.linePrefix, initialSize + 1)//吃不超过原缩进+1 的空白
          : content,//无前缀则直接回 content
      )(code)//用当前码点启动
    }//结束 afterContinuation

    function valueStart(code: number | null): State | undefined {//开始一段 mathFlowValue
      effects.enter('mathFlowValue')//进入块值记号
      oddBackslashRun = code === codes.backslash//本段是否以反斜杠起头
      effects.consume(code)//吃掉当前码点
      return value//继续块值
    }//结束 valueStart

    function markerValueStart(code: number | null): State | undefined {//闭合失败的标记改当块值
      effects.enter('mathFlowValue')//进入块值记号
      oddBackslashRun = false//从标记起头，反斜杠奇偶清零
      effects.consume(code)//吃掉标记码
      return valueAfterMarker//看标记是否成对出现
    }//结束 markerValueStart

    function valueAfterMarker(code: number | null): State | undefined {//刚把失败的闭标记当内容
      if (code === marker) {//紧接着又一个同样标记
        effects.consume(code)//吃掉第二个标记
        return value//回到普通块值
      }//结束 双标记
      return value(code)//否则按普通块值分发
    }//结束 valueAfterMarker

    function value(code: number | null): State | undefined {//消费 mathFlowValue
      if (code === codes.eof || code === marker || markdownLineEnding(code)) {//块值在这些码点处结束
        effects.exit('mathFlowValue')//结束块值记号
        return content(code)//回到内容区再分发
      }//结束 块值边界
      oddBackslashRun = code === codes.backslash ? !oddBackslashRun : false//遇反斜杠翻转奇偶，其他码清零
      effects.consume(code)//吃掉块值字符
      return value//继续块值
    }//结束 value

    function closed(code: number | null): State | undefined {//闭合围栏已匹配
      effects.exit('mathFlow')//结束块级数学
      return ok(code)//本构造成功
    }//结束 closed

    function tokenizeClosingFence(//闭合围栏的部分构造
      closeEffects: Parameters<Tokenizer>[0],//闭合用的 effects
      closeOk: State,//闭合成功
      closeNok: State,//闭合失败
    ): State {//先吃行前缀空白
      return factorySpace(closeEffects, sequenceStart, types.linePrefix, constants.tabSize)//最多一制表位的行前缀

      function sequenceStart(code: number | null): State | undefined {//闭围栏序列第一码
        if (code !== marker) return closeNok(code)//不是本构造标记则闭合失败
        closeEffects.enter('mathFlowFence')//进入闭围栏
        closeEffects.enter('mathFlowFenceSequence')//进入闭围栏序列
        closeEffects.consume(code)//吃掉闭标记第一码
        return sequenceEnd//等闭标记第二码
      }//结束 sequenceStart

      function sequenceEnd(code: number | null): State | undefined {//闭围栏序列第二码
        if (code !== closeMarker) return closeNok(code)//不是约定的闭标记则失败
        closeEffects.consume(code)//吃掉闭标记第二码
        closeEffects.exit('mathFlowFenceSequence')//结束闭围栏序列
        return factorySpace(closeEffects, after, types.whitespace)//围栏后只允许空白
      }//结束 sequenceEnd

      function after(code: number | null): State | undefined {//闭围栏后直到行尾
        if (code !== codes.eof && !markdownLineEnding(code)) return closeNok(code)//行尾前还有非空白则闭合失败
        closeEffects.exit('mathFlowFence')//结束闭围栏
        return closeOk(code)//闭合成功
      }//结束 after
    }//结束 tokenizeClosingFence

    function tokenizeOpeningFence(//部分构造：检查是否又是开围栏
      openEffects: Parameters<Tokenizer>[0],//检查用的 effects
      openOk: State,//确认是开围栏
      openNok: State,//不是开围栏
    ): State {//从序列第一码开始
      return sequenceStart//从开标记第一码开始

      function sequenceStart(code: number | null): State | undefined {//疑似开围栏第一码
        /* v8 ignore next -- the opening check follows a failed close attempt at the marker. */
        if (code !== marker) return openNok(code)//不是本构造标记则不是开围栏
        openEffects.enter(types.chunkString)//暂记为字符串块（只检查）
        openEffects.consume(code)//吃掉第一码
        return sequenceEnd//等开标记第二码
      }//结束 sequenceStart

      function sequenceEnd(code: number | null): State | undefined {//疑似开围栏第二码
        if (code !== openMarker) return openNok(code)//不是约定的开标记则不是开围栏
        openEffects.consume(code)//吃掉第二码
        openEffects.exit(types.chunkString)//结束检查用字符串块
        return openOk//确认是开围栏
      }//结束 sequenceEnd
    }//结束 tokenizeOpeningFence
  }//结束 tokenize

  return {//本构造的 micromark 描述
    concrete: true,//具体构造，不与其他流构造竞争
    name: marker === codes.dollarSign ? 'sameLineDollarMathFlow' : 'backslashMathFlow',//美元同行或反斜杠块
    tokenize,//上面的分词器
  }//结束 构造描述
}//结束 createMathFlow

const tokenizeNonLazyContinuation: Tokenizer = function (effects, ok, nok) {//多行块的非惰性续行
  const self = this//保存分词器 this

  return start//从 start 状态开始

  function start(code: number | null): State | undefined {//续行构造只在换行后尝试
    /* v8 ignore next -- continuation constructs are attempted only after a line ending. */
    if (code === codes.eof) return ok(code)//文件结束当作可续（交给后续 eof 处理）
    /* v8 ignore next -- continuation constructs are attempted only after a line ending. */
    if (!markdownLineEnding(code)) return nok(code)//不是换行则失败
    effects.enter(types.lineEnding)//进入换行记号
    effects.consume(code)//吃掉换行
    effects.exit(types.lineEnding)//结束换行记号
    return lineStart//看下一行是否惰性
  }//结束 start

  function lineStart(code: number | null): State | undefined {//下一行行首
    return self.parser.lazy[self.now().line] ? nok(code) : ok(code)//惰性行则失败，否则续行成功
  }//结束 lineStart
}//结束 tokenizeNonLazyContinuation

const nonLazyContinuation: Construct = {//供 attempt 使用的部分续行构造
  partial: true,//部分构造，失败不消耗
  tokenize: tokenizeNonLazyContinuation,//非惰性续行分词器
}//结束 nonLazyContinuation

const backslashMathText: Construct = {//`\(...\)` 行内数学构造
  name: 'backslashMathText',//构造名
  previous: previousBackslash,//前一码须允许以反斜杠开头
  tokenize: tokenizeBackslashMathText,//行内数学分词器
}//结束 backslashMathText

const backslashMathFlow = createMathFlow(//`\[...\]` 多行数学块构造
  codes.backslash,//开闭都以反斜杠起头
  codes.leftSquareBracket,//开标记 `[`
  codes.rightSquareBracket,//闭标记 `]`
  true,//允许多行
)//结束 backslashMathFlow

const sameLineDollarMathFlow = createMathFlow(//`$$...$$` 同行展示块构造
  codes.dollarSign,//开闭都以美元起头
  codes.dollarSign,//开标记第二码也是 `$`
  codes.dollarSign,//闭标记第二码也是 `$`
  false,//不允许换行
)//结束 sameLineDollarMathFlow

const backslashMath: Extension = {//反斜杠与同行美元的语法扩展
  flow: {//流构造：块级数学
    [codes.backslash]: backslashMathFlow,//`\[...\]` 多行块
    [codes.dollarSign]: sameLineDollarMathFlow,//`$$...$$` 同行块
  },//结束 flow
  text: { [codes.backslash]: backslashMathText },//文本构造：`\(...\)` 行内
}//结束 backslashMath

/**
 * 把 TeX 反斜杠分隔符与同行美元展示块做成 micromark 语法扩展，
 * 复用 `micromark-extension-math` 的记号词表；调用方必须在同一次解析上
 * 再注册 `math()`，发出的记号才会编译成标准数学节点。
 * @returns micromark 语法扩展。
 */
export function mathCompatibility(): Extension {//供解析器注册的兼容扩展
  return backslashMath//反斜杠行内/块 + 同行美元块
}//结束 mathCompatibility
