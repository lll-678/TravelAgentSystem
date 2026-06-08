from typing import Any

from app.algorithms.compression import compress_text, compression_ratio


def run_aigc_agent(payload: dict[str, Any]) -> dict[str, Any]:
    task = str(payload.get("task") or "diary_animation")
    text = _clean_text(payload.get("text"), "从校园入口出发，记录一次完整的导览体验。")
    destination_name = _clean_text(payload.get("destination_name"), "北京邮电大学沙河校区")
    style = _clean_text(payload.get("style"), "natural")
    media_urls = _normalize_list(payload.get("media_urls"))
    scene_count = _bounded_int(payload.get("scene_count"), default=4, minimum=1, maximum=8)

    trace_steps: list[dict[str, Any]] = []

    media = _run_tool(
        trace_steps,
        tool="media_analyzer",
        input_summary=f"{len(media_urls)} media urls, destination={destination_name}",
        output=_media_analyzer(media_urls, text, destination_name),
    )
    diary = _run_tool(
        trace_steps,
        tool="diary_writer",
        input_summary=f"task={task}, style={style}, text_len={len(text)}",
        output=_diary_writer(text, destination_name, style, media),
    )
    storyboard = _run_tool(
        trace_steps,
        tool="storyboard_planner",
        input_summary=f"scene_count={scene_count}, media_count={media['media_count']}",
        output=_storyboard_planner(diary["draft"], destination_name, scene_count, media),
    )
    prompt = _run_tool(
        trace_steps,
        tool="prompt_builder",
        input_summary=f"title={diary['title']}, scenes={len(storyboard['scenes'])}",
        output=_prompt_builder(task, diary, storyboard, style, media),
    )
    video = _run_tool(
        trace_steps,
        tool="video_generator_mock",
        input_summary=f"prompt_len={len(prompt['prompt'])}, scenes={len(storyboard['scenes'])}",
        output=_video_generator_mock(destination_name, task, scene_count),
    )
    compression = _run_tool(
        trace_steps,
        tool="diary_compressor_summary",
        input_summary=f"draft_len={len(diary['draft'])}",
        output=_compression_summary(diary["draft"]),
    )

    total_duration_ms = sum(int(step["duration_ms"]) for step in trace_steps)

    return {
        "result": {
            "title": diary["title"],
            "draft": diary["draft"],
            "storyboard": storyboard["scenes"],
            "prompt": prompt["prompt"],
            "simulated_video_url": video["simulated_video_url"],
            "compression": compression,
            "media_analysis": media,
        },
        "agent_trace": {
            "steps": trace_steps,
            "total_duration_ms": total_duration_ms,
        },
        "algorithm_trace": {
            "stage": "stage-32-aigc-agent",
            "mode": "deterministic local workflow agent",
            "task": task,
            "tool_count": str(len(trace_steps)),
            "media_inputs": str(len(media_urls)),
            "scene_count": str(scene_count),
            "network": "disabled",
        },
    }


def _run_tool(
    trace_steps: list[dict[str, Any]],
    tool: str,
    input_summary: str,
    output: dict[str, Any],
) -> dict[str, Any]:
    output_summary = str(output.get("summary") or "ok")
    duration_ms = _deterministic_duration(tool, input_summary, output_summary)
    trace_steps.append(
        {
            "step": len(trace_steps) + 1,
            "tool": tool,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "status": "success",
            "duration_ms": duration_ms,
        }
    )
    return output


def _media_analyzer(media_urls: list[str], text: str, destination_name: str) -> dict[str, Any]:
    image_count = sum(1 for url in media_urls if _media_type(url) == "image")
    video_count = sum(1 for url in media_urls if _media_type(url) == "video")
    other_count = max(len(media_urls) - image_count - video_count, 0)
    keywords = _keyword_hints(" ".join([text, destination_name, " ".join(media_urls)]))
    media_keywords = []
    if image_count:
        media_keywords.append("照片素材")
    if video_count:
        media_keywords.append("视频素材")
    keywords = media_keywords + keywords
    if not keywords:
        keywords = ["校园路线", "游览体验"]
    keywords = _unique(keywords)[:6]
    summary = (
        f"识别到 {len(media_urls)} 个媒体素材，"
        f"图片 {image_count} 个、视频 {video_count} 个、其他 {other_count} 个；"
        f"关键词：{'、'.join(keywords)}。"
    )
    return {
        "media_count": len(media_urls),
        "image_count": image_count,
        "video_count": video_count,
        "other_count": other_count,
        "keywords": keywords,
        "summary": summary,
    }


