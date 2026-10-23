# -*- coding: utf-8 -*-
"""四六级作文真题题目 + 万能模板库

真题题目按「话题类型」整理（题目是历年真题的改写/归纳，不是官方原卷，写作用来练手够了）。
模板分三段：开头点题、中间展开、结尾收束；每个空位用 {topic} 之类的占位，页面里替换。
"""

# ---------------------------------------------------------------- 真题话题
# (标题, 年份/来源, 题型, 题干中文提示, 英文题目, 关键词)
WRITING_TOPICS = [
    ("On the Importance of Reading", "四级 常考", "议论",
     "写一篇短文，谈谈阅读的重要性并给出建议。",
     'Write an essay on the importance of reading. You should write at least 120 words.',
     ["reading", "knowledge", "habit"]),
    ("Should Students Take Part-time Jobs?", "四级 常考", "议论",
     "大学生做兼职是利是弊？谈谈你的看法。",
     'Some people believe college students should take part-time jobs. What is your opinion? '
     'Write at least 120 words.', ["part-time job", "experience", "balance"]),
    ("The Impact of Short Videos", "四级 2023 类", "议论",
     "短视频对年轻人的影响，谈谈你的看法。",
     'Write an essay on the influence of short videos on young people. '
     'You should write at least 120 words.', ["short video", "screen time", "attention"]),
    ("Online Learning vs. Traditional Classes", "四级 常考", "对比",
     "线上学习和线下课堂，你更支持哪一种？说明理由。",
     'Write an essay comparing online learning with traditional classroom learning. '
     'State your preference with reasons. Write at least 120 words.',
     ["online learning", "interaction", "flexibility"]),
    ("How to Deal with Stress", "四级 常考", "说明",
     "写一篇短文，说明大学生如何应对压力。",
     'Write an essay on how college students can deal with stress. '
     'You should write at least 120 words.', ["stress", "exercise", "support"]),
    ("The Value of Teamwork", "六级 常考", "议论",
     "谈谈团队合作的价值，并结合例子说明。",
     'Write an essay on the value of teamwork. Support your view with examples. '
     'You should write at least 150 words.', ["teamwork", "communication", "goal"]),
    ("Artificial Intelligence and Our Future", "六级 常考", "议论",
     "人工智能将如何改变我们的生活？谈谈机遇与挑战。",
     'Write an essay on how artificial intelligence will change our lives. '
     'Discuss both opportunities and challenges. Write at least 150 words.',
     ["artificial intelligence", "job market", "ethics"]),
    ("The Importance of Environmental Protection", "六级 常考", "议论",
     "环境保护人人有责，谈谈你的理解和行动建议。",
     'Write an essay on the importance of environmental protection. '
     'You should write at least 150 words.', ["environment", "carbon", "recycling"]),
    ("A Letter of Application", "四级 书信", "书信",
     "写一封信，申请一个志愿者岗位，介绍你的优势。",
     'Write a letter to apply for a volunteer position. Introduce your strengths. '
     'You should write at least 120 words.', ["volunteer", "experience", "responsible"]),
    ("A Letter of Suggestion to the Library", "四级 书信", "书信",
     "给图书馆写一封建议信，指出问题并提出改进。",
     'Write a letter to the university library giving suggestions on how to improve '
     'its service. Write at least 120 words.', ["library", "suggestion", "service"]),
    ("Describe a Person Who Influenced You", "六级 叙事", "叙事",
     "描述一位对你影响很大的人，说明他/她改变了你什么。",
     'Write an essay about a person who has influenced you deeply. '
     'Explain how he or she changed you. Write at least 150 words.',
     ["influence", "example", "change"]),
    ("My View on Part-time Entrepreneurship", "六级 议论", "议论",
     "谈谈你对大学生创业的看法。",
     'Write an essay on college students starting their own businesses. '
     'What is your view? Write at least 150 words.',
     ["startup", "risk", "experience"]),
]

