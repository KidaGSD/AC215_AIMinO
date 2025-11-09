import os
import logging
import json
import asyncio
from typing import AsyncGenerator, Literal, Annotated, List, Dict, Any

from pydantic import BaseModel, Field, confloat, TypeAdapter, ValidationError

from google.adk.agents import LlmAgent, BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from typing_extensions import override
from google.genai import types


APP_NAME = "napari_adk_app"
USER_ID = "napari_user"
SESSION_ID = "napari_session"
os.environ["GOOGLE_API_KEY"] = ""
GEMINI_MODEL = "gemini-2.0-flash"

#Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic v2
Float = confloat(strict=False)

class CmdLayerVisibility(BaseModel):
    action: Literal["layer_visibility"]
    name: str
    op: Literal["show", "hide", "toggle"]

class CmdPanelToggle(BaseModel):
    action: Literal["panel_toggle"]
    name: str
    op: Literal["open", "close"]

class CmdZoomBox(BaseModel):
    action: Literal["zoom_box"]
    box: Annotated[list[Float], Field(min_length=4, max_length=4)]  # [x1,y1,x2,y2]

class CmdCenterOn(BaseModel):
    action: Literal["center_on"]
    point: Annotated[list[Float], Field(min_length=2, max_length=2)]  # [x,y]

class CmdSetZoom(BaseModel):
    action: Literal["set_zoom"]
    zoom: Float

#Commands for each worker(two here)
WORKER1_COMMANDS = (CmdLayerVisibility | CmdPanelToggle)
WORKER2_COMMANDS = (CmdZoomBox | CmdCenterOn | CmdSetZoom)

Worker1Adapter = TypeAdapter(WORKER1_COMMANDS)
Worker2Adapter = TypeAdapter(WORKER2_COMMANDS)

class TaskParserInput(BaseModel):
    user_input: str

class WorkerInput(BaseModel):
    sub_task: str



def create_layer_panel_worker() -> LlmAgent:
    """
    Worker 1：for layer panel
    """
    
    instruction = """
    You are an expert napari command generator. Your ONLY job is to convert
    a short task description into a single, specific JSON command.

    You ONLY know about these two (2) command schemas:

    1. Layer Visibility:
    {"action":"layer_visibility","op":"show|hide|toggle","name":"<layer name>"}

    2. Panel Toggle:
    {"action":"panel_toggle","op":"open|close","name":"<panel name>"}

    The user will give you a simple task, like "show nuclei" or "open the layers panel".
    You must respond ONLY with the valid JSON object that matches one of
    the schemas above. Do not add any other text or explanation.

    Task: {{sub_task}}
    """
    return LlmAgent(
        name="LayerPanelWorker",
        model=GEMINI_MODEL,
        instruction=instruction,
        input_schema=WorkerInput,
        output_key="command_json",
        generate_content_config=types.GenerateContentConfig(
        temperature=0.1,
        response_mime_type = 'application/json'

     )

    )


def create_view_zoom_worker() -> LlmAgent:
    """
    Worker 2 for zooming
    """
    instruction = """
    You are an expert napari command generator. Your ONLY job is to convert
    a short task description into a single, specific JSON command.

    You ONLY know about these three (3) command schemas:

    1. Zoom to Box:
    {"action":"zoom_box","box":[x1,y1,x2,y2]}

    2. Center On Point:
    {"action":"center_on","point":[x,y]}

    3. Set Zoom Level:
    {"action":"set_zoom","zoom":1.6}

    The user will give you a simple task, like "center on 100, 200" or "zoom to 1.5".
    You must respond ONLY with the valid JSON object that matches one of
    the schemas above. Do not add any other text or explanation.

    Task: {{sub_task}}
    """
    return LlmAgent(
        name="ViewZoomWorker",
        model=GEMINI_MODEL,
        instruction=instruction,
        input_schema=WorkerInput,
        output_key="command_json",
        generate_content_config=types.GenerateContentConfig(
        temperature=0.1,
        response_mime_type = 'application/json'

     )
    )



