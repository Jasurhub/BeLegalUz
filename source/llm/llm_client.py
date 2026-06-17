# source/llm/llm_client.py
"""
LLM client - Groq/Gemini/OpenAI qo'llab-quvvatlaydi
"""

import asyncio
from typing import AsyncGenerator, Optional, Dict, Any
from source.utils.logger import get_logger
from source.utils.config import get_settings

logger = get_logger(__name__)


class LLMClient:
    """Universal LLM client - Groq, Gemini, OpenAI"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logger
        self.provider = getattr(self.settings, 'llm_provider', 'openai').lower()
        
        # Provayderga qarab client yaratish
        if self.provider == 'groq':
            from groq import AsyncGroq
            self.client = AsyncGroq(api_key=self.settings.groq_api_key)
            self.model = getattr(self.settings, 'groq_model', 'llama-3.3-70b-versatile')
        elif self.provider == 'gemini':
            import google.generativeai as genai
            genai.configure(api_key=self.settings.gemini_api_key)
            self.client = genai.GenerativeModel(
                getattr(self.settings, 'gemini_model', 'gemini-2.0-flash')
            )
            self.model = self.client.model_name
        else:  # openai
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=self.settings.openai_api_key,
                max_retries=3,
                timeout=60.0
            )
            self.model = self.settings.openai_model
        
        self.temperature = self.settings.llm_temperature
        self.max_tokens = self.settings.llm_max_tokens
        
        self.logger.info(f"✅ LLM Client initialized: {self.provider} / {self.model}")
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Generate response from LLM"""
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        
        try:
            if self.provider == 'groq':
                async for chunk in self._generate_groq(prompt, system_prompt, temperature, max_tokens, stream):
                    yield chunk
            elif self.provider == 'gemini':
                async for chunk in self._generate_gemini(prompt, system_prompt, temperature, max_tokens, stream):
                    yield chunk
            else:
                async for chunk in self._generate_openai(prompt, system_prompt, temperature, max_tokens, stream):
                    yield chunk
        except Exception as e:
            self.logger.error(f"LLM generation error: {e}")
            raise
    
    async def _generate_groq(
        self, prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, stream: bool
    ) -> AsyncGenerator[str, None]:
        """Groq orqali javob yaratish"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        if stream:
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            yield response.choices[0].message.content
    
    async def _generate_gemini(
        self, prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, stream: bool
    ) -> AsyncGenerator[str, None]:
        """Gemini orqali javob yaratish"""
        full_prompt = ""
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        loop = asyncio.get_event_loop()
        
        if stream:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.generate_content(
                    full_prompt,
                    generation_config={
                        'temperature': temperature,
                        'max_output_tokens': max_tokens,
                    },
                    stream=True
                )
            )
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        else:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.generate_content(
                    full_prompt,
                    generation_config={
                        'temperature': temperature,
                        'max_output_tokens': max_tokens,
                    }
                )
            )
            yield response.text
    
    async def _generate_openai(
        self, prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, stream: bool
    ) -> AsyncGenerator[str, None]:
        """OpenAI orqali javob yaratish"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
        
        if stream:
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            yield response.choices[0].message.content
    
    async def generate_complete_response(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> str:
        """To'liq javob olish (streaming siz)"""
        full_response = ""
        async for chunk in self.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            stream=False,
            **kwargs
        ):
            full_response += chunk
        return full_response