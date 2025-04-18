from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field
from brand_monitoring_flow.crews.llm_config import get_llm
import os

class YoutubeWriterReport(BaseModel):
    video_title: str = Field(description="The title explaining how the brand was used in an individual video")
    video_link: str = Field(description="The link to the Youtube video")
    content_lines: list[str] = Field(description="The bullet points within the Youtube video that are relevant to the brand")

class YoutubeReport(BaseModel):   
    content: list[YoutubeWriterReport] = Field(description=("A list of extracted content with title, the video link, "
                                                              "and the bullet points within each unique video. "
                                                              "The size of the output list will be the same as the number of videos in the input data.")
                                                              )

# Instead of creating the LLM at module level, we'll create it inside the agent methods
# llm = get_llm(provider=os.getenv("LLM_PROVIDER"), model=os.getenv("LLM_MODEL"))

@CrewBase
class YoutubeCrew:
    """YouTube Analysis Crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def analysis_agent(self) -> Agent:
        # Get LLM at runtime
        llm = get_llm(provider=os.getenv("LLM_PROVIDER"), model=os.getenv("LLM_MODEL"))
        return Agent(
            config=self.agents_config["analysis_agent"],
            llm=llm,
        )
        
    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["analysis_task"],
        )
    
    @agent
    def writer_agent(self) -> Agent:
        # Get LLM at runtime
        llm = get_llm(provider=os.getenv("LLM_PROVIDER"), model=os.getenv("LLM_MODEL"))
        return Agent(
            config=self.agents_config["writer_agent"],
            llm=llm,
        )

    @task
    def write_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["write_report_task"],
            output_pydantic=YoutubeReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the YouTube Analysis Crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
