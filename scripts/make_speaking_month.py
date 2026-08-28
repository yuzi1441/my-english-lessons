#!/usr/bin/env python3
"""Generate the 30-day speaking course: one continuous story per day, built on that day's 18 vocabulary items.

Design contract:
- Vocabulary is the main line: every one of the day's 18 items (6 computer, 6 daily, 6 GitHub)
  appears verbatim in the day's spoken English, verified before anything is written.
- The story is continuous: a fixed cast (Alex, mentor Maria, teammates Leo and Priya) moves
  through a 30-day arc from onboarding to release to month review, with each day getting its
  own opening, life beat, and closing hook.
- Difficulty climbs day by day: tier 1 short simple sentences up to tier 4 professional
  register; speech rate rises with the tiers.
- Every English sentence is authored together with its exact Chinese translation, so the
  page's 原文翻译 is a true translation, not a mechanical fill-in.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOCAB = ROOT / "examples" / "vocabulary-month" / "month.json"
OUT = ROOT / "examples" / "custom" / "week"

sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lesson_quality import word_audio_slug  # noqa: E402
from make_vocabulary_month import speech_text  # noqa: E402

VERB_STARTS = {
    "accept", "add", "amend", "approve", "assign", "cancel", "catch", "check", "cite", "clean",
    "clone", "close", "complete", "confirm", "convert", "create", "debug", "discard", "do", "download",
    "execute", "fetch", "finish", "fix", "fork", "free", "go", "handle", "install", "leave", "link",
    "make", "mark", "merge", "mention", "open", "parse", "pick", "process", "publish", "pull", "push",
    "rebase", "receive", "remove", "reproduce", "request", "reset", "resolve", "restart", "restore",
    "restrict", "retry", "revert",
    "revoke", "run", "save", "send", "sign", "squash", "start", "stop", "subscribe", "switch", "sync",
    "take", "turn", "uninstall", "unsubscribe", "update", "verify", "wash", "watch",
}

# terms that begin with a verb-looking word but are noun phrases
NP_ALWAYS = {
    "process", "retry", "retry limit", "request", "open source", "open question",
    "clean state", "clone URL", "pull request template", "request for comments",
}

# terms verified as verb + object/modifier phrases
VP_COMPOUNDS = {
    "clone a repository", "download the code", "run a program", "execute code", "stop a process",
    "save a snapshot", "make a commit", "create a branch", "switch branches", "process data",
    "push changes", "pull changes", "fetch updates", "sync with remote", "fix a bug",
    "open an issue", "close an issue", "install software", "uninstall a program",
    "open a pull request", "request a review", "save to disk", "free up space", "approve changes",
    "request changes", "leave a comment", "resolve a conversation", "take out the trash",
    "wash the dishes", "clean the room", "pick up groceries", "finish the chores", "do the laundry",
    "merge branches", "resolve a conflict", "accept incoming change", "complete the merge",
    "make an appointment", "cancel an appointment", "confirm the time", "check details",
    "fork a repository", "watch a repository", "resolve a domain", "add a label", "remove a label",
    "assign an issue", "mention a teammate", "subscribe to an issue", "unsubscribe from updates",
    "send a request", "receive a response", "mark as ready", "convert to draft", "parse data",
    "sign out", "revoke a token", "restore data", "restrict pushes", "start a container",
    "publish a release", "amend a commit", "revert a commit", "reset a branch", "discard changes",
    "restore a file", "catch an exception", "handle an error", "squash and merge", "rebase and merge",
    "squash commits", "rebase a branch", "verify the answer", "link to documentation",
    "cite a source", "link a commit", "update immediately",
    "reproduce an error", "restart the computer",
}

# plural-form noun terms: singular "be" frames would break agreement
PLURAL_NPS = {"draft changes", "system settings"}

SPEAKERS = ["Maria", "Leo", "Priya"]

# When both daily items of a scene share the same wording (repeated drill phrases),
# a two-person exchange would echo; narrate it as one heard line plus a repeat.
ECHO_SOLE = {
    1: [
        ('{spk} says, "{d1}" I repeat it.', '{spk}说："{d1z}"我跟着重复了一遍。'),
        ('I hear, "{d1}" then I say it too.', '我听到："{d1z}"然后我也说了一遍。'),
    ],
    2: [
        ('{spk} says, "{d1}" and I repeat it twice.', '{spk}说："{d1z}"我重复了两遍。'),
        ('First I hear, "{d1}" then I say it myself.', '我先听到："{d1z}"然后自己说了一遍。'),
    ],
    3: [
        ('{spk} says, "{d1}" and I repeat it until it feels natural.', '{spk}说："{d1z}"我反复练习，直到说起来自然。'),
        ('We both use the same words today: "{d1}"', '我们今天都用了同一句话："{d1z}"'),
    ],
    4: [
        ('{spk} says, "{d1}" and I repeat it to make it stick.', '{spk}说："{d1z}"我又重复了一遍，好把它记牢。'),
        ('The phrase of the day is "{d1}" and I use it twice.', '今天的重点句型是"{d1z}"，我用了两次。'),
    ],
}


# ---------------------------------------------------------------------------
# Difficulty tiers
# ---------------------------------------------------------------------------

def tier_of(day: int) -> int:
    if day <= 7:
        return 1
    if day <= 14:
        return 2
    if day <= 21:
        return 3
    return 4


TIER_META = {
    1: {"name": "入门短句", "rate": "-22%", "speed": 0.82,
        "pace": "先盲听 · 逐句跟读 · 看着中文说出英文",
        "practice": "听短句 · 跟读 · 替换成自己的话"},
    2: {"name": "基础表达", "rate": "-16%", "speed": 0.86,
        "pace": "先猜大意 · 听读 2 遍 · 遮住中文复述",
        "practice": "听完整段 · 跟读 · 用连接词复述"},
    3: {"name": "连贯叙述", "rate": "-10%", "speed": 0.90,
        "pace": "先盲听全篇 · 精读从句 · 复述剧情",
        "practice": "听细节 · 解释因果 · 连贯复述"},
    4: {"name": "专业场景", "rate": "-5%", "speed": 0.95,
        "pace": "先听更新要点 · 记下风险词 · 模拟汇报",
        "practice": "听专业表达 · 提炼观点 · 做一次英文汇报"},
}


# ---------------------------------------------------------------------------
# 30-day story arc: unique bilingual framing for every day
# ---------------------------------------------------------------------------

PLOT = [
    {"title_en": "The First Morning", "title_zh": "第一个早晨",
     "open_en": "Today is Monday. It is my first day at a new job. My team makes a chat program.",
     "open_zh": "今天是周一，是我新工作的第一天。我的团队在做一个聊天程序。",
     "life_en": "At noon, Maria sits with me. She introduces the team.",
     "life_zh": "中午，Maria 和我坐在一起。她把我介绍给团队。",
     "close_en": "I am tired, but happy. Tomorrow I will learn more.",
     "close_zh": "我有点累，但很开心。明天我会学到更多。"},
    {"title_en": "Copy the First Code", "title_zh": "复制第一份代码",
     "open_en": "Yesterday I met the team. Today Maria gives me my first job: copy the project code to my computer.",
     "open_zh": "昨天我认识了团队。今天 Maria 给了我第一个任务：把项目代码复制到我的电脑上。",
     "life_en": "I need help, and I learn to ask for it.",
     "life_zh": "我需要帮助，也学会了开口求助。",
     "close_en": "The code is on my computer now. I feel ready for tomorrow.",
     "close_zh": "代码现在在我的电脑上了。我为明天做好了准备。"},
    {"title_en": "The First Commit", "title_zh": "第一次提交",
     "open_en": "Today I run a small program, and it works.",
     "open_zh": "今天我运行了一个小程序，它成功了。",
     "life_en": "At lunch, we talk about the time for a short meeting.",
     "life_zh": "午饭时，我们讨论了一个短会的时间。",
     "close_en": "Before I leave, I save my first commit. My name is in the history now.",
     "close_zh": "离开前，我保存了第一次提交。我的名字现在进入了历史记录。"},
    {"title_en": "My Own Branch", "title_zh": "我的分支",
     "open_en": "Maria says my code is fine. Today I learn to make my own branch.",
     "open_zh": "Maria 说我的代码没问题。今天我学习建立自己的分支。",
     "life_en": "After work, I buy a new notebook. I ask about the price.",
     "life_zh": "下班后，我买了一个新笔记本。我询问了价格。",
     "close_en": "My branch is small, but it is mine.",
     "close_zh": "我的分支很小，但它是我自己的。"},
    {"title_en": "Push and Pull", "title_zh": "推送与拉取",
     "open_en": "My branch is ready. Today I push it to the team's server.",
     "open_zh": "我的分支准备好了。今天我把它推送到团队的服务器上。",
     "life_en": "The team orders lunch together, and I order too.",
     "life_zh": "团队一起点午餐，我也点了。",
     "close_en": "I pull the team's new code before I leave. We are in sync now.",
     "close_zh": "离开前，我拉取了团队的新代码。我们同步了。"},
    {"title_en": "An Issue for the Bug", "title_zh": "给缺陷开个单子",
     "open_en": "This morning, my program stops with an error.",
     "open_zh": "今天早上，我的程序报错停了。",
     "life_en": "After work, I take the bus home and ask about the way.",
     "life_zh": "下班后，我坐公交回家，问了路。",
     "close_en": "I open an issue for the bug. The team can see it now.",
     "close_zh": "我为这个缺陷开了一个问题单。团队现在能看到了。"},
    {"title_en": "My First Pull Request", "title_zh": "第一个拉取请求",
     "open_en": "The bug is fixed. Today I ask the team to review my work.",
     "open_zh": "缺陷修好了。今天我请团队评审我的工作。",
     "life_en": "Leo invites me to coffee on Friday. I say yes.",
     "life_zh": "Leo 邀请我周五去喝咖啡。我答应了。",
     "close_en": "My first pull request is open. This week, I learned a lot.",
     "close_zh": "我的第一个拉取请求打开了。这一周，我学到了很多。"},
    {"title_en": "Reading the Review", "title_zh": "读懂评审意见",
     "open_en": "Week two starts. My pull request has comments.",
     "open_zh": "第二周开始了。我的拉取请求收到了评论。",
     "life_en": "I call a teammate on video. The connection is bad, but we talk.",
     "life_zh": "我和一位队友视频通话。连接不好，但我们聊了很久。",
     "close_en": "The comments are kind. I know what to fix.",
     "close_zh": "评论很友善。我知道该改什么了。"},
    {"title_en": "The Merge Conflict", "title_zh": "合并冲突",
     "open_en": "I fix the code and try to merge. But two changes fight.",
     "open_zh": "我改好代码，尝试合并。但两处改动冲突了。",
     "life_en": "At home, I do the laundry and wash the dishes.",
     "life_zh": "在家里，我洗衣服、洗碗。",
     "close_en": "Maria helps me resolve the conflict. The merge is complete.",
     "close_zh": "Maria 帮我解决了冲突。合并完成了。"},
    {"title_en": "Waiting for the Checks", "title_zh": "等待检查通过",
     "open_en": "Before we merge, the automatic checks must pass.",
     "open_zh": "合并之前，自动检查必须通过。",
     "life_en": "I reschedule a short meeting, because the time does not work.",
     "life_zh": "我重新安排了一个短会，因为那个时间不方便。",
     "close_en": "All checks are green. We merge tomorrow.",
     "close_zh": "所有检查都是绿色的。我们明天合并。"},
    {"title_en": "Looking at Open Source", "title_zh": "看看开源世界",
     "open_en": "The merge is done. Today we look at a famous open source project.",
     "open_zh": "合并完成了。今天我们研究一个著名的开源项目。",
     "life_en": "The weather is nice, and we chat at the window.",
     "life_zh": "天气不错，我们在窗边聊天。",
     "close_en": "I star the project and follow its updates.",
     "close_zh": "我给项目点了星，并关注它的动态。"},
    {"title_en": "Labels and Milestones", "title_zh": "标签与里程碑",
     "open_en": "The team plans the next version. We organize the work.",
     "open_zh": "团队在规划下一个版本。我们把工作整理归类。",
     "life_en": "Maria travels next week. She talks about her hotel.",
     "life_zh": "Maria 下周要出差。她聊起了她的酒店。",
     "close_en": "Every issue now has a label and a due date.",
     "close_zh": "现在每个问题单都有了标签和截止日期。"},
    {"title_en": "Who Takes the Issue", "title_zh": "谁来负责",
     "open_en": "A new issue comes in. The team asks who can take it.",
     "open_zh": "一个新的问题单进来了。团队问谁能负责。",
     "life_en": "Leo goes to the airport. His flight is delayed.",
     "life_zh": "Leo 去机场。他的航班延误了。",
     "close_en": "I take the issue. The team mentions me, and I see it.",
     "close_zh": "我接下了这个问题单。团队提到了我，我看到了提醒。"},
    {"title_en": "The Draft Lesson", "title_zh": "草稿的学问",
     "open_en": "I start the new work, but it is not ready for review.",
     "open_zh": "我开始做新工作，但还不到评审的时候。",
     "life_en": "We eat at a new restaurant. I ask about the menu.",
     "life_zh": "我们去了一家新餐厅。我询问了菜单。",
     "close_en": "I open a draft pull request. The team can watch it grow.",
     "close_zh": "我开了一个草稿拉取请求。团队可以看着它慢慢成形。"},
    {"title_en": "The Pipeline", "title_zh": "自动化的流水线",
     "open_en": "Week three. My draft is ready, and the pipeline runs.",
     "open_zh": "第三周。我的草稿准备好了，流水线开始运行。",
     "life_en": "At standup, I say what I finished and what is next.",
     "life_zh": "站会上，我说了已完成的内容和下一步。",
     "close_en": "The automated tests pass. The team trusts the pipeline.",
     "close_zh": "自动化测试通过了。团队信任这条流水线。"},
    {"title_en": "Test, Build, Deploy", "title_zh": "测试、构建、部署",
     "open_en": "Today the team deploys a small change to the real users.",
     "open_zh": "今天团队向真实用户部署一个小改动。",
     "life_en": "My order is wrong at the shop, and I ask to change it.",
     "life_zh": "我在商店拿错了订单，我请求更换。",
     "close_en": "The deployment works. We watch the logs together.",
     "close_zh": "部署成功了。我们一起观察日志。"},
    {"title_en": "Keep the Secret Safe", "title_zh": "密钥不能泄露",
     "open_en": "I feel sick today, but an important task waits.",
     "open_zh": "我今天不太舒服，但一个重要任务在等着我。",
     "life_en": "I visit the pharmacy and ask about the medicine.",
     "life_zh": "我去了药店，询问了这种药。",
     "close_en": "The token is safe, and the secret stays outside the code.",
     "close_zh": "令牌是安全的，机密留在代码之外。"},
    {"title_en": "The Protected Branch", "title_zh": "受保护的主分支",
     "open_en": "I try to push to the main branch, but it is protected.",
     "open_zh": "我想直接推送到主分支，但它是受保护的。",
     "life_en": "In the afternoon, there is a fire drill. Everyone is safe.",
     "life_zh": "下午，大楼有消防演习。所有人都安全。",
     "close_en": "Now I understand the rule: reviews protect the main branch.",
     "close_zh": "现在我理解了规则：评审保护主分支。"},
    {"title_en": "Our First Release", "title_zh": "第一次发布",
     "open_en": "The version is ready. Today we publish a release.",
     "open_zh": "版本准备好了。今天我们发布一个正式版本。",
     "life_en": "I have a different view, and I say it politely.",
     "life_zh": "我有不同的看法，我礼貌地说了出来。",
     "close_en": "The release is out. Users can see the new feature.",
     "close_zh": "版本发布了。用户能看到新功能了。"},
    {"title_en": "The Changelog", "title_zh": "变更日志",
     "open_en": "After the release, we write down what changed.",
     "open_zh": "发布之后，我们记录有哪些变化。",
     "life_en": "We compare two plans and choose one.",
     "life_zh": "我们比较了两个方案，选择了一个。",
     "close_en": "The changelog is clear. New users can understand it.",
     "close_zh": "变更日志很清楚。新用户能看懂。"},
    {"title_en": "Fixing a Wrong Commit", "title_zh": "改错了怎么办",
     "open_en": "I find a mistake in my last commit.",
     "open_zh": "我发现上次提交里有个错误。",
     "life_en": "The sink at home is leaking. I call for help.",
     "life_zh": "家里的水槽漏水了。我打电话求助。",
     "close_en": "I revert the commit and make a clean one. The history is safe.",
     "close_zh": "我还原了那次提交，重新做了一个干净的提交。历史是安全的。"},
    {"title_en": "Reproduce the Problem", "title_zh": "复现那个问题",
     "open_en": "Week four. A user reports a strange problem.",
     "open_zh": "第四周。一位用户报告了一个奇怪的问题。",
     "life_en": "My package is late. I call customer service.",
     "life_zh": "我的包裹迟到了。我打了客服电话。",
     "close_en": "I write the steps to reproduce. Now the team can see the bug.",
     "close_zh": "我写下了复现步骤。现在团队能看到这个缺陷了。"},
    {"title_en": "Words for Review", "title_zh": "评审用语",
     "open_en": "I review a teammate's code today.",
     "open_zh": "今天我评审队友的代码。",
     "life_en": "The deadline is close, and I ask for one more day.",
     "life_zh": "截止时间快到了，我请求多一天。",
     "close_en": "My comments are kind and clear. The team thanks me.",
     "close_zh": "我的评论友善而清楚。团队向我道谢。"},
    {"title_en": "Choosing How to Merge", "title_zh": "合并的策略",
     "open_en": "The team must choose how to merge our work.",
     "open_zh": "团队必须选择合并工作的方式。",
     "life_en": "We compare two options and make a decision.",
     "life_zh": "我们比较了两个选项，做出了决定。",
     "close_en": "We squash the small commits. The history is clean.",
     "close_zh": "我们压缩了小提交。历史变得干净了。"},
    {"title_en": "Discuss Before We Build", "title_zh": "先讨论，再动手",
     "open_en": "A big idea comes up. We open a discussion first.",
     "open_zh": "一个大想法出现了。我们先开了一个讨论。",
     "life_en": "I am not completely sure, and I say so.",
     "life_zh": "我不是完全确定，我如实说了。",
     "close_en": "The discussion becomes a decision record. We build next week.",
     "close_zh": "讨论变成了一份决策记录。下周开始实现。"},
    {"title_en": "Cite Your Sources", "title_zh": "注明来源",
     "open_en": "I use an AI tool to check an answer.",
     "open_zh": "我用一个 AI 工具核对答案。",
     "life_en": "We talk about a piece of news at lunch.",
     "life_zh": "午饭时，我们讨论了一条新闻。",
     "close_en": "Every claim now links to a source. The note is strong.",
     "close_zh": "每个说法现在都有来源链接。这份笔记很扎实。"},
    {"title_en": "The Security Alert", "title_zh": "安全警报",
     "open_en": "This morning, a security alert arrives.",
     "open_zh": "今天早上，一个安全警报来了。",
     "life_en": "I check a strange charge at the bank.",
     "life_zh": "我在银行核查了一笔可疑的扣款。",
     "close_en": "We update the dependency. The alert is resolved.",
     "close_zh": "我们更新了依赖。警报解除了。"},
    {"title_en": "Welcoming Contributors", "title_zh": "欢迎贡献者",
     "open_en": "A new contributor joins our project.",
     "open_zh": "一位新贡献者加入了我们的项目。",
     "life_en": "Everyone is welcome here, and we keep the talk respectful.",
     "life_zh": "这里欢迎每个人，我们让讨论保持尊重。",
     "close_en": "The guide is clear. The first outside contribution is merged.",
     "close_zh": "指南很清楚。第一个外部贡献合并了。"},
    {"title_en": "The Release Checklist", "title_zh": "上线清单",
     "open_en": "Tomorrow we ship a big version. Today we check the plan.",
     "open_zh": "明天我们要上线一个大版本。今天我们检查计划。",
     "life_en": "I practice my short presentation for the team.",
     "life_zh": "我为团队演练了我的简短介绍。",
     "close_en": "The checklist is done. The rollback plan is ready too.",
     "close_zh": "检查表完成了。回滚方案也准备好了。"},
    {"title_en": "The Month Review", "title_zh": "一个月的路",
     "open_en": "It is my last day of this month. I look back at the road.",
     "open_zh": "这是这个月的最后一天。我回望走过的路。",
     "life_en": "I say what I learned and what I will improve.",
     "life_zh": "我说了自己学到的，还要改进的。",
     "close_en": "The project update is clear. Next month, I am ready for more.",
     "close_zh": "项目更新很清楚。下个月，我准备好了更多。"},
]


# ---------------------------------------------------------------------------
# Bilingual sentence templates. Each English template is authored together
# with its exact Chinese translation; slots are filled from month.json.
# ---------------------------------------------------------------------------

NP_POOL = {
    1: [
        ("I look at {np}.", "我看着{z}。"),
        ("This is {np}.", "这是{z}。"),
        ("I see {np}.", "我看到了{z}。"),
        ("{np_cap} is new to me.", "{z}对我来说很新。"),
        ("Maria shows me {np}.", "Maria 给我看了{z}。"),
        ("I point to {np}.", "我指着{z}。"),
    ],
    2: [
        ("Maria explains {np} to me.", "Maria 给我讲解{z}。"),
        ("I learn about {np} because it is useful.", "我学习{z}，因为它很有用。"),
        ("Now I understand {np}.", "现在我理解了{z}。"),
        ("I write a short note about {np}.", "我给{z}写了一条简短的笔记。"),
        ("I ask one question about {np}.", "我问了一个关于{z}的问题。"),
        ("Leo tells me a story about {np}.", "Leo 给我讲了一个关于{z}的小故事。"),
    ],
    3: [
        ("Before the meeting, I review {np} one more time.", "开会前，我又复习了一遍{z}。"),
        ("The team talks about {np} at the standup.", "团队在站会上讨论了{z}。"),
        ("When I use {np}, I ask Maria for advice.", "使用{z}时，我向 Maria 请教。"),
        ("I compare {np} with my notes.", "我把{z}和我的笔记做了比较。"),
        ("Priya and I look for a detail in {np}.", "Priya 和我在{z}里找一个细节。"),
        ("After lunch, I check {np} again.", "午饭后，我又检查了一遍{z}。"),
    ],
    4: [
        ("If {np} fails, we need a clear plan.", "如果{z}失败，我们需要一个清晰的方案。"),
        ("I suggest that we check {np} first.", "我建议我们先检查{z}。"),
        ("The result depends on {np}, so I check it twice.", "结果取决于{z}，所以我检查了两遍。"),
        ("I explain {np} to a new teammate.", "我向一位新队友解释了{z}。"),
        ("We discuss the risk around {np}.", "我们讨论了{z}相关的风险。"),
        ("I document {np} so the team can review it later.", "我把{z}写成文档，方便团队之后查看。"),
    ],
}

VP_POOL = {
    1: [
        ("I {vp}.", "我{vz}。"),
        ("I {vp} slowly.", "我慢慢{vz}。"),
        ("Now I can {vp}.", "现在我会{vz}了。"),
        ("I try to {vp}.", "我试着{vz}。"),
        ("Maria asks me to {vp}.", "Maria 让我{vz}。"),
        ("I {vp} with Maria.", "我和 Maria 一起{vz}。"),
    ],
    2: [
        ("Today I {vp} for the first time.", "今天我第一次{vz}。"),
        ("I {vp}, and Maria checks it.", "我{vz}，Maria 来检查。"),
        ("I need to {vp} before lunch.", "午饭前，我需要{vz}。"),
        ("I {vp} carefully.", "我认真地{vz}。"),
        ("Leo shows me how to {vp}.", "Leo 教我怎样{vz}。"),
        ("I {vp} one small step at a time.", "我一步一步地{vz}。"),
    ],
    3: [
        ("After I {vp}, I tell the team.", "我{vz}之后，告诉了团队。"),
        ("I {vp} so the team can see the change.", "我{vz}，好让团队看到变化。"),
        ("Before I {vp}, I read the note.", "在{vz}之前，我先看了说明。"),
        ("When I {vp}, I follow the guide.", "我{vz}时，按照指南操作。"),
        ("I {vp}, and Priya watches the result.", "我{vz}，Priya 在旁边看结果。"),
        ("It takes me ten minutes to {vp}.", "我花了十分钟{vz}。"),
    ],
    4: [
        ("I {vp} and then explain the risk.", "我{vz}，然后解释了风险。"),
        ("We decide to {vp} after the review.", "评审之后，我们决定{vz}。"),
        ("If we {vp}, the result should be safe.", "如果我们{vz}，结果应该是安全的。"),
        ("I {vp}, and I record the reason.", "我{vz}，并记录了原因。"),
        ("The team agrees to {vp} before Friday.", "团队同意在周五之前{vz}。"),
        ("I {vp} while the others watch the dashboard.", "我{vz}，其他队友盯着仪表盘。"),
    ],
}

VP_LIFE_POOL = {
    1: [
        ("At home, I {vp}.", "在家里，我{vz}。"),
        ("In the evening, I {vp}.", "晚上，我{vz}。"),
        ("I {vp} every day.", "我每天都{vz}。"),
    ],
    2: [
        ("After work, I {vp}.", "下班后，我{vz}。"),
        ("Before bed, I {vp}.", "睡觉前，我{vz}。"),
        ("On my way home, I {vp}.", "回家路上，我{vz}。"),
    ],
    3: [
        ("When I get home, I {vp} first.", "到家后，我先{vz}。"),
        ("I {vp} while I listen to the news.", "我一边听新闻，一边{vz}。"),
        ("This week, I {vp} a little faster.", "这周，我{vz}得快了一些。"),
    ],
    4: [
        ("Even on busy days, I {vp} without rushing.", "即使在忙碌的日子，我也不慌不忙地{vz}。"),
        ("I {vp}, and then I plan the next morning.", "我{vz}，然后安排第二天早上。"),
        ("I {vp} and remind myself that rest matters too.", "我{vz}，也提醒自己休息同样重要。"),
    ],
}

DLG_POOL = {
    1: [
        ('{spk} says, "{d1}" and I say, "{d2}"', '{spk}说："{d1z}"我说："{d2z}"'),
        ('I hear, "{d1}" then I answer, "{d2}"', '我听到："{d1z}"然后我回答："{d2z}"'),
        ('{spk} smiles and says, "{d1}" I answer, "{d2}"', '{spk}微笑着说："{d1z}"我回答："{d2z}"'),
    ],
    2: [
        ('{spk} says, "{d1}" so I answer, "{d2}"', '{spk}说："{d1z}"于是我回答："{d2z}"'),
        ('First {spk} says, "{d1}" then I reply, "{d2}"', '先是{spk}说："{d1z}"然后我回答："{d2z}"'),
        ('During our chat, {spk} says, "{d1}" I answer, "{d2}"', '聊天时，{spk}说："{d1z}"我回答："{d2z}"'),
    ],
    3: [
        ('When we meet, {spk} says, "{d1}" I reply, "{d2}"', '见面时，{spk}说："{d1z}"我回答："{d2z}"'),
        ('{spk} starts with "{d1}" and I continue with "{d2}"', '{spk}先说了"{d1z}"我接着说："{d2z}"'),
        ('At the table, {spk} says, "{d1}" I think, then answer, "{d2}"', '桌边，{spk}说："{d1z}"我想了想，回答："{d2z}"'),
    ],
    4: [
        ('Before we part, {spk} says, "{d1}" I answer, "{d2}"', '分开前，{spk}说："{d1z}"我回答："{d2z}"'),
        ('{spk} checks with me, "{d1}" I answer clearly, "{d2}"', '{spk}向我确认："{d1z}"我清楚地回答："{d2z}"'),
        ('At the end of the day, {spk} says, "{d1}" I reply, "{d2}"', '一天结束时，{spk}说："{d1z}"我回答："{d2z}"'),
    ],
}

PATTERN_POOL = {
    1: [
        ("I practise the pattern out loud: {dl}", "我大声练习这个句型：{dlz}"),
        ("I say the new pattern twice: {dl}", "我把新句型读了两遍：{dlz}"),
        ("I read the pattern slowly: {dl}", "我慢慢读出这个句型：{dlz}"),
        ("Maria says the pattern, and I repeat it: {dl}", "Maria 说出这个句型，我跟着重复：{dlz}"),
    ],
    2: [
        ("Maria asks me to use the pattern: {dl}", "Maria 让我用上这个句型：{dlz}"),
        ("I repeat the pattern after Maria: {dl}", "我跟着 Maria 重复这个句型：{dlz}"),
        ("I write the pattern in my notebook: {dl}", "我把这个句型写在笔记本上：{dlz}"),
        ("The pattern of the day is {dl}", "今天的重点句型是{dlz}"),
    ],
    3: [
        ("I put the pattern into my own sentence: {dl}", "我把这个句型放进自己的句子里：{dlz}"),
        ("The team practises the pattern together: {dl}", "团队一起练习这个句型：{dlz}"),
        ("I use the pattern to ask a question: {dl}", "我用这个句型提了一个问题：{dlz}"),
        ("Leo corrects my use of the pattern: {dl}", "Leo 纠正了我对这个句型的用法：{dlz}"),
    ],
    4: [
        ("In my update, I use the pattern naturally: {dl}", "在汇报里，我自然地用上了这个句型：{dlz}"),
        ("I teach the pattern to a new teammate: {dl}", "我把这个句型教给一位新队友：{dlz}"),
        ("I build a full answer around the pattern: {dl}", "我围绕这个句型组织了一个完整的回答：{dlz}"),
        ("The pattern helps me sound clear and calm: {dl}", "这个句型让我听起来清楚又从容：{dlz}"),
    ],
}

SCENE_CLOSE_POOL = {
    1: [
        ("I feel good today.", "我今天感觉很好。"),
        ("I learn one new thing.", "我学到了一件新东西。"),
        ("Maria helps me a lot.", "Maria 帮了我很多。"),
    ],
    2: [
        ("The day is busy, but I learn a lot.", "这天很忙，但我学到了很多。"),
        ("I understand a little more than yesterday.", "我比昨天多懂了一点。"),
        ("The team gives me good advice.", "团队给了我很好的建议。"),
    ],
    3: [
        ("The work is not easy, but I keep going.", "工作不容易，但我继续前进。"),
        ("I write down what I learned today.", "我记下了今天学到的东西。"),
        ("With the team's help, the problem becomes smaller.", "在团队的帮助下，问题变小了。"),
    ],
    4: [
        ("The day ends with a clear plan for tomorrow.", "这一天以一份清晰的明日计划结束。"),
        ("I check my notes and confirm the next step.", "我检查笔记，确认了下一步。"),
        ("The team agrees on the plan, and I record the decision.", "团队就计划达成一致，我记录了决定。"),
    ],
}

SEG3_INTRO = {
    1: ("Before I leave, I do one last thing.", "离开前，我做最后一件事。"),
    2: ("Before I leave, I finish one last task.", "离开前，我完成最后一项任务。"),
    3: ("Before I leave, I review what I did today.", "离开前，我回顾了今天做的事。"),
    4: ("Before I leave, I write a short summary for the team.", "离开前，我给团队写了一份简短的总结。"),
}

PATTERNS_BY_TIER = {
    1: [
        {"t": "I see the X.", "cn": "我看到了 X。"},
        {"t": "This is X.", "cn": "这是 X。"},
        {"t": "Now I can X.", "cn": "现在我会 X 了。"},
    ],
    2: [
        {"t": "First I X, then I Y.", "cn": "我先 X，然后 Y。"},
        {"t": "I X because Y.", "cn": "我 X，因为 Y。"},
        {"t": "Today I X for the first time.", "cn": "今天我第一次 X。"},
    ],
    3: [
        {"t": "Before I X, I Y.", "cn": "在 X 之前，我先 Y。"},
        {"t": "When I X, I Y.", "cn": "我 X 的时候，Y。"},
        {"t": "I X so the team can Y.", "cn": "我 X，好让团队 Y。"},
    ],
    4: [
        {"t": "If X fails, we need Y.", "cn": "如果 X 失败，我们需要 Y。"},
        {"t": "I suggest that we X first.", "cn": "我建议我们先 X。"},
        {"t": "X is done, but Y still needs Z.", "cn": "X 完成了，但 Y 还需要 Z。"},
    ],
}

TRANSFER_GENRES = ["standup_update", "slack_message", "design_note", "code_review_comment", "pr_description"]

# Offline dictionary entries for high-frequency story words beyond the day's 18.
STORY_LEXICON = {
    "team": "团队，一起工作的一群人", "meeting": "会议", "morning": "早上", "afternoon": "下午",
    "evening": "晚上", "today": "今天", "tomorrow": "明天", "yesterday": "昨天",
    "lunch": "午餐", "dinner": "晚餐", "break": "休息", "week": "周；星期",
    "month": "月", "day": "天；日子", "time": "时间", "job": "工作；职位",
    "work": "工作", "task": "任务", "plan": "计划", "step": "步骤",
    "help": "帮助", "question": "问题", "answer": "回答", "advice": "建议",
    "note": "笔记", "history": "历史；记录", "change": "改动；变化", "result": "结果",
    "reason": "原因", "risk": "风险", "decision": "决定", "guide": "指南",
    "error": "错误", "bug": "缺陷", "fix": "修复", "check": "检查",
    "test": "测试", "review": "评审；回顾", "update": "更新", "release": "发布；版本",
    "server": "服务器", "user": "用户", "code": "代码", "project": "项目",
    "computer": "电脑", "screen": "屏幕", "desk": "桌子", "office": "办公室",
    "friend": "朋友", "teammate": "队友", "mentor": "导师", "leader": "组长",
    "happy": "开心的", "tired": "累的", "nervous": "紧张的", "ready": "准备好的",
    "kind": "友善的", "clear": "清楚的", "careful": "仔细的", "safe": "安全的",
    "new": "新的", "first": "第一", "last": "最后的", "next": "下一个",
    "small": "小的", "big": "大的", "short": "短的", "long": "长的",
    "learn": "学习", "teach": "教", "practice": "练习", "repeat": "重复",
    "listen": "听", "smile": "微笑", "ask": "问；请求", "say": "说",
    "show": "展示", "explain": "解释", "record": "记录", "finish": "完成",
    "start": "开始", "leave": "离开", "arrive": "到达", "join": "加入",
    "merge": "合并", "push": "推送", "pull": "拉取", "commit": "提交",
    "branch": "分支", "deploy": "部署", "rollback": "回滚", "pipeline": "流水线",
    # high-frequency story words
    "maria": "Maria，Alex 的导师", "leo": "Leo，Alex 的队友", "priya": "Priya，Alex 的队友",
    "alex": "Alex，本课主角", "one": "一；一个", "two": "两；二", "write": "写",
    "now": "现在", "look": "看", "twice": "两次", "reply": "回答",
    "lot": "许多", "pattern": "句型；模式", "good": "好的", "later": "稍后",
    "point": "指；要点", "see": "看见", "need": "需要", "understand": "理解",
    "use": "使用", "depends": "取决于", "fails": "失败", "summary": "总结",
    "around": "围绕；大约", "discuss": "讨论", "document": "记录成文档", "suggest": "建议",
    "thing": "事情", "talk": "交谈", "compare": "比较", "detail": "细节",
    "agrees": "同意", "chat": "聊天", "try": "尝试", "learned": "学到的",
    "becomes": "变得", "standup": "站会", "ends": "结束", "confirm": "确认",
    "feel": "感觉", "gives": "给", "read": "读", "meet": "见面",
    "busy": "忙碌的", "little": "一点；小的", "story": "故事", "tells": "告诉",
    "useful": "有用的", "smaller": "更小的", "build": "构建", "clearly": "清楚地",
    "end": "结尾", "full": "完整的", "hear": "听到", "carefully": "认真地",
    "watch": "观察", "problem": "问题", "continue": "继续", "easy": "容易的",
    "going": "going to 表将要", "keep": "保持", "part": "部分", "slowly": "慢慢地",
    "make": "制作", "together": "一起", "home": "家", "friday": "周五",
    "table": "桌子；表格", "think": "想", "decide": "决定", "move": "前进；移动",
    "calm": "从容的", "sound": "听起来", "program": "程序", "late": "迟的",
    "included": "包含在内", "take": "拿；采取", "know": "知道", "back": "回来；向后",
    "monday": "周一", "road": "路", "chat program": "聊天程序", "dashboard": "仪表盘",
    "fire drill": "消防演习", "pharmacy": "药店", "medicine": "药", "bank": "银行",
    "charge": "扣款", "package": "包裹", "customer service": "客服", "deadline": "截止时间",
    "extension": "延期", "trade-offs": "取舍", "option": "选项", "presenter": "介绍人",
    "presentation": "介绍；演示", "menu": "菜单", "price": "价格", "notebook": "笔记本",
    "airport": "机场", "flight": "航班", "hotel": "酒店", "restaurant": "餐厅",
    "bus": "公交车", "way": "路；方式", "weather": "天气", "window": "窗户",
    "news": "新闻", "opinion": "看法", "version": "版本", "feature": "功能",
    "rule": "规则", "security": "安全", "alert": "警报", "dependency": "依赖",
    "contributor": "贡献者", "respect": "尊重", "claim": "说法", "source": "来源",
    "link": "链接", "discussion": "讨论", "idea": "想法", "record": "记录",
}
STORY_LEMMAS = {
    "says": "say", "asks": "ask", "answers": "answer", "helps": "help",
    "checks": "check", "fixes": "fix", "learns": "learn", "shows": "show",
    "smiles": "smile", "explains": "explain", "records": "record", "finishes": "finish",
    "starts": "start", "leaves": "leave", "joins": "join", "merges": "merge",
    "pushes": "push", "pulls": "pull", "reviews": "review", "tests": "test",
    "plans": "plan", "notes": "note", "tasks": "task", "steps": "step",
    "changes": "change", "results": "result", "users": "user", "days": "day",
    "weeks": "week", "meetings": "meeting", "questions": "question", "errors": "error",
    "writes": "write", "looks": "look", "points": "point", "sees": "see",
    "needs": "need", "understands": "understand", "uses": "use", "suggests": "suggest",
    "compares": "compare", "talks": "talk", "tries": "try", "reads": "read",
    "hears": "hear", "watches": "watch", "thinks": "think", "makes": "make",
    "gives": "give", "tells": "tell", "feels": "feel", "meets": "meet",
    "keeps": "keep", "moves": "move", "decides": "decide", "confirms": "confirm",
    "discusses": "discuss", "documents": "document", "repeats": "repeat", "practises": "practice",
    "thanks": "thank", "orders": "order", "works": "work", "runs": "run",
    "hands": "hand", "minutes": "minute", "commits": "commit", "branches": "branch",
    "issues": "issue", "labels": "label",
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def cap(sentence: str) -> str:
    return sentence[:1].upper() + sentence[1:]


# mass / abstract terms read ungrammatically with a definite article
ARTLESS = {
    "source code", "code hosting", "continuous integration", "open source",
    "data flow", "training data", "structured data", "linear history",
    "machine learning", "secret scanning", "JSON", "CSV", "debugging",
}


def np_form(term: str) -> str:
    lowered = term.strip().lower()
    if lowered in ARTLESS:
        return term
    first = term.split()[0] if term.split() else ""
    if first == "GitHub":
        return term
    return f"the {term}"


def zh_core(item: dict) -> str:
    meaning = str(item.get("meaning", "")).strip()
    if item.get("domain") == "daily":
        return meaning
    return meaning.split("，", 1)[0].strip()


def term_kind(item: dict) -> str:
    """Route each item to a sentence shape that keeps grammar safe."""
    term = str(item.get("term", "")).strip()
    lowered = term.lower()
    if term.endswith("..."):
        return "pattern"
    if term.endswith((".", "?", "!")):
        return "line"
    if lowered in NP_ALWAYS:
        return "np"
    if lowered in VP_COMPOUNDS:
        return "vp"
    first = re.sub(r"[^a-z]", "", lowered.split()[0]) if lowered.split() else ""
    if item.get("domain") == "daily" and first in VERB_STARTS:
        return "vp"
    return "np"


SOLO_LINE = {
    1: ('{spk} {verb}, "{d1}"', '{spk}{verbz}："{d1z}"'),
    2: ('Then {spk} {verb}, "{d1}"', '接着{spk}{verbz}："{d1z}"'),
    3: ('At that moment, {spk} {verb}, "{d1}"', '这时，{spk}{verbz}："{d1z}"'),
    4: ('Before we move on, {spk} {verb}, "{d1}"', '继续之前，{spk}{verbz}："{d1z}"'),
}


def pick(pool: list, day: int, salt: int):
    return pool[(day + salt) % len(pool)]


def pick_seq(pool: list, day: int, cursor: dict):
    """Sequential cursor pick: consecutive sentences never reuse a template."""
    item = pool[(day + cursor["n"]) % len(pool)]
    cursor["n"] += 1
    return item


def solo_line_sentence(item: dict, tier: int, day: int, cursor: dict) -> tuple[str, str]:
    term = str(item["term"]).strip()
    core = zh_core(item)
    verb, verbz = ("asks", "问") if term.endswith("?") else ("says", "说")
    en_t, zh_t = SOLO_LINE[tier]
    spk = SPEAKERS[(day + cursor["n"]) % len(SPEAKERS)]
    cursor["n"] += 1
    return cap(en_t.format(spk=spk, verb=verb, d1=term, d1z=core)), zh_t.format(spk=spk, verbz=verbz, d1z=core)


NP_PLURAL_SWAP = {
    "This is {np}.": ("These are {np}.", "这些是{z}。"),
    "{np_cap} is new to me.": ("{np_cap} are new to me.", "{z}对我来说很新。"),
    "If {np} fails, we need a clear plan.": ("If {np} fail, we need a clear plan.", "如果{z}失败，我们需要一个清晰的方案。"),
}


def term_sentence(item: dict, tier: int, day: int, cursor: dict) -> tuple[str, str]:
    kind = term_kind(item)
    term = str(item["term"]).strip()
    core = zh_core(item)
    if kind == "np":
        en_t, zh_t = pick_seq(NP_POOL[tier], day, cursor)
        if term.lower() in PLURAL_NPS and en_t in NP_PLURAL_SWAP:
            en_t, zh_t = NP_PLURAL_SWAP[en_t]
        np = np_form(term)
        en = en_t.format(np=np, np_cap=cap(np))
        zh = zh_t.format(z=core)
    elif kind == "vp":
        pool = VP_LIFE_POOL[tier] if item.get("domain") == "daily" else VP_POOL[tier]
        en_t, zh_t = pick_seq(pool, day, cursor)
        en = en_t.format(vp=term)
        zh = zh_t.format(vz=core)
    elif kind == "pattern":
        en_t, zh_t = pick_seq(PATTERN_POOL[tier], day, cursor)
        en = en_t.format(dl=term)
        zh = zh_t.format(dlz=core)
    else:  # a complete spoken line without a partner line: narrate it alone
        return solo_line_sentence(item, tier, day, cursor)
    return cap(en), zh


def dialogue_sentence(d1: dict, d2: dict, tier: int, day: int, cursor: dict) -> tuple[str, str]:
    t1, t2 = str(d1["term"]).strip(), str(d2["term"]).strip()
    if norm_term(t1) == norm_term(t2):
        en_t, zh_t = pick_seq(ECHO_SOLE[tier], day, cursor)
    else:
        en_t, zh_t = pick_seq(DLG_POOL[tier], day, cursor)
    spk = SPEAKERS[(day + cursor["n"]) % len(SPEAKERS)]
    cursor["n"] += 1
    en = cap(en_t.format(spk=spk, d1=t1, d2=t2, d1z=zh_core(d1), d2z=zh_core(d2)))
    zh = zh_t.format(spk=spk, d1z=zh_core(d1), d2z=zh_core(d2))
    return en, zh


def render_items(items: list[dict], tier: int, day: int, cursor: dict) -> list[tuple[str, str]]:
    """Render a scene's items; two adjacent complete spoken lines become one dialogue exchange."""
    out: list[tuple[str, str]] = []
    pending_line: dict | None = None
    for item in items:
        if term_kind(item) == "line":
            if pending_line is None:
                pending_line = item
                continue
            out.append(dialogue_sentence(pending_line, item, tier, day, cursor))
            pending_line = None
            continue
        if pending_line is not None:
            out.append(solo_line_sentence(pending_line, tier, day, cursor))
            pending_line = None
        out.append(term_sentence(item, tier, day, cursor))
    if pending_line is not None:
        out.append(solo_line_sentence(pending_line, tier, day, cursor))
    return out


