import asyncio

import chainlit as cl

from metagpt.environment import Environment
from metagpt.logs import logger, set_llm_stream_logfunc
from metagpt.roles import Role
from metagpt.utils.common import any_to_name
from metagpt.schema import Message

def log_llm_stream_chainlit(msg):
    # Stream the message token into Chainlit UI.
    cl.run_sync(chainlit_message.stream_token(msg))


set_llm_stream_logfunc(func=log_llm_stream_chainlit)


class ChainlitEnv(Environment):
    """Chainlit Environment for UI Integration"""
            
    async def run(self, k=1):
        """按顺序执行角色任务，而非并行"""
        for _ in range(k):
            for role in self.roles.values():
                await self._chainlit_role_run(role=role)  # 逐个执行角色
            logger.debug(f"is idle: {self.is_idle}")
            
    async def _chainlit_role_run(self, role: Role) -> None:
        """To run the role with chainlit config

        Args:
            role (Role): metagpt.role.Role
        """
        global chainlit_message
        chainlit_message = cl.Message(content="")
        
        print(f"/n Running role: {role._setting} /n")

        # Capture existing images
        project_path = getattr(role.context.config, 'project_path', None)
        existing_images = set()
        image_dir = None
        if project_path:
            image_dir = project_path / "image"
            if image_dir.exists():
                existing_images = set(image_dir.glob("*"))

        # 针对高负载角色禁用流式日志，防止前端卡顿
        # Researcher 和 Expert 通常会进行大量的 LLM 调用和并发操作
        heavy_roles = ["Drawer", "Expert"]
        should_disable_stream = role.profile in heavy_roles
        
        if should_disable_stream:
            set_llm_stream_logfunc(None)
            await chainlit_message.send() # 先发送一个空消息占位，或者不发，等待最终结果
            # 如果不发送，用户可能不知道正在运行。我们可以发一个 "正在思考..." 的消息
            chainlit_message.content = f"**{role.profile}** 正在处理大量数据，请稍候..."
            await chainlit_message.update()
        else:
            set_llm_stream_logfunc(func=log_llm_stream_chainlit)

        try:
            if role._setting == "Reviewer(HumanReviewer)":
                res = await cl.AskUserMessage(content="请提出修改意见", timeout=100).send()
                if res:
                    msg = Message(
                        content=res['output'],
                        role=role._setting,
                        cause_by="finacial_writer.actions.HumanReview.HumanReview",
                        sent_from=role,
                    )
                    role.publish_message(msg)
                return
            
            message = await role.run()
        finally:
            # 恢复流式日志
            set_llm_stream_logfunc(func=log_llm_stream_chainlit)

        if message is not None and message.content != "No actions taken yet":
            # Convert a message from action node in json format
            
            final_content = await self._convert_message_to_markdownjson(message=message.content)
            # message content from which role and its action...
            footer = f"---\n\nAction: `{any_to_name(message.cause_by)}` done by `{role._setting}`."
            
            chainlit_message.content = final_content + footer

            # Check for new images and attach them
            if image_dir and image_dir.exists():
                current_images = set(image_dir.glob("*"))
                new_images = current_images - existing_images
                elements = []
                for img_path in new_images:
                    if img_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
                        # Create an Image element
                        elements.append(
                            cl.Image(name=img_path.name, display="inline", path=str(img_path))
                        )
                if elements:
                    chainlit_message.elements = elements

            await chainlit_message.update()
        


# for clean view in UI
    async def _convert_message_to_markdownjson(self, message: str) -> str:
        """If the message is from MetaGPT Action Node output, then
        convert it into markdown json for clear view in UI.

        Args:
            message (str): message by role._act

        Returns:
            str: message in mardown from
        """
        if message.startswith("[CONTENT]"):
            return f"```json\n{message}\n```\n"
        
        return message
