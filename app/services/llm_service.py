"""LLM service for generating trip plans"""

import json
import logging
from datetime import datetime, timedelta

from openai import OpenAI

from app.core.config import llm_config
from app.db.models import POI

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-based trip generation"""

    def __init__(self):
        self.client: OpenAI | None = None
        if llm_config.is_configured:
            self.client = OpenAI(
                api_key=llm_config.openai_api_key,
                base_url=llm_config.openai_base_url,
            )

    def _build_prompt(
        self,
        city: str,
        start_date: str,
        end_date: str,
        travel_days: int,
        pois: list[POI],
        transportation: str | None = None,
        accommodation: str | None = None,
        preferences: str | None = None,
        free_text_input: str | None = None,
    ) -> str:
        """Build prompt for LLM"""

        # Format POI list
        poi_list_text = "\n".join([
            f"- {poi.name} ({poi.type}): {poi.description or '暂无描述'}"
            for poi in pois[:30]  # Limit to 30 POIs to avoid token limit
        ])

        prompt = f"""你是一个专业的旅游规划师。请根据以下信息生成详细的旅游行程：

## 基本信息
- 城市：{city}
- 日期：{start_date} 到 {end_date}
- 天数：{travel_days} 天
- 交通偏好：{transportation or '无特殊偏好'}
- 住宿偏好：{accommodation or '舒适型酒店'}
- 兴趣偏好：{preferences or '无特殊偏好'}

## 用户额外需求
{free_text_input or '无'}

## 可用景点（请从中选择）
{poi_list_text}

## 要求
1. 每天安排 2-4 个景点，合理分配时间
2. 景点顺序要考虑地理位置，尽量减少往返
3. 每个景点包含：名称、预计游览时间（小时）、简要描述
4. 每天包含：早餐、午餐、晚餐建议（简单描述即可）
5. 包含交通方式建议（步行、地铁、公交、打车等）
6. 提供总体建议和预算估算

## 输出格式
请严格按照以下 JSON 格式返回，不要包含其他内容：

{{
  "city": "{city}",
  "start_date": "{start_date}",
  "end_date": "{end_date}",
  "overall_suggestions": "总体建议文本（200字左右）",
  "budget": {{
    "total_attractions": 门票总费用数字,
    "total_hotels": 住宿预估费用数字,
    "total_meals": 餐饮预估费用数字,
    "total_transportation": 交通预估费用数字,
    "total": 总费用数字
  }},
  "days": [
    {{
      "date": "日期",
      "day_index": 0,
      "description": "当天行程概述",
      "transportation": "主要交通方式",
      "accommodation": "住宿建议",
      "attractions": [
        {{
          "name": "景点名称",
          "address": "地址（可选）",
          "location": {{"longitude": 经度, "latitude": 纬度}},
          "visit_duration": 游览小时数,
          "description": "景点描述",
          "category": "景点类型"
        }}
      ],
      "meals": [
        {{
          "type": "breakfast/lunch/dinner",
          "name": "餐厅或食物建议",
          "description": "简要描述"
        }}
      ]
    }}
  ]
}}

注意事项：
1. 必须返回合法的 JSON 格式
2. 所有景点必须从提供的可用景点列表中选择
3. 预算单位为人民币（元）
4. 如果某天的景点较少，可以增加休息时间或自由活动
"""
        return prompt

    def generate_trip_plan(
        self,
        city: str,
        start_date: str,
        end_date: str,
        travel_days: int,
        pois: list[POI],
        transportation: str | None = None,
        accommodation: str | None = None,
        preferences: str | None = None,
        free_text_input: str | None = None,
    ) -> dict | None:
        """Generate trip plan using LLM"""

        if not self.client:
            logger.warning("LLM not configured, skipping generation")
            return None

        try:
            prompt = self._build_prompt(
                city=city,
                start_date=start_date,
                end_date=end_date,
                travel_days=travel_days,
                pois=pois,
                transportation=transportation,
                accommodation=accommodation,
                preferences=preferences,
                free_text_input=free_text_input,
            )

            response = self.client.chat.completions.create(
                model=llm_config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的旅游规划助手，擅长根据用户需求生成详细的旅游行程。请始终返回合法的 JSON 格式。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
            )

            content = response.choices[0].message.content
            if not content:
                logger.error("LLM returned empty content")
                return None

            # Extract JSON from response (handle markdown code blocks)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            # Parse JSON
            trip_data = json.loads(content)

            # Validate required fields
            required_fields = ["city", "days", "budget", "overall_suggestions"]
            for field in required_fields:
                if field not in trip_data:
                    logger.error(f"Missing required field: {field}")
                    return None

            return trip_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return None

    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.client is not None


# Global instance
llm_service = LLMService()