# ---------------------------------------------------------------- 模板库
# 说明：{...} 里的内容用题目关键词替换，页面会提示怎么填
TEMPLATES = [
    {
        "name": "议论文万能三段（最稳）",
        "level": 2,
        "scene": "议论 / 说明",
        "opening": (
            "Nowadays, {topic} has become a topic of heated discussion among {people}. "
            "Opinions on it vary from person to person, but as far as I am concerned, "
            "{stance}."
        ),
        "body": (
            "First and foremost, {reason1}. To be specific, {detail1}. "
            "Furthermore, {reason2}. Take {example} as an example: {detail2}. "
            "Last but not least, {reason3}."
        ),
        "closing": (
            "In conclusion, {restate}. Only in this way can we {hope}."
        ),
        "tips": "开头一句破题 + 三个并列理由（each 一句主旨一句细节）+ 一句总结，120 词轻松够。",
    },
    {
        "name": "正反对比（讨论双方观点）",
        "level": 2,
        "scene": "议论（Should / Is it good）",
        "opening": (
            "When it comes to {topic}, people's views differ sharply. "
            "Some hold that {view_a}, while others argue that {view_b}."
        ),
        "body": (
            "Those who support {topic} point out that {support_reason}. "
            "In their eyes, {support_detail}. However, opponents maintain that "
            "{against_reason}. They also worry that {against_detail}."
        ),
        "closing": (
            "Weighing the two sides, I am inclined to believe that {my_view}. "
            "After all, {final_reason}."
        ),
        "tips": "双方各写一句观点 + 一句理由，最后明确站队，比单边论述显得有思辨。",
    },
    {
        "name": "书信模板（申请 / 建议 / 感谢）",
        "level": 1,
        "scene": "书信",
        "opening": (
            "Dear {name},\n\nI am {self_intro}. I am writing to {purpose}."
        ),
        "body": (
            "To begin with, {point1}. In addition, {point2}. "
            "If possible, I would appreciate it if you could {request}."
        ),
        "closing": (
            "Thank you for your time and consideration. I am looking forward to "
            "your early reply.\n\nYours sincerely,\nLi Ming"
        ),
        "tips": "书信注意：开头说明身份和目的，中间分点陈述，结尾致谢 + 期待回复；署名统一写 Li Ming。",
    },
    {
        "name": "图表 / 现象描述",
        "level": 3,
        "scene": "图表作文",
        "opening": (
            "As is vividly shown in the chart, {phenomenon}. The figure has "
            "{trend} over the past few years, which has aroused wide public concern."
        ),
        "body": (
            "Several factors may account for this phenomenon. For one thing, {cause1}. "
            "For another, {cause2}. Besides, {cause3}."
        ),
        "closing": (
            "In my opinion, it is high time that we {action}. Only when {condition} "
            "can we {result}."
        ),
        "tips": "图表题第一句必须描述趋势（rise / drop / remain stable），不要一上来就讲原因。",
    },
    {
        "name": "六级高阶（含倒装与从句）",
        "level": 3,
        "scene": "议论（冲高分）",
        "opening": (
            "It is no exaggeration to say that {topic} has reshaped the way we live, "
            "work and interact with one another."
        ),
        "body": (
            "What deserves our attention first is that {point1}. Not only does it "
            "{point1_effect}, but it also {point1_more}. Equally important is {point2}, "
            "which {point2_effect}. Admittedly, {concession}; nevertheless, {rebuttal}."
        ),
        "closing": (
            "Therefore, rather than {negative}, we should {positive}. "
            "It is through such efforts that we can truly {goal}."
        ),
        "tips": "用 Not only...but also 倒装、which 非限定从句、Admittedly...nevertheless 让步，句型分就上来了。",
    },
    {
        "name": "叙事（描写人物 / 经历）",
        "level": 2,
        "scene": "叙事",
        "opening": (
            "Among all the people I have met, {who} is the one who has influenced me "
            "most deeply. I still remember clearly the day {scene}."
        ),
        "body": (
            "What impressed me most was that {event}. At that moment, I realized "
            "{realization}. Since then, {change}. Whenever I {setback}, I would think of "
            "{memory} and keep going."
        ),
        "closing": (
            "Looking back, I have come to understand that {lesson}. "
            "His / Her influence will stay with me for the rest of my life."
        ),
        "tips": "叙事要有具体场景（时间、动作、对话），比空泛地说「他很好」得分高得多。",
    },
]

# 高分替换词（避免通篇 good / very / important）
UPGRADE_WORDS = [
    ("good", "beneficial / favorable / rewarding"),
    ("bad", "detrimental / unfavorable"),
    ("very important", "crucial / vital / of great significance"),
    ("many", "numerous / a considerable number of"),
    ("think", "hold the view that / be convinced that"),
    ("get", "obtain / acquire"),
    ("help", "contribute to / facilitate"),
    ("show", "demonstrate / reveal"),
    ("because", "owing to / on account of"),
    ("but", "however / nevertheless"),
    ("so", "therefore / consequently"),
    ("I think", "in my opinion / from my perspective"),
    ("more and more", "an increasing number of"),
    ("in modern society", "in contemporary society"),
    ("do something", "take effective measures to do something"),
]

# 常用连接词
CONNECTORS = [
    ("开头", "To begin with / First and foremost / It is universally acknowledged that"),
    ("递进", "Furthermore / What is more / In addition / Moreover"),
    ("转折", "However / Nevertheless / On the contrary / Admittedly"),
    ("举例", "Take ... as an example / A case in point is ..."),
    ("因果", "owing to / as a result / consequently / therefore"),
    ("总结", "In conclusion / To sum up / From what has been discussed above"),
]