def build_scene(day: int, tier: int, scene: int, groups: list[dict], plot: dict, cursor: dict) -> tuple[str, str]:
    computer, daily, github = (g.get("items", []) for g in groups)
    start = (scene - 1) * 2
    c = computer[start:start + 2]
    d = daily[start:start + 2]
    g = github[start:start + 2]

    en_parts: list[str] = []
    zh_parts: list[str] = []

    if scene == 1:
        en_parts.append(plot["open_en"])
        zh_parts.append(plot["open_zh"])
        blocks = [c, g, d]
    elif scene == 2:
        en_parts.append(plot["life_en"])
        zh_parts.append(plot["life_zh"])
        blocks = [d, c, g]
    else:
        intro_en, intro_zh = SEG3_INTRO[tier]
        en_parts.append(intro_en)
        zh_parts.append(intro_zh)
        blocks = [g, c, d]

    for items in blocks:
        for en, zh in render_items(items, tier, day, cursor):
            en_parts.append(en)
            zh_parts.append(zh)

    if scene == 3:
        en_parts.append(plot["close_en"])
        zh_parts.append(plot["close_zh"])
    else:
        close_en, close_zh = pick(SCENE_CLOSE_POOL[tier], day, scene)
        en_parts.append(close_en)
        zh_parts.append(close_zh)

    return " ".join(en_parts), "".join(zh_parts)


