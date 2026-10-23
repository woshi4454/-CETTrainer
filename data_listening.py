# -*- coding: utf-8 -*-
"""听力材料库

说明：这里是自己编写的四六级难度听力材料（短对话、长对话、短文），
配程序内的朗读引擎出声。不是官方真题音频，用来练「听懂」这件事足够。
每篇字段：kind(dialogue/news/passage)、title、level、script(全文，按说话人分行)、
questions=[{q, options[4], answer(字母), explain}]
"""

LISTENING_ITEMS = [
    # ------------------------------------------------------------ 短对话
    {
        "kind": "dialogue",
        "title": "短对话 1 · 图书馆续借",
        "level": 1,
        "script": [
            "M: Excuse me, I'd like to renew these two books. They're due tomorrow.",
            "W: Let me check. I'm afraid the first one has been reserved by another student, "
            "so you can only renew the second one.",
            "M: I see. Then I'll return the first one this afternoon.",
            "W: Good. And the second one can be kept for another two weeks.",
            "Q: What will the man probably do?",
        ],
        "questions": [
            {"q": "What will the man probably do?",
             "options": ["A. Return the first book today",
                         "B. Renew both books online",
                         "C. Borrow two more books",
                         "D. Ask the woman for a new card"],
             "answer": "A",
             "explain": "女生说第一本已被别人预约，只能续借第二本，所以男生说他今天就还第一本。"},
            {"q": "How long can the second book be kept?",
             "options": ["A. One week", "B. Two weeks",
                         "C. One month", "D. Until tomorrow"],
             "answer": "B",
             "explain": "原句 another two weeks，即再借两周。"},
        ],
    },
    {
        "kind": "dialogue",
        "title": "短对话 2 · 订会议室",
        "level": 1,
        "script": [
            "W: Hi, this is Lucy from the marketing department. Is the meeting room on the "
            "fourth floor available at three this afternoon?",
            "M: I'm sorry, it's been booked for a video conference until four thirty.",
            "W: What about the one on the second floor? We only need it for about forty minutes.",
            "M: That one is free, but the projector is broken.",
            "W: That's all right. We just need a place to sit and talk.",
            "Q: Which room will the woman use?",
        ],
        "questions": [
            {"q": "Which room will the woman use?",
             "options": ["A. The one on the fourth floor",
                         "B. The one on the third floor",
                         "C. The one on the second floor",
                         "D. The one on the first floor"],
             "answer": "C",
             "explain": "四楼会议室被占用，二楼那间空着，女生说只要能坐下谈话就行，所以选 C。"},
            {"q": "What is wrong with the second-floor room?",
             "options": ["A. There is no projector working",
                         "B. It is too small",
                         "C. It is being cleaned",
                         "D. It has no Wi-Fi"],
             "answer": "A",
             "explain": "原文 but the projector is broken，即投影仪坏了。"},
        ],
    },
    # ------------------------------------------------------------ 长对话
    {
        "kind": "dialogue",
        "title": "长对话 1 · 实习经历",
        "level": 2,
        "script": [
            "M: Hi Anna, how was your summer internship at the newspaper?",
            "W: It was exhausting but I learned a lot. I was assigned to the city desk and had "
            "to interview ordinary people on the street almost every day.",
            "M: That sounds hard. What did you find most difficult?",
            "W: Honestly, the first few days. I was too nervous to stop people and ask questions, "
            "and my editor told me my writing was too formal.",
            "M: How did you get over that?",
            "W: My mentor took me along for a whole week and let me watch how she opened a "
            "conversation. After that, I started writing the way people actually speak.",
            "M: So would you like to work there after graduation?",
            "W: Maybe, but I also want to try broadcast news. Talking to people taught me "
            "that stories are better told than written down.",
            "Q: What did the woman find most difficult at the beginning?",
        ],
        "questions": [
            {"q": "What did the woman find most difficult at the beginning?",
             "options": ["A. Working long hours in the office",
                         "B. Approaching strangers to ask questions",
                         "C. Writing news in English",
                         "D. Getting along with her editor"],
             "answer": "B",
             "explain": "她说 the first few days …… too nervous to stop people and ask questions。"},
            {"q": "What did her mentor do for her?",
             "options": ["A. Corrected every article she wrote",
                         "B. Introduced her to the editor",
                         "C. Let her observe how to start conversations",
                         "D. Found her a job in broadcast news"],
             "answer": "C",
             "explain": "mentor 带着她看了一周 how she opened a conversation。"},
            {"q": "What is the woman's plan for the future?",
             "options": ["A. She has decided to stay at the newspaper",
                         "B. She wants to become a teacher",
                         "C. She is considering broadcast news",
                         "D. She plans to study abroad"],
             "answer": "C",
             "explain": "她说 but I also want to try broadcast news，还在考虑。"},
        ],
    },
    {
        "kind": "dialogue",
        "title": "长对话 2 · 租房",
        "level": 2,
        "script": [
            "W: Hello, I'm calling about the apartment you advertised near the university.",
            "M: Yes, it's still available. It's a two-bedroom flat on the fifth floor, "
            "and the rent is three thousand yuan a month, including water and heating but "
            "not electricity.",
            "W: Is there an elevator? My mother has trouble with stairs.",
            "M: I'm afraid not, the building is quite old. But the flat was repainted last year "
            "and the kitchen was completely renewed.",
            "W: Could I see it tomorrow evening? I have classes in the daytime.",
            "M: Sure. Let's meet at the gate of the compound at seven.",
            "W: By the way, is it far from the subway station?",
            "M: About eight minutes on foot, and there's a bus stop right outside.",
            "Q: What is NOT included in the rent?",
        ],
        "questions": [
            {"q": "What is NOT included in the rent?",
             "options": ["A. Water", "B. Heating",
                         "C. Electricity", "D. Internet"],
             "answer": "C",
             "explain": "including water and heating but not electricity，电费不包。"},
            {"q": "Why is the woman worried about the building?",
             "options": ["A. It has no elevator", "B. It is too expensive",
                         "C. It is far from her school", "D. It is noisy at night"],
             "answer": "A",
             "explain": "她问有没有电梯，因为母亲上楼梯不方便；回答是 I'm afraid not。"},
            {"q": "When will they meet?",
             "options": ["A. Tomorrow morning", "B. Tomorrow evening",
                         "C. This afternoon", "D. Next week"],
             "answer": "B",
             "explain": "约在明天晚上七点，小区门口。"},
        ],
    },
    # ------------------------------------------------------------ 短文
    {
        "kind": "passage",
        "title": "短文 1 · 睡眠与学习",
        "level": 2,
        "script": [
            "Many students believe that staying up late is the only way to prepare for exams. "
            "Research, however, suggests the opposite. During deep sleep, the brain replays what "
            "we learned during the day and moves it into long-term memory.",
            "In one experiment, two groups of students were given the same list of new words. "
            "The first group studied in the morning and was tested in the evening. The second "
            "group studied in the evening, slept, and was tested the next morning. The second "
            "group remembered nearly forty percent more.",
            "But sleep does more than store facts. It also helps us deal with emotions. People "
            "who sleep badly tend to react more strongly to small problems. So if you want to "
            "remember more and stay calm before an examination, the most useful thing may be to "
            "close the book and go to bed on time.",
            "Q: What does the passage mainly discuss?",
        ],
        "questions": [
            {"q": "What does the passage mainly discuss?",
             "options": ["A. How to take better notes",
                         "B. Why sleep matters for learning",
                         "C. The best time to take exams",
                         "D. Ways to control emotions"],
             "answer": "B",
             "explain": "全文围绕睡眠对记忆和情绪的作用展开。"},
            {"q": "How much more did the second group remember?",
             "options": ["A. About 14 percent", "B. About 20 percent",
                         "C. About 40 percent", "D. About 60 percent"],
             "answer": "C",
             "explain": "原文 nearly forty percent more。"},
        ],
    },
    {
        "kind": "passage",
        "title": "短文 2 · 旧衣回收",
        "level": 3,
        "script": [
            "Every year, millions of tons of clothing end up in landfills. Many people assume "
            "that donating old clothes is always good for the environment, but the reality is "
            "more complex. Only a small share of donated clothes is sold again in local shops. "
            "A large part is shipped abroad or turned into cleaning cloths and insulation.",
            "Shipping itself uses energy, and some receiving countries now complain that cheap "
            "second-hand clothing is hurting their own textile industries. Experts therefore "
            "suggest a simpler rule: buy less, wear longer, and repair before you replace.",
            "Some cities have started repair cafés where volunteers help people mend clothes for "
            "free. The idea is not only to save money, but to make people feel connected to the "
            "things they own.",
            "Q: What do experts suggest?",
        ],
        "questions": [
            {"q": "What do experts suggest?",
             "options": ["A. Donating clothes more often",
                         "B. Buying less and wearing longer",
                         "C. Stopping the export of old clothes",
                         "D. Building more landfills"],
             "answer": "B",
             "explain": "buy less, wear longer, and repair before you replace。"},
            {"q": "What is the purpose of repair cafés?",
             "options": ["A. To sell second-hand clothes",
                         "B. To help people mend clothes and feel attached",
                         "C. To teach people how to recycle plastic",
                         "D. To collect clothing for export"],
             "answer": "B",
             "explain": "免费帮人修补衣服，同时让人对物品产生感情。"},
        ],
    },
    {
        "kind": "passage",
        "title": "短文 3 · 城市夜跑",
        "level": 2,
        "script": [
            "Running at night has become popular among young office workers in big cities. "
            "For many of them, it is the only hour of the day that truly belongs to themselves.",
            "Doctors point out that evening exercise can improve sleep, as long as it ends at "
            "least two hours before bedtime. They also warn runners to choose well-lit routes, "
            "wear something bright, and avoid listening to music that is too loud, because they "
            "need to hear traffic.",
            "Running clubs have appeared in many neighbourhoods. Members say the biggest benefit "
            "is not the exercise itself but the company: it is much easier to keep going when "
            "someone is waiting for you at the gate.",
            "Q: According to doctors, when should evening exercise end?",
        ],
        "questions": [
            {"q": "According to doctors, when should evening exercise end?",
             "options": ["A. Right before going to bed",
                         "B. At least two hours before bedtime",
                         "C. At midnight at the latest",
                         "D. At least half an hour before dinner"],
             "answer": "B",
             "explain": "at least two hours before bedtime。"},
            {"q": "What do club members value most?",
             "options": ["A. Losing weight", "B. Competing with others",
                         "C. The company of other runners", "D. Running faster"],
             "answer": "C",
             "explain": "the benefit is not the exercise itself but the company。"},
        ],
    },
    {
        "kind": "news",
        "title": "新闻 1 · 大学图书馆延时开放",
        "level": 1,
        "script": [
            "The university library announced on Monday that it will stay open until midnight "
            "during the two weeks before the final examinations. The reading rooms on the second "
            "and third floors will be open, while the book stacks on the upper floors will close "
            "at ten as usual.",
            "The library also reminded students that food and drinks are not allowed in the "
            "reading rooms, and that seats left unused for more than one hour may be cleared.",
            "Q: Which floors will stay open until midnight?",
        ],
        "questions": [
            {"q": "Which floors will stay open until midnight?",
             "options": ["A. The first and second", "B. The second and third",
                         "C. The third and fourth", "D. All floors"],
             "answer": "B",
             "explain": "The reading rooms on the second and third floors will be open。"},
            {"q": "What may happen to a seat unused for over an hour?",
             "options": ["A. It will be given to someone else",
                         "B. It will be locked",
                         "C. A fine will be charged",
                         "D. It will be kept for the same student for a day"],
             "answer": "A",
             "explain": "seats left unused for more than one hour may be cleared。"},
        ],
    },
]

# 难度标签
LEVEL_LABEL = {1: "四级基础", 2: "四级提高", 3: "六级冲刺"}
