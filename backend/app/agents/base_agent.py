"""Base agent class for all procurement agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from app.config import settings
from app.core.gemini_client import gemini_client
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all procurement agents."""
    
    def __init__(self, name: str, description: str):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            description: Agent description
        """
        self.name = name
        self.description = description
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            temperature=settings.GEMINI_TEMPERATURE,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        self.tools = self._create_tools()
        self.agent_executor = None
        
        if self.tools:
            self._setup_agent_executor()
    
    @abstractmethod
    def _create_tools(self) -> list[BaseTool]:
        """
        Create tools for this agent.
        
        Returns:
            List of tools
        """
        pass
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """
        Get system prompt for this agent.
        
        Returns:
            System prompt string
        """
        pass
    
    def _setup_agent_executor(self) -> None:
        """Setup the agent executor with tools and prompt."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
        )
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        try:
            logger.info(f"{self.name} executing...")
            result = await self._execute_logic(state)
            logger.info(f"{self.name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{self.name} error: {str(e)}")
            state["errors"].append(f"{self.name}: {str(e)}")
            return state
    
    @abstractmethod
    async def _execute_logic(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement agent-specific logic.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        pass
    
    async def invoke_with_tools(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Invoke agent with tools.
        
        Args:
            input_text: Input for the agent
            context: Additional context
            
        Returns:
            Agent response
        """
        if not self.agent_executor:
            raise ValueError(f"{self.name} has no agent executor configured")
        
        result = await self.agent_executor.ainvoke({
            "input": input_text,
            "chat_history": context.get("chat_history", []) if context else [],
        })
        
        return result["output"]
    
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Generate text using Gemini directly (without tools).
        
        Args:
            prompt: Prompt text
            system_instruction: Optional system instruction
            
        Returns:
            Generated text
        """
        return await gemini_client.generate_text(
            prompt=prompt,
            system_instruction=system_instruction or self._get_system_prompt(),
        )
