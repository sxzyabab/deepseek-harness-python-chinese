/** 让星号加粗在标点后仍能闭合：CJK 正文无空白继续时也认结束标记。 */

import { attention } from 'micromark-core-commonmark'//CommonMark 强调构造（取 resolveAll）
import { unicodePunctuation } from 'micromark-util-character'//Unicode 标点判定
import { classifyCharacter } from 'micromark-util-classify-character'//把码点分成空白/标点/其他
import { codes, constants } from 'micromark-util-symbol'//码点常量与字符分组常量
import type { Construct, Extension, State, Tokenizer } from 'micromark-util-types'//micromark 构造/扩展/状态机类型

const cjkCharacter = new RegExp([//匹配 CJK 文种扩展的正则
  '\\p{Script_Extensions=Han}',//汉字
  '\\p{Script_Extensions=Hiragana}',//平假名
  '\\p{Script_Extensions=Katakana}',//片假名
  '\\p{Script_Extensions=Hangul}',//谚文
  '\\p{Script_Extensions=Bopomofo}',//注音
].join('|'), 'u')//用 | 拼成一类并开 Unicode 标志

function isCjkCharacter(code: number | null): boolean {//码点是否属于 CJK 文种
  return code !== null && code >= 0 && cjkCharacter.test(String.fromCodePoint(code))//有效码点且命中 CJK 正则
}//结束 isCjkCharacter

const tokenizeCjkFriendlyAttention: Tokenizer = function (effects, ok, nok) {//CJK 友好的星号强调分词器
  const configuredAttentionMarkers = this.parser.constructs.attentionMarkers.null//解析器配置的强调标记集合
  if (configuredAttentionMarkers === undefined) {//CommonMark 强调标记未挂上
    throw new Error('micromark CommonMark attention markers are unavailable')//没有强调标记则无法分词
  }//结束 标记缺失
  const attentionMarkers = configuredAttentionMarkers//收窄后的强调标记表
  const previous = this.previous//序列前一个码点
  const before = classifyCharacter(previous)//前一码点的字符分组
  let marker: number | null = codes.eof//当前强调标记，初始为 eof 哨兵

  return start//从 start 状态开始

  function start(code: number | null): State | undefined {//遇到可能的星号序列
    /* v8 ignore next -- this text construct is dispatched only for an asterisk. */
    if (code !== codes.asterisk) return nok(code)//非星号则失败（按约定只会派发星号）
    marker = code//记下本序列标记（星号）
    effects.enter('attentionSequence')//进入强调序列记号
    return inside(code)//转入 inside 吃完整序列
  }//结束 start

  function inside(code: number | null): State | undefined {//消费连续星号
    if (code === marker) {//仍是同一标记
      effects.consume(code)//吃掉一颗星号
      return inside//继续吃
    }//结束 连续星号

    const token = effects.exit('attentionSequence')//结束序列并取出记号
    const after = classifyCharacter(code)//序列后第一个码点的分组
    const open = !after || (after === constants.characterGroupPunctuation && Boolean(before))//后侧空/eof，或后侧标点且前侧非空 → 可开
      || attentionMarkers.includes(code)//后侧本身是强调标记也可开
    const commonMarkClose = !before//前侧空/eof → CommonMark 可关
      || (before === constants.characterGroupPunctuation && Boolean(after))//前侧标点且后侧非空
      || attentionMarkers.includes(previous)//前一码点是强调标记
    const markerCount = token.end.offset - token.start.offset//本序列星号个数
    const cjkStrongClose = markerCount >= 2//至少两颗星（加粗，不是斜体）
      && unicodePunctuation(previous)//前一码点是 Unicode 标点
      && isCjkCharacter(code)//后接 CJK 字符
    const close = commonMarkClose || cjkStrongClose//CommonMark 可关或 CJK 加粗可关

    token._open = open//可否作开标记
    token._close = close//可否作关标记
    return ok(code)//本构造成功，把当前码点交还
  }//结束 inside
}//结束 tokenizeCjkFriendlyAttention

const cjkFriendlyAttention: Construct = {//替换默认星号强调的构造
  name: 'cjkFriendlyAttention',//构造名
  resolveAll: attention.resolveAll,//复用 CommonMark 的 resolveAll
  tokenize: tokenizeCjkFriendlyAttention,//用 CJK 友好分词器
}//结束 cjkFriendlyAttention

const cjkFriendlyStrongExtension: Extension = {//micromark 语法扩展
  text: { [codes.asterisk]: cjkFriendlyAttention },//在文本态把星号派给本构造
}//结束 cjkFriendlyStrongExtension

/**
 * 扩展 CommonMark 星号加粗：标点分隔的 CJK 正文无空白时仍能闭合，
 * 作为供 `fromMarkdown` 使用的 micromark 语法扩展。
 * @returns micromark 语法扩展。
 */
export function cjkFriendlyStrong(): Extension {//导出 CJK 友好加粗扩展
  return cjkFriendlyStrongExtension//单例扩展对象
}//结束 cjkFriendlyStrong