class NapariLeadManager(BaseAgent):
    """
    will parse user instruction and distribute tasks to workers
    """

    task_parser: LlmAgent
    layer_panel_worker: LlmAgent
    view_zoom_worker: LlmAgent
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        task_parser: LlmAgent,
        layer_panel_worker: LlmAgent,
        view_zoom_worker: LlmAgent,
    ):
        super().__init__(
            name="NapariLeadManager",
            sub_agents=[task_parser, layer_panel_worker, view_zoom_worker],
            task_parser=task_parser,
            layer_panel_worker=layer_panel_worker,
            view_zoom_worker=view_zoom_worker,
        )
    def _extract_json_from_llm_output(self, text: str) -> dict:
        """
        extract json from llm output
        """
        try:
   
            start_index = text.find('{')
     
            end_index = text.rfind('}')

            if start_index == -1 or end_index == -1:
                logger.error(f"[{self.name}] didn't find {{}} : {text[:100]}")
                return {}

         
            json_str = text[start_index : end_index + 1]

      
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"[{self.name}] failed to parse json: {e}\nString was: {json_str}")
            return {}
        except Exception as e:
            logger.error(f"[{self.name}] _extract_json_from_llm_output error: {e}")
            return {}

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:

        user_input = ctx.session.state.get("user_input", "")
        logger.info(f"[{self.name}] user instruction: '{user_input}'")

    
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=f"parsing: {user_input}")])
        )

#Task parser
        logger.info(f"[{self.name}] TaskParser working ...")

        task_plan: Dict[str, Any] = {}
        try:
  
            async for event in self.task_parser.run_async(ctx):
                pass
                yield event

            task_plan = self._extract_json_from_llm_output(ctx.session.state.get("task_plan", {}))

            print(ctx.session.state)

            if not task_plan or "tasks" not in task_plan:
                raise ValueError("TaskParser didn't produce valid task")

            logger.info(f"[{self.name}] get task: {json.dumps(task_plan, indent=2)}")

       
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text=f"number of tasks：{len(task_plan['tasks'])}")])
            )

        except Exception as e:
            logger.error(f"[{self.name}] TaskParser failed: {e}")

            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text=f"couldn't parse the task: {e}")])
            )
            return

# workers
        generated_commands: List[Dict[str, Any]] = []
        original_sub_task = ctx.session.state.get("sub_task")

        for task in task_plan.get("tasks", []):
            task_desc = task.get("task_description")
            worker_type = task.get("worker_type")

            if not task_desc or not worker_type:
                logger.warning(f"[{self.name}] not a valid task: {task}")
                continue

            logger.info(f"[{self.name}] distributing task '{task_desc}' -> '{worker_type}'")

     
            yield Event(
                author=self.name,
                content=types.Content(parts=[types.Part(text=f"parsing task: {task_desc}...")])
            )


            worker_to_run: LlmAgent
            adapter_to_use: TypeAdapter

            if worker_type == "layer_panel":
                worker_to_run = self.layer_panel_worker
                adapter_to_use = Worker1Adapter
            elif worker_type == "view_zoom":
                worker_to_run = self.view_zoom_worker
                adapter_to_use = Worker2Adapter
            else:
                logger.error(f"[{self.name}] unknown worker_type: {worker_type}")
                continue

    
            try:
             
                ctx.session.state["sub_task"] = task_desc

                async for event in worker_to_run.run_async(ctx):
                    yield event

                command_json = self._extract_json_from_llm_output(ctx.session.state.get("command_json"))
                if not command_json:
                    raise ValueError("Worker didn't produce 'command_json'。")

                validated_command = adapter_to_use.validate_python(command_json)
                generated_commands.append(validated_command.model_dump())
                logger.info(f"[{self.name}] command produced: {validated_command.model_dump_json()}")

            except (ValidationError, Exception) as e:
                logger.error(f"[{worker_to_run.name}] error: {e}")

    
                yield Event(
                    author=worker_to_run.name,
                    content=types.Content(parts=[types.Part(text=f"error of '{task_desc}': {e}")])
                )



        logger.info(f"[{self.name}] workflow done")


        ctx.session.state["final_commands"] = generated_commands
        # print(ctx.session.state)
        yield Event(
            author=self.name,
            content=types.Content(parts=[types.Part(text=f"number of commands: {len(generated_commands)}。")]),
            partial=False,
            turn_complete=True,
            actions={"state_delta": {"final_commands": generated_commands}}
        )


