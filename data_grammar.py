# -*- coding: utf-8 -*-
"""四六级常考语法知识

每条字段：
  title    标题
  level    1=四级基础 / 2=四级进阶 / 3=六级重点
  point    规则说明（一两句话讲清楚）
  wrong    常错示例（错句）
  right    正确改写（对句）
  note     补充说明 / 记忆点
"""

GRAMMAR = [
    # ---------------- 四级基础 ----------------
    {
        "title": "主谓一致：each / every / no + 名词作主语",
        "level": 1,
        "point": "each、every、no 修饰的并列主语，谓语一律用单数；主语被 each of、"
                 "neither of、the number of 修饰时也用单数。",
        "wrong": "Each of the students have a dictionary.",
        "right": "Each of the students has a dictionary.",
        "note": "对比：A number of students have...（许多……）谓语用复数；"
                "the number of students is...（……的数量）用单数。",
    },
    {
        "title": "时态：since 引导的时间状语从句",
        "level": 1,
        "point": "since 从句用一般过去时，主句用现在完成时；这是四六级阅读和翻译的高频考点。",
        "wrong": "He lives here since 2015.",
        "right": "He has lived here since 2015.",
        "note": "since 后面接时间点；for 接时间段，如 for three years。",
    },
    {
        "title": "被动语态：不及物动词没有被动式",
        "level": 1,
        "point": "happen、appear、occur、belong to、consist of 等不及物动词或短语不能变被动。",
        "wrong": "The accident was happened last night.",
        "right": "The accident happened last night.",
        "note": "常考搭配：The meeting will take place tomorrow.（不能写 will be taken place）",
    },
    {
        "title": "情态动词：should have done 表示“本该做却没做”",
        "level": 1,
        "point": "should/ought to/must + have done 表示对过去情况的推测或责备；"
                 "needn't have done 表示“本来不必做却做了”。",
        "wrong": "You should finish it yesterday.",
        "right": "You should have finished it yesterday.",
        "note": "理解类：must have done（一定做过）／can't have done（不可能做过）",
    },
    {
        "title": "非谓语：不定式与动名词作宾语",
        "level": 1,
        "point": "只接动名词的常见动词：enjoy、mind、avoid、suggest、finish、consider、"
                 "imagine、risk、practise；只接不定式的常见动词：decide、hope、"
                 "manage、refuse、expect、afford。",
        "wrong": "I enjoy to read novels.",
        "right": "I enjoy reading novels.",
        "note": "stop to do（停下来去做另一件事）≠ stop doing（停止正在做的事），"
                "remember/forget 同理。",
    },
    {
        "title": "定语从句：关系代词的选择",
        "level": 1,
        "point": "先行词指人用 who/whom/whose/that，指物用 which/that；"
                 "介词后只能用 which/whom，不能用 that。",
        "wrong": "This is the house in that he lived.",
        "right": "This is the house in which he lived.",
        "note": "非限制性定语从句（逗号后）不能用 that。",
    },
    {
        "title": "比较结构：as ... as 与 not as ... as",
        "level": 1,
        "point": "同级比较用 as + 形容词/副词原级 + as；倍数放最前面：three times as "
                 "large as。the + 比较级，the + 比较级表示“越……越……”。",
        "wrong": "This room is twice as larger as that one.",
        "right": "This room is twice as large as that one.",
        "note": "“越……越……”的语序不能倒：The more you practice, the better you will become.",
    },
    {
        "title": "虚拟语气：if 从句的三种时间",
        "level": 2,
        "point": "与现在事实相反：if + 过去式，主句 would/could + do；"
                 "与过去事实相反：if + had done，主句 would have done；"
                 "与将来相反：if + were to do / should do。",
        "wrong": "If I were you, I will accept the offer.",
        "right": "If I were you, I would accept the offer.",
        "note": "省略 if 时把 were/had/should 提前：Were I you, I would accept it.",
    },
    {
        "title": "倒装：否定词置于句首",
        "level": 2,
        "point": "never、seldom、hardly、not until、no sooner ... than、"
                 "only + 状语 放句首时，主句要部分倒装（把助动词提到主语前）。",
        "wrong": "Never I have seen such a beautiful scene.",
        "right": "Never have I seen such a beautiful scene.",
        "note": "only + 状语从句倒装主句：Only when he came did we know the truth.",
    },
    {
        "title": "it 作形式主语与形式宾语",
        "level": 2,
        "point": "真正的主语/宾语是不定式或从句时，先用 it 占位：It is important to do sth. / "
                 "I find it hard to concentrate。",
        "wrong": "To learn English well is necessary for us.",
        "right": "It is necessary for us to learn English well.",
        "note": "四六级翻译里 This is because ... / It is widely believed that ... 都是固定结构。",
    },
    {
        "title": "平行结构：and / or / but 前后一致",
        "level": 2,
        "point": "并列连接词连接的两个成分词性或形式必须一致。",
        "wrong": "She likes swimming, hiking and to ride a bike.",
        "right": "She likes swimming, hiking and riding a bike.",
        "note": "not only ... but also ... 也要前后对称。",
    },
    {
        "title": "现在分词作状语：主动与被动",
        "level": 2,
        "point": "逻辑主语与主句主语一致且是主动关系用 -ing；被动关系用 -ed。",
        "wrong": "Walking along the street, the shop was seen by me.",
        "right": "Walking along the street, I saw the shop.",
        "note": "判断口径：分词结构的逻辑主语必须是主句主语。",
    },
    {
        "title": "强调句型 It is ... that ...",
        "level": 2,
        "point": "强调人可用 who 或 that，其他成分一律用 that；去掉 It is 和 that 后句子仍成立。",
        "wrong": "It was in 2010 when the project started.",
        "right": "It was in 2010 that the project started.",
        "note": "和状语从句区分：It was 10 o'clock when he came back.（这是 when 时间状语从句）",
    },
    {
        "title": "虚拟语气：建议/命令类动词后的 should 省略",
        "level": 3,
        "point": "suggest、demand、require、insist、propose、recommend、order 等后的宾语从句"
                 "用 (should) + 动词原形；同源的 It is suggested that ... 也一样。",
        "wrong": "He suggested that we went there by bus.",
        "right": "He suggested that we (should) go there by bus.",
        "note": "suggest 作“暗示、表明”讲时不用虚拟：Her smile suggested that she was pleased.",
    },
    {
        "title": "同位语从句 vs 定语从句",
        "level": 3,
        "point": "that 在同位语从句里不充当成分（只起连接作用），在定语从句里要充当主语或宾语。",
        "wrong": "The news which he had passed the exam made us happy.",
        "right": "The news that he had passed the exam made us happy.",
        "note": "常接同位语从句的名词：news、fact、idea、belief、evidence、doubt、hope。",
    },
    {
        "title": "独立主格结构",
        "level": 3,
        "point": "名词/代词 + 分词（或 to do、形容词、介词短语）构成独立主格，"
                 "和主句之间用逗号隔开，表示伴随、原因或条件。",
        "wrong": "The weather being fine, so we went out for a walk.",
        "right": "The weather being fine, we went out for a walk.",
        "note": "独立主格前面不能再加 so/and 这类连词。",
    },
    {
        "title": "倍数表达三种句型",
        "level": 3,
        "point": "A is three times as large as B. / A is three times the size of B. / "
                 "A is three times larger than B.（争议句式，四六级里以 as ... as 为最稳）",
        "wrong": "The new library is three times as bigger as the old one.",
        "right": "The new library is three times as big as the old one.",
        "note": "翻译里写 as ... as 结构最不容易错。",
    },
    {
        "title": "非谓语：need / want / require + doing",
        "level": 3,
        "point": "need/want/require/deserve 后面接动名词表被动含义，等于 to be done。",
        "wrong": "The machine needs repair immediately.",
        "right": "The machine needs repairing immediately.（或 needs to be repaired）",
        "note": "这是六级翻译与改错的常考点。",
    },
    {
        "title": "as 引导的让步倒装",
        "level": 3,
        "point": "形容词/副词 + as + 主语 + 谓语，表示“尽管……”。as 可以换成 though，"
                 "但不能用 although。",
        "wrong": "Although hard as he tried, he failed.",
        "right": "Hard as he tried, he failed.",
        "note": "注意语序：表语或状语必须提到 as 前面。",
    },
    {
        "title": "非限制性定语从句：which 指代整句",
        "level": 3,
        "point": "which 可以指代前面整句话，只能用非限制性形式（逗号 + which），"
                 "不能用 that，也不能用 what。",
        "wrong": "He passed the exam, that surprised us.",
        "right": "He passed the exam, which surprised us.",
        "note": "同类结构：as we all know / as is often the case。",
    },
    {
        "title": "一般现在时与现在完成时的区别",
        "level": 1,
        "point": "一般现在时表习惯或事实；现在完成时强调对现在的影响或从过去持续到现在。",
        "wrong": "I am a student in this school for three years.",
        "right": "I have been a student in this school for three years.",
        "note": "since、so far、recently、in the past few years 常配现在完成时。",
    },
]
