from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field
from brand_monitoring_flow.crews.llm_config import get_llm
import os

class WebWriterReport(BaseModel):
    page_title: str = Field(description="The title explaining how the brand was used in an individual web page")
    page_link: str = Field(description="The link to the web page")
    content_lines: list[str] = Field(description="The bullet points within the web page that are relevant to the brand")

class WebReport(BaseModel):   
    content: list[WebWriterReport] = Field(description=("A list of extracted content with title, the web page link, "
                                                              "and the bullet points within each unique web page. "
                                                              "The size of the output list will be the same as the number of web pages in the input data.")
                                                              )

# Get configurable LLM based on environment settings
llm = get_llm(provider=os.getenv("LLM_PROVIDER"), model=os.getenv("LLM_MODEL"))

@CrewBase
class WebCrew:
    """Web Analysis Crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def analysis_agent(self) -> Agent:
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
        return Agent(
            config=self.agents_config["writer_agent"],
            llm=llm,
        )

    @task
    def write_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["write_report_task"],
            output_pydantic=WebReport,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Web Analysis Crew"""

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
