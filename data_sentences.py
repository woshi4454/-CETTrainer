# -*- coding: utf-8 -*-
"""听写句子库

按难度分级，覆盖四六级常见句型与主题。
字段: (句子, 中文翻译, 难度 1-3, 主题)
难度: 1=短句/四级基础  2=中长句/四级进阶  3=长难句/六级
"""

SENTENCES = [
    # ---------- 难度 1：短句，四级基础 ----------
    ("The weather is getting colder day by day.", "天气一天天变冷了。", 1, "日常"),
    ("I usually get up at seven in the morning.", "我通常早上七点起床。", 1, "日常"),
    ("She is interested in learning foreign languages.", "她对学习外语很感兴趣。", 1, "学习"),
    ("We should take good care of our health.", "我们应该好好照顾自己的健康。", 1, "健康"),
    ("Reading books can help us relax after work.", "读书能帮助我们在工作后放松。", 1, "学习"),
    ("He failed the exam because he did not study hard.", "他因为没努力学习而考试不及格。", 1, "学习"),
    ("The library is open from nine to five.", "图书馆从九点开到五点。", 1, "日常"),
    ("My parents always support my decisions.", "我父母总是支持我的决定。", 1, "家庭"),
    ("It is important to keep a balanced diet.", "保持均衡饮食很重要。", 1, "健康"),
    ("They plan to travel abroad next summer.", "他们计划明年夏天出国旅行。", 1, "旅行"),

    # ---------- 难度 2：中长句，四级进阶 ----------
    ("With the development of technology, our life has become much more convenient.", "随着科技的发展，我们的生活变得方便多了。", 2, "科技"),
    ("More and more young people choose to work in big cities.", "越来越多的年轻人选择在大城市工作。", 2, "社会"),
    ("Although the task was difficult, they managed to finish it on time.", "尽管任务很难，他们还是设法按时完成了。", 2, "工作"),
    ("The government has taken measures to reduce air pollution.", "政府已采取措施减少空气污染。", 2, "环境"),
    ("It is widely believed that education plays a key role in personal development.", "人们普遍认为教育在个人发展中起着关键作用。", 2, "教育"),
    ("Many students find it hard to balance study and part-time jobs.", "许多学生发现很难平衡学习和兼职工作。", 2, "学习"),
    ("The number of people who prefer online shopping keeps growing.", "喜欢网购的人数持续增长。", 2, "消费"),
    ("Compared with the past, people today pay more attention to mental health.", "与过去相比，今天的人们更关注心理健康。", 2, "健康"),
    ("In recent years, environmental protection has attracted worldwide attention.", "近年来，环境保护引起了全世界的关注。", 2, "环境"),
    ("Working overtime for a long time may cause serious health problems.", "长期加班可能导致严重的健康问题。", 2, "工作"),
    ("The company decided to invest more money in research and development.", "公司决定在研发上投入更多资金。", 2, "商业"),
    ("We often take for granted the things that are most important to us.", "我们常常把对我们最重要的东西视为理所当然。", 2, "生活"),
    ("Instead of complaining, we should try to find a solution to the problem.", "与其抱怨，我们应该设法找到解决问题的办法。", 2, "生活"),
    ("The teacher encouraged us to express our opinions freely in class.", "老师鼓励我们在课堂上自由表达观点。", 2, "教育"),
    ("Living alone taught me how to take care of myself.", "独自生活教会了我如何照顾自己。", 2, "生活"),
    ("Some people believe that money can bring happiness, but others disagree.", "有些人认为金钱能带来幸福，但另一些人不同意。", 2, "社会"),

    # ---------- 难度 3：长难句，六级 ----------
    ("What matters most is not how much you earn, but whether you enjoy what you do.", "最重要的不是你挣多少钱，而是你是否享受你所做的事。", 3, "生活"),
    ("The rapid growth of artificial intelligence has raised concerns about job security.", "人工智能的快速增长引发了人们对工作保障的担忧。", 3, "科技"),
    ("Researchers have found that regular exercise can significantly improve memory and concentration.", "研究人员发现规律锻炼能显著提高记忆力和注意力。", 3, "健康"),
    ("It is often argued that the advantages of urbanization outweigh its disadvantages.", "人们常常争论城市化的好处大于其弊端。", 3, "社会"),
    ("Those who are willing to take risks are more likely to achieve great success.", "那些愿意承担风险的人更有可能取得巨大成功。", 3, "成功"),
    ("The problem is not that we lack resources, but that we fail to use them wisely.", "问题不在于我们缺乏资源，而在于我们没有明智地利用它们。", 3, "社会"),
    ("Despite the enormous progress made in medicine, many diseases remain incurable.", "尽管医学取得了巨大进步，许多疾病仍无法治愈。", 3, "健康"),
    ("Global warming poses a serious threat to the survival of many species.", "全球变暖对许多物种的生存构成严重威胁。", 3, "环境"),
    ("Children who grow up in a supportive environment tend to be more confident.", "在支持性环境中长大的孩子往往更自信。", 3, "教育"),
    ("The ability to adapt to change is essential in today's fast-paced world.", "在当今快节奏的世界里，适应变化的能力至关重要。", 3, "社会"),
    ("It takes years of practice to master a skill, but only a moment to lose it.", "掌握一项技能需要多年练习，但失去它只需一瞬间。", 3, "学习"),
    ("No matter how difficult the situation is, we should never give up hope.", "无论处境多么艰难，我们都不应放弃希望。", 3, "励志"),
    ("The gap between the rich and the poor continues to widen in many countries.", "许多国家的贫富差距持续扩大。", 3, "社会"),
    ("Scientists warn that unless we act now, the damage may become irreversible.", "科学家警告说，除非我们现在行动，否则损害可能变得无法逆转。", 3, "环境"),
    ("A person's character is shaped not only by education but also by experience.", "一个人的性格不仅由教育塑造，也由经历塑造。", 3, "教育"),
    ("The most valuable lesson I learned from failure was how to stand up again.", "我从失败中学到的最宝贵的教训是如何重新站起来。", 3, "励志"),
    ("Many people spend so much time worrying about the future that they forget to enjoy the present.", "许多人花太多时间担忧未来，以至于忘了享受当下。", 3, "生活"),
    ("Technology should serve human beings, rather than the other way around.", "技术应当服务于人类，而不是反过来。", 3, "科技"),
    ("We must strike a balance between economic development and environmental protection.", "我们必须在经济发展与环境保护之间取得平衡。", 3, "环境"),
    ("The real test of friendship is not in good times, but in difficult times.", "友谊的真正考验不在顺境，而在逆境。", 3, "人际"),
    ("It is a common misconception that talent alone guarantees success.", "一个普遍的误解是：仅靠天赋就能保证成功。", 3, "成功"),
    ("What we do today will determine what kind of world our children live in.", "我们今天所做的一切将决定我们的孩子生活在怎样的世界里。", 3, "环境"),
    ("The more you read, the more you realize how much you do not know.", "你读得越多，就越意识到自己不知道的有多么多。", 3, "学习"),
    ("Although the road ahead is full of uncertainty, we are ready to face it.", "尽管前方的路充满不确定，我们已准备好面对它。", 3, "励志"),
    ("Social media has changed the way people communicate and express themselves.", "社交媒体改变了人们沟通和表达的方式。", 3, "科技"),
]


