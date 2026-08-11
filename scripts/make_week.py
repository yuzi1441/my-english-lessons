#!/usr/bin/env python3
"""Generate a week (7 days) of beginner-friendly Immersion Reader lessons.

A continuous story: Alex, a new engineer, from Monday to Sunday.
Each day is one independent lesson page. Vocabulary repeats and builds up.
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
WEEK_DIR = ROOT / "examples" / "custom" / "week"
LESSONS_DIR = ROOT / "lessons"

STOPWORDS = set(
    """a an the and or but if then than that this these those it its is are was were be been being am
    do does did done doing have has had having will would can could should may might must shall not no
    nor so to of in on at by for with from as about into over after before between out against during
    without within above below under again once because while until too very just more most much many
    some any each both few other another such only own same up down off he she they we you i his her
    their our your my me him them us who whom which what when where why how there here also all
    s t don ll re ve d m o y""".split()
)

DAYS = [
    {
        "day": "day-01",
        "title": "Lesson 1: My First Standup",
        "title_zh": "第 1 课：我的第一次站会",
        "source": "Week 1 - Day 1",
        "segments": [
            {
                "en": (
                    "My name is Alex. Today is Monday, my first day at a new job. "
                    "I am a new engineer. My team makes a chat program. "
                    "In the morning, we have a short meeting. We call it a standup. "
                    "Everyone stands and talks. I am a little nervous. "
                    "It is my first time at a standup."
                ),
                "zh": (
                    "我叫 Alex。今天是周一，新工作的第一天。我是新来的工程师，团队在做一个聊天程序。"
                    "早上我们开个短会，叫站会。大家都站着说话。我有点紧张，这是我第一次参加站会。"
                    "讲解：engineer=工程师，nervous=紧张的，first time=第一次。"
                    "句形 my first day at a new job=新工作的第一天，have a meeting=开会。"
                ),
            },
            {
                "en": (
                    "The team leader starts. He says hello and asks everyone to say one thing. "
                    "I say: I am Alex, and I will learn the chat program today. "
                    "My teammate Maria is kind. She says: welcome, Alex. "
                    "She shows me where the code lives. "
                    "I feel better now. The team is friendly."
                ),
                "zh": (
                    "组长先开口，问大家好，然后让每个人说一件事。我说：我叫 Alex，今天要学习聊天程序。"
                    "队友 Maria 很友善，她说：欢迎你，Alex。她带我看代码放在哪里。我现在感觉好多了，"
                    "团队很友好。讲解：leader=组长/领导，kind=友善的，welcome=欢迎，"
                    "friendly=友好的。句形 say one thing=说一件事，show me where X lives=带我看 X 在哪。"
                ),
            },
            {
                "en": (
                    "After the standup, I get my first task. "
                    "My task is small: fix a small bug in the chat program. "
                    "A bug is a small problem in the code. "
                    "Maria tells me: take your time, ask questions. "
                    "I open the code and look around. "
                    "I find the problem. It is a small one. "
                    "I can fix it today."
                ),
                "zh": (
                    "站会后我接到第一个任务，任务很小：修复聊天程序里的一个小 bug。"
                    "bug 就是代码里的小问题。Maria 说：慢慢来，有问题就问。"
                    "我打开代码四处看看，找到了问题，是个小问题，今天就能修好。"
                    "讲解：task=任务，take your time=慢慢来/别着急，look around=四处看看，"
                    "fix=修复。句形 get my first task=接到第一个任务，find the problem=找到问题。"
                ),
            },
        ],
        "chunks": [
            {"t": "have a meeting", "cn": "开会", "eg": "We have a meeting every morning."},
            {"t": "first day at work", "cn": "上班第一天", "eg": "Today is my first day at work."},
            {"t": "take your time", "cn": "慢慢来;别着急", "eg": "Please take your time with the task."},
            {"t": "look around", "cn": "四处看看;熟悉一下", "eg": "I look around the code first."},
        ],
        "patterns": [
            {"t": "My name is X.", "cn": "我叫 X。例如：My name is Alex."},
            {"t": "Today is my first day at X.", "cn": "今天是我在 X 的第一天。"},
            {"t": "A bug is a small problem in X.", "cn": "bug 就是 X 里的小问题。"},
            {"t": "I find the problem.", "cn": "我找到了问题。"},
        ],
        "task": {
            "genre": "standup_update",
            "task": (
                "Write 3 short sentences in English: say your name, what you did today, "
                "and what you will do tomorrow. Try to use have a meeting, take your time, "
                "and look around."
            ),
            "hint_chunks": ["have a meeting", "take your time", "look around"],
        },
    },
    {
        "day": "day-02",
        "title": "Lesson 2: The Branch and the Bug",
        "title_zh": "第 2 课：分支与 Bug",
        "source": "Week 1 - Day 2",
        "segments": [
            {
                "en": (
                    "On Tuesday, I fix the bug. First, I make a new branch. "
                    "A branch is a copy of the code. I work in the branch. "
                    "This is safe. The main branch stays clean. "
                    "I change one line of code. "
                    "Then I test it. The bug is gone. "
                    "I am happy. My first fix is done."
                ),
                "zh": (
                    "周二我修 bug。先新建一个分支，分支是代码的副本，我在分支里改。"
                    "这样很安全，主干分支保持干净。我改了一行代码，然后测试，bug 消失了。"
                    "我很开心，第一次修复完成了。"
                    "讲解：safe=安全的，clean=干净的，line=行，gone=消失了。"
                    "句形 make a new branch=新建分支，change one line of code=改一行代码，"
                    "be done=完成了。"
                ),
            },
            {
                "en": (
                    "Maria checks my work. She says: good job, Alex. "
                    "Then she shows me how to push the code. "
                    "Push means send the code to GitHub. "
                    "GitHub is a website for code. "
                    "I type one command and push. "
                    "The code is on GitHub now. "
                    "Everyone on the team can see it. "
                    "I feel proud of my small change."
                ),
                "zh": (
                    "Maria 检查我的工作，她说：干得好，Alex。然后她教我怎么 push 代码。"
                    "push 就是把代码发到 GitHub，GitHub 是个存放代码的网站。"
                    "我敲一条命令就推送了，现在代码在 GitHub 上，队友都能看到。"
                    "我为这个小改动感到自豪。"
                    "讲解：good job=干得好，type a command=敲命令，proud=自豪的，"
                    "see=看到。句形 show me how to X=教我怎么做 X，feel proud of X=为 X 自豪。"
                ),
            },
            {
                "en": (
                    "After lunch, I learn more about the chat program. "
                    "It has two parts. The first part talks to users. "
                    "The second part is the AI brain. "
                    "The AI brain reads the message and writes an answer. "
                    "I read the code slowly. "
                    "Some words are new to me. "
                    "Maria helps me. I write the new words in my notebook."
                ),
                "zh": (
                    "午饭后我继续了解聊天程序。它有两部分：第一部分和用户对话，第二部分是 AI 大脑。"
                    "AI 大脑读消息、写回答。我慢慢读代码，有些词我不认识，Maria 帮我，我把新词记在笔记本上。"
                    "讲解：part=部分，brain=大脑，message=消息，answer=回答，notebook=笔记本。"
                    "句形 learn about X=了解 X，read the code slowly=慢慢读代码，"
                    "write in my notebook=记在笔记本上。"
                ),
            },
        ],
        "chunks": [
            {"t": "make a new branch", "cn": "新建分支", "eg": "Make a new branch before you code."},
            {"t": "good job", "cn": "干得好", "eg": "Good job on the fix, Alex."},
            {"t": "push the code", "cn": "推送代码", "eg": "I push the code to GitHub."},
            {"t": "write in my notebook", "cn": "记在笔记本上", "eg": "I write new words in my notebook."},
        ],
        "patterns": [
            {"t": "X means Y.", "cn": "X 的意思是 Y。例如：Push means send the code."},
            {"t": "I feel proud of X.", "cn": "我为 X 感到自豪。"},
            {"t": "It has two parts.", "cn": "它有两部分。"},
            {"t": "Some words are new to me.", "cn": "有些词我不认识。"},
        ],
        "task": {
            "genre": "pr_description",
            "task": (
                "Write 3 short sentences about your first fix, like a note to the team. "
                "Say what the bug was and how you fixed it. Use make a new branch, "
                "push the code, and good job."
            ),
            "hint_chunks": ["make a new branch", "push the code", "good job"],
        },
    },
    {
        "day": "day-03",
        "title": "Lesson 3: The Pull Request",
        "title_zh": "第 3 课：提交 PR",
        "source": "Week 1 - Day 3",
        "segments": [
            {
                "en": (
                    "On Wednesday, I finish a bigger task. "
                    "I add a small feature to the chat program. "
                    "A feature is a new ability. "
                    "Now the program can say hello to users. "
                    "I write the code in my branch. "
                    "Then I need to share it with the team. "
                    "I open a pull request. We call it a PR for short."
                ),
                "zh": (
                    "周三我完成一个稍大的任务：给聊天程序加个小功能。feature 就是新能力。"
                    "现在程序能跟用户打招呼了。我在分支里写完代码，需要分享给团队，于是开了一个 pull request，"
                    "简称 PR。讲解：ability=能力，say hello=打招呼，share=分享，for short=简称。"
                    "句形 add a feature=加功能，open a pull request=开一个 PR，need to X=需要做 X。"
                ),
            },
            {
                "en": (
                    "A pull request asks the team to check my code. "
                    "This check is called a review. "
                    "The computer also checks my code. "
                    "It runs the tests by itself. "
                    "The tests pass. I am happy. "
                    "Then Maria looks at my code. "
                    "She finds one small problem. "
                    "She writes a comment under my code."
                ),
                "zh": (
                    "PR 就是请团队检查我的代码，这个检查叫 review（评审）。电脑也会自动检查，跑测试。"
                    "测试通过了，我很开心。然后 Maria 看我的代码，发现一个小问题，在我的代码下面写了条评论。"
                    "讲解：check=检查，pass=通过，look at=看，write a comment=写评论。"
                    "句形 ask the team to check=请团队检查，run the tests=跑测试，"
                    "find a problem=发现问题。"
                ),
            },
            {
                "en": (
                    "I read Maria's comment. "
                    "She says: this line is a little slow. "
                    "You can make it faster. "
                    "I am not upset. Good feedback helps me learn. "
                    "I thank her and fix the line. "
                    "I push the code again. "
                    "Now Maria says: it looks good. "
                    "The review is done."
                ),
                "zh": (
                    "我读了 Maria 的评论。她说：这行代码有点慢，可以改快一点。我没有不高兴，"
                    "好的反馈能帮我进步。我谢过她，修好那行，重新推送。Maria 说看起来不错了，评审完成。"
                    "讲解：a little=一点，faster=更快的，upset=不高兴的，again=再一次。"
                    "句形 thank her and fix=谢过她并修复，it looks good=看起来不错，"
                    "help me learn=帮我学习。"
                ),
            },
        ],
        "chunks": [
            {"t": "open a pull request", "cn": "开一个 PR", "eg": "I open a pull request for the new feature."},
            {"t": "for short", "cn": "简称", "eg": "We call it a PR for short."},
            {"t": "run the tests", "cn": "跑测试", "eg": "The computer runs the tests."},
            {"t": "good feedback", "cn": "好的反馈", "eg": "Good feedback helps me learn."},
        ],
        "patterns": [
            {"t": "We call it X for short.", "cn": "我们简称它为 X。"},
            {"t": "This check is called X.", "cn": "这个检查叫做 X。"},
            {"t": "Good feedback helps me X.", "cn": "好的反馈帮我 X。"},
            {"t": "It looks good.", "cn": "看起来不错。"},
        ],
        "task": {
            "genre": "code_review_comment",
            "task": (
                "Write 2 short review comments in English. Say one thing is good, "
                "and one thing can be better. Use open a pull request, run the tests, "
                "and good feedback."
            ),
            "hint_chunks": ["open a pull request", "run the tests", "good feedback"],
        },
    },
    {
        "day": "day-04",
        "title": "Lesson 4: The AI Brain",
        "title_zh": "第 4 课：AI 大脑",
        "source": "Week 1 - Day 4",
        "segments": [
            {
                "en": (
                    "On Thursday, I learn about the AI brain. "
                    "The brain is a language model. "
                    "A language model is a big program. "
                    "It reads words and writes new words. "
                    "It is like a smart friend that knows English. "
                    "I ask the model a question in English. "
                    "It answers in English. I am amazed."
                ),
                "zh": (
                    "周四我学习 AI 大脑。大脑是个语言模型，语言模型是个很大的程序，"
                    "它能读文字、写新文字，像个懂英语的聪明朋友。我用英文问它问题，它用英文回答，我很惊叹。"
                    "讲解：language model=语言模型，smart=聪明的，question=问题，"
                    "amazed=惊叹的。句形 learn about X=学习 X，ask a question=问问题，"
                    "answer in English=用英文回答。"
                ),
            },
            {
                "en": (
                    "I give the model a prompt. "
                    "A prompt is the instruction I give it. "
                    "I write: you are a friendly teacher. "
                    "Answer in short sentences. "
                    "The model follows my prompt. "
                    "It answers in short sentences. "
                    "A good prompt makes a big difference. "
                    "I learn that prompt engineering is a real job."
                ),
                "zh": (
                    "我给模型一个 prompt（提示词），就是给它的指令。我写：你是一个友善的老师，用短句回答。"
                    "模型照做了，用短句回答。好的 prompt 效果差别很大。我了解到提示词工程是真实的工作。"
                    "讲解：friendly=友善的，teacher=老师，follow=跟随/照做，"
                    "difference=差别。句形 give a prompt=给提示词，make a big difference=效果差别很大，"
                    "a real job=一个真实的工作。"
                ),
            },
            {
                "en": (
                    "In the afternoon, I try many prompts. "
                    "One prompt is too long. The answer is messy. "
                    "Another prompt is too short. The answer is unclear. "
                    "I find a good one: short, clear, and friendly. "
                    "The answer is clean. "
                    "Testing is how I learn. "
                    "I feel like a small scientist today."
                ),
                "zh": (
                    "下午我试了很多提示词。一个太长了，答案乱；一个太短了，答案不清楚。"
                    "我找到一个好的：简短、清楚、友善，答案就干净了。靠试错来学习，今天我觉得自己像个小学者。"
                    "讲解：messy=凌乱的，unclear=不清楚的，clean=干净的，scientist=科学家。"
                    "句形 too long / too short=太长/太短，feel like=感觉像，"
                    "testing is how I learn=试错就是我学习的方式。"
                ),
            },
        ],
        "chunks": [
            {"t": "a language model", "cn": "语言模型", "eg": "The chat program uses a language model."},
            {"t": "ask a question", "cn": "问问题", "eg": "I ask the model a question."},
            {"t": "give a prompt", "cn": "给提示词", "eg": "I give the model a clear prompt."},
            {"t": "make a difference", "cn": "产生差别;起作用", "eg": "A good prompt makes a difference."},
        ],
        "patterns": [
            {"t": "X is like Y.", "cn": "X 就像 Y。例如：It is like a smart friend."},
            {"t": "X makes a big difference.", "cn": "X 效果差别很大。"},
            {"t": "One X is too long. Another X is too short.", "cn": "一个 X 太长，另一个太短。"},
            {"t": "Testing is how I learn.", "cn": "试错是我学习的方式。"},
        ],
        "task": {
            "genre": "design_note",
            "task": (
                "Write 3 short sentences about how to write a good prompt, like a small design note. "
                "Use a language model, ask a question, and make a difference."
            ),
            "hint_chunks": ["a language model", "ask a question", "make a difference"],
        },
    },
    {
        "day": "day-05",
        "title": "Lesson 5: Deploy Day",
        "title_zh": "第 5 课：上线日",
        "source": "Week 1 - Day 5",
        "segments": [
            {
                "en": (
                    "On Friday, we put the feature online. "
                    "We call this deploy. "
                    "The team is a little excited. "
                    "Deploy day is a big day. "
                    "First, I check the logs. "
                    "Logs are the records the program writes. "
                    "The logs look clean. No errors."
                ),
                "zh": (
                    "周五我们把功能上线，这叫 deploy（部署）。团队有点兴奋，上线日是大日子。"
                    "先检查日志，日志是程序写下的记录。日志看起来很干净，没有错误。"
                    "讲解：put online=上线，excited=兴奋的，records=记录，"
                    "clean=干净的，errors=错误们。句形 put X online=把 X 上线，"
                    "check the logs=检查日志，a big day=重要的一天。"
                ),
            },
            {
                "en": (
                    "Then I watch the error rate. "
                    "Error rate is how many requests fail. "
                    "A request is when a user asks for something. "
                    "The rate is low. We are safe. "
                    "Maria says: ready to go. "
                    "I press the deploy button. "
                    "We wait. Then we see: it is live."
                ),
                "zh": (
                    "然后我盯错误率，就是请求失败的占比。请求就是用户向程序要东西。"
                    "比率很低，我们很安全。Maria 说：准备上线。我按下部署按钮，我们等待，然后看到：上线了。"
                    "讲解：watch=观察，low=低的，safe=安全的，press=按，"
                    "live=上线/在线的。句形 error rate=错误率，ready to go=准备出发/可以上了，"
                    "press the button=按按钮。"
                ),
            },
            {
                "en": (
                    "The feature is live. Users can use it now. "
                    "I watch the screen for ten minutes. "
                    "Everything works. No problems. "
                    "The team is happy. We high-five. "
                    "I finish my first week with a win. "
                    "On the way home, I feel proud. "
                    "I am learning so much."
                ),
                "zh": (
                    "功能上线了，用户现在能用了。我盯着屏幕看了十分钟，一切正常，没有问题。"
                    "团队很开心，我们击掌庆祝。第一周以一场胜利结束。回家的路上我很自豪，我学到了好多。"
                    "讲解：works=正常运作，high-five=击掌，win=胜利，on the way home=回家路上。"
                    "句形 everything works=一切正常，with a win=以一场胜利，"
                    "learn so much=学到很多。"
                ),
            },
        ],
        "chunks": [
            {"t": "put online", "cn": "上线", "eg": "We put the feature online on Friday."},
            {"t": "error rate", "cn": "错误率", "eg": "I watch the error rate after deploy."},
            {"t": "ready to go", "cn": "准备就绪;可以上了", "eg": "The code is ready to go."},
            {"t": "on the way home", "cn": "回家路上", "eg": "I feel proud on the way home."},
        ],
        "patterns": [
            {"t": "We call this X.", "cn": "我们叫它 X。例如：We call this deploy."},
            {"t": "X is when Y.", "cn": "X 就是 Y 的时候。例如：A request is when a user asks."},
            {"t": "We are safe.", "cn": "我们是安全的。"},
            {"t": "Everything works.", "cn": "一切正常。"},
        ],
        "task": {
            "genre": "slack_message",
            "task": (
                "Write 3 short sentences in English, like a message to the team after deploy. "
                "Say the feature is live and all is well. Use put online, error rate, "
                "and ready to go."
            ),
            "hint_chunks": ["put online", "error rate", "ready to go"],
        },
    },
    {
        "day": "day-06",
        "title": "Lesson 6: English and Coffee",
        "title_zh": "第 6 课：英语与咖啡",
        "source": "Week 1 - Day 6",
        "segments": [
            {
                "en": (
                    "On Saturday, I rest. I do not code. "
                    "I meet my friend Lucy at a coffee shop. "
                    "Lucy speaks English well. "
                    "She wants to practice with me. "
                    "I order a coffee in English. "
                    "The waiter smiles. I am a little shy, "
                    "but I do it. I am proud."
                ),
                "zh": (
                    "周六我休息，不写代码。我和朋友 Lucy 在咖啡店见面，她英语很好，想陪我练习。"
                    "我用英语点了杯咖啡，服务员对我微笑。我有点害羞，但还是做到了，我很自豪。"
                    "讲解：rest=休息，coffee shop=咖啡店，waiter=服务员，shy=害羞的，"
                    "order=点单。句形 meet my friend=见朋友，speak English well=英语说得很好，"
                    "order a coffee=点咖啡。"
                ),
            },
            {
                "en": (
                    "Lucy teaches me a trick. "
                    "She says: do not be afraid of mistakes. "
                    "Mistakes are how we learn. "
                    "Say the word slowly. "
                    "Then say it again, faster. "
                    "I practice ten words with her. "
                    "The last one sounds good. "
                    "She claps. I laugh."
                ),
                "zh": (
                    "Lucy 教我一个小技巧。她说：别怕犯错，错误就是我们学习的方式。"
                    "慢慢说一个词，然后再说一遍，快一点。我陪她练了十个词，最后一个说得很不错，"
                    "她鼓掌，我笑了。讲解：trick=技巧/诀窍，afraid=害怕的，mistakes=错误们，"
                    "claps=鼓掌，laugh=笑。句形 be afraid of X=害怕 X，"
                    "practice words=练单词，say it again=再说一遍。"
                ),
            },
            {
                "en": (
                    "We talk about my week. "
                    "I tell her about the deploy and the AI brain. "
                    "She asks: what is your favorite word this week? "
                    "I think and say: deploy. "
                    "It is short and strong. "
                    "She laughs and says: good choice. "
                    "I write my new words in my notebook. "
                    "Learning can be fun."
                ),
                "zh": (
                    "我们聊我这周的经历，我跟她讲了上线和 AI 大脑的事。"
                    "她问：这周你最喜欢的词是什么？我想了想，说：deploy，它又短又有力。"
                    "她笑着说：好选择。我把新词记进笔记本。学习也可以是件开心的事。"
                    "讲解：favorite=最喜欢的，choice=选择，strong=有力的，fun=有趣的。"
                    "句形 talk about X=谈论 X，tell her about X=跟她讲 X，"
                    "learning can be fun=学习可以很有趣。"
                ),
            },
        ],
        "chunks": [
            {"t": "be afraid of mistakes", "cn": "害怕犯错", "eg": "Do not be afraid of mistakes."},
            {"t": "order a coffee", "cn": "点咖啡", "eg": "I order a coffee in English."},
            {"t": "say it again", "cn": "再说一遍", "eg": "Say the word again, faster."},
            {"t": "talk about", "cn": "谈论", "eg": "We talk about my week."},
        ],
        "patterns": [
            {"t": "X is how we learn.", "cn": "X 就是我们学习的方式。例如：Mistakes are how we learn."},
            {"t": "Do not be afraid of X.", "cn": "不要害怕 X。"},
            {"t": "My favorite X is Y.", "cn": "我最喜欢的 X 是 Y。"},
            {"t": "Learning can be fun.", "cn": "学习可以很有趣。"},
        ],
        "task": {
            "genre": "slack_message",
            "task": (
                "Write 2 short sentences in English about your favorite word of the week "
                "and why. Use talk about, be afraid of mistakes, and say it again."
            ),
            "hint_chunks": ["talk about", "be afraid of mistakes", "say it again"],
        },
    },
    {
        "day": "day-07",
        "title": "Lesson 7: Plan the Next Week",
        "title_zh": "第 7 课：规划下周",
        "source": "Week 1 - Day 7",
        "segments": [
            {
                "en": (
                    "On Sunday, I rest at home. "
                    "I look at my notebook. "
                    "I wrote many new words this week. "
                    "I read them slowly. "
                    "I remember most of them. "
                    "I am happy with my progress. "
                    "Practice works."
                ),
                "zh": (
                    "周日我在家休息，翻开笔记本，这周我记了好多新词。我慢慢地读，大部分都记得。"
                    "我对自己的进步很满意，练习真的有用。"
                    "讲解：at home=在家，remember=记得，most=大部分，progress=进步，"
                    "works=有用/起作用。句形 look at X=看 X，be happy with X=对 X 满意，"
                    "practice works=练习有用。"
                ),
            },
            {
                "en": (
                    "I plan the next week. "
                    "Next week, I will learn ten new words every day. "
                    "I will read one short article in English. "
                    "I will say three sentences in the standup. "
                    "I will not be afraid of mistakes. "
                    "Small steps every day. "
                    "That is the plan."
                ),
                "zh": (
                    "我规划下周。下周我每天学十个新词，读一篇短的英文文章，在站会上说三句话，"
                    "不怕犯错。每天一小步，这就是计划。"
                    "讲解：plan=计划，every day=每天，short=短的，steps=步骤，"
                    "small steps=小步。句形 I will X=我将要做 X（未来时），"
                    "every day=每天，that is the plan=这就是计划。"
                ),
            },
            {
                "en": (
                    "On Monday, a new week starts. "
                    "I will meet my team again. "
                    "I will say hello in English. "
                    "I will tell them about my weekend. "
                    "They will say: welcome back. "
                    "I feel ready. "
                    "Learning a language is a journey. "
                    "I take it one step at a time."
                ),
                "zh": (
                    "周一新的星期开始。我会再见到团队，用英文打招呼，跟他们讲我的周末。"
                    "他们会说：欢迎回来。我觉得准备好了。学语言是一段旅程，我一步一个脚印地走。"
                    "讲解：weekend=周末，welcome back=欢迎回来，ready=准备好的，"
                    "journey=旅程。句形 a new week starts=新的一周开始，"
                    "one step at a time=一步一个脚印，feel ready=感觉准备好了。"
                ),
            },
        ],
        "chunks": [
            {"t": "be happy with", "cn": "对…满意", "eg": "I am happy with my progress."},
            {"t": "small steps", "cn": "小步;循序渐进", "eg": "Small steps every day work."},
            {"t": "welcome back", "cn": "欢迎回来", "eg": "My team says welcome back."},
            {"t": "one step at a time", "cn": "一步一个脚印", "eg": "I take it one step at a time."},
        ],
        "patterns": [
            {"t": "I am happy with X.", "cn": "我对 X 很满意。"},
            {"t": "I will X next week.", "cn": "下周我要 X。"},
            {"t": "Small steps every day.", "cn": "每天一小步。"},
            {"t": "I take it one step at a time.", "cn": "我一步一个脚印地走。"},
        ],
        "task": {
            "genre": "standup_update",
            "task": (
                "Write 3 short sentences about your plan for the next week. "
                "Say one thing you will learn and one thing you will do. "
                "Use be happy with, small steps, and one step at a time."
            ),
            "hint_chunks": ["be happy with", "small steps", "one step at a time"],
        },
    },
]

# Shared basic lexicon: reused across all days.
BASE_LEXICON = {
    "morning": {"def": "早晨", "ipa": "/ˈmɔr.nɪŋ/"},
    "short": {"def": "短的", "ipa": "/ʃɔrt/"},
    "meeting": {"def": "会议", "ipa": "/ˈmi.tɪŋ/"},
    "call": {"def": "称呼;打电话", "ipa": "/kɔl/"},
    "standup": {"def": "站会", "ipa": "/ˈstænd.ʌp/"},
    "tell": {"def": "告诉", "ipa": "/tel/"},
    "team": {"def": "团队", "ipa": "/tiːm/"},
    "everyone": {"def": "每个人", "ipa": "/ˈev.ri.wʌn/"},
    "today": {"def": "今天", "ipa": "/təˈdeɪ/"},
    "only": {"def": "只有;仅仅", "ipa": "/ˈoʊn.li/"},
    "helps": {"def": "帮助", "ipa": "/helps/"},
    "know": {"def": "知道", "ipa": "/noʊ/"},
    "plan": {"def": "计划", "ipa": "/plæn/"},
    "chat": {"def": "聊天", "ipa": "/tʃæt/"},
    "feature": {"def": "功能", "ipa": "/ˈfi.tʃər/"},
    "users": {"def": "用户们", "ipa": "/ˈju.zərz/"},
    "talk": {"def": "交谈", "ipa": "/tɔk/"},
    "computer": {"def": "电脑", "ipa": "/kəmˈpju.tər/"},
    "program": {"def": "程序", "ipa": "/ˈproʊ.ɡræm/"},
    "make": {"def": "做;制造", "ipa": "/meɪk/"},
    "branch": {"def": "分支", "ipa": "/bræntʃ/"},
    "copy": {"def": "副本;复制", "ipa": "/ˈkɑ.pi/"},
    "write": {"def": "写", "ipa": "/raɪt/"},
    "push": {"def": "推送", "ipa": "/pʊʃ/"},
    "GitHub": {"def": "代码托管网站", "ipa": "/ˈɡɪt.hʌb/"},
    "website": {"def": "网站", "ipa": "/ˈweb.saɪt/"},
    "open": {"def": "打开;开启", "ipa": "/ˈoʊ.pən/"},
    "review": {"def": "评审;回顾", "ipa": "/rɪˈvju/"},
    "tests": {"def": "测试们", "ipa": "/tests/"},
    "fix": {"def": "修复", "ipa": "/fɪks/"},
    "green": {"def": "绿色的;通过的", "ipa": "/ɡriːn/"},
    "feedback": {"def": "反馈", "ipa": "/ˈfid.bæk/"},
    "merge": {"def": "合并", "ipa": "/mɝdʒ/"},
    "main": {"def": "主要的", "ipa": "/meɪn/"},
    "language": {"def": "语言", "ipa": "/ˈlæŋ.ɡwɪdʒ/"},
    "model": {"def": "模型", "ipa": "/ˈmɑ.dəl/"},
    "prompt": {"def": "提示词", "ipa": "/prɑmpt/"},
    "deploy": {"def": "部署;上线", "ipa": "/dɪˈplɔɪ/"},
    "online": {"def": "在线的", "ipa": "/ˈɑn.laɪn/"},
    "error": {"def": "错误", "ipa": "/ˈer.ər/"},
    "rate": {"def": "比率", "ipa": "/reɪt/"},
    "check": {"def": "检查", "ipa": "/tʃek/"},
    "logs": {"def": "日志们", "ipa": "/lɔɡz/"},
    "push": {"def": "推送", "ipa": "/pʊʃ/"},
    "write": {"def": "写", "ipa": "/raɪt/"},
    "learn": {"def": "学习", "ipa": "/lɝn/"},
    "code": {"def": "代码", "ipa": "/koʊd/"},
    "bug": {"def": "缺陷;小问题", "ipa": "/bʌɡ/"},
    "work": {"def": "工作", "ipa": "/wɝk/"},
    "job": {"def": "工作", "ipa": "/dʒɑb/"},
    "new": {"def": "新的", "ipa": "/nu/"},
    "first": {"def": "第一个;初次", "ipa": "/fɝst/"},
    "day": {"def": "一天", "ipa": "/deɪ/"},
    "nervous": {"def": "紧张的", "ipa": "/ˈnɝ.vəs/"},
    "time": {"def": "时间;次", "ipa": "/taɪm/"},
    "leader": {"def": "组长;领导", "ipa": "/ˈli.dər/"},
    "starts": {"def": "开始", "ipa": "/stɑrts/"},
    "says": {"def": "说", "ipa": "/sez/"},
    "one": {"def": "一个", "ipa": "/wʌn/"},
    "kind": {"def": "友善的", "ipa": "/kaɪnd/"},
    "welcome": {"def": "欢迎", "ipa": "/ˈwel.kəm/"},
    "shows": {"def": "展示", "ipa": "/ʃoʊz/"},
    "where": {"def": "哪里", "ipa": "/wer/"},
    "lives": {"def": "存在;住", "ipa": "/lɪvz/"},
    "better": {"def": "更好的", "ipa": "/ˈbet.ər/"},
    "friendly": {"def": "友好的", "ipa": "/ˈfrend.li/"},
    "task": {"def": "任务", "ipa": "/tæsk/"},
    "small": {"def": "小的", "ipa": "/smɔl/"},
    "problem": {"def": "问题", "ipa": "/ˈprɑ.bləm/"},
    "questions": {"def": "问题们", "ipa": "/ˈkwes.tʃənz/"},
    "around": {"def": "周围;四处", "ipa": "/əˈraʊnd/"},
    "find": {"def": "找到;发现", "ipa": "/faɪnd/"},
    "fix": {"def": "修复", "ipa": "/fɪks/"},
    "safe": {"def": "安全的", "ipa": "/seɪf/"},
    "clean": {"def": "干净的", "ipa": "/kliːn/"},
    "change": {"def": "改变;改动", "ipa": "/tʃeɪndʒ/"},
    "line": {"def": "行;线路", "ipa": "/laɪn/"},
    "test": {"def": "测试", "ipa": "/test/"},
    "gone": {"def": "消失的", "ipa": "/ɡɔn/"},
    "happy": {"def": "开心的", "ipa": "/ˈhæp.i/"},
    "done": {"def": "完成的", "ipa": "/dʌn/"},
    "checks": {"def": "检查", "ipa": "/tʃeks/"},
    "good": {"def": "好的", "ipa": "/ɡʊd/"},
    "how": {"def": "怎样", "ipa": "/haʊ/"},
    "send": {"def": "发送", "ipa": "/send/"},
    "type": {"def": "敲;打字", "ipa": "/taɪp/"},
    "command": {"def": "命令", "ipa": "/kəˈmænd/"},
    "see": {"def": "看到", "ipa": "/siː/"},
    "proud": {"def": "自豪的", "ipa": "/praʊd/"},
    "lunch": {"def": "午餐", "ipa": "/lʌntʃ/"},
    "parts": {"def": "部分们", "ipa": "/pɑrts/"},
    "brain": {"def": "大脑", "ipa": "/breɪn/"},
    "message": {"def": "消息", "ipa": "/ˈmes.ɪdʒ/"},
    "answer": {"def": "回答", "ipa": "/ˈæn.sər/"},
    "slowly": {"def": "慢慢地", "ipa": "/ˈsloʊ.li/"},
    "words": {"def": "单词们", "ipa": "/wɝdz/"},
    "notebook": {"def": "笔记本", "ipa": "/ˈnoʊt.bʊk/"},
    "bigger": {"def": "更大的", "ipa": "/ˈbɪɡ.ər/"},
    "ability": {"def": "能力", "ipa": "/əˈbɪl.ə.ti/"},
    "share": {"def": "分享", "ipa": "/ʃer/"},
    "asks": {"def": "请求;问", "ipa": "/æsks/"},
    "called": {"def": "被叫做", "ipa": "/kɔld/"},
    "runs": {"def": "运行", "ipa": "/rʌnz/"},
    "pass": {"def": "通过", "ipa": "/pæs/"},
    "looks": {"def": "看起来", "ipa": "/lʊks/"},
    "comment": {"def": "评论", "ipa": "/ˈkɑ.ment/"},
    "little": {"def": "一点", "ipa": "/ˈlɪt.əl/"},
    "slow": {"def": "慢的", "ipa": "/sloʊ/"},
    "faster": {"def": "更快的", "ipa": "/ˈfæs.tər/"},
    "upset": {"def": "不高兴的", "ipa": "/ʌpˈset/"},
    "thank": {"def": "感谢", "ipa": "/θæŋk/"},
    "again": {"def": "再一次", "ipa": "/əˈɡen/"},
    "big": {"def": "大的", "ipa": "/bɪɡ/"},
    "reads": {"def": "阅读", "ipa": "/riːdz/"},
    "smart": {"def": "聪明的", "ipa": "/smɑrt/"},
    "friend": {"def": "朋友", "ipa": "/frend/"},
    "knows": {"def": "知道", "ipa": "/noʊz/"},
    "amazed": {"def": "惊叹的", "ipa": "/əˈmeɪzd/"},
    "instruction": {"def": "指令", "ipa": "/ɪnˈstrʌk.ʃən/"},
    "give": {"def": "给", "ipa": "/ɡɪv/"},
    "friendly": {"def": "友好的", "ipa": "/ˈfrend.li/"},
    "teacher": {"def": "老师", "ipa": "/ˈti.tʃər/"},
    "follows": {"def": "遵循", "ipa": "/ˈfɑ.loʊz/"},
    "difference": {"def": "差别", "ipa": "/ˈdɪf.ər.əns/"},
    "engineering": {"def": "工程", "ipa": "/ˌen.dʒɪˈnɪr.ɪŋ/"},
    "real": {"def": "真实的", "ipa": "/riːl/"},
    "afternoon": {"def": "下午", "ipa": "/ˌæf.tərˈnuːn/"},
    "try": {"def": "尝试", "ipa": "/traɪ/"},
    "many": {"def": "许多", "ipa": "/ˈmen.i/"},
    "messy": {"def": "凌乱的", "ipa": "/ˈmes.i/"},
    "another": {"def": "另一个", "ipa": "/əˈnʌð.ər/"},
    "unclear": {"def": "不清楚的", "ipa": "/ʌnˈklɪr/"},
    "scientist": {"def": "科学家", "ipa": "/ˈsaɪ.ən.tɪst/"},
    "works": {"def": "起作用;运作", "ipa": "/wɝks/"},
    "excited": {"def": "兴奋的", "ipa": "/ɪkˈsaɪ.tɪd/"},
    "records": {"def": "记录们", "ipa": "/ˈrek.ərdz/"},
    "errors": {"def": "错误们", "ipa": "/ˈer.ərz/"},
    "when": {"def": "当…时", "ipa": "/wen/"},
    "request": {"def": "请求", "ipa": "/rɪˈkwest/"},
    "press": {"def": "按", "ipa": "/pres/"},
    "button": {"def": "按钮", "ipa": "/ˈbʌt.ən/"},
    "wait": {"def": "等待", "ipa": "/weɪt/"},
    "live": {"def": "上线;直播", "ipa": "/lɪv/"},
    "screen": {"def": "屏幕", "ipa": "/skriːn/"},
    "everything": {"def": "一切", "ipa": "/ˈev.ri.θɪŋ/"},
    "high-five": {"def": "击掌", "ipa": "/ˈhaɪ.faɪv/"},
    "finish": {"def": "完成", "ipa": "/ˈfɪn.ɪʃ/"},
    "week": {"def": "周;星期", "ipa": "/wiːk/"},
    "win": {"def": "胜利", "ipa": "/wɪn/"},
    "way": {"def": "路;方式", "ipa": "/weɪ/"},
    "home": {"def": "家", "ipa": "/hoʊm/"},
    "much": {"def": "很多", "ipa": "/mʌtʃ/"},
    "rest": {"def": "休息", "ipa": "/rest/"},
    "meet": {"def": "见面", "ipa": "/miːt/"},
    "coffee": {"def": "咖啡", "ipa": "/ˈkɔ.fi/"},
    "speaks": {"def": "说;讲", "ipa": "/spiːks/"},
    "well": {"def": "好地", "ipa": "/wel/"},
    "wants": {"def": "想要", "ipa": "/wɑnts/"},
    "practice": {"def": "练习", "ipa": "/ˈpræk.tɪs/"},
    "order": {"def": "点单", "ipa": "/ˈɔr.dər/"},
    "waiter": {"def": "服务员", "ipa": "/ˈweɪ.tər/"},
    "smiles": {"def": "微笑", "ipa": "/smaɪlz/"},
    "shy": {"def": "害羞的", "ipa": "/ʃaɪ/"},
    "teaches": {"def": "教", "ipa": "/tiːtʃɪz/"},
    "trick": {"def": "技巧", "ipa": "/trɪk/"},
    "afraid": {"def": "害怕的", "ipa": "/əˈfreɪd/"},
    "mistakes": {"def": "错误们", "ipa": "/mɪˈsteɪks/"},
    "last": {"def": "最后一个", "ipa": "/læst/"},
    "sounds": {"def": "听起来", "ipa": "/saʊndz/"},
    "claps": {"def": "鼓掌", "ipa": "/klæps/"},
    "laugh": {"def": "笑", "ipa": "/læf/"},
    "favorite": {"def": "最喜欢的", "ipa": "/ˈfeɪ.vər.ɪt/"},
    "think": {"def": "想", "ipa": "/θɪŋk/"},
    "strong": {"def": "有力的", "ipa": "/strɔŋ/"},
    "choice": {"def": "选择", "ipa": "/tʃɔɪs/"},
    "fun": {"def": "有趣的", "ipa": "/fʌn/"},
    "remember": {"def": "记得", "ipa": "/rɪˈmem.bər/"},
    "most": {"def": "大部分", "ipa": "/moʊst/"},
    "progress": {"def": "进步", "ipa": "/ˈprɑ.ɡres/"},
    "next": {"def": "下一个", "ipa": "/nekst/"},
    "article": {"def": "文章", "ipa": "/ˈɑr.tɪ.kəl/"},
    "three": {"def": "三", "ipa": "/θriː/"},
    "sentences": {"def": "句子们", "ipa": "/ˈsen.tənsɪz/"},
    "steps": {"def": "步骤们", "ipa": "/steps/"},
    "starts": {"def": "开始", "ipa": "/stɑrts/"},
    "hello": {"def": "你好", "ipa": "/həˈloʊ/"},
    "weekend": {"def": "周末", "ipa": "/ˈwiːk.end/"},
    "ready": {"def": "准备好的", "ipa": "/ˈred.i/"},
    "journey": {"def": "旅程", "ipa": "/ˈdʒɝ.ni/"},
    "add": {"def": "添加", "ipa": "/æd/"},
    "alex": {"def": "人名;Alex", "ipa": "/ˈæl.ɪks/"},
    "answers": {"def": "回答", "ipa": "/ˈæn.sərz/"},
    "ask": {"def": "问", "ipa": "/æsk/"},
    "back": {"def": "回来", "ipa": "/bæk/"},
    "clear": {"def": "清楚的", "ipa": "/klɪr/"},
    "engineer": {"def": "工程师", "ipa": "/ˌen.dʒɪˈnɪr/"},
    "english": {"def": "英语", "ipa": "/ˈɪŋ.ɡlɪʃ/"},
    "every": {"def": "每一个", "ipa": "/ˈev.ri/"},
    "fail": {"def": "失败", "ipa": "/feɪl/"},
    "feel": {"def": "感觉", "ipa": "/fiːl/"},
    "finds": {"def": "发现", "ipa": "/faɪndz/"},
    "friday": {"def": "星期五", "ipa": "/ˈfraɪ.deɪ/"},
    "get": {"def": "得到;变得", "ipa": "/ɡet/"},
    "github": {"def": "代码托管网站", "ipa": "/ˈɡɪt.hʌb/"},
    "itself": {"def": "它自己", "ipa": "/ɪtˈself/"},
    "laughs": {"def": "笑", "ipa": "/læfs/"},
    "learning": {"def": "学习", "ipa": "/ˈlɝ.nɪŋ/"},
    "like": {"def": "像;喜欢", "ipa": "/laɪk/"},
    "long": {"def": "长的", "ipa": "/lɔŋ/"},
    "look": {"def": "看", "ipa": "/lʊk/"},
    "low": {"def": "低的", "ipa": "/loʊ/"},
    "lucy": {"def": "人名;Lucy", "ipa": "/ˈlu.si/"},
    "makes": {"def": "做;使", "ipa": "/meɪks/"},
    "maria": {"def": "人名;Maria", "ipa": "/məˈri.ə/"},
    "means": {"def": "意思是", "ipa": "/miːnz/"},
    "minutes": {"def": "分钟", "ipa": "/ˈmɪn.ɪts/"},
    "monday": {"def": "星期一", "ipa": "/ˈmʌn.deɪ/"},
    "name": {"def": "名字", "ipa": "/neɪm/"},
    "need": {"def": "需要", "ipa": "/niːd/"},
    "now": {"def": "现在", "ipa": "/naʊ/"},
    "part": {"def": "部分", "ipa": "/pɑrt/"},
    "problems": {"def": "问题们", "ipa": "/ˈprɑ.bləmz/"},
    "prompts": {"def": "提示词们", "ipa": "/prɑmpts/"},
    "pull": {"def": "拉;拉取", "ipa": "/pʊl/"},
    "put": {"def": "放;放置", "ipa": "/pʊt/"},
    "question": {"def": "问题", "ipa": "/ˈkwes.tʃən/"},
    "read": {"def": "阅读", "ipa": "/riːd/"},
    "requests": {"def": "请求们", "ipa": "/rɪˈkwests/"},
    "saturday": {"def": "星期六", "ipa": "/ˈsæt.ər.deɪ/"},
    "say": {"def": "说", "ipa": "/seɪ/"},
    "second": {"def": "第二;秒", "ipa": "/ˈsek.ənd/"},
    "shop": {"def": "店铺", "ipa": "/ʃɑp/"},
    "something": {"def": "某事", "ipa": "/ˈsʌm.θɪŋ/"},
    "stands": {"def": "站立", "ipa": "/stændz/"},
    "stays": {"def": "保持;停留", "ipa": "/steɪz/"},
    "step": {"def": "一步;步骤", "ipa": "/step/"},
    "sunday": {"def": "星期日", "ipa": "/ˈsʌn.deɪ/"},
    "take": {"def": "拿;花费", "ipa": "/teɪk/"},
    "talks": {"def": "交谈", "ipa": "/tɔks/"},
    "teammate": {"def": "队友", "ipa": "/ˈtim.meɪt/"},
    "tells": {"def": "告诉", "ipa": "/telz/"},
    "ten": {"def": "十", "ipa": "/ten/"},
    "testing": {"def": "测试;试错", "ipa": "/ˈtes.tɪŋ/"},
    "thing": {"def": "事情", "ipa": "/θɪŋ/"},
    "thursday": {"def": "星期四", "ipa": "/ˈθɝz.deɪ/"},
    "tuesday": {"def": "星期二", "ipa": "/ˈtuz.deɪ/"},
    "two": {"def": "二", "ipa": "/tu/"},
    "use": {"def": "使用", "ipa": "/juːz/"},
    "user": {"def": "用户", "ipa": "/ˈju.zər/"},
    "watch": {"def": "观察;看", "ipa": "/wɑtʃ/"},
    "wednesday": {"def": "星期三", "ipa": "/ˈwenz.deɪ/"},
    "word": {"def": "单词", "ipa": "/wɝd/"},
    "writes": {"def": "写", "ipa": "/raɪts/"},
    "wrote": {"def": "写了(write的过去式)", "ipa": "/roʊt/"},
    "clap": {"def": "鼓掌", "ipa": "/klæp/"},
    "follow": {"def": "遵循;跟随", "ipa": "/ˈfɑ.loʊ/"},
    "help": {"def": "帮助", "ipa": "/help/"},
    "log": {"def": "日志", "ipa": "/lɔɡ/"},
    "mean": {"def": "意思是;意味着", "ipa": "/miːn/"},
    "minute": {"def": "分钟", "ipa": "/ˈmɪn.ɪt/"},
    "mistake": {"def": "错误", "ipa": "/mɪˈsteɪk/"},
    "pre": {"def": "前;预(前缀)", "ipa": "/pri/"},
    "progre": {"def": "进步(progress的误切)", "ipa": "/ˈprɑ.ɡres/"},
    "record": {"def": "记录", "ipa": "/rɪˈkɔrd/"},
    "run": {"def": "跑;运行", "ipa": "/rʌn/"},
    "sentence": {"def": "句子", "ipa": "/ˈsen.təns/"},
    "show": {"def": "展示", "ipa": "/ʃoʊ/"},
    "smile": {"def": "微笑", "ipa": "/smaɪl/"},
    "sound": {"def": "听起来;声音", "ipa": "/saʊnd/"},
    "speak": {"def": "说;讲", "ipa": "/spiːk/"},
    "stand": {"def": "站立", "ipa": "/stænd/"},
    "start": {"def": "开始", "ipa": "/stɑrt/"},
    "stay": {"def": "保持;停留", "ipa": "/steɪ/"},
    "teache": {"def": "教(teacher的误切)", "ipa": "/tiːtʃ/"},
    "thi": {"def": "这(this的误切)", "ipa": "/ðɪs/"},
    "want": {"def": "想要", "ipa": "/wɑnt/"},
}


def build_day(day: dict) -> dict:
    segments = []
    for idx, seg in enumerate(day["segments"], start=1):
        segments.append(
            {
                "id": f"seg-{idx:02d}",
                "en": seg["en"],
                "tts": seg["en"],
                "zh": seg["zh"],
                "hard": [],
            }
        )
    # Build hard words: top content words of the day not covered by base lesson
    day_words = content_words_of_day(day)
    base_known = {
        "morning", "short", "meeting", "call", "standup", "tell", "team", "plan", "chat",
        "feature", "talk", "program", "make", "branch", "push", "GitHub", "code", "review",
        "test", "fix", "green", "feedback", "merge", "main", "language", "model", "prompt",
        "deploy", "online", "error", "rate", "check", "log", "learn", "bug", "work", "job",
        "new", "first", "day", "time", "problem", "find", "safe", "clean", "change", "write",
        "open", "comment", "give", "message", "answer", "week", "computer", "run", "pass",
    }
    hard_terms = sorted(w for w in day_words if w not in base_known and w in BASE_LEXICON)
    hard = []
    for w in hard_terms[:5]:
        entry = BASE_LEXICON[w]
        hard.append({"w": w, "type": "word", "def": entry["def"]})
    for seg, seg_hard in zip(segments, hard_terms[:3]):
        pass
    if hard:
        segments[0]["hard"] = hard
    return segments


def content_words_of_day(day: dict) -> set[str]:
    words: set[str] = set()
    for seg in day["segments"]:
        for token in re.findall(r"[a-z][a-z'-]*", seg["en"].lower()):
            if token.endswith("'s"):
                token = token[:-2]
            if token not in STOPWORDS and len(token) > 2:
                words.add(token)
    return words


def all_content_words() -> set[str]:
    words: set[str] = set()
    for day in DAYS:
        words |= content_words_of_day(day)
    return words
def build_lexicon_for_day(day: dict) -> dict:
    lexicon = {}
    raw_words: set[str] = set()
    for seg in day["segments"]:
        for token in re.findall(r"[a-z][a-z'-]*", seg["en"].lower()):
            raw_words.add(token)
    for w in raw_words:
        if w in BASE_LEXICON:
            lexicon[w] = BASE_LEXICON[w]
        elif w.endswith("'s") and w[:-2] in BASE_LEXICON:
            lexicon[w] = {"lemma": w[:-2]}
    return lexicon


def normalize_ipa(ipa: str) -> str:
    return ipa.replace("ɒ", "ɑ").replace("əʊ", "oʊ").replace("ː", "")


def make_data(day: dict) -> dict:
    segments = build_day(day)
    total_words = sum(len(s["en"].split()) for s in segments)
    lexicon = {w: {**e, "ipa": normalize_ipa(e["ipa"])} if e.get("ipa") else e for w, e in build_lexicon_for_day(day).items()}
    return {
        "meta": {
            "title": day["title"],
            "title_zh": day["title_zh"],
            "source": day["source"],
            "url": "",
            "kind": "article",
            "lang": "en",
            "study_card": {
                "word_count": total_words,
                "segment_count": len(segments),
                "difficulty": "入门",
                "estimated_days": 1,
                "main_practice": "跟读 + 精读 + 中文讲解对照",
                "value_points": [
                    day["chunks"][0]["cn"],
                    day["chunks"][1]["cn"],
                    "每日一次英文小练习",
                ],
                "suggested_pace": "先逐句听读一遍 · 再看中文讲解 · 最后完成英文小练习",
            },
        },
        "voice": {"engine": "edge", "voice": "en-US-AndrewNeural", "rate": "-20%", "speed": 0.8},
        "segments": segments,
        "chunks": day["chunks"],
        "patterns": day["patterns"],
        "transfer_tasks": [day["task"]],
        "lexicon": lexicon,
    }


def build_index() -> str:
    rows = []
    for day in DAYS:
        link = f"{day['day']}/index.html"
        rows.append(
            f'<li><a href="{link}"><h2>{day["title"]}</h2><p>{day["title_zh"]} · 3 段 · 约 15 分钟</p></a></li>'
        )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>英语学习周计划 · Week 1</title>
<style>
body{{font-family:-apple-system,sans-serif;max-width:720px;margin:0 auto;padding:32px 20px;line-height:1.6;background:#fafafa;color:#222}}
h1{{font-size:28px;margin-bottom:4px}}
.sub{{color:#666;margin-bottom:24px}}
ul{{list-style:none;padding:0}}
li{{background:#fff;border:1px solid #e3e3e3;border-radius:10px;margin-bottom:12px;overflow:hidden}}
a{{display:block;padding:16px 20px;text-decoration:none;color:#222}}
a:hover{{background:#f0f7ff}}
h2{{margin:0 0 4px;font-size:18px}}
p{{margin:0;color:#666;font-size:14px}}
</style>
</head>
<body>
<h1>英语学习周计划 · Week 1</h1>
<p class="sub">连续剧情：新工程师 Alex 的一周 · 每天一课 · 入门难度 · 全部含中文讲解</p>
<ul>
{''.join(rows)}
</ul>
</body>
</html>
"""


def main() -> int:
    all_words = all_content_words()
    missing = sorted(w for w in all_words if w not in BASE_LEXICON)
    if missing:
        print(f"missing lexicon: {missing}")
        return 1
    for day in DAYS:
        day_dir = WEEK_DIR / day["day"]
        day_dir.mkdir(parents=True, exist_ok=True)
        data = make_data(day)
        out = day_dir / "segments.json"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        lexicon = build_lexicon_for_day(day)
        all_day = content_words_of_day(day)
        cov_missing = sorted(w for w in all_day if w not in lexicon)
        print(f"{day['day']}: words={data['meta']['study_card']['word_count']} lexicon={len(lexicon)}/{len(all_day)} missing={cov_missing}")
    print(f"week written to {WEEK_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
