from metagpt.logs import logger
import fire
import os
from metagpt.team import Team
from finacial_writer.roles.leader import Leader
from finacial_writer.roles.researcher import Researcher
from finacial_writer.roles.drawer import Drawer
from finacial_writer.roles.writer import Writer
from finacial_writer.roles.examiner import Examiner
from finacial_writer.roles.human import HumanExaminer
from finacial_writer.roles.reviewer import Reviewer
from finacial_writer.roles.expert import Expert

async def main(
    idea: str = "水产养殖",
    investment: float = 5.0,
    n_round: int = 10,
    decomposition_nums: int = 1,
    url_per_query: int = 1,
):
    logger.info(idea)
    
    # 自动下载并设置ChromeDriver
    # try:
    #     chromedriver_path = setup_chromedriver()
    #     logger.info(f"ChromeDriver已准备就绪: {chromedriver_path}")
    #     # 设置环境变量，供SeleniumWrapper使用
    #     os.environ['CHROMEDRIVER_PATH'] = chromedriver_path
    # except Exception as e:
    #     logger.error(f"ChromeDriver设置失败: {e}")
    #     logger.warning("将尝试使用系统PATH中的ChromeDriver")
    
    team = Team()
    team.hire(
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
    team.invest(investment=investment)
    team.run_project(idea)
    await team.run(n_round=n_round)


if __name__ == "__main__":
    fire.Fire(main)