def hard_type(item: dict) -> str:
    part = str(item.get("part", ""))
    if "术语" in part or "技术" in part:
        return "term"
    if item.get("domain") == "daily":
        return "idiom"
    return "term"


def segment_for_scene(day: int, tier: int, scene: int, groups: list[dict], plot: dict, cursor: dict) -> dict:
    en, zh = build_scene(day, tier, scene, groups, plot, cursor)
    start = (scene - 1) * 2
    terms = []
    for group in groups:
        terms.extend(group.get("items", [])[start:start + 2])
    hard = [{"w": item["term"], "type": hard_type(item), "def": str(item.get("meaning", ""))} for item in terms]
    return {
        "id": f"seg-{scene:02d}",
        "spk": "Alex",
        "en": en,
        "tts": speech_text(en),
        "audio_file": f"audio/seg-{scene:02d}.mp3",
        "zh": zh,
        "hard": hard,
    }


def make_lesson(day_data: dict) -> dict:
    day = int(day_data["day"])
    groups = day_data.get("groups", [])
    tier = tier_of(day)
    meta_tier = TIER_META[tier]
    plot = PLOT[day - 1]
    cursor = {"n": 0}
    segments = [segment_for_scene(day, tier, scene, groups, plot, cursor) for scene in (1, 2, 3)]
    assert_coverage(day, groups, segments)

    all_items = [item for group in groups for item in group.get("items", [])]
    chunk_items = [group["items"][idx] for group in groups for idx in (0, 3)]
    chunks = [
        {"t": item["term"], "cn": zh_core(item), "eg": item.get("example", "")}
        for item in chunk_items if item.get("term")
    ]
    topics = " × ".join(str(group.get("topic", "")) for group in groups)
    word_count = sum(len(segment["en"].split()) for segment in segments)
    genre = TRANSFER_GENRES[(day - 1) % len(TRANSFER_GENRES)]

    lexicon = {}
    for item in all_items:
        term = str(item.get("term", "")).strip()
        if term and " " not in term:
            lexicon[term.lower()] = {"def": str(item.get("meaning", "")).strip()}
    for word, definition in STORY_LEXICON.items():
        lexicon.setdefault(word, {"def": definition})
    for inflected, lemma in STORY_LEMMAS.items():
        lexicon.setdefault(inflected, {"lemma": lemma})

    return {
        "meta": {
            "title": f"Day {day}: {plot['title_en']}",
            "title_zh": f"第 {day} 天：{plot['title_zh']}",
            "source": f"Vocabulary Month · Day {day}",
            "url": "",
            "kind": "article",
            "lang": "en",
            "study_card": {
                "word_count": word_count,
                "segment_count": len(segments),
                "difficulty": f"{meta_tier['name']} · 词汇主线",
                "estimated_days": 1,
                "main_practice": meta_tier["practice"],
                "value_points": [
                    "当天 18 个词汇全部进入故事正文",
                    topics,
                    f"{meta_tier['name']} · 语速与句长随天数递增",
                ],
                "suggested_pace": meta_tier["pace"],
            },
        },
        "voice": {"engine": "edge", "voice": "en-US-AndrewNeural",
                  "rate": meta_tier["rate"], "speed": meta_tier["speed"]},
        "segments": segments,
        "chunks": chunks,
        "patterns": PATTERNS_BY_TIER[tier],
        "transfer_tasks": [{
            "genre": genre,
            "task": f"Use any three Day {day} vocabulary items. Retell Alex's story in your own words, then say what you did, what was difficult, and what you will do next.",
            "hint_chunks": [chunk["t"] for chunk in chunks[:3]],
        }],
        "lexicon": lexicon,
    }


