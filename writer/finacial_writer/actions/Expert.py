from typing import Optional

from pydantic import Field, model_validator

from finacial_writer.actions.SearchAndSummarize import SearchAndSummarize
from metagpt.roles import Role
from metagpt.tools.search_engine import SearchEngine
from metagpt.roles.role import Role
from finacial_writer.actions.FindFileAndDraw import FindFileAndDraw
from llama_index.embeddings.zhipuai import ZhipuAIEmbedding

embedding = ZhipuAIEmbedding(model="embedding-2", api_key="3114a609d68448efb5d459ee5b7e10da.3fbNyLNPdeOtoJbF")


    
class Expert(Role):
    name: str = "John Smith"
    profile: str = "Indusrty Expert"
    desc: str = (
        "As a Indusrty Expert, my name is John Smith. I specialize in addressing customer inquiries with "
        "expertise and precision. My responses are based solely on the information available in our knowledge"
        " base. In instances where your query extends beyond this scope, I'll honestly indicate my inability "
        "to provide an answer, rather than speculate or assume. "
    )

    store: Optional[object] = Field(default=None, exclude=True)  # must inplement tools.SearchInterface

    @model_validator(mode="after")
    def validate_stroe(self):
        if self.store:
            search_engine = SearchEngine.from_search_func(search_func=self.store.asearch, proxy=self.config.proxy)
            action = SearchAndSummarize(search_engine=search_engine, context=self.context)
        else:
            action = SearchAndSummarize
        self.set_actions([action])
        return self

    