# 翻译练习（中译英）：(中文, 参考译文, 难度)
TRANSLATIONS = [
    ("随着人们生活水平的提高，越来越多的人开始关注健康问题。",
     "With the improvement of living standards, more and more people have begun to pay attention to health problems.", 2),
    ("读书不仅能开阔我们的视野，还能丰富我们的思想。",
     "Reading can not only broaden our horizons, but also enrich our minds.", 2),
    ("虽然工作很忙，他还是坚持每天锻炼身体。",
     "Although he is very busy with work, he still insists on exercising every day.", 2),
    ("互联网的发展极大地改变了人们的生活方式。",
     "The development of the Internet has greatly changed people's way of life.", 2),
    ("保护环境是每个人的责任，而不只是政府的责任。",
     "Protecting the environment is everyone's responsibility, not just that of the government.", 2),
    ("只有通过不断的努力，我们才能实现自己的梦想。",
     "Only through continuous efforts can we realize our dreams.", 3),
    ("越来越多的大学生选择毕业后自己创业。",
     "More and more college students choose to start their own businesses after graduation.", 2),
    ("在我看来，健康比财富更重要。",
     "In my opinion, health is more important than wealth.", 1),
    ("中国传统节日体现了中华民族的文化传统。",
     "Traditional Chinese festivals reflect the cultural traditions of the Chinese nation.", 3),
    ("我们应该学会合理安排时间，而不是把时间浪费在无意义的事情上。",
     "We should learn to manage our time properly instead of wasting it on meaningless things.", 3),
    ("由于天气原因，运动会将推迟到下周举行。",
     "Because of the weather, the sports meeting will be postponed until next week.", 2),
    ("我宁愿在家看书，也不愿去参加那种吵闹的聚会。",
     "I would rather read at home than go to such a noisy party.", 2),
    ("这项研究表明，睡眠不足会影响学生的学习效率。",
     "This study shows that lack of sleep can affect students' learning efficiency.", 3),
    ("秋天的校园格外美丽，吸引了很多人来拍照。",
     "The campus in autumn is especially beautiful and attracts many people to take photos.", 2),
    ("我们应当尊重不同的文化，因为世界因多样而精彩。",
     "We should respect different cultures, because the world is wonderful for its diversity.", 3),
]