# ---------------------------------------------------------------------------
# coverage contract: all 18 items must appear in the spoken English
# ---------------------------------------------------------------------------

def norm_text(text: str) -> str:
    text = str(text or "").lower().replace("’", "'").replace("'", "").replace("...", " ")
    return re.sub(r"\s+", " ", text).strip()


def norm_term(term: str) -> str:
    return norm_text(str(term or "").rstrip(".!?"))


def assert_coverage(day: int, groups: list[dict], segments: list[dict]) -> None:
    haystack = norm_text(" ".join(segment["en"] for segment in segments))
    missing = []
    count = 0
    for group in groups:
        for item in group.get("items", []):
            count += 1
            if norm_term(item.get("term", "")) not in haystack:
                missing.append(str(item.get("term", "")))
    if count != 18:
        raise ValueError(f"day {day}: expected 18 vocabulary items, found {count}")
    if missing:
        raise ValueError(f"day {day}: vocabulary missing from story: {', '.join(missing)}")


# ---------------------------------------------------------------------------
# index page
# ---------------------------------------------------------------------------

def write_index(days: list[dict]) -> None:
    rows = []
    for raw in days:
        number = int(raw["day"])
        plot = PLOT[number - 1]
        tier_name = TIER_META[tier_of(number)]["name"]
        topics = " × ".join(str(group.get("topic", "")) for group in raw.get("groups", []))
        rows.append(
            f'<li><a href="day-{number:02d}/index.html"><h2>Day {number} · {plot["title_zh"]}</h2>'
            f'<p>{tier_name} · {topics}</p></a></li>'
        )
    html = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>英语学习 · 30 天词汇口语课</title><style>body{{font-family:-apple-system,sans-serif;max-width:760px;margin:0 auto;padding:32px 20px;line-height:1.6;background:#fafafa;color:#222}}h1{{font-size:28px;margin-bottom:4px}}.sub{{color:#666;margin-bottom:24px}}ul{{list-style:none;padding:0}}li{{background:#fff;border:1px solid #e3e3e3;border-radius:10px;margin:10px 0;overflow:hidden}}a{{display:block;padding:14px 18px;text-decoration:none;color:#222}}a:hover{{background:#f0f7ff}}h2{{margin:0 0 3px;font-size:17px}}p{{margin:0;color:#666;font-size:13px}}.vocab-entry{{display:block;margin:22px 0 30px;padding:22px;border-radius:16px;background:linear-gradient(135deg,#163e33,#2d6b55);color:white;text-decoration:none}}.vocab-entry strong{{display:block;font-size:21px}}.vocab-entry span{{display:block;margin-top:4px;color:rgba(255,255,255,.78);font-size:14px}}</style></head><body><h1>英语学习 · 30 天词汇口语课</h1><p class="sub">词汇是主线 · Alex 的 30 天入职故事 · 从零基础短句到专业场景</p><a class="vocab-entry" href="vocabulary-month/"><strong>30 天专业英语词汇强化 →</strong><span>计算机 × 日常交流 × GitHub · 每天 18 个 · 口语课的词汇主线</span></a><ul>{''.join(rows)}</ul></body></html>'''
    week_dir = ROOT / "lessons" / "week"
    week_dir.mkdir(parents=True, exist_ok=True)
    (week_dir / "index.html").write_text(html, encoding="utf-8")


def build_all(days: list[dict]) -> list[dict]:
    return [make_lesson(raw) for raw in days]


def main() -> None:
    data = json.loads(VOCAB.read_text(encoding="utf-8"))
    days = data.get("days", [])
    if len(days) != 30:
        raise SystemExit(f"vocabulary month must contain 30 days, found {len(days)}")
    for raw in days:
        lesson = make_lesson(raw)
        out = OUT / f"day-{int(raw['day']):02d}" / "segments.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(lesson, ensure_ascii=False, indent=1), encoding="utf-8")
    write_index(days)
    print(f"written 30 progressive story lessons to {OUT}")


if __name__ == "__main__":
    main()