def _diary_writer(text: str, destination_name: str, style: str, media: dict[str, Any]) -> dict[str, Any]:
    style_label = _style_label(style)
    focus = media["keywords"][0] if media.get("keywords") else "路线体验"
    title = f"{destination_name}：{focus}游记"
    draft = (
        f"这次我以{destination_name}为目的地，围绕{focus}完成了一次{style_label}风格的导览记录。"
        f"行程从“{_shorten(text, 44)}”展开，沿途把路线、场所和个人感受串联起来。"
        f"{media['summary']}整体体验适合整理成图文游记，并进一步生成短视频分镜。"
    )
    return {
        "title": title,
        "draft": draft,
        "summary": f"生成标题《{title}》和 {len(draft)} 字草稿。",
    }


def _storyboard_planner(
    draft: str,
    destination_name: str,
    scene_count: int,
    media: dict[str, Any],
) -> dict[str, Any]:
    themes = ["抵达目的地", "路线展开", "场所特写", "互动体验", "回顾总结", "地图转场", "媒体快闪", "发布游记"]
    keywords = media.get("keywords") or ["校园路线"]
    scenes = []
    for index in range(1, scene_count + 1):
        theme = themes[(index - 1) % len(themes)]
        keyword = keywords[(index - 1) % len(keywords)]
        scenes.append(
            {
                "index": index,
                "title": f"镜头 {index}：{theme}",
                "description": f"围绕{destination_name}的{keyword}展开画面，承接“{_shorten(draft, 32)}”。",
                "narration": f"用一句旁白说明{keyword}带来的游览感受。",
                "duration_seconds": 5 + index,
            }
        )
    return {
        "scenes": scenes,
        "summary": f"规划 {len(scenes)} 个分镜，关键词覆盖 {'、'.join(keywords[:4])}。",
    }


def _prompt_builder(
    task: str,
    diary: dict[str, Any],
    storyboard: dict[str, Any],
    style: str,
    media: dict[str, Any],
) -> dict[str, Any]:
    scene_lines = "；".join(f"{scene['index']}.{scene['title']}" for scene in storyboard["scenes"])
    prompt = (
        f"任务={task}；风格={_style_label(style)}；标题={diary['title']}；"
        f"媒体分析={media['summary']}；分镜={scene_lines}；"
        "请生成适合校园/旅游动画的画面提示词、旁白和转场建议。"
    )
    return {
        "prompt": prompt,
        "summary": f"生成 {len(prompt)} 字可复制提示词。",
    }


def _video_generator_mock(destination_name: str, task: str, scene_count: int) -> dict[str, Any]:
    slug = _slug(destination_name)
    return {
        "simulated_video_url": f"https://example.local/aigc/agent/{slug}-{task}-{scene_count}.mp4",
        "summary": "生成本地模拟视频链接，不调用外部视频模型。",
    }


def _compression_summary(draft: str) -> dict[str, Any]:
    _, original_size, compressed_size = compress_text(draft)
    ratio = compression_ratio(original_size, compressed_size)
    return {
        "algorithm": "zlib+base64 summary",
        "original_size": original_size,
        "compressed_size": compressed_size,
        "compression_ratio": ratio,
        "summary": f"草稿可无损压缩，压缩率 {ratio}。",
    }


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.replace("\n", ",").split(",") if item.strip()]
    return []


def _clean_text(value: Any, fallback: str) -> str:
    text = str(value).strip() if value is not None else ""
    return text or fallback


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return min(max(number, minimum), maximum)


def _media_type(url: str) -> str:
    lowered = url.lower()
    if lowered.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        return "image"
    if lowered.endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
        return "video"
    return "other"


def _keyword_hints(text: str) -> list[str]:
    candidates = [
        ("图书馆", "图书馆"),
        ("食堂", "食堂"),
        ("校门", "校门"),
        ("教学", "教学楼"),
        ("操场", "操场"),
        ("实验", "实验楼"),
        ("宿舍", "宿舍区"),
        ("路线", "校园路线"),
        ("沙河", "沙河校区"),
        ("校园", "校园风景"),
    ]
    return [label for needle, label in candidates if needle.lower() in text.lower()]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _style_label(style: str) -> str:
    labels = {
        "natural": "自然",
        "lively": "轻快",
        "formal": "正式",
        "cinematic": "电影感",
        "自然": "自然",
        "轻松": "轻快",
        "正式": "正式",
    }
    return labels.get(style, style)


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _slug(text: str) -> str:
    if "北京邮电大学" in text or "北邮" in text:
        return "bupt-shahe"
    if "沙河" in text:
        return "shahe-campus"
    return "tour-destination"


def _deterministic_duration(tool: str, input_summary: str, output_summary: str) -> int:
    return 8 + (len(tool) * 3 + len(input_summary) + len(output_summary)) % 37