# 选词填空语料（每个空设计为上下文唯一的正确答案）
CLOZE_PASSAGES = [
    {
        "title": "Reading Habits",
        "text": "Reading is one of the best habits a person can develop. It not only ___1___ our knowledge but also helps us think more clearly. Many people say they are too busy to read, but in fact we can ___2___ a few minutes between tasks. Over time, these small moments ___3___ into a meaningful habit. The key is to choose books that genuinely ___4___ you, rather than those you think you should read.",
        "blanks": [
            ("expands", ["expands", "expands", "expand", "expansion"], "动词原形第三人称：主语 It，一般现在时。"),
            ("spare", ["spare", "spend", "save", "share"], "spare a few minutes 抽出几分钟。"),
            ("accumulate", ["accumulate", "accumulate", "accumulated", "accumulating"], "accumulate into 逐渐积累成为。"),
            ("interest", ["interest", "interested", "interesting", "interests"], "genuinely interest you 真正让你感兴趣的。"),
        ],
    },
    {
        "title": "Slow Down",
        "text": "In modern society, speed seems to be everything. We rush to work, rush to eat, and even rush to relax. However, constant ___1___ often leads to burnout. Researchers suggest that we should ___2___ time to rest and reflect. Taking a short walk or simply sitting in silence can ___3___ our minds significantly. Perhaps what we really need is not more hours, but a better ___4___ of time.",
        "blanks": [
            ("pressure", ["pressure", "pressing", "pressured", "compress"], "constant pressure 持续的压力。"),
            ("allocate", ["allocate", "allocated", "allocation", "allocating"], "allocate time 分配时间。"),
            ("refresh", ["refresh", "refreshing", "refreshed", "refreshment"], "can refresh 能刷新/恢复。"),
            ("sense", ["sense", "senses", "sensible", "sensitive"], "a better sense of time 更好的时间感。"),
        ],
    },
]


