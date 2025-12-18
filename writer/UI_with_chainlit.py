import chainlit as cl
from init_setup import ChainlitEnv
from finacial_writer.roles.leader import Leader
from finacial_writer.roles.researcher import Researcher
from finacial_writer.roles.drawer import Drawer
from finacial_writer.roles.writer import Writer
from finacial_writer.roles.examiner import Examiner
from finacial_writer.roles.reviewer import Reviewer
from finacial_writer.roles.human import HumanExaminer
from finacial_writer.roles.expert import Expert
from metagpt.team import Team
from metagpt.logs import logger
import os


@cl.set_chat_profiles
async def chat_profile() -> list[cl.ChatProfile]:
    """Generates a chat profile containing starter messages which can be triggered to run MetaGPT

    Returns:
        list[chainlit.ChatProfile]: List of Chat Profile
    """
    return [
        cl.ChatProfile(
            name="MetaGPT",
            icon="/public/MetaGPT-new-log.jpg",
            markdown_description="输入某个行业,生成相关研究报告",
            starters=[
                cl.Starter(
                    label="人工智能",
                    message="人工智能",
                    icon="/public/2048.jpg",
                ),
                cl.Starter(
                    label="互联网",
                    message="互联网",
                    icon="/public/blackjack.jpg",
                ),
            ],
        )
    ]


# https://docs.chainlit.io/concepts/message
@cl.on_message
async def startup(message: cl.Message) -> None:
    """On Message in UI, Create a MetaGPT software company

    Args:
        message (chainlit.Message): message by chainlist
    """
    idea = message.content
    company = Team(env=ChainlitEnv())

    
    res = await cl.AskUserMessage(content="请输入针对行业的生成查询的数量 (decomposition_nums), 默认为 2:", timeout=60).send()
    decomposition_nums = int(res['output']) if res and res['output'].isdigit() else 2
    
    # Ask for url_per_query
    res = await cl.AskUserMessage(content="请输入每个查询的URL数量 (url_per_query), 默认为 2:", timeout=60).send()
    url_per_query = int(res['output']) if res and res['output'].isdigit() else 2
        
    # Similar to software_company.py
    company.hire(
        [
            Leader(),
            Researcher(decomposition_nums=decomposition_nums, url_per_query=url_per_query),
            Drawer(),
            Expert(),
            Writer(),
            Examiner(),
            Reviewer(is_human=True),
            HumanExaminer(),
        ]
    )

    company.invest(investment=3.0)
    company.run_project(idea=idea)

    await company.run(n_round=10)

    await cl.Message(
        content=f"""
        Total cost: `{company.cost_manager.total_cost}`
        """
        ).send()