def create_manager_agent() -> NapariLeadManager:


    task_parser_instruction = f"""
    You are a task orchestrator for a napari viewer.
    Your job is to parse a single user command into a list of one or more sub-tasks.
    You must classify each sub-task into one of two categories:
    1. "layer_panel": For tasks related to showing, hiding, or toggling layers and UI panels.
    2. "view_zoom": For tasks related to camera movement, like zooming or centering.

    You must output ONLY a JSON object with a single key "tasks",
    which contains a list of task objects.

    Example 1:
    User Input: "show the nuclei layer"
    Your JSON Output:
    {{
      "tasks": [
        {{ "task_description": "show the nuclei layer", "worker_type": "layer_panel" }}
      ]
    }}

    Example 2:
    User Input: "hide cells and center on 100, 200"
    Your JSON Output:
    {{
      "tasks": [
        {{ "task_description": "hide cells layer", "worker_type": "layer_panel" }},
        {{ "task_description": "center on 100, 200", "worker_type": "view_zoom" }}
      ]
    }}

    Example 3:
    User Input: "set zoom to 5.5 and open the layers panel"
    Your JSON Output:
    {{
      "tasks": [
        {{ "task_description": "set zoom to 5.5", "worker_type": "view_zoom" }},
        {{ "task_description": "open the layers panel", "worker_type": "layer_panel" }}
      ]
    }}

    Now, parse the following user input:
    User Input: {{user_input}}
    """

    task_parser = LlmAgent(
        name="TaskParser",
        model=GEMINI_MODEL,
        instruction=task_parser_instruction,
        input_schema=TaskParserInput,
        output_key="task_plan",
    )


    layer_worker = create_layer_panel_worker()
    view_worker = create_view_zoom_worker()

    manager = NapariLeadManager(
        task_parser=task_parser,
        layer_panel_worker=layer_worker,
        view_zoom_worker=view_worker,
    )
    return manager

#set up session of context

async def setup_session_and_runner(agent: BaseAgent):
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    return session_service, runner

async def call_agent_async(user_input_text: str):


    manager_agent = create_manager_agent()


    session_service, runner = await setup_session_and_runner(manager_agent)

 
    initial_state = {"user_input": user_input_text}

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state=initial_state
    )
    logger.info(f"---user instruction:'{user_input_text}' ---")

    events = runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=types.Content(role='user', parts=[types.Part(text=f"{user_input_text}")])
    )
    final_response = "No response"
    # print(session.state,'test_1')
    async for event in events:

        if (event.content is not None) and event.author != "user":
            logger.info(f"  [EVENT] {event.author}: {event.content.parts[0].text}")


        if event.is_final_response:
            final_response = event.content.parts[0].text


    # print(final_response)
    final_session = await session_service.get_session(
    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    # print(final_session.state,'test_2')
    final_commands = final_session.state.get("final_commands", [])
    # print(final_commands)
    # print(json.dumps(final_commands, indent=2))
    return final_commands

#To test the agent workflow, use  y = await call_agent_async("hello,I want to parse my file, please hide the 'cells' layer, center on 250.5, 300 and then set zoom to 3.0"), y will be the final command parsed from user's input to json.