# 阅读模拟题（结构对齐真题：细节题/推断题/主旨题/词义猜测题）
READING_PASSAGES = [
    {
        "title": "The Rise of Remote Work",
        "passage": (
            "Before 2020, working from home was an exception rather than a rule. Few companies had the tools to support it, "
            "and many managers doubted that employees could stay productive away from the office. The pandemic changed that almost overnight. "
            "Millions of workers suddenly found themselves attending meetings through screens and sharing files online.\n\n"
            "Five years on, the picture is far from simple. Research suggests that remote work can increase productivity for tasks that require "
            "deep concentration, because employees are interrupted less often. However, it also weakens the informal conversations that often "
            "spark new ideas. Junior employees seem to suffer most, since they lose the chance to learn simply by observing experienced colleagues.\n\n"
            "Most companies have therefore settled on a hybrid model, in which staff spend two or three days in the office and the rest at home. "
            "This approach tries to combine the flexibility of remote work with the value of face-to-face contact. Yet even hybrid arrangements "
            "face resistance: some employees feel that time in the office is simply used for meetings they could have joined from home, while "
            "others worry that being seen at a desk matters more than the quality of their work."
        ),
        "questions": [
            {
                "q": "What was the attitude of many managers toward remote work before 2020?",
                "options": ["A. Enthusiastic", "B. Doubtful", "C. Indifferent", "D. Hostile"],
                "answer": "B",
                "explain": "第一段明确指出 many managers doubted that employees could stay productive away from the office，即怀疑态度。",
            },
            {
                "q": "According to the passage, remote work may benefit tasks that require deep concentration because ______.",
                "options": [
                    "A. employees can choose their own hours",
                    "B. companies save on office costs",
                    "C. employees are interrupted less often",
                    "D. managers can monitor progress closely",
                ],
                "answer": "C",
                "explain": "第二段 because employees are interrupted less often 直接给出因果。",
            },
            {
                "q": "Why do junior employees seem to suffer most from remote work?",
                "options": [
                    "A. They earn lower salaries.",
                    "B. They have less access to technology.",
                    "C. They lose chances to learn by observing senior colleagues.",
                    "D. They are unable to work independently.",
                ],
                "answer": "C",
                "explain": "第二段 since they lose the chance to learn simply by observing experienced colleagues。",
            },
            {
                "q": "What does the word \"resistance\" in the last paragraph most probably mean?",
                "options": ["A. Support", "B. Opposition", "C. Confusion", "D. Agreement"],
                "answer": "B",
                "explain": "下文举了员工不满的例子（feels that time in the office is simply used for meetings...），因此 resistance 指反对。",
            },
            {
                "q": "What is the passage mainly about?",
                "options": [
                    "A. Why the pandemic ended remote work",
                    "B. The benefits and challenges of remote and hybrid work",
                    "C. How to improve productivity in the office",
                    "D. The history of office design",
                ],
                "answer": "B",
                "explain": "全文依次讲了远程工作的好处、问题与混合模式的困境，主旨是利与弊。",
            },
        ],
    },
    {
        "title": "Why We Forget",
        "passage": (
            "Forgetting is usually treated as a failure of memory, but psychologists increasingly see it as a feature rather than a bug. "
            "A mind that remembered everything would be overwhelmed by useless details, unable to identify what matters. "
            "In this sense, forgetting helps us generalise from experience and adapt to new situations.\n\n"
            "That does not mean all forgetting is harmless. The most common cause of everyday forgetting is not decay of memory traces, "
            "as people often assume, but interference: new information competes with old information and makes it harder to retrieve. "
            "This is why studying for an examination in one long session is inefficient. Spacing the same study over several days produces "
            "far more durable memory, even though the total time is identical.\n\n"
            "Sleep also plays a crucial role. During deep sleep the brain replays patterns of activity from the day, strengthening some "
            "connections and weakening others. Students who sleep well after learning new material consistently perform better than "
            "those who stay up late reviewing it. The lesson is clear: memory is not a container to be filled, but a system to be maintained."
        ),
        "questions": [
            {
                "q": "How do psychologists increasingly view forgetting?",
                "options": [
                    "A. As a serious disease",
                    "B. As a useful feature of the mind",
                    "C. As proof of weak intelligence",
                    "D. As something that cannot be studied",
                ],
                "answer": "B",
                "explain": "第一段 psychologists increasingly see it as a feature rather than a bug。",
            },
            {
                "q": "According to the passage, what is the most common cause of everyday forgetting?",
                "options": ["A. Decay of memory traces", "B. Lack of sleep", "C. Interference from new information", "D. Poor nutrition"],
                "answer": "C",
                "explain": "第二段 The most common cause... is not decay... but interference。",
            },
            {
                "q": "Why is studying in one long session inefficient?",
                "options": [
                    "A. Because it takes too much time overall.",
                    "B. Because interference makes retrieval harder.",
                    "C. Because students lose interest quickly.",
                    "D. Because teachers cannot help.",
                ],
                "answer": "B",
                "explain": "第二段解释 spacing 更有效，反衬一次长时间学习因干扰而低效。",
            },
            {
                "q": "What happens during deep sleep according to the passage?",
                "options": [
                    "A. The brain forgets everything from the day.",
                    "B. The brain replays activity patterns and adjusts connections.",
                    "C. The brain stops all activity.",
                    "D. The brain stores new information permanently.",
                ],
                "answer": "B",
                "explain": "第三段 the brain replays patterns of activity from the day, strengthening some connections and weakening others。",
            },
            {
                "q": "What can be inferred from the last sentence of the passage?",
                "options": [
                    "A. Memory capacity is fixed and limited.",
                    "B. Memory requires active maintenance rather than passive filling.",
                    "C. Sleep is unnecessary for memory.",
                    "D. Memorising facts is the goal of education.",
                ],
                "answer": "B",
                "explain": "memory is not a container to be filled, but a system to be maintained 强调主动维护。",
            },
        ],
    },
]


# ============================================================
# 合并扩充题库（data_extra.py）
# 句子/翻译按内容去重；阅读与选词填空按标题去重
# ============================================================
def _merge_unique(base, extra, key_index=0):
    seen = {item[key_index] for item in base}
    out = list(base)
    for item in extra:
        if item[key_index] not in seen:
            seen.add(item[key_index])
            out.append(item)
    return out


try:
    from data_extra import (
        EXTRA_SENTENCES,
        EXTRA_TRANSLATIONS,
        EXTRA_CLOZE,
        EXTRA_READING,
    )

    SENTENCES = _merge_unique(SENTENCES, EXTRA_SENTENCES, 0)
    TRANSLATIONS = _merge_unique(TRANSLATIONS, EXTRA_TRANSLATIONS, 0)
    CLOZE_PASSAGES = _merge_unique(CLOZE_PASSAGES, EXTRA_CLOZE, "title")
    READING_PASSAGES = _merge_unique(READING_PASSAGES, EXTRA_READING, "title")
except Exception:
    # 扩充文件缺失时不影响主程序运行
    pass
