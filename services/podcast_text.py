import asyncio
import logging
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage

from services.rag_service import RAGService

load_dotenv()
logger = logging.getLogger(__name__)

llm_client = ChatGroq(
    model=os.getenv("GROQ_MODEL"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.85
)

# Emotion detection patterns
EMOTION_PATTERNS = {
    "excited": {'wow', 'amazing', 'incredible', '!', 'great', 'wonderful'},
    "concerned": {'concern', 'worry', 'careful', 'watch', 'risk', 'issue'},
    "curious": {'?', 'wonder', 'think', 'curious'},
    "thoughtful": {'interesting', 'consider', 'perspective', 'note'}
}

class PodcastSegment(BaseModel):
    speaker: str = Field(description="Host1 or Host2")
    text: str
    emotion: Optional[str] = Field(default="neutral")

class PodcastScript(BaseModel):
    title: str
    intro: List[PodcastSegment]
    main_discussion: List[PodcastSegment]
    red_flags_section: List[PodcastSegment]
    action_items_section: List[PodcastSegment]
    outro: List[PodcastSegment]

class PodcastGenerator:
    """Generates conversational podcasts from document analysis"""
    
    PROMPT_TEMPLATE = """Generate {section_type} dialogue between {host1} and {host2}.

{context}

Requirements:
- Format: "Speaker: dialogue" per line
- Keep casual, conversational tone
- {length} exchanges
- Natural flow with follow-ups

Output dialogue now:"""

    SECTIONS = {
        "intro": {
            "context": "SUMMARY:\n{summary}",
            "length": "4-6",
            "focus": "Introduce topic and build interest"
        },
        "main": {
            "context": "THEMES:\n{themes}",
            "length": "10-15",
            "focus": "Discuss themes with examples and balance perspectives"
        },
        "red_flags": {
            "context": "CONCERNS:\n{concerns}",
            "length": "8-12",
            "focus": "Address issues seriously with context"
        },
        "actions": {
            "context": "RECOMMENDATIONS:\n{actions}",
            "length": "6-10",
            "focus": "Provide actionable, empowering steps"
        },
        "outro": {
            "context": "SUMMARY:\n{summary}",
            "length": "3-5",
            "focus": "Recap key points and inspire action"
        }
    }
    
    def __init__(self, host1: str = "Sarah", host2: str = "Mike"):
        self.host1 = host1
        self.host2 = host2
        self.rag_service = RAGService()
        logger.info(f"PodcastGenerator: {host1} & {host2}")

    async def _call_llm(self, prompt: str) -> str:
        try:
            response = await llm_client.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise

    def _detect_emotion(self, text: str) -> str:
        lower_text = text.lower()
        for emotion, keywords in EMOTION_PATTERNS.items():
            if any(kw in lower_text for kw in keywords):
                return emotion
        return "neutral"

    def _parse_dialogue(self, text: str) -> List[PodcastSegment]:
        segments = []
        for line in text.strip().split('\n'):
            line = line.strip()
            if not line or ':' not in line:
                continue
            speaker, dialogue = line.split(':', 1)
            segments.append(PodcastSegment(
                speaker=speaker.strip(),
                text=dialogue.strip(),
                emotion=self._detect_emotion(dialogue)
            ))
        return segments

    def _format_context(self, section: str, analysis: Dict) -> str:
        config = self.SECTIONS[section]
        
        if section == "intro":
            return config["context"].format(summary=analysis['summary'][:200])
        
        elif section == "main":
            themes_text = "\n".join([
                f"• {t['name']}: +[{', '.join(t['positives'][:2])}] "
                f"-[{', '.join(t['negatives'][:2])}]"
                for t in analysis['themes'][:4]
            ])
            return config["context"].format(themes=themes_text)
        
        elif section == "red_flags":
            flags_text = "\n".join([
                f"• [{f['severity']}] {f['clause'][:80]}"
                for f in analysis['top_red_flags'][:3]
            ])
            return config["context"].format(concerns=flags_text)
        
        elif section == "actions":
            actions_text = "\n".join([
                f"• [{a['urgency']}] {a['action'][:80]}"
                for a in analysis['user_actions'][:3]
            ])
            return config["context"].format(actions=actions_text)
        
        else:  # outro
            return config["context"].format(summary=analysis['summary'][:150])

    async def _generate_section(self, section: str, analysis: Dict) -> List[PodcastSegment]:
        config = self.SECTIONS[section]
        context = self._format_context(section, analysis)
        
        prompt = self.PROMPT_TEMPLATE.format(
            section_type=config["focus"],
            host1=self.host1,
            host2=self.host2,
            context=context,
            length=config["length"]
        )
        
        response = await self._call_llm(prompt)
        return self._parse_dialogue(response)

    async def generate_podcast(self, doc_id: str, top_k: int = 8) -> PodcastScript:
        logger.info(f"Generating podcast: {doc_id}")
        
        analysis = await self.rag_service.generate_structured_analysis(doc_id, top_k)
        
        # Parallel generation
        intro, main, flags, actions, outro = await asyncio.gather(
            self._generate_section("intro", analysis),
            self._generate_section("main", analysis),
            self._generate_section("red_flags", analysis),
            self._generate_section("actions", analysis),
            self._generate_section("outro", analysis)
        )
        
        podcast = PodcastScript(
            title=f"Deep Dive: {analysis['summary'][:45]}...",
            intro=intro,
            main_discussion=main,
            red_flags_section=flags,
            action_items_section=actions,
            outro=outro
        )
        
        logger.info(f"Podcast generated: {podcast.title}")
        return podcast

    def format_for_display(self, podcast: PodcastScript) -> str:
        sections = [
            ("📻 INTRO", podcast.intro),
            ("💬 MAIN", podcast.main_discussion),
            ("⚠️  FLAGS", podcast.red_flags_section),
            ("✅ ACTIONS", podcast.action_items_section),
            ("👋 END", podcast.outro)
        ]
        
        lines = [f"🎙️  {podcast.title}".center(60)]
        for title, segs in sections:
            lines.append(f"\n{title}")
            for seg in segs:
                emoji = {"excited": "😃", "concerned": "😟", "curious": "🤔", 
                        "thoughtful": "💭", "surprised": "😲"}.get(seg.emotion, "")
                lines.append(f"{seg.speaker} {emoji}: {seg.text}")
        
        return "\n".join(lines)

    def format_for_tts(self, podcast: PodcastScript) -> List[Dict]:
        return [
            {"speaker": s.speaker, "text": s.text, "emotion": s.emotion}
            for s in (podcast.intro + podcast.main_discussion + 
                     podcast.red_flags_section + podcast.action_items_section + 
                     podcast.outro)
        ]

# async def main():
#     generator = PodcastGenerator()
#     podcast = await generator.generate_podcast(doc_id="ec3df64b", top_k=8)
#     print(generator.format_for_display(podcast))
    
#     import json
#     with open("podcast_script.json", "w") as f:
#         json.dump(podcast.model_dump(), f, indent=2)

# if __name__ == "__main__":
#     asyncio.run(main())