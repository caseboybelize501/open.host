"""
Local LLM Inference Engine

Provides unified interface for running inference on local GGUF models.
Supports:
- Chat completion format
- Task-specific prompts
- Streaming responses
- Model switching
"""

import json
import time
from typing import Dict, List, Optional, Any, Generator
from dataclasses import dataclass
from src.llm.model_pool import GGUFModelPool, get_model_pool, GGUFModel


@dataclass
class LLMResponse:
    """Response from LLM inference."""
    text: str
    model_used: str
    tokens_generated: int
    inference_time_ms: float
    prompt_tokens: int
    success: bool
    error: Optional[str] = None


class LocalLLM:
    """
    Local LLM inference engine.
    
    Uses llama-cpp-python backend for GGUF model inference.
    Provides chat-style interface for local models.
    """
    
    def __init__(self, model_pool: Optional[GGUFModelPool] = None):
        self.model_pool = model_pool or get_model_pool()
        self.default_model: Optional[str] = None
        self._set_default_model()
    
    def _set_default_model(self):
        """Set default model for inference."""
        # Try to find a master model first
        master = self.model_pool.get_model("master")
        if master:
            self.default_model = master.path
            return
        
        # Fall back to any available model
        for model in self.model_pool.models.values():
            self.default_model = model.path
            return
        
        print("Warning: No models available. Run model_pool.scan_models() first.")
    
    def chat(self, messages: List[Dict[str, str]], 
             model_path: Optional[str] = None,
             temperature: float = 0.7,
             max_tokens: int = 512,
             system_prompt: Optional[str] = None) -> LLMResponse:
        """
        Chat completion with local model.
        
        Args:
            messages: List of {role, content} dicts
            model_path: Optional specific model path
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            system_prompt: Optional system prompt
        
        Returns:
            LLMResponse with generated text
        """
        start_time = time.time()
        
        # Determine model to use
        model = model_path or self.default_model
        if not model:
            return LLMResponse(
                text="",
                model_used="",
                tokens_generated=0,
                inference_time_ms=0,
                prompt_tokens=0,
                success=False,
                error="No model available"
            )
        
        # Format prompt for chat
        prompt = self._format_chat_prompt(messages, system_prompt)
        
        # Generate
        try:
            generated = self.model_pool.generate(
                model_path=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            inference_time = (time.time() - start_time) * 1000
            
            return LLMResponse(
                text=generated,
                model_used=model,
                tokens_generated=len(generated.split()),  # Rough estimate
                inference_time_ms=inference_time,
                prompt_tokens=len(prompt.split()),
                success=True
            )
            
        except Exception as e:
            return LLMResponse(
                text="",
                model_used=model,
                tokens_generated=0,
                inference_time_ms=(time.time() - start_time) * 1000,
                prompt_tokens=0,
                success=False,
                error=str(e)
            )
    
    def _format_chat_prompt(self, messages: List[Dict[str, str]], 
                           system_prompt: Optional[str]) -> str:
        """Format messages into prompt string."""
        prompt_parts = []
        
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}\n")
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"{role.capitalize()}: {content}")
        
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    def complete(self, prompt: str, model_path: Optional[str] = None,
                temperature: float = 0.7, max_tokens: int = 256) -> LLMResponse:
        """
        Simple completion (non-chat).
        
        Args:
            prompt: Input prompt
            model_path: Optional specific model path
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
        
        Returns:
            LLMResponse
        """
        start_time = time.time()
        
        model = model_path or self.default_model
        if not model:
            return LLMResponse(
                text="",
                model_used="",
                tokens_generated=0,
                inference_time_ms=0,
                prompt_tokens=0,
                success=False,
                error="No model available"
            )
        
        try:
            generated = self.model_pool.generate(
                model_path=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return LLMResponse(
                text=generated,
                model_used=model,
                tokens_generated=len(generated.split()),
                inference_time_ms=(time.time() - start_time) * 1000,
                prompt_tokens=len(prompt.split()),
                success=True
            )
        except Exception as e:
            return LLMResponse(
                text="",
                model_used=model,
                tokens_generated=0,
                inference_time_ms=0,
                prompt_tokens=0,
                success=False,
                error=str(e)
            )
    
    def stream_chat(self, messages: List[Dict[str, str]],
                   model_path: Optional[str] = None,
                   temperature: float = 0.7,
                   max_tokens: int = 512) -> Generator[str, None, None]:
        """
        Streaming chat completion.
        
        Yields tokens as they are generated.
        """
        # Note: Streaming requires llama-cpp-python with streaming support
        # This is a simplified version
        response = self.chat(messages, model_path, temperature, max_tokens)
        yield response.text
    
    def extract_json(self, prompt: str, schema: Dict, 
                    model_path: Optional[str] = None) -> Optional[Dict]:
        """
        Extract structured JSON from model.
        
        Args:
            prompt: Input prompt
            schema: Expected JSON schema
            model_path: Optional model path
        
        Returns:
            Parsed JSON dict or None
        """
        system_prompt = f"""You are a JSON extraction assistant. 
Extract information from the input and format it as valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Respond with ONLY valid JSON. No explanations."""

        response = self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            model_path=model_path,
            temperature=0.1,  # Low temp for deterministic output
            max_tokens=1024
        )
        
        if not response.success:
            return None
        
        # Try to parse JSON from response
        try:
            # Find JSON in response (may have markdown formatting)
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
            return None
    
    def classify(self, prompt: str, categories: List[str],
                model_path: Optional[str] = None) -> Optional[str]:
        """
        Classify input into one of categories.
        
        Args:
            prompt: Input to classify
            categories: List of possible categories
            model_path: Optional model path
        
        Returns:
            Selected category or None
        """
        categories_str = ", ".join(categories)
        system_prompt = f"""You are a classification assistant.
Classify the input into exactly ONE of these categories: {categories_str}
Respond with ONLY the category name."""

        response = self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            model_path=model_path,
            temperature=0.1,
            max_tokens=50
        )
        
        if not response.success:
            return None
        
        # Find matching category
        predicted = response.text.strip().lower()
        for cat in categories:
            if cat.lower() in predicted:
                return cat
        
        return categories[0]  # Default to first
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models."""
        return self.model_pool.get_available_models_summary()


# Global singleton
_llm_instance: Optional[LocalLLM] = None


def get_llm() -> LocalLLM:
    """Get global LLM instance."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LocalLLM()
    return _llm_instance


def chat(messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
    """Convenience function for chat."""
    return get_llm().chat(messages, **kwargs)


def complete(prompt: str, **kwargs) -> LLMResponse:
    """Convenience function for completion."""
    return get_llm().complete(prompt, **kwargs)


def extract_json(prompt: str, schema: Dict, **kwargs) -> Optional[Dict]:
    """Convenience function for JSON extraction."""
    return get_llm().extract_json(prompt, schema, **kwargs)


def classify(prompt: str, categories: List[str], **kwargs) -> Optional[str]:
    """Convenience function for classification."""
    return get_llm().classify(prompt, categories, **kwargs